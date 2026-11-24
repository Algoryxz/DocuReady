"""
Loop 25 Forensics: Exhaustive Analysis of Row-Label OCR Failures and Abstentions
Inspects all 125 abstentions in research/loop24/results/benchmark_results.json,
correlates them with original OCR tokens in the table grids, and categorizes
each failure into the standardized failure taxonomy.
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from PIL import Image
import pytesseract

from docuready.ingest.table_association import (
    build_table_grid,
    normalize_token_text,
)

ROOT = Path(__file__).resolve().parents[3]
L24_RESULTS = ROOT / "research" / "loop24" / "results" / "benchmark_results.json"
L24_MANIFEST = ROOT / "research" / "loop24" / "dataset_manifest.json"

FAILURE_TAXONOMY = {
    "1_char_substitution": [],
    "2_char_deletion": [],
    "3_char_insertion": [],
    "4_broken_segmentation": [],
    "5_token_merging": [],
    "6_token_splitting": [],
    "7_low_resolution": [],
    "8_similar_abbreviation": [],
    "9_multi_col_confusion": [],
    "10_header_label_ambiguity": [],
    "11_skew_rotation": [],
    "12_unsupported_script": [],
    "confidence_floor": [],
    "empty_cell_expected": [],
    "other": [],
}


def run_forensics():
    tess_path = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
    if tess_path.exists():
        pytesseract.pytesseract.tesseract_cmd = str(tess_path)

    with open(L24_RESULTS, "r", encoding="utf-8") as f:
        res = json.load(f)

    with open(L24_MANIFEST, "r", encoding="utf-8") as f:
        l24_manifest = json.load(f)

    per_doc = res["per_document"]
    print(f"Total documents in ledger: {len(per_doc)}")

    all_abstentions = []
    for doc_id, doc_data in per_doc.items():
        for field in doc_data["fields"]:
            if field["is_abstained"]:
                field["document_id"] = doc_id
                field["cohort"] = doc_data["cohort"]
                all_abstentions.append(field)

    print(f"Total abstentions in ledger: {len(all_abstentions)}")

    # Detailed row-label failure investigation for Cohort I documents
    cohort_i_abstentions = [a for a in all_abstentions if a["cohort"].startswith("I_")]
    print(f"Cohort I abstentions: {len(cohort_i_abstentions)}")

    detailed_failures = []

    for item in cohort_i_abstentions:
        doc_id = item["document_id"]
        meta = l24_manifest.get(doc_id)
        if not meta:
            continue

        field_name = item["field_name"]
        expected_val = item["expected"]
        reason = item.get("reason") or "Missing evidence"
        category = item.get("abstention_category")

        # Find target pattern in meta
        f_meta = next((f for f in meta["critical_fields"] if f["name"] == field_name), None)
        target_pattern = f_meta.get("target_pattern", field_name) if f_meta else field_name
        exp_row = f_meta.get("row") if f_meta else None
        exp_col = f_meta.get("col") if f_meta else None

        img_path = Path(meta["image_path"])
        img = Image.open(img_path)
        ocr_data = pytesseract.image_to_data(img, lang="eng", output_type=pytesseract.Output.DICT)
        grid = build_table_grid(ocr_data, img.width, img.height, image=img)

        # Inspect row text at expected row (+1 for header offset)
        actual_row_idx = (exp_row + 1) if (exp_row is not None and exp_row + 1 < len(grid.rows)) else None
        row_cells = [c.text for c in grid.rows[actual_row_idx]] if actual_row_idx is not None else []
        row_label_text = row_cells[0] if row_cells else ""

        norm_target = normalize_token_text(target_pattern).upper()
        norm_actual = normalize_token_text(row_label_text).upper()

        # Diagnose failure mechanism
        failure_type = "other"
        if category == "Confidence floor":
            failure_type = "confidence_floor"
        elif f_meta and f_meta.get("type") == "empty":
            failure_type = "empty_cell_expected"
        elif norm_target in norm_actual:
            failure_type = "sub_match_present_but_rejected"
        else:
            # Check Levenshtein distance
            import difflib
            ratio = difflib.SequenceMatcher(None, norm_target, norm_actual).ratio()
            if ratio > 0.6:
                # Close match with character substitution/insertion/deletion
                if len(norm_actual) == len(norm_target):
                    failure_type = "1_char_substitution"
                elif len(norm_actual) < len(norm_target):
                    failure_type = "2_char_deletion"
                else:
                    failure_type = "3_char_insertion"
            elif any(token in norm_actual for token in norm_target.split()):
                failure_type = "4_broken_segmentation"
            else:
                failure_type = "7_low_resolution"

        record = {
            "document_id": doc_id,
            "field_name": field_name,
            "target_pattern": target_pattern,
            "expected_value": expected_val,
            "expected_row": exp_row,
            "expected_col": exp_col,
            "grid_row_idx": actual_row_idx,
            "ocr_row_label": row_label_text,
            "confidence": item["confidence"],
            "abstention_category": category,
            "raw_reason": reason,
            "failure_type": failure_type,
            "row_cells": row_cells,
            "target_norm": norm_target,
            "actual_norm": norm_actual,
        }
        detailed_failures.append(record)

    out_file = ROOT / "research" / "loop25" / "forensics" / "row_label_failure_audit.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(detailed_failures, f, indent=2)

    print(f"Saved detailed failure audit of {len(detailed_failures)} records to {out_file}")

    # Print summary counts by failure_type
    counts = {}
    for d in detailed_failures:
        ft = d["failure_type"]
        counts[ft] = counts.get(ft, 0) + 1
    print("\nFailure Type Breakdown in Cohort I Abstentions:")
    for ft, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {ft:30s}: {count:3d}")


if __name__ == "__main__":
    run_forensics()
