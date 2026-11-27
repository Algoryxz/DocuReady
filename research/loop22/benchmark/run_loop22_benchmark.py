"""
Loop 22 Evidence Association Reliability & Risk-Calibrated Abstention Benchmark
Evaluates DocuReady across all 46 documents (83 Loop 21 + 12 Loop 22 = 95 critical fields) across 7 cohorts:
  A_development (8 docs)
  B_validation (8 docs)
  C_blind_evaluation (10 docs)
  D_challenge_adversarial (8 docs)
  E_hierarchical_headers (3 docs)
  F_decimal_integrity (3 docs)
  G_evidence_association (6 docs)

Enforces closed accounting ledger:
  Total Eligible Fields = Verified Claims + Abstained Fields
  Verified Claims = Correct Verifications + False Verifications
  Coverage = Verified Claims / Total Eligible Fields
  Abstention Rate = Abstained Fields / Total Eligible Fields
  Critical Field Precision (CFP) = Correct Verifications / Verified Claims
  False Verification Rate (FVR) = False Verifications / Verified Claims
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pytesseract
from PIL import Image

from docuready.ingest.tesseract_discovery import configure_pytesseract
from docuready.ingest.table_association import (
    build_table_grid,
    extract_field_by_spatial_association,
    FieldEvidence,
    TableGrid,
)

ROOT = Path(__file__).resolve().parents[3]
L20_DIR = ROOT / "research" / "loop20"
L21_DIR = ROOT / "research" / "loop21"
L22_DIR = ROOT / "research" / "loop22"
RESULTS_DIR = L22_DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def evaluate_field(
    grid: TableGrid,
    field_spec: Dict[str, Any],
    doc_id: str,
    page_text: str,
    img: Optional[Image.Image] = None,
    conf_threshold: float = 60.0,
) -> Dict[str, Any]:
    field_name = field_spec["name"]
    expected_val = str(field_spec["expected"]).strip()
    exp_row = field_spec.get("row")
    exp_col = field_spec.get("col")
    field_type = field_spec.get("type", "text")
    target_pattern = field_spec.get("target_pattern", "")
    col_pattern = field_spec.get("col_pattern")

    # Baseline Substring Match (BSM)
    bsm_pass = (expected_val != "" and expected_val in page_text) or (expected_val == "" and True)

    evidence: Optional[FieldEvidence] = None
    if target_pattern:
        evidence = extract_field_by_spatial_association(
            grid=grid,
            field_name=field_name,
            target_pattern=target_pattern,
            col_pattern=col_pattern,
            col_idx=exp_col,
            expected_type=field_type,
            doc_id=doc_id,
            image=img,
        )

    # 1. Expected Empty Cell Case
    if expected_val == "":
        if evidence is None or evidence.value == "":
            status = "PASS_EMPTY_CORRECT"
            is_sem = True
            is_verified = False
            is_false_verification = False
            is_abstained = True
            abstention_reason = "Empty cell correctly preserved without spurious value inheritance"
        else:
            status = f"FAIL_SPURIOUS_VALUE (got: '{evidence.value}')"
            is_sem = False
            is_verified = True
            is_false_verification = True
            is_abstained = False
            abstention_reason = None

        return {
            "field_name": field_name,
            "expected": expected_val,
            "extracted_value": evidence.value if evidence else "",
            "status": status,
            "sem_pass": is_sem,
            "bsm_pass": bsm_pass,
            "is_verified": is_verified,
            "is_false_verification": is_false_verification,
            "is_abstained": is_abstained,
            "abstention_reason": abstention_reason,
            "row_match": True,
            "col_match": True,
            "row": evidence.row_idx if evidence else -1,
            "col": evidence.col_idx if evidence else -1,
            "confidence": evidence.confidence if evidence else 0.0,
            "is_ambiguous": evidence.is_ambiguous if evidence else False,
            "bbox": evidence.bbox if evidence else [0, 0, 0, 0],
            "traceable": (evidence is not None and evidence.bbox != (0, 0, 0, 0)),
        }

    # 2. Expected Non-Empty Field Case
    if evidence is None:
        status = "ABSTAIN_NOT_EXTRACTED"
        is_sem = False
        is_verified = False
        is_false_verification = False
        is_abstained = True
        abstention_reason = "No candidate cell identified for target pattern"
        ext_val = ""
        row_match = False
        col_match = False
    else:
        ext_val = evidence.value.strip()
        norm_ext = ext_val.replace("₹", "").replace("Rs.", "").replace(",", "").strip()
        norm_exp = expected_val.replace("₹", "").replace("Rs.", "").replace(",", "").strip()

        row_match = (exp_row is None or evidence.row_idx == exp_row or evidence.row_idx == exp_row + 1)
        col_match = (exp_col is None or evidence.col_idx == exp_col)

        # Risk-Calibrated Trust & Abstention Policy
        # Check if evidence should be abstained based on confidence threshold sweep or flagged ambiguity
        should_abstain = (
            evidence.is_ambiguous or
            evidence.verification_decision == "ABSTAIN" or
            evidence.confidence < conf_threshold
        )

        if should_abstain:
            reason = evidence.abstention_reason or f"Confidence below threshold ({evidence.confidence:.1f} < {conf_threshold:.1f})"
            status = f"ABSTAIN_FILTERED (val='{ext_val}', reason='{reason}')"
            is_sem = (norm_ext == norm_exp and row_match and col_match)  # Record if spatial match would have occurred
            is_verified = False
            is_false_verification = False
            is_abstained = True
            abstention_reason = reason
        elif norm_ext == norm_exp and row_match and col_match:
            status = "PASS_SPATIAL_EXACT"
            is_sem = True
            is_verified = True
            is_false_verification = False
            is_abstained = False
            abstention_reason = None
        elif norm_ext == norm_exp and (not row_match or not col_match):
            status = f"FAIL_WRONG_COORDINATE (row={evidence.row_idx} vs exp={exp_row}, col={evidence.col_idx} vs exp={exp_col})"
            is_sem = False
            is_verified = True
            is_false_verification = True
            is_abstained = False
            abstention_reason = None
        else:
            status = f"FAIL_MISMATCH (got: '{ext_val}')"
            is_sem = False
            is_verified = True
            is_false_verification = True
            is_abstained = False
            abstention_reason = None

    return {
        "field_name": field_name,
        "expected": expected_val,
        "extracted_value": ext_val,
        "status": status,
        "sem_pass": is_sem,
        "bsm_pass": bsm_pass,
        "is_verified": is_verified,
        "is_false_verification": is_false_verification,
        "is_abstained": is_abstained,
        "abstention_reason": abstention_reason,
        "row_match": row_match,
        "col_match": col_match,
        "row": evidence.row_idx if evidence else -1,
        "col": evidence.col_idx if evidence else -1,
        "confidence": evidence.confidence if evidence else 0.0,
        "is_ambiguous": evidence.is_ambiguous if evidence else False,
        "bbox": evidence.bbox if evidence else [0, 0, 0, 0],
        "traceable": (evidence is not None and evidence.bbox != (0, 0, 0, 0)),
    }


def run_benchmark() -> Dict[str, Any]:
    configure_pytesseract()

    # Load Loop 20, 21, and 22 manifests
    with open(L20_DIR / "dataset_manifest.json", "r", encoding="utf-8") as f:
        l20_manifest = json.load(f)

    with open(L21_DIR / "dataset_manifest.json", "r", encoding="utf-8") as f:
        l21_manifest = json.load(f)

    with open(L22_DIR / "dataset_manifest.json", "r", encoding="utf-8") as f:
        l22_manifest = json.load(f)

    all_docs = {}
    doc_paths = {}

    for doc_id, meta in l20_manifest["documents"].items():
        all_docs[doc_id] = meta
        doc_paths[doc_id] = L20_DIR / "tables" / f"{doc_id}.png"

    for doc_id, meta in l21_manifest["documents"].items():
        all_docs[doc_id] = meta
        doc_paths[doc_id] = L21_DIR / "tables" / f"{doc_id}.png"

    for doc_id, meta in l22_manifest["documents"].items():
        all_docs[doc_id] = meta
        doc_paths[doc_id] = L22_DIR / "tables" / f"{doc_id}.png"

    cohorts = [
        "A_development",
        "B_validation",
        "C_blind_evaluation",
        "D_challenge_adversarial",
        "E_hierarchical_headers",
        "F_decimal_integrity",
        "G_evidence_association",
    ]

    results: Dict[str, Any] = {
        "benchmark_name": "Loop 22 Evidence Association Reliability & Risk-Calibrated Abstention Benchmark",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_documents": len(all_docs),
        "per_cohort": {
            c: {
                "total_docs": 0,
                "total_fields": 0,
                "sem_passes": 0,
                "false_verifications": 0,
                "abstentions": 0,
                "verified_claims": 0,
                "latencies": [],
                "overheads": [],
            }
            for c in cohorts
        },
        "per_document": {},
    }

    doc_ids = sorted(all_docs.keys())
    print(f"Executing Loop 22 Benchmark across {len(doc_ids)} documents...")

    all_evaluated_fields = []

    for idx, doc_id in enumerate(doc_ids, start=1):
        meta = all_docs[doc_id]
        cohort = meta["cohort"]
        img_path = doc_paths[doc_id]
        img = Image.open(img_path)
        w, h = img.size

        # 1. Raw OCR
        t0 = time.perf_counter()
        ocr_data = pytesseract.image_to_data(img, lang="eng", output_type=pytesseract.Output.DICT)
        raw_ocr_ms = round((time.perf_counter() - t0) * 1000, 2)

        valid_words = [str(txt).strip() for txt in ocr_data.get("text", []) if str(txt).strip()]
        page_text = " ".join(valid_words)

        # 2. Table Grid Assembly
        t1 = time.perf_counter()
        grid = build_table_grid(ocr_data=ocr_data, page_width=w, page_height=h, image=img)
        table_overhead_ms = round((time.perf_counter() - t1) * 1000, 2)
        total_latency_ms = round(raw_ocr_ms + table_overhead_ms, 2)

        # 3. Critical Fields Evaluation
        cf_list = meta["critical_fields"]
        doc_fields_eval = {}
        sem_count = 0
        fv_count = 0
        abstain_count = 0
        verif_count = 0

        for cf in cf_list:
            res = evaluate_field(grid, cf, doc_id, page_text, img=img, conf_threshold=60.0)
            doc_fields_eval[cf["name"]] = res
            all_evaluated_fields.append((doc_id, cohort, cf, res))

            if res["sem_pass"]:
                sem_count += 1
            if res["is_verified"]:
                verif_count += 1
            if res["is_false_verification"]:
                fv_count += 1
            if res["is_abstained"]:
                abstain_count += 1

        sem_rate = round(sem_count / len(cf_list), 4) if cf_list else 1.0

        c_stats = results["per_cohort"][cohort]
        c_stats["total_docs"] += 1
        c_stats["total_fields"] += len(cf_list)
        c_stats["sem_passes"] += sem_count
        c_stats["false_verifications"] += fv_count
        c_stats["abstentions"] += abstain_count
        c_stats["verified_claims"] += verif_count
        c_stats["latencies"].append(total_latency_ms)
        c_stats["overheads"].append(table_overhead_ms)

        results["per_document"][doc_id] = {
            "cohort": cohort,
            "category": meta.get("category", ""),
            "grid_rows": grid.num_rows,
            "grid_cols": grid.num_cols,
            "total_cells": grid.num_rows * grid.num_cols,
            "raw_ocr_ms": raw_ocr_ms,
            "table_overhead_ms": table_overhead_ms,
            "total_latency_ms": total_latency_ms,
            "sem_rate": sem_rate,
            "sem_count": sem_count,
            "total_fields": len(cf_list),
            "false_verifications": fv_count,
            "abstentions": abstain_count,
            "fields": doc_fields_eval,
        }

        print(
            f"[{idx:02d}/{len(doc_ids)}] {doc_id:<40} ({cohort}): "
            f"SEM={sem_count}/{len(cf_list)} FV={fv_count} ABST={abstain_count} | "
            f"{total_latency_ms}ms (overhead {table_overhead_ms}ms)"
        )

    # Aggregate Accounting
    total_fields = sum(c["total_fields"] for c in results["per_cohort"].values())
    total_sem = sum(c["sem_passes"] for c in results["per_cohort"].values())
    total_fv = sum(c["false_verifications"] for c in results["per_cohort"].values())
    total_abstain = sum(c["abstentions"] for c in results["per_cohort"].values())
    verified_claims = sum(c["verified_claims"] for c in results["per_cohort"].values())

    exact_verified = verified_claims - total_fv

    all_latencies = [d["total_latency_ms"] for d in results["per_document"].values()]
    all_overheads = [d["table_overhead_ms"] for d in results["per_document"].values()]

    cfp = round(exact_verified / verified_claims, 4) if verified_claims > 0 else 0.0
    fvr = round(total_fv / verified_claims, 4) if verified_claims > 0 else 0.0
    cov = round(verified_claims / total_fields, 4) if total_fields > 0 else 0.0
    ar = round(total_abstain / total_fields, 4) if total_fields > 0 else 0.0

    # Calibration Bins Analysis
    bins = [(0, 50), (50, 70), (70, 85), (85, 95), (95, 101)]
    calib_results = {}
    for b_low, b_high in bins:
        b_items = [f for f in all_evaluated_fields if b_low <= f[3]["confidence"] < b_high]
        b_count = len(b_items)
        b_corr = len([f for f in b_items if f[3]["sem_pass"]])
        b_acc = round(b_corr / b_count, 4) if b_count > 0 else 0.0
        calib_results[f"[{b_low}, {b_high})"] = {
            "count": b_count,
            "correct": b_corr,
            "accuracy": b_acc,
        }

    # Threshold Sweeps: Evaluate metrics at thresholds T in [40, 50, 60, 70, 80]
    sweep_results = []
    for t_thresh in [40.0, 50.0, 60.0, 70.0, 80.0]:
        sw_verif = 0
        sw_fv = 0
        sw_abst = 0
        sw_corr = 0
        for doc_id, cohort, cf, res in all_evaluated_fields:
            exp_val = str(cf["expected"]).strip()
            conf = res["confidence"]
            ext_val = res["extracted_value"]
            norm_ext = ext_val.replace("₹", "").replace("Rs.", "").replace(",", "").strip()
            norm_exp = exp_val.replace("₹", "").replace("Rs.", "").replace(",", "").strip()
            row_m = res.get("row_match", False)
            col_m = res.get("col_match", False)

            if exp_val == "":
                sw_abst += 1
                continue

            if res["is_ambiguous"] or conf < t_thresh:
                sw_abst += 1
            else:
                sw_verif += 1
                if norm_ext == norm_exp and row_m and col_m:
                    sw_corr += 1
                else:
                    sw_fv += 1

        sw_prec = round(sw_corr / sw_verif, 4) if sw_verif > 0 else 0.0
        sw_cov = round(sw_verif / total_fields, 4) if total_fields > 0 else 0.0
        sw_fvr = round(sw_fv / sw_verif, 4) if sw_verif > 0 else 0.0
        sweep_results.append({
            "threshold": t_thresh,
            "verified": sw_verif,
            "correct": sw_corr,
            "false_verifications": sw_fv,
            "abstained": sw_abst,
            "precision": sw_prec,
            "coverage": sw_cov,
            "fvr": sw_fvr,
        })

    summary = {
        "total_documents": len(all_docs),
        "total_critical_fields": total_fields,
        "sem_matches": total_sem,
        "verified_claims": verified_claims,
        "verified_exact_matches": exact_verified,
        "false_verifications": total_fv,
        "abstentions": total_abstain,
        "sem_accuracy_rate": round(total_sem / total_fields, 4),
        "critical_field_precision": cfp,
        "false_verification_rate": fvr,
        "verification_coverage": cov,
        "abstention_rate": ar,
        "accounting_check_verified_plus_abstain": f"{verified_claims} + {total_abstain} = {verified_claims + total_abstain} / {total_fields} ({round((verified_claims + total_abstain)/total_fields*100, 2)}%)",
        "accounting_check_coverage_plus_abstention": f"{cov} + {ar} = {round(cov + ar, 4)}",
        "accounting_check_cfp_plus_fvr": f"{cfp} + {fvr} = {round(cfp + fvr, 4)}",
        "confidence_calibration_bins": calib_results,
        "threshold_sweeps": sweep_results,
        "latency_mean_ms": round(float(np.mean(all_latencies)), 2),
        "latency_median_ms": round(float(np.median(all_latencies)), 2),
        "latency_p95_ms": round(float(np.percentile(all_latencies, 95)), 2),
        "overhead_mean_ms": round(float(np.mean(all_overheads)), 2),
        "overhead_median_ms": round(float(np.median(all_overheads)), 2),
        "overhead_p95_ms": round(float(np.percentile(all_overheads, 95)), 2),
    }

    results["summary"] = summary

    # Save results to JSON
    out_file = RESULTS_DIR / "benchmark_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 70)
    print("LOOP 22 BENCHMARK COMPLETE")
    print(f"Total Documents: {len(all_docs)}")
    print(f"Total Fields:    {total_fields}")
    print(f"SEM Matches:     {total_sem} ({summary['sem_accuracy_rate']*100:.2f}%)")
    print(f"Verified Claims: {verified_claims} ({cov*100:.2f}% coverage)")
    print(f"  - Exact Match: {exact_verified}")
    print(f"  - False Verif: {total_fv}")
    print(f"Abstentions:     {total_abstain} ({ar*100:.2f}% abstention rate)")
    print(f"Critical Field Precision (CFP): {cfp*100:.2f}%")
    print(f"False Verification Rate (FVR):  {fvr*100:.2f}%")
    print(f"Mean Latency:    {summary['latency_mean_ms']} ms")
    print(f"Mean Overhead:   {summary['overhead_mean_ms']} ms")
    print(f"Output saved to: {out_file}")
    print("=" * 70)

    return results


if __name__ == "__main__":
    run_benchmark()
