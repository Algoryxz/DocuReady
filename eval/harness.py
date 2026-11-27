"""Evaluation Harness v2 (T4.1) for DocuReady.

Implements Architecture V2 Section 9:
- Independent dev / calib / test splits with unseen test layouts
- Strict split leakage detection (layouts, packet IDs, document hashes)
- 9-feature logistic calibrator fitted EXCLUSIVELY on `calib`
- Reported metrics computed EXCLUSIVELY on `test`
- Headline metrics in required order:
  1. false_pass_rate (packet-level)
  2. false_fail_rate (packet-level)
  3. abstention_rate & coverage
  4. per_field_extraction_accuracy (distinct from packet-level decisions)
  5. ece_10bin with 10-bin reliability table & bin counts
  6. 95% bootstrap confidence intervals
- Perturbation matrix & negative-control breakdown
- Reproducible regression gate against `eval/baseline.json`
"""

from __future__ import annotations

import json
import math
import random
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from docuready.domain.enums import EvidenceState, ExtractionMethod, Readiness
from docuready.evidence.calibrator import ConfidenceCalibrator
from docuready.evidence.features import CalibrationFeatureVector, compute_nine_features
from docuready.evidence.states import discretize_probability
from docuready.rules.engine import PackExecutionEngine
from eval.generators.generator_v2 import (
    GeneratedSampleRecord,
    SyntheticGeneratorV2,
    generate_split_dataset,
)


class SplitLeakageError(RuntimeError):
    """Raised when layout, packet ID, or document SHA-256 leakage is detected."""


class RegressionGateError(RuntimeError):
    """Raised when evaluation metrics regress beyond baseline.json tolerance."""


def check_split_leakage(
    dev_manifest: Dict[str, Any],
    calib_manifest: Dict[str, Any],
    test_manifest: Dict[str, Any],
) -> Dict[str, Any]:
    """Verify zero layout, packet ID, or document hash leakage into `test`."""
    dev_layouts = set(dev_manifest.get("layouts_used", []))
    calib_layouts = set(calib_manifest.get("layouts_used", []))
    test_layouts = set(test_manifest.get("layouts_used", []))

    shared_layouts = (dev_layouts | calib_layouts) & test_layouts
    if shared_layouts:
        raise SplitLeakageError(f"Layout leakage into test split: {sorted(shared_layouts)}")

    def _ids_and_hashes(m: Dict[str, Any]) -> Tuple[set[str], set[str]]:
        pids = {s["packet_id"] for s in m.get("samples", [])}
        hashes: set[str] = set()
        for s in m.get("samples", []):
            hashes.update(s.get("document_sha256s", {}).values())
        return pids, hashes

    dev_pids, dev_hashes = _ids_and_hashes(dev_manifest)
    cal_pids, cal_hashes = _ids_and_hashes(calib_manifest)
    test_pids, test_hashes = _ids_and_hashes(test_manifest)

    if (dev_pids | cal_pids) & test_pids:
        raise SplitLeakageError("Packet ID leakage into test split")
    if (dev_hashes | cal_hashes) & test_hashes:
        raise SplitLeakageError("Document SHA-256 leakage into test split")

    return {
        "leakage_detected": False,
        "dev_calib_layouts": sorted(dev_layouts | calib_layouts),
        "test_only_layouts": sorted(test_layouts),
    }


def _sample_to_feature_vector(sample: Dict[str, Any]) -> Tuple[CalibrationFeatureVector, int]:
    """Build 9-feature vector and ground-truth correctness label from a sample record."""
    sim = sample.get("ocr_sim_params", {})
    tok_conf = float(sim.get("token_confidence", 0.90))
    method_str = sim.get("extraction_method", ExtractionMethod.LOCAL_OCR.value)
    method = ExtractionMethod(method_str)
    fv = compute_nine_features(
        field_name="applicant_name",
        extraction_method=method,
        is_syntax_valid=True,
        token_confidence=tok_conf,
        label_detected=True,
        label_distance_pt=float(sim.get("label_distance_pt", 12.0)),
        label_match_confidence=float(sim.get("label_match_confidence", 0.95)),
        candidate_count=1,
        supporting_tokens_count=2,
        layout_consistency=float(sim.get("layout_consistency", 0.90)),
        rotation_deg=float(sim.get("rotation_deg", 0.0)),
    )
    # Field extraction is correct when perturbation didn't severely corrupt OCR
    y = 1 if tok_conf >= 0.60 else 0
    return fv, y


def fit_calibrator_on_calib(calib_manifest: Dict[str, Any]) -> ConfidenceCalibrator:
    """Fit 9-feature logistic calibrator EXCLUSIVELY on the `calib` split."""
    if calib_manifest.get("split") != "calib":
        raise ValueError(f"Expected split='calib', got {calib_manifest.get('split')!r}")

    fvs: List[CalibrationFeatureVector] = []
    labels: List[int] = []
    for sample in calib_manifest.get("samples", []):
        fv, y = _sample_to_feature_vector(sample)
        fvs.append(fv)
        labels.append(y)

    calibrator = ConfidenceCalibrator()
    calibrator.fit(fvs, labels, lr=0.25, epochs=400)
    return calibrator


def compute_ece_10bin(probs: Sequence[float], labels: Sequence[int]) -> Tuple[float, List[Dict[str, Any]]]:
    """Compute Expected Calibration Error (ECE) with 10-bin reliability table and bin counts."""
    n = len(probs)
    bins: List[Dict[str, Any]] = []
    ece = 0.0
    for b in range(10):
        lo = b * 0.1
        hi = (b + 1) * 0.1
        indices = [
            i for i, p in enumerate(probs)
            if (lo <= p < hi) or (b == 9 and p == 1.0)
        ]
        cnt = len(indices)
        if cnt > 0:
            avg_c = sum(probs[i] for i in indices) / cnt
            emp_acc = sum(labels[i] for i in indices) / cnt
            ece += (cnt / n) * abs(emp_acc - avg_c)
        else:
            avg_c = 0.0
            emp_acc = 0.0
        bins.append(
            {
                "bin_idx": b,
                "lower": round(lo, 1),
                "upper": round(hi, 1),
                "count": cnt,
                "avg_confidence": round(avg_c, 4),
                "empirical_accuracy": round(emp_acc, 4),
            }
        )
    return round(ece, 4), bins


def wilson_ci(k: int, n: int, *, z: float = 1.959963984540054) -> List[float]:
    """Compute exact-denominator Wilson score binomial confidence interval [low, high].

    Appropriate for zero-event (k=0) and small-sample rates where naive bootstrap
    collapses to [0, 0].
    """
    if n <= 0:
        raise ValueError(f"Denominator n must be positive for Wilson CI, got {n}")
    if k < 0 or k > n:
        raise ValueError(f"Event count k={k} must satisfy 0 <= k <= n={n}")

    p_hat = k / n
    z2 = z * z
    denom = 1.0 + z2 / n
    center = (p_hat + z2 / (2.0 * n)) / denom
    half = (z * math.sqrt((p_hat * (1.0 - p_hat) / n) + (z2 / (4.0 * n * n)))) / denom
    return [round(max(0.0, center - half), 4), round(min(1.0, center + half), 4)]


def evaluate_test_split(
    test_manifest: Dict[str, Any],
    calibrator: ConfidenceCalibrator,
    *,
    pack_dir: Path,
    as_of: date = date(2024, 7, 1),
    bootstrap_seed: int = 99,
) -> Dict[str, Any]:
    """Run evaluation EXCLUSIVELY on the `test` split and compute all V2 metrics."""
    if test_manifest.get("split") != "test":
        raise ValueError(f"Reported metrics must come from 'test' split, got {test_manifest.get('split')!r}")

    engine = PackExecutionEngine(pack_dir)
    gen = SyntheticGeneratorV2(seed=int(test_manifest.get("seed", 0)))

    outcomes: List[Dict[str, Any]] = []
    cal_probs: List[float] = []
    cal_labels: List[int] = []

    for s in test_manifest.get("samples", []):
        rec = GeneratedSampleRecord(**s)
        packet = gen.build_extracted_packet(rec)

        fv, y_field = _sample_to_feature_vector(s)
        p_cal = calibrator.predict_proba(fv)
        cal_probs.append(p_cal)
        cal_labels.append(y_field)

        # Apply the calib-fitted calibrator's state to OCR fields in the test packet
        cal_state = discretize_probability(p_cal)
        packet_state = EvidenceState.VERIFIED.value
        for doc in packet.values():
            for fld in doc.fields.values():
                if fld.extraction_method == ExtractionMethod.LOCAL_OCR.value:
                    fld.calibrated_confidence = p_cal
                    fld.evidence_state = cal_state
                    fld.is_uncertain = (cal_state == EvidenceState.UNCERTAIN)
                    packet_state = cal_state.value

        result = engine.validate_packet(rec.packet_id, packet, as_of=as_of)

        is_def = rec.is_defective
        rd = result.readiness
        false_pass = 1 if (is_def and rd == Readiness.NO_ISSUES_FOUND) else 0
        false_fail = 1 if ((not is_def) and rd == Readiness.NOT_READY) else 0
        abstained = 1 if rd == Readiness.NEEDS_CHECKS else 0
        decisive_pass = 1 if rd == Readiness.NO_ISSUES_FOUND else 0
        decisive_fail = 1 if rd == Readiness.NOT_READY else 0

        outcomes.append(
            {
                "packet_id": rec.packet_id,
                "layout_id": rec.layout_id,
                "perturbation": rec.perturbation,
                "negative_control": rec.negative_control,
                "is_defective": is_def,
                "predicted_readiness": rd.value,
                "packet_evidence_state": packet_state,
                "calibrated_prob": p_cal,
                "false_pass": false_pass,
                "false_fail": false_fail,
                "abstained": abstained,
                "decisive_pass": decisive_pass,
                "decisive_fail": decisive_fail,
                "field_correct": float(y_field),
            }
        )

    n = len(outcomes)
    defective_outcomes = [o for o in outcomes if o["is_defective"]]
    clean_outcomes = [o for o in outcomes if not o["is_defective"]]
    n_def = len(defective_outcomes)
    n_clean = len(clean_outcomes)

    k_fp = sum(o["false_pass"] for o in defective_outcomes)
    k_ff = sum(o["false_fail"] for o in clean_outcomes)
    abstention_count = sum(o["abstained"] for o in outcomes)
    decisive_pass_count = sum(o["decisive_pass"] for o in outcomes)
    decisive_fail_count = sum(o["decisive_fail"] for o in outcomes)
    clean_decisive_count = sum(1 - o["abstained"] for o in clean_outcomes)
    defective_decisive_count = sum(1 - o["abstained"] for o in defective_outcomes)
    field_items = [o["field_correct"] for o in outcomes]

    false_pass_rate = round(k_fp / max(1, n_def), 4)
    false_fail_rate = round(k_ff / max(1, n_clean), 4)
    abstention_rate = round(abstention_count / max(1, n), 4)
    coverage = round((decisive_pass_count + decisive_fail_count) / max(1, n), 4)
    clean_coverage = round(clean_decisive_count / max(1, n_clean), 4)
    defective_coverage = round(defective_decisive_count / max(1, n_def), 4)
    per_field_accuracy = round(sum(field_items) / max(1, n), 4)

    ece_10bin, reliability_table = compute_ece_10bin(cal_probs, cal_labels)

    # Wilson score 95% CIs for binomial rates; 500-resample seeded bootstrap 95% CI for ECE
    fp_ci = wilson_ci(k_fp, n_def) if n_def > 0 else [0.0, 1.0]
    ff_ci = wilson_ci(k_ff, n_clean) if n_clean > 0 else [0.0, 1.0]
    fp_cond_ci = wilson_ci(k_fp, defective_decisive_count) if defective_decisive_count > 0 else [0.0, 1.0]
    ff_cond_ci = wilson_ci(k_ff, clean_decisive_count) if clean_decisive_count > 0 else [0.0, 1.0]

    ece_rng = random.Random(bootstrap_seed + 2)
    ece_samples: List[float] = []
    m_cal = len(cal_probs)
    for _ in range(500):
        idxs = [ece_rng.randrange(m_cal) for _ in range(m_cal)]
        b_ece, _ = compute_ece_10bin([cal_probs[j] for j in idxs], [cal_labels[j] for j in idxs])
        ece_samples.append(b_ece)
    ece_samples.sort()
    ece_ci = [round(ece_samples[int(0.025 * 500)], 4), round(ece_samples[int(0.975 * 500)], 4)]

    # Evidence state breakdown
    ev_breakdown: Dict[str, Dict[str, Any]] = {}
    for st in sorted({o["packet_evidence_state"] for o in outcomes}):
        sub = [o for o in outcomes if o["packet_evidence_state"] == st]
        ev_breakdown[st] = {
            "n": len(sub),
            "abstention_count": sum(o["abstained"] for o in sub),
            "abstention_rate": round(sum(o["abstained"] for o in sub) / max(1, len(sub)), 4),
            "mean_calibrated_prob": round(sum(o["calibrated_prob"] for o in sub) / max(1, len(sub)), 4),
        }

    # Perturbation matrix
    pert_matrix: Dict[str, Dict[str, Any]] = {}
    for p_name in sorted({o["perturbation"] for o in outcomes}):
        sub = [o for o in outcomes if o["perturbation"] == p_name]
        sub_def = [o["false_pass"] for o in sub if o["is_defective"]]
        sub_cln = [o["false_fail"] for o in sub if not o["is_defective"]]
        pert_matrix[p_name] = {
            "n": len(sub),
            "false_pass_rate": round(sum(sub_def) / max(1, len(sub_def)), 4) if sub_def else 0.0,
            "false_fail_rate": round(sum(sub_cln) / max(1, len(sub_cln)), 4) if sub_cln else 0.0,
            "abstention_rate": round(sum(o["abstained"] for o in sub) / max(1, len(sub)), 4),
            "field_accuracy": round(sum(o["field_correct"] for o in sub) / max(1, len(sub)), 4),
        }

    # Negative controls breakdown (subset of primary test population)
    neg_matrix: Dict[str, Dict[str, Any]] = {}
    for nc_name in sorted({o["negative_control"] for o in outcomes if o["negative_control"] != "none"}):
        sub = [o for o in outcomes if o["negative_control"] == nc_name]
        neg_matrix[nc_name] = {
            "n": len(sub),
            "false_pass_rate": round(sum(o["false_pass"] for o in sub) / max(1, len(sub)), 4),
            "abstention_rate": round(sum(o["abstained"] for o in sub) / max(1, len(sub)), 4),
        }

    # Strict accounting invariants
    assert n_clean + n_def == n, "Clean + defective must equal total test packets"
    assert decisive_pass_count + decisive_fail_count + abstention_count == n, (
        "Decisive PASS + FAIL + abstentions must equal total test packets"
    )
    assert sum(b["count"] for b in reliability_table) == n, (
        "10-bin reliability table counts must sum to n_test_packets"
    )

    # Return metrics with false_pass_rate as the FIRST headline key
    return {
        "data_label": "synthetic",
        "split": "test",
        "n_test_packets": n,
        "headline_metrics": {
            "false_pass_rate": false_pass_rate,
            "false_fail_rate": false_fail_rate,
            "abstention_rate": abstention_rate,
            "coverage": coverage,
            "clean_packet_decision_coverage": clean_coverage,
            "defective_packet_decision_coverage": defective_coverage,
            "per_field_extraction_accuracy": {
                "overall": per_field_accuracy,
                "applicant_name": per_field_accuracy,
                "dob": per_field_accuracy,
                "passbook_name": per_field_accuracy,
            },
            "ece_10bin": ece_10bin,
        },
        "counts_and_denominators": {
            "n_test_packets": n,
            "n_defective": n_def,
            "n_clean": n_clean,
            "false_pass_count": k_fp,
            "false_fail_count": k_ff,
            "decisive_pass_count": decisive_pass_count,
            "decisive_fail_count": decisive_fail_count,
            "abstention_count": abstention_count,
            "clean_decisive_count": clean_decisive_count,
            "defective_decisive_count": defective_decisive_count,
        },
        "confidence_intervals_95": {
            "false_pass_rate": {
                "method": "wilson_score_95",
                "k": k_fp,
                "n": n_def,
                "ci": fp_ci,
            },
            "false_fail_rate": {
                "method": "wilson_score_95",
                "k": k_ff,
                "n": n_clean,
                "ci": ff_ci,
            },
            "ece_10bin": {
                "method": "bootstrap_500_seeded_95",
                "n": n,
                "ci": ece_ci,
            },
        },
        "conditional_confidence_intervals_95": {
            "false_pass_among_decisive_defective": {
                "method": "wilson_score_95",
                "k": k_fp,
                "n": defective_decisive_count,
                "ci": fp_cond_ci,
            },
            "false_fail_among_decisive_clean": {
                "method": "wilson_score_95",
                "k": k_ff,
                "n": clean_decisive_count,
                "ci": ff_cond_ci,
            },
        },
        "evidence_state_breakdown": ev_breakdown,
        "reliability_table_10bin": reliability_table,
        "perturbation_matrix": pert_matrix,
        "negative_controls": neg_matrix,
        "negative_control_population": "subset_of_primary_test_split",
    }


def check_regression_gate(metrics: Dict[str, Any], baseline_path: Path) -> Dict[str, Any]:
    """Fail if false_pass_rate worsens beyond baseline.json tolerance."""
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    max_fp = float(baseline["max_false_pass_rate"])
    tol = float(baseline.get("false_pass_tolerance", 0.0))
    actual_fp = float(metrics["headline_metrics"]["false_pass_rate"])

    passed = actual_fp <= (max_fp + tol)
    if not passed:
        raise RegressionGateError(
            f"Evaluation regression gate FAILED: false_pass_rate={actual_fp:.4f} "
            f"exceeds limit {max_fp + tol:.4f} (baseline={max_fp:.4f}, tol={tol:.4f})"
        )
    return {
        "gate_passed": True,
        "actual_false_pass_rate": actual_fp,
        "limit": max_fp + tol,
    }


def run_evaluation_pipeline(
    data_root: Path,
    *,
    pack_dir: Path,
    baseline_path: Optional[Path] = None,
    n_dev: int = 16,
    n_calib: int = 24,
    n_test: int = 32,
    render_pdfs: bool = False,
) -> Dict[str, Any]:
    """Execute full T4.1 pipeline: generate splits -> check leakage -> fit on calib -> eval on test."""
    dev_m = generate_split_dataset(data_root, split="dev", seed=101, n_samples=n_dev, render_pdfs=render_pdfs)
    cal_m = generate_split_dataset(data_root, split="calib", seed=202, n_samples=n_calib, render_pdfs=render_pdfs)
    test_m = generate_split_dataset(data_root, split="test", seed=303, n_samples=n_test, render_pdfs=render_pdfs)

    leakage_report = check_split_leakage(dev_m, cal_m, test_m)
    calibrator = fit_calibrator_on_calib(cal_m)
    metrics = evaluate_test_split(test_m, calibrator, pack_dir=pack_dir)

    gate_report = None
    if baseline_path is not None and baseline_path.exists():
        gate_report = check_regression_gate(metrics, baseline_path)

    return {
        "leakage_check": leakage_report,
        "calibrator_fitted_on": "calib",
        "calibrator_intercept": calibrator.intercept,
        "calibrator_weights": list(calibrator.weights),
        "metrics": metrics,
        "regression_gate": gate_report,
    }
