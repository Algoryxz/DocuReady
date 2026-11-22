"""
DocuReady Loop 21 Comprehensive Multi-Cohort Benchmark Runner
Validates:
1. Cohorts A, B, C, D (Loop 20 34-document corpus) to measure exact regression & improvement
   - Specifically verifying VAL_05 (hierarchical header reconstruction)
   - Specifically verifying BLIND_06 (decimal-point retention)
2. Cohorts E, F (Loop 21 6-document dedicated stress corpus)
   - Cohort E: Hierarchical Multi-Tier Headers (HIER_01, HIER_02, HIER_03)
   - Cohort F: Low-Resolution Decimal Integrity (DEC_01, DEC_02, DEC_03)

Computes mutually exclusive & exhaustive verification metrics:
  Verified Claims + Abstentions = Total Fields (100%)
  Coverage + Abstention Rate = 100%
  Critical Field Precision + False Verification Rate = 100%
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
    TableGrid,
    FieldEvidence,
    build_table_grid,
    extract_field_by_spatial_association,
    extract_cell_by_intersection,
    normalize_token_text,
)

ROOT = Path(__file__).resolve().parents[3]
L20_DIR = ROOT / "research" / "loop20"
L21_DIR = ROOT / "research" / "loop21"
RESULTS_PATH = L21_DIR / "results" / "benchmark_results.json"


def evaluate_field(
    grid: TableGrid,
    field_spec: Dict[str, Any],
    doc_id: str,
    page_text: str,
    img: Optional[Image.Image] = None,
) -> Dict[str, Any]:
    field_name = field_spec["name"]
    expected_val = str(field_spec["expected"]).strip()
    exp_row = field_spec.get("row")
    exp_col = field_spec.get("col")
    field_type = field_spec.get("type", "text")
    target_pattern = field_spec.get("target_pattern", "")

    # Baseline Substring Match (BSM)
    bsm_pass = (expected_val != "" and expected_val in page_text) or (expected_val == "" and True)

    # Attempt spatial extraction using table grid
    evidence: Optional[FieldEvidence] = None

    if target_pattern:
        evidence = extract_field_by_spatial_association(
            grid=grid,
            field_name=field_name,
            target_pattern=target_pattern,
            col_pattern=field_spec.get("col_pattern"),
            col_idx=exp_col,
            expected_type=field_type,
            doc_id=doc_id,
            image=img,
        )

    # If expected is empty (e.g. blank cell in form or trap)
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
            "row": evidence.row_idx if evidence else -1,
            "col": evidence.col_idx if evidence else -1,
            "confidence": evidence.confidence if evidence else 0.0,
            "is_ambiguous": evidence.is_ambiguous if evidence else False,
            "bbox": evidence.bbox if evidence else [0, 0, 0, 0],
            "traceable": (evidence is not None and evidence.bbox != (0, 0, 0, 0)),
        }

    # If expected is a non-empty value
    if evidence is None:
        status = "FAIL_NOT_EXTRACTED"
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

        if evidence.is_ambiguous:
            status = f"ABSTAIN_AMBIGUOUS (val='{ext_val}', reason='Ambiguity flagged in spatial extraction')"
            is_sem = False
            is_verified = False
            is_false_verification = False
            is_abstained = True
            abstention_reason = "Ambiguous cell boundaries, label-echo, or multi-row candidate collision"
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

    # Load Loop 20 manifest
    with open(L20_DIR / "dataset_manifest.json", "r", encoding="utf-8") as f:
        l20_manifest = json.load(f)

    # Load Loop 21 manifest
    with open(L21_DIR / "dataset_manifest.json", "r", encoding="utf-8") as f:
        l21_manifest = json.load(f)

    all_docs = {}
    doc_paths = {}

    for doc_id, meta in l20_manifest["documents"].items():
        all_docs[doc_id] = meta
        doc_paths[doc_id] = L20_DIR / "tables" / f"{doc_id}.png"

    for doc_id, meta in l21_manifest["documents"].items():
        all_docs[doc_id] = meta
        doc_paths[doc_id] = L21_DIR / "tables" / f"{doc_id}.png"

    cohorts = [
        "A_development",
        "B_validation",
        "C_blind_evaluation",
        "D_challenge_adversarial",
        "E_hierarchical_headers",
        "F_decimal_integrity",
    ]

    results: Dict[str, Any] = {
        "benchmark_name": "Loop 21 Hierarchical Header & Decimal Integrity Benchmark",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_documents": len(all_docs),
        "per_cohort": {
            c: {
                "total_docs": 0,
                "total_fields": 0,
                "sem_passes": 0,
                "false_verifications": 0,
                "abstentions": 0,
                "latencies": [],
                "overheads": [],
            }
            for c in cohorts
        },
        "per_document": {},
    }

    doc_ids = sorted(all_docs.keys())
    print(f"Executing Loop 21 Benchmark across {len(doc_ids)} documents...")

    for idx, doc_id in enumerate(doc_ids, start=1):
        meta = all_docs[doc_id]
        cohort = meta["cohort"]
        img_path = doc_paths[doc_id]
        img = Image.open(img_path)
        w, h = img.size

        # 1. Measure raw OCR
        t0 = time.perf_counter()
        ocr_data = pytesseract.image_to_data(img, lang="eng", output_type=pytesseract.Output.DICT)
        raw_ocr_ms = round((time.perf_counter() - t0) * 1000, 2)

        # Whole page text for BSM
        valid_words = [str(txt).strip() for txt in ocr_data.get("text", []) if str(txt).strip()]
        page_text = " ".join(valid_words)

        # 2. Measure Table Grid Assembly
        t1 = time.perf_counter()
        grid = build_table_grid(ocr_data=ocr_data, page_width=w, page_height=h, image=img)
        table_overhead_ms = round((time.perf_counter() - t1) * 1000, 2)
        total_latency_ms = round(raw_ocr_ms + table_overhead_ms, 2)

        # 3. Evaluate Critical Fields
        cf_list = meta["critical_fields"]
        doc_fields_eval = {}
        sem_count = 0
        fv_count = 0
        abstain_count = 0

        for cf in cf_list:
            res = evaluate_field(grid, cf, doc_id, page_text, img=img)
            doc_fields_eval[cf["name"]] = res
            if res["sem_pass"]:
                sem_count += 1
            if res["is_false_verification"]:
                fv_count += 1
            if res["is_abstained"]:
                abstain_count += 1

        sem_rate = round(sem_count / len(cf_list), 4) if cf_list else 1.0

        # Update cohort stats
        c_stats = results["per_cohort"][cohort]
        c_stats["total_docs"] += 1
        c_stats["total_fields"] += len(cf_list)
        c_stats["sem_passes"] += sem_count
        c_stats["false_verifications"] += fv_count
        c_stats["abstentions"] += abstain_count
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

        print(f"[{idx:02d}/{len(doc_ids)}] {doc_id:<36} ({cohort}): SEM={sem_count}/{len(cf_list)} FV={fv_count} ABST={abstain_count} | {total_latency_ms}ms (overhead {table_overhead_ms}ms)")

    # Aggregate summaries
    total_fields = sum(c["total_fields"] for c in results["per_cohort"].values())
    total_sem = sum(c["sem_passes"] for c in results["per_cohort"].values())
    total_fv = sum(c["false_verifications"] for c in results["per_cohort"].values())
    total_abstain = sum(c["abstentions"] for c in results["per_cohort"].values())

    all_lats = [d["total_latency_ms"] for d in results["per_document"].values()]
    all_ovhs = [d["table_overhead_ms"] for d in results["per_document"].values()]

    # Compute mutually exclusive verified claims
    # Verified Claims = total_fields - total_abstain
    verified_claims = total_fields - total_abstain
    # Precision among verified claims
    # Note: SEM passes that are verified are exact matches
    # Empty cells that passed are counted under abstentions
    verified_exact_matches = total_sem - (1 if "PASS_EMPTY_CORRECT" in [f["status"] for d in results["per_document"].values() for f in d["fields"].values()] else 0)
    # Recalculate precisely
    verified_exact_count = 0
    for d in results["per_document"].values():
        for f in d["fields"].values():
            if f["is_verified"] and f["sem_pass"]:
                verified_exact_count += 1

    cfp = round(verified_exact_count / verified_claims, 4) if verified_claims > 0 else 1.0
    fvr = round(total_fv / verified_claims, 4) if verified_claims > 0 else 0.0
    vc = round(verified_claims / total_fields, 4) if total_fields > 0 else 0.0
    ar = round(total_abstain / total_fields, 4) if total_fields > 0 else 0.0

    for c_name, c_data in results["per_cohort"].items():
        c_data["sem_rate"] = round(c_data["sem_passes"] / c_data["total_fields"], 4) if c_data["total_fields"] else 1.0
        c_data["mean_latency_ms"] = round(float(np.mean(c_data["latencies"])), 2) if c_data["latencies"] else 0.0
        c_data["mean_overhead_ms"] = round(float(np.mean(c_data["overheads"])), 2) if c_data["overheads"] else 0.0

    results["summary"] = {
        "total_documents": len(all_docs),
        "total_critical_fields": total_fields,
        "sem_matches": total_sem,
        "verified_claims": verified_claims,
        "verified_exact_matches": verified_exact_count,
        "false_verifications": total_fv,
        "abstentions": total_abstain,
        "sem_accuracy_rate": round(total_sem / total_fields, 4),
        "critical_field_precision": cfp,
        "false_verification_rate": fvr,
        "verification_coverage": vc,
        "abstention_rate": ar,
        "accounting_check_verified_plus_abstain": f"{verified_claims} + {total_abstain} = {verified_claims + total_abstain} / {total_fields} ({round((verified_claims + total_abstain)/total_fields*100, 2)}%)",
        "accounting_check_coverage_plus_abstention": f"{vc} + {ar} = {round(vc + ar, 4)}",
        "accounting_check_cfp_plus_fvr": f"{cfp} + {fvr} = {round(cfp + fvr, 4)}",
        "latency_mean_ms": round(float(np.mean(all_lats)), 2),
        "latency_median_ms": round(float(np.median(all_lats)), 2),
        "latency_p95_ms": round(float(np.percentile(all_lats, 95)), 2),
        "overhead_mean_ms": round(float(np.mean(all_ovhs)), 2),
        "overhead_median_ms": round(float(np.median(all_ovhs)), 2),
        "overhead_p95_ms": round(float(np.percentile(all_ovhs, 95)), 2),
    }

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 70)
    print("LOOP 21 BENCHMARK COMPLETE")
    print(f"Total Documents: {len(all_docs)}")
    print(f"Total Fields:    {total_fields}")
    print(f"SEM Matches:     {total_sem} ({round(total_sem/total_fields*100, 2)}%)")
    print(f"Verified Claims: {verified_claims}")
    print(f"  - Exact Match: {verified_exact_count}")
    print(f"  - False Verif: {total_fv}")
    print(f"Abstentions:     {total_abstain}")
    print(f"Critical Field Precision: {round(cfp*100, 2)}%")
    print(f"False Verification Rate:  {round(fvr*100, 2)}%")
    print(f"Mean Latency:    {results['summary']['latency_mean_ms']} ms")
    print(f"Mean Overhead:   {results['summary']['overhead_mean_ms']} ms")
    print("=" * 70)

    return results


if __name__ == "__main__":
    run_benchmark()
