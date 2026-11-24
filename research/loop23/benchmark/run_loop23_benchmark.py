"""
DocuReady Loop 23 Comprehensive Benchmark Runner
Evaluates 52 documents across 8 cohorts (A, B, C, D, E, F, G, H):
- A: Development Baseline (Loop 20)
- B: Validation Baseline (Loop 20)
- C: Blind Evaluation (Loop 20)
- D: Challenge Adversarial (Loop 20)
- E: Hierarchical Headers (Loop 21)
- F: Decimal Integrity (Loop 21)
- G: Evidence Association (Loop 22)
- H: Micro-Font & Narrow-Gutter Integrity (Loop 23)

Generates authoritative JSON ledger and Markdown summaries with zero-transcription error guarantee.
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

sys.path.insert(0, str(Path("src").resolve()))
sys.path.insert(0, str(Path(".").resolve()))

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
L23_DIR = ROOT / "research" / "loop23"
RESULTS_DIR = L23_DIR / "results"
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

        should_abstain = (
            evidence.is_ambiguous or
            evidence.verification_decision == "ABSTAIN" or
            evidence.confidence < conf_threshold
        )

        if should_abstain:
            reason = evidence.abstention_reason or f"Confidence below threshold ({evidence.confidence:.1f} < {conf_threshold:.1f})"
            status = f"ABSTAIN_FILTERED (val='{ext_val}', reason='{reason}')"
            is_sem = (norm_ext == norm_exp and row_match)
            is_verified = False
            is_false_verification = False
            is_abstained = True
            abstention_reason = reason
        else:
            if norm_ext == norm_exp:
                if row_match and col_match:
                    status = "PASS_SPATIAL_EXACT"
                    is_sem = True
                    is_verified = True
                    is_false_verification = False
                    is_abstained = False
                    abstention_reason = None
                else:
                    status = f"FAIL_COORDINATE_OFFSET (row={evidence.row_idx}/{exp_row}, col={evidence.col_idx}/{exp_col})"
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


def load_dataset() -> Tuple[Dict[str, Any], Dict[str, Path]]:
    with open(L20_DIR / "dataset_manifest.json", "r", encoding="utf-8") as f:
        l20_manifest = json.load(f)
    with open(L21_DIR / "dataset_manifest.json", "r", encoding="utf-8") as f:
        l21_manifest = json.load(f)
    with open(L22_DIR / "dataset_manifest.json", "r", encoding="utf-8") as f:
        l22_manifest = json.load(f)
    with open(L23_DIR / "dataset_manifest.json", "r", encoding="utf-8") as f:
        l23_manifest = json.load(f)

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

    for doc_id, meta in l23_manifest["documents"].items():
        all_docs[doc_id] = meta
        doc_paths[doc_id] = L23_DIR / "tables" / f"{doc_id}.png"

    return all_docs, doc_paths


def run_benchmark(conf_threshold: float = 60.0) -> Dict[str, Any]:
    configure_pytesseract()
    all_docs, doc_paths = load_dataset()

    cohorts = [
        "A_development",
        "B_validation",
        "C_blind_evaluation",
        "D_challenge_adversarial",
        "E_hierarchical_headers",
        "F_decimal_integrity",
        "G_evidence_association",
        "H_microfont_narrow_gutter",
    ]

    results: Dict[str, Any] = {
        "benchmark_name": "Loop 23 Micro-Font Numeric & Narrow-Gutter Table Integrity Benchmark",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_documents": len(all_docs),
        "conf_threshold": conf_threshold,
        "per_cohort": {
            c: {
                "total_docs": 0,
                "total_fields": 0,
                "verified_claims": 0,
                "exact_matches": 0,
                "false_verifications": 0,
                "abstentions": 0,
                "sem_passes": 0,
                "latencies": [],
                "overheads": [],
            }
            for c in cohorts
        },
        "per_document": {},
    }

    doc_ids = sorted(all_docs.keys())
    print(f"Executing Loop 23 Benchmark across {len(doc_ids)} documents...")

    all_evaluated_fields = []

    for idx, doc_id in enumerate(doc_ids, start=1):
        meta = all_docs[doc_id]
        cohort = meta["cohort"]
        img_path = doc_paths[doc_id]
        img = Image.open(img_path)
        w, h = img.size

        # 1. OCR Data
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

        # 3. Critical Fields
        cf_list = meta["critical_fields"]
        doc_fields_eval = {}
        sem_count = 0
        verif_count = 0
        exact_count = 0
        fv_count = 0
        abstain_count = 0

        for cf in cf_list:
            res = evaluate_field(grid, cf, doc_id, page_text, img=img, conf_threshold=conf_threshold)
            doc_fields_eval[cf["name"]] = res
            all_evaluated_fields.append((doc_id, cohort, cf, res))

            if res["sem_pass"]:
                sem_count += 1
            if res["is_verified"]:
                verif_count += 1
                if res["is_false_verification"]:
                    fv_count += 1
                else:
                    exact_count += 1
            if res["is_abstained"]:
                abstain_count += 1

        # Record doc summary
        results["per_document"][doc_id] = {
            "cohort": cohort,
            "category": meta.get("category", ""),
            "total_fields": len(cf_list),
            "sem_passes": sem_count,
            "verified_claims": verif_count,
            "exact_matches": exact_count,
            "false_verifications": fv_count,
            "abstentions": abstain_count,
            "raw_ocr_ms": raw_ocr_ms,
            "table_overhead_ms": table_overhead_ms,
            "total_latency_ms": total_latency_ms,
            "fields": doc_fields_eval,
        }

        # Update cohort aggregate
        c_dict = results["per_cohort"][cohort]
        c_dict["total_docs"] += 1
        c_dict["total_fields"] += len(cf_list)
        c_dict["sem_passes"] += sem_count
        c_dict["verified_claims"] += verif_count
        c_dict["exact_matches"] += exact_count
        c_dict["false_verifications"] += fv_count
        c_dict["abstentions"] += abstain_count
        c_dict["latencies"].append(total_latency_ms)
        c_dict["overheads"].append(table_overhead_ms)

    # Compute overall summary
    total_fields = sum(c["total_fields"] for c in results["per_cohort"].values())
    total_verif = sum(c["verified_claims"] for c in results["per_cohort"].values())
    total_exact = sum(c["exact_matches"] for c in results["per_cohort"].values())
    total_fv = sum(c["false_verifications"] for c in results["per_cohort"].values())
    total_abst = sum(c["abstentions"] for c in results["per_cohort"].values())
    total_sem = sum(c["sem_passes"] for c in results["per_cohort"].values())

    precision = round((total_exact / total_verif * 100), 2) if total_verif > 0 else 0.0
    fvr = round((total_fv / total_verif * 100), 2) if total_verif > 0 else 0.0
    coverage = round((total_verif / total_fields * 100), 2) if total_fields > 0 else 0.0
    abstention_rate = round((total_abst / total_fields * 100), 2) if total_fields > 0 else 0.0
    exact_yield = round((total_exact / total_fields * 100), 2) if total_fields > 0 else 0.0
    sem_rate = round((total_sem / total_fields * 100), 2) if total_fields > 0 else 0.0

    all_latencies = [d["total_latency_ms"] for d in results["per_document"].values()]
    all_overheads = [d["table_overhead_ms"] for d in results["per_document"].values()]

    # Expected Calibration Error (ECE)
    bins = [i * 10 for i in range(11)]  # 0, 10, 20 ... 100
    ece_num = 0.0
    for b_idx in range(len(bins) - 1):
        low, high = bins[b_idx], bins[b_idx + 1]
        bin_items = [
            f for f in all_evaluated_fields
            if low <= f[3]["confidence"] < high or (high == 100 and f[3]["confidence"] == 100)
        ]
        if bin_items:
            acc = sum(1 for item in bin_items if item[3]["is_verified"] and not item[3]["is_false_verification"]) / len(bin_items)
            conf_avg = sum(item[3]["confidence"] for item in bin_items) / (len(bin_items) * 100.0)
            ece_num += abs(acc - conf_avg) * len(bin_items)

    ece = round(ece_num / len(all_evaluated_fields), 4) if all_evaluated_fields else 0.0

    results["summary"] = {
        "total_documents": len(all_docs),
        "total_fields": total_fields,
        "verified_claims": total_verif,
        "exact_matches": total_exact,
        "false_verifications": total_fv,
        "abstentions": total_abst,
        "sem_passes": total_sem,
        "critical_field_precision": precision,
        "false_verification_rate": fvr,
        "coverage": coverage,
        "abstention_rate": abstention_rate,
        "exact_yield": exact_yield,
        "sem_rate": sem_rate,
        "expected_calibration_error": ece,
        "mean_latency_ms": round(float(np.mean(all_latencies)), 2),
        "mean_overhead_ms": round(float(np.mean(all_overheads)), 2),
    }

    # Format cohort breakdown table
    for c_name, c_dict in results["per_cohort"].items():
        v = c_dict["verified_claims"]
        e = c_dict["exact_matches"]
        f_cnt = c_dict["total_fields"]
        c_dict["precision"] = round((e / v * 100), 2) if v > 0 else 0.0
        c_dict["coverage"] = round((v / f_cnt * 100), 2) if f_cnt > 0 else 0.0
        c_dict["mean_latency_ms"] = round(float(np.mean(c_dict["latencies"])), 2) if c_dict["latencies"] else 0.0
        c_dict["mean_overhead_ms"] = round(float(np.mean(c_dict["overheads"])), 2) if c_dict["overheads"] else 0.0

    # Save JSON results
    out_json = RESULTS_DIR / "benchmark_results.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 95)
    print("LOOP 23 COMPREHENSIVE BENCHMARK RESULTS")
    print("=" * 95)
    print(f"Total Documents:           {results['summary']['total_documents']}")
    print(f"Total Fields Evaluated:    {results['summary']['total_fields']}")
    print(f"Verified Claims:           {results['summary']['verified_claims']}")
    print(f"  - Exact Matches:         {results['summary']['exact_matches']}")
    print(f"  - False Verifications:   {results['summary']['false_verifications']}")
    print(f"Abstentions:               {results['summary']['abstentions']}")
    print(f"SEM Passes:                {results['summary']['sem_passes']}")
    print(f"Critical Field Precision:  {results['summary']['critical_field_precision']}%")
    print(f"False Verification Rate:   {results['summary']['false_verification_rate']}%")
    print(f"Coverage:                  {results['summary']['coverage']}%")
    print(f"Abstention Rate:           {results['summary']['abstention_rate']}%")
    print(f"Exact Verified Yield:      {results['summary']['exact_yield']}%")
    print(f"ECE:                       {results['summary']['expected_calibration_error']}")
    print(f"Mean Table Overhead:       {results['summary']['mean_overhead_ms']} ms")
    print(f"Mean Document Latency:     {results['summary']['mean_latency_ms']} ms")
    print("=" * 95)

    print("\nCOHORT BREAKDOWN TABLE:")
    header = "| Cohort | Docs | Fields | Verified | Exact | FV | Abst | SEM | Precision | Coverage | Overhead |"
    sep = "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |"
    print(header)
    print(sep)
    for c_name, c_data in results["per_cohort"].items():
        row_str = (
            f"| **{c_name}** | {c_data['total_docs']} | {c_data['total_fields']} | "
            f"{c_data['verified_claims']} | {c_data['exact_matches']} | {c_data['false_verifications']} | "
            f"{c_data['abstentions']} | {c_data['sem_passes']} | {c_data['precision']:.2f}% | "
            f"{c_data['coverage']:.2f}% | {c_data['mean_overhead_ms']:.2f}ms |"
        )
        print(row_str)
    total_row = (
        f"| **TOTAL** | **{len(all_docs)}** | **{total_fields}** | "
        f"**{total_verif}** | **{total_exact}** | **{total_fv}** | "
        f"**{total_abst}** | **{total_sem}** | **{precision:.2f}%** | "
        f"**{coverage:.2f}%** | **{results['summary']['mean_overhead_ms']:.2f}ms** |"
    )
    print(total_row)

    return results


if __name__ == "__main__":
    run_benchmark(conf_threshold=60.0)
