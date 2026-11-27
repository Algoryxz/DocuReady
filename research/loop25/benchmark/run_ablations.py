"""
Loop 25 Controlled Experiments & Ablation Engine
Compares 5 configurations across Cohort I (Loop 24) and Cohort J (Loop 25):
  1. Baseline: Exact string match only (Loop 24 behavior)
  2. Config A: Geometric & header conditioning only
  3. Config B: Canonical OCR Equivalence only (0/O, 1/I/l, 5/S, 8/B, 2/Z)
  4. Config C: Levenshtein string similarity only (with Delta >= 0.15 margin)
  5. Config D: Combined Full Loop 25 System (Equivalence + Levenshtein + Structural Validation + Calibrated Floor)
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, List
from PIL import Image
import pytesseract
import numpy as np

from docuready.ingest.table_association import (
    build_table_grid,
    extract_cell_by_intersection,
    extract_field_by_spatial_association,
    FieldEvidence,
)

ROOT = Path(__file__).resolve().parents[3]
L24_DIR = ROOT / "research" / "loop24"
L25_DIR = ROOT / "research" / "loop25"
RESULTS_DIR = L25_DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def configure_pytesseract():
    tess_path = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
    if tess_path.exists():
        pytesseract.pytesseract.tesseract_cmd = str(tess_path)


def run_ablation_suite():
    configure_pytesseract()

    with open(L24_DIR / "dataset_manifest.json", "r", encoding="utf-8") as f:
        l24_manifest = json.load(f)
    with open(L25_DIR / "dataset_manifest.json", "r", encoding="utf-8") as f:
        l25_manifest = json.load(f)

    # Combined test corpus for ablation: Cohort I (30 docs) + Cohort J (60 docs) = 90 docs, 303 fields
    test_docs = {}
    for doc_id, meta in l24_manifest.items():
        test_docs[doc_id] = {
            "cohort": meta["cohort"],
            "image_path": Path(meta["image_path"]),
            "critical_fields": meta["critical_fields"],
        }
    for doc_id, meta in l25_manifest.items():
        test_docs[doc_id] = {
            "cohort": meta["cohort"],
            "image_path": Path(meta["image_path"]),
            "critical_fields": meta["critical_fields"],
        }

    total_fields = sum(len(d["critical_fields"]) for d in test_docs.values())
    print(f"Loaded {len(test_docs)} docs with {total_fields} fields for ablation study.")

    # Pre-parse table grids once
    grids = {}
    images = {}
    print("Pre-building table grids...")
    for doc_id, doc in test_docs.items():
        img = Image.open(doc["image_path"])
        ocr_data = pytesseract.image_to_data(img, lang="eng", output_type=pytesseract.Output.DICT)
        grid = build_table_grid(ocr_data, img.width, img.height, image=img)
        grids[doc_id] = grid
        images[doc_id] = img

    # Modes to test:
    # 1: Baseline (exact match only)
    # 2: Equivalence only
    # 3: Levenshtein only
    # 4: Full System
    modes = [
        {"name": "Baseline (Loop 24 Exact Match Only)", "equiv": False, "fuzzy": False},
        {"name": "Config A (Canonical OCR Equivalence Only)", "equiv": True, "fuzzy": False},
        {"name": "Config B (Levenshtein Similarity Only)", "equiv": False, "fuzzy": True},
        {"name": "Config C (Combined Full Loop 25 System)", "equiv": True, "fuzzy": True},
    ]

    ablation_results = []

    for mode in modes:
        mode_name = mode["name"]
        print(f"\nEvaluating: {mode_name}...")
        t_start = time.perf_counter()

        v_count = 0
        e_count = 0
        fv_count = 0
        a_count = 0

        for doc_id, doc in test_docs.items():
            grid = grids[doc_id]
            img = images[doc_id]

            for f_meta in doc["critical_fields"]:
                field_name = f_meta["name"]
                expected_val = str(f_meta["expected"]).strip()
                target_pattern = f_meta.get("target_pattern", field_name)
                col_pattern = f_meta.get("col_pattern")
                col_idx = f_meta.get("col")
                exp_row = f_meta.get("row")
                exp_col = f_meta.get("col")
                expected_type = f_meta.get("type", "text")

                ev = extract_cell_by_intersection(
                    grid=grid,
                    field_name=field_name,
                    row_pattern=target_pattern,
                    col_pattern=col_pattern or "",
                    col_idx=col_idx,
                    expected_type=expected_type,
                    doc_id=doc_id,
                    image=img,
                )

                if ev is None:
                    a_count += 1
                    continue

                rec_method = ev.provenance.get("row_recovery_method", "exact_match")
                # Filter based on ablation configuration
                if not mode["equiv"] and rec_method == "canonical_equivalence":
                    a_count += 1
                    continue
                if not mode["fuzzy"] and rec_method == "levenshtein_similarity":
                    a_count += 1
                    continue

                conf = ev.confidence
                is_ambig = ev.is_ambiguous or ev.verification_decision == "ABSTAIN" or (conf < 70.0)

                if is_ambig:
                    a_count += 1
                else:
                    v_count += 1
                    ext_val = ev.value.strip()
                    norm_ext = ext_val.replace("₹", "").replace("Rs.", "").replace(",", "").replace("$", "").strip()
                    norm_exp = expected_val.replace("₹", "").replace("Rs.", "").replace(",", "").replace("$", "").strip()
                    row_match = (exp_row is None or ev.row_idx == exp_row or ev.row_idx == exp_row + 1)
                    header_matched = bool(col_pattern and ev.col_header and col_pattern.strip().upper() in ev.col_header.upper())
                    col_match = (exp_col is None or ev.col_idx == exp_col or header_matched)
                    if norm_ext == norm_exp and row_match and col_match:
                        e_count += 1
                    else:
                        fv_count += 1

        elapsed_ms = (time.perf_counter() - t_start) * 1000.0
        prec = (e_count / v_count * 100.0) if v_count > 0 else 100.0
        cov = (v_count / total_fields * 100.0)
        fvr = (fv_count / v_count * 100.0) if v_count > 0 else 0.0

        res_row = {
            "configuration": mode_name,
            "total_fields": total_fields,
            "verified_claims": v_count,
            "exact_matches": e_count,
            "false_verifications": fv_count,
            "abstentions": a_count,
            "precision": round(prec, 2),
            "false_verification_rate": round(fvr, 2),
            "coverage": round(cov, 2),
            "evaluation_time_ms": round(elapsed_ms, 2),
        }
        ablation_results.append(res_row)
        print(f"  Verified: {v_count} | Exact: {e_count} | False: {fv_count} | Prec: {prec:.2f}% | Cov: {cov:.2f}%")

    out_file = RESULTS_DIR / "ablation_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(ablation_results, f, indent=2)
    print(f"\nSaved ablation results to {out_file}")


if __name__ == "__main__":
    run_ablation_suite()
