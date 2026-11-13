"""
Comprehensive Multi-Mode Extraction and Calibration Evaluation Script for DocuReady Loop 3
Evaluates 100 held-out document samples across 3 operating modes:
- Mode A: Current Uncalibrated (Loop 2 behavior)
- Mode B: Conservative Hard-Abstain (tau = 0.85)
- Mode C: Label-Aware Calibrated Fallback (tau = 0.70, abstain = 0.45)

Measures:
- Exact-Match Accuracy
- Normalized-Match Accuracy
- False Accept Rate (FAR)
- False Reject Rate (FRR)
- Abstention Rate
- Expected Calibration Error (ECE)
- Latency per page
"""

import os
import json
import time
from collections import defaultdict
from typing import Dict, Any, List, Tuple
import math

from src.models import DocumentType, ExtractionMethod, EvidenceState
from src.extractor import DocumentExtractor
from src.normalizer import (
    normalize_name, normalize_income, normalize_cert_number,
    parse_and_normalize_date, validate_ifsc_code
)

GROUND_TRUTH_PATH = "docuready-mvp/HELD_OUT_GROUND_TRUTH.json"
RESULTS_OUTPUT_PATH = "docuready-mvp/EVALUATION_RESULTS_MODES.json"


def evaluate_field_match(
    field_name: str,
    extracted_val: Any,
    norm_val: Any,
    expected_raw: Any,
    expected_norm: Any
) -> Tuple[bool, bool]:
    """
    Returns (is_exact_match, is_norm_match).
    """
    if extracted_val is None or str(extracted_val).strip() == "":
        return False, False

    clean_ext = str(extracted_val).strip()
    clean_exp = str(expected_raw).strip()

    # Exact match (case insensitive)
    is_exact = clean_ext.upper() == clean_exp.upper()

    # Normalized match
    is_norm = False
    if field_name == "applicant_name":
        ext_n = normalize_name(clean_ext)
        exp_n = normalize_name(clean_exp)
        is_norm = ext_n == exp_n
    elif "income" in field_name:
        ext_inc = normalize_income(clean_ext)
        exp_inc = float(expected_norm) if expected_norm is not None else normalize_income(clean_exp)
        if ext_inc is not None and exp_inc is not None:
            is_norm = abs(ext_inc - exp_inc) < 1.0
    elif "date" in field_name or field_name == "dob":
        ext_d, _, _ = parse_and_normalize_date(clean_ext)
        exp_d, _, _ = parse_and_normalize_date(clean_exp)
        is_norm = (ext_d is not None and ext_d == exp_d)
    elif "cert_no" in field_name or "certificate_no" in field_name:
        ext_c = normalize_cert_number(clean_ext)
        exp_c = normalize_cert_number(clean_exp)
        is_norm = ext_c == exp_c
    elif field_name == "percentage":
        try:
            import re
            m1 = re.search(r"[\d.]+", clean_ext)
            m2 = re.search(r"[\d.]+", clean_exp)
            if m1 and m2:
                is_norm = abs(float(m1.group(0)) - float(m2.group(0))) < 0.2
        except Exception:
            is_norm = False
    elif field_name == "ifsc":
        is_norm = clean_ext.upper().replace(" ", "") == clean_exp.upper().replace(" ", "")
    else:
        is_norm = clean_ext.upper() == clean_exp.upper()

    return is_exact, is_norm


def compute_ece(confidences: List[float], accuracies: List[int], n_bins: int = 10) -> float:
    """
    Computes Expected Calibration Error (ECE) across n_bins.
    """
    if not confidences or len(confidences) != len(accuracies):
        return 0.0

    total_samples = len(confidences)
    bin_boundaries = [i / n_bins for i in range(n_bins + 1)]
    ece = 0.0

    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]

        # Gather samples in bin
        bin_indices = [
            idx for idx, c in enumerate(confidences)
            if (bin_lower <= c < bin_upper) or (i == n_bins - 1 and bin_lower <= c <= bin_upper)
        ]
        bin_size = len(bin_indices)
        if bin_size > 0:
            bin_acc = sum(accuracies[idx] for idx in bin_indices) / bin_size
            bin_conf = sum(confidences[idx] for idx in bin_indices) / bin_size
            ece += (bin_size / total_samples) * abs(bin_acc - bin_conf)

    return round(ece, 4)


def run_evaluation():
    with open(GROUND_TRUTH_PATH, "r", encoding="utf-8") as f:
        ground_truth_data = json.load(f)

    samples = ground_truth_data.get("samples", [])
    print(f"Loaded {len(samples)} samples from {GROUND_TRUTH_PATH}")

    modes = {
        "Mode A: Uncalibrated (Loop 2)": {
            "operating_mode": "CURRENT_UNCALIBRATED",
            "low_conf_threshold": 0.0,
            "tau_abstain": 0.0
        },
        "Mode B: Conservative Abstain (tau=0.85)": {
            "operating_mode": "CONSERVATIVE_ABSTAIN",
            "low_conf_threshold": 0.85,
            "tau_abstain": 0.85
        },
        "Mode C: Calibrated Label-Aware": {
            "operating_mode": "CALIBRATED_LABEL_AWARE",
            "low_conf_threshold": 0.70,
            "tau_abstain": 0.45
        }
    }

    all_mode_results = {}

    for mode_name, mode_cfg in modes.items():
        print(f"\n==================================================")
        print(f"Evaluating {mode_name} ...")
        print(f"==================================================")

        extractor = DocumentExtractor(
            dpi=200,
            low_conf_threshold=mode_cfg["low_conf_threshold"],
            tau_abstain=mode_cfg["tau_abstain"],
            operating_mode=mode_cfg["operating_mode"]
        )

        total_samples = len(samples)
        exact_matches = 0
        norm_matches = 0
        abstained_count = 0
        false_accepts = 0
        false_rejects = 0
        latencies_ms = []

        confidences = []
        accuracies = []

        category_stats = defaultdict(lambda: {
            "total": 0, "exact": 0, "norm": 0, "abstained": 0, "false_accept": 0
        })

        field_stats = defaultdict(lambda: {
            "total": 0, "exact": 0, "norm": 0, "abstained": 0, "false_accept": 0
        })

        for sample in samples:
            file_path = sample["file_path"]
            target_field = sample["target_field"]
            expected_raw = sample["ground_truth_raw"]
            expected_norm = sample["ground_truth_normalized"]
            category = sample["category"]

            t0 = time.perf_counter()
            doc = extractor.extract_document(file_path)
            elap_ms = (time.perf_counter() - t0) * 1000.0
            latencies_ms.append(elap_ms)

            fld = doc.fields.get(target_field)

            category_stats[category]["total"] += 1
            field_stats[target_field]["total"] += 1

            if not fld or fld.raw_value is None or str(fld.raw_value).strip() == "":
                # Abstained
                abstained_count += 1
                category_stats[category]["abstained"] += 1
                field_stats[target_field]["abstained"] += 1

                # If it was clean vector or clean scan, abstaining might be a false reject
                if category in ["CLEAN_VECTOR", "RASTER_SCAN_CLEAN"]:
                    false_rejects += 1
            else:
                is_exact, is_norm = evaluate_field_match(
                    field_name=target_field,
                    extracted_val=fld.raw_value,
                    norm_val=fld.normalized_value,
                    expected_raw=expected_raw,
                    expected_norm=expected_norm
                )

                conf = fld.calibrated_confidence if fld.calibrated_confidence is not None else 0.50
                confidences.append(conf)
                accuracies.append(1 if is_norm else 0)

                if is_exact:
                    exact_matches += 1
                    category_stats[category]["exact"] += 1
                    field_stats[target_field]["exact"] += 1

                if is_norm:
                    norm_matches += 1
                    category_stats[category]["norm"] += 1
                    field_stats[target_field]["norm"] += 1
                else:
                    # Model returned a value, but it was incorrect -> False Accept!
                    false_accepts += 1
                    category_stats[category]["false_accept"] += 1
                    field_stats[target_field]["false_accept"] += 1

        ece = compute_ece(confidences, accuracies, n_bins=10)
        mean_lat_ms = sum(latencies_ms) / len(latencies_ms) if latencies_ms else 0.0

        exact_acc_pct = round(100.0 * exact_matches / total_samples, 2)
        norm_acc_pct = round(100.0 * norm_matches / total_samples, 2)
        abstain_pct = round(100.0 * abstained_count / total_samples, 2)
        far_pct = round(100.0 * false_accepts / total_samples, 2)
        frr_pct = round(100.0 * false_rejects / total_samples, 2)
        coverage_pct = round(100.0 * (total_samples - abstained_count) / total_samples, 2)
        precision_on_covered = round(100.0 * norm_matches / (total_samples - abstained_count), 2) if (total_samples - abstained_count) > 0 else 0.0

        mode_summary = {
            "mode_name": mode_name,
            "total_samples": total_samples,
            "exact_match_pct": exact_acc_pct,
            "normalized_match_pct": norm_acc_pct,
            "coverage_pct": coverage_pct,
            "precision_on_covered_pct": precision_on_covered,
            "abstention_pct": abstain_pct,
            "false_accept_pct": far_pct,
            "false_reject_pct": frr_pct,
            "ece": ece,
            "mean_latency_ms": round(mean_lat_ms, 2),
            "category_breakdown": dict(category_stats),
            "field_breakdown": dict(field_stats)
        }

        all_mode_results[mode_name] = mode_summary

        print(f"Results for {mode_name}:")
        print(f"  Exact Match Acc:      {exact_acc_pct}% ({exact_matches}/{total_samples})")
        print(f"  Normalized Match Acc: {norm_acc_pct}% ({norm_matches}/{total_samples})")
        print(f"  Coverage:             {coverage_pct}%")
        print(f"  Precision on Covered: {precision_on_covered}%")
        print(f"  Abstention Rate:      {abstain_pct}% ({abstained_count}/{total_samples})")
        print(f"  False Accept Rate:    {far_pct}% ({false_accepts}/{total_samples})")
        print(f"  False Reject Rate:    {frr_pct}%")
        print(f"  Expected Calib Error: {ece}")
        print(f"  Mean Page Latency:    {mean_lat_ms:.1f} ms")

    with open(RESULTS_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(all_mode_results, f, indent=2)

    print(f"\nAll mode results saved to {RESULTS_OUTPUT_PATH}")


if __name__ == "__main__":
    run_evaluation()
