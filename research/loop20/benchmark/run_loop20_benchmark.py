"""
Loop 20 - Blind Generalization & Verification Reliability Benchmark Runner
DocuReady Engineering Research

Evaluates DocuReady's table-aware evidence extraction, spatial field association,
false-verification prevention, and evidence-based abstention across all 34 documents
in the multi-cohort corpus.
"""

from __future__ import annotations

import json
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
RESEARCH_DIR = ROOT / "research" / "loop20"
MANIFEST_PATH = RESEARCH_DIR / "dataset_manifest.json"
RESULTS_PATH = RESEARCH_DIR / "results" / "benchmark_results.json"


def evaluate_field(
    grid: TableGrid,
    field_spec: Dict[str, Any],
    doc_id: str,
    page_text: str,
) -> Dict[str, Any]:
    field_name = field_spec["name"]
    expected_val = str(field_spec["expected"]).strip()
    exp_row = field_spec.get("row")
    exp_col = field_spec.get("col")
    field_type = field_spec.get("type", "text")
    target_pattern = field_spec.get("target_pattern", "")

    # Baseline Substring Match (BSM) - The naive Loop 18 check
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
            is_verified = True # Confidently returned spurious value!
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
        # Clean currency symbols for matching
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


def run_benchmark():
    configure_pytesseract()
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)

    results: Dict[str, Any] = {
        "benchmark_name": "Loop 20 Blind Generalization & Verification Reliability",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_documents": len(manifest["documents"]),
        "per_cohort": {
            "A_development": {"total_docs": 0, "total_fields": 0, "sem_passes": 0, "false_verifications": 0, "abstentions": 0, "latencies": [], "overheads": []},
            "B_validation": {"total_docs": 0, "total_fields": 0, "sem_passes": 0, "false_verifications": 0, "abstentions": 0, "latencies": [], "overheads": []},
            "C_blind_evaluation": {"total_docs": 0, "total_fields": 0, "sem_passes": 0, "false_verifications": 0, "abstentions": 0, "latencies": [], "overheads": []},
            "D_challenge_adversarial": {"total_docs": 0, "total_fields": 0, "sem_passes": 0, "false_verifications": 0, "abstentions": 0, "latencies": [], "overheads": []},
        },
        "per_document": {},
    }

    doc_ids = sorted(manifest["documents"].keys())
    print(f"Executing Loop 20 Benchmark across {len(doc_ids)} documents...")

    for idx, doc_id in enumerate(doc_ids, start=1):
        meta = manifest["documents"][doc_id]
        cohort = meta["cohort"]
        img_path = RESEARCH_DIR / "tables" / f"{doc_id}.png"
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
        grid = build_table_grid(ocr_data=ocr_data, page_width=w, page_height=h)
        table_overhead_ms = round((time.perf_counter() - t1) * 1000, 2)
        total_latency_ms = round(raw_ocr_ms + table_overhead_ms, 2)

        # 3. Evaluate Critical Fields
        cf_list = meta["critical_fields"]
        doc_fields_eval = {}
        sem_count = 0
        fv_count = 0
        abstain_count = 0

        for cf in cf_list:
            res = evaluate_field(grid, cf, doc_id, page_text)
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
            "category": meta.get("category", "General"),
            "grid_rows": grid.num_rows,
            "grid_cols": grid.num_cols,
            "total_cells": len(grid.cells),
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

        print(f"[{idx:02d}/34] {doc_id} ({cohort}) - SEM: {sem_count}/{len(cf_list)} ({sem_rate*100:.1f}%) | Overhead: {table_overhead_ms}ms")

    # Aggregate metrics
    total_fields = sum(c["total_fields"] for c in results["per_cohort"].values())
    total_sem = sum(c["sem_passes"] for c in results["per_cohort"].values())
    total_fv = sum(c["false_verifications"] for c in results["per_cohort"].values())
    total_abstain = sum(c["abstentions"] for c in results["per_cohort"].values())
    all_latencies = [l for c in results["per_cohort"].values() for l in c["latencies"]]
    all_overheads = [o for c in results["per_cohort"].values() for o in c["overheads"]]

    results["summary"] = {
        "total_documents": 34,
        "total_critical_fields": total_fields,
        "total_sem_passes": total_sem,
        "mean_sem_rate": round(total_sem / total_fields, 4),
        "total_false_verifications": total_fv,
        "false_verification_rate": round(total_fv / (total_sem + total_fv), 4) if (total_sem + total_fv) > 0 else 0.0,
        "critical_field_precision": round(total_sem / (total_sem + total_fv), 4) if (total_sem + total_fv) > 0 else 0.0,
        "verification_coverage": round((total_sem + total_fv) / total_fields, 4),
        "abstention_rate": round(total_abstain / total_fields, 4),
        "latency_mean_ms": round(float(np.mean(all_latencies)), 2),
        "latency_median_ms": round(float(np.median(all_latencies)), 2),
        "latency_p95_ms": round(float(np.percentile(all_latencies, 95)), 2),
        "overhead_mean_ms": round(float(np.mean(all_overheads)), 2),
        "overhead_median_ms": round(float(np.median(all_overheads)), 2),
        "overhead_p95_ms": round(float(np.percentile(all_overheads, 95)), 2),
    }

    # Summary by cohort
    for c_name, c in results["per_cohort"].items():
        c["sem_rate"] = round(c["sem_passes"] / c["total_fields"], 4) if c["total_fields"] > 0 else 0.0
        c["mean_latency_ms"] = round(float(np.mean(c["latencies"])), 2) if c["latencies"] else 0.0
        c["mean_overhead_ms"] = round(float(np.mean(c["overheads"])), 2) if c["overheads"] else 0.0

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n================== LOOP 20 BENCHMARK SUMMARY ==================")
    print(f"Total Evaluated Fields:     {total_fields}")
    print(f"Spatial Exact Matches:      {total_sem} / {total_fields} ({results['summary']['mean_sem_rate']*100:.2f}%)")
    print(f"False Verifications:        {total_fv}")
    print(f"False Verification Rate:    {results['summary']['false_verification_rate']*100:.2f}%")
    print(f"Critical Field Precision:   {results['summary']['critical_field_precision']*100:.2f}%")
    print(f"Verification Coverage:      {results['summary']['verification_coverage']*100:.2f}%")
    print(f"Abstention Rate:            {results['summary']['abstention_rate']*100:.2f}%")
    print(f"Mean Spatial Overhead:      {results['summary']['overhead_mean_ms']} ms")
    print(f"Mean Page Latency:          {results['summary']['latency_mean_ms']} ms")
    print("---------------------------------------------------------------")
    for c_name, c in results["per_cohort"].items():
        print(f"[{c_name}] SEM: {c['sem_passes']}/{c['total_fields']} ({c['sem_rate']*100:.1f}%) | FV: {c['false_verifications']} | Overhead: {c['mean_overhead_ms']}ms")
    print(f"Results written to: {RESULTS_PATH}")


if __name__ == "__main__":
    run_benchmark()
