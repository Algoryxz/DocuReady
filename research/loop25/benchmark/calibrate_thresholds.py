"""
Loop 25 Calibration and Threshold Sweep Engine
Evaluates Development (Cohort J Dev, 15 docs) and Calibration (Cohort J Calib, 15 docs)
across candidate thresholds T in [40.0, 90.0] with step 5.0.
Calculates ECE, MCE, Brier score, False Verification Rate, and Coverage.
Freezes operating threshold T* prior to blind evaluation.
"""

import json
import math
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

L25_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = L25_DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def configure_pytesseract():
    tess_path = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
    if tess_path.exists():
        pytesseract.pytesseract.tesseract_cmd = str(tess_path)


def compute_calibration_metrics(predictions: List[Dict[str, Any]], n_bins: int = 5) -> Dict[str, float]:
    """
    Computes ECE, MCE, and Brier score over verified claims.
    """
    if not predictions:
        return {"ece": 0.0, "mce": 0.0, "brier": 0.0}

    verified = [p for p in predictions if p["is_verified"]]
    if not verified:
        return {"ece": 0.0, "mce": 0.0, "brier": 0.0}

    confidences = np.array([p["confidence"] / 100.0 for p in verified])
    accuracies = np.array([1.0 if p["is_exact"] else 0.0 for p in verified])

    brier = float(np.mean((confidences - accuracies) ** 2))

    bin_boundaries = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    mce = 0.0
    total_samples = len(verified)

    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]

        in_bin = (confidences > bin_lower) & (confidences <= bin_upper) if i > 0 else (confidences >= bin_lower) & (confidences <= bin_upper)
        bin_size = np.sum(in_bin)

        if bin_size > 0:
            bin_acc = np.mean(accuracies[in_bin])
            bin_conf = np.mean(confidences[in_bin])
            gap = abs(bin_acc - bin_conf)
            ece += (bin_size / total_samples) * gap
            mce = max(mce, gap)

    return {
        "ece": round(float(ece), 4),
        "mce": round(float(mce), 4),
        "brier": round(float(brier), 4),
    }


def evaluate_field(
    grid: Any,
    field_meta: Dict[str, Any],
    doc_id: str,
    img: Image.Image,
    conf_threshold: float,
) -> Dict[str, Any]:
    field_name = field_meta["name"]
    expected_val = str(field_meta["expected"]).strip()
    target_pattern = field_meta.get("target_pattern", field_name)
    col_pattern = field_meta.get("col_pattern")
    col_idx = field_meta.get("col")
    expected_type = field_meta.get("type", "text")

    if col_pattern or col_idx is not None:
        evidence = extract_cell_by_intersection(
            grid=grid,
            field_name=field_name,
            row_pattern=target_pattern,
            col_pattern=col_pattern or "",
            col_idx=col_idx,
            expected_type=expected_type,
            doc_id=doc_id,
            image=img,
        )
    else:
        evidence = extract_field_by_spatial_association(
            grid=grid,
            field_name=field_name,
            target_pattern=target_pattern,
            expected_type=expected_type,
            doc_id=doc_id,
            image=img,
        )

    if evidence is None:
        return {
            "field": field_name,
            "expected": expected_val,
            "extracted": "",
            "confidence": 0.0,
            "is_verified": False,
            "is_exact": False,
            "decision": "ABSTAIN",
            "reason": "Missing evidence / row not found",
        }

    extracted_val = str(evidence.value).strip()
    confidence = float(evidence.confidence)
    is_ambiguous = bool(evidence.is_ambiguous)

    # Verification decision under threshold T
    if is_ambiguous or (confidence < conf_threshold):
        is_verified = False
        decision = "ABSTAIN"
        reason = evidence.abstention_reason or f"Confidence below threshold ({confidence:.1f} < {conf_threshold:.1f})"
    else:
        is_verified = True
        decision = "VERIFY"
        reason = None

    is_exact = (extracted_val == expected_val)

    return {
        "field": field_name,
        "expected": expected_val,
        "extracted": extracted_val,
        "confidence": confidence,
        "is_verified": is_verified,
        "is_exact": is_exact,
        "decision": decision,
        "reason": reason,
    }


def run_calibration_sweep():
    configure_pytesseract()

    manifest_path = L25_DIR / "dataset_manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Combine Development and Calibration partitions
    eval_docs = []
    for doc_id, doc_data in manifest.items():
        if doc_data.get("cohort") in ["J_development", "J_calibration"]:
            doc_entry = dict(doc_data)
            doc_entry["id"] = doc_id
            doc_entry["fields"] = doc_data["critical_fields"]
            eval_docs.append(doc_entry)

    total_docs = len(eval_docs)
    total_fields = sum(len(d["fields"]) for d in eval_docs)
    print(f"Loaded {total_docs} calibration/dev docs with {total_fields} critical fields.")

    # Pre-parse table grids for efficiency
    doc_grids = {}
    doc_images = {}
    print("Pre-parsing table grids via pytesseract...")
    for doc in eval_docs:
        doc_id = doc["id"]
        img_path = Path(doc["image_path"])
        img = Image.open(img_path)
        ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
        grid = build_table_grid(ocr_data, page_width=img.width, page_height=img.height, image=img)
        doc_grids[doc_id] = grid
        doc_images[doc_id] = img

    thresholds = [40.0, 45.0, 50.0, 55.0, 60.0, 65.0, 70.0, 75.0, 80.0, 85.0, 90.0]
    sweep_results = []

    print("\nRunning threshold sweep across T in [40.0, 90.0]...")
    for T in thresholds:
        all_preds = []
        for doc in eval_docs:
            doc_id = doc["id"]
            grid = doc_grids[doc_id]
            img = doc_images[doc_id]
            for field in doc["fields"]:
                pred = evaluate_field(grid, field, doc_id, img, conf_threshold=T)
                all_preds.append(pred)

        n_verified = sum(1 for p in all_preds if p["is_verified"])
        n_exact = sum(1 for p in all_preds if p["is_verified"] and p["is_exact"])
        n_false = sum(1 for p in all_preds if p["is_verified"] and not p["is_exact"])
        n_abstain = sum(1 for p in all_preds if not p["is_verified"])

        precision = (n_exact / n_verified * 100.0) if n_verified > 0 else 100.0
        coverage = (n_verified / total_fields * 100.0)
        fvr = (n_false / n_verified * 100.0) if n_verified > 0 else 0.0

        calib = compute_calibration_metrics(all_preds)

        row = {
            "threshold": T,
            "total_fields": total_fields,
            "verified": n_verified,
            "exact": n_exact,
            "false_verifications": n_false,
            "abstentions": n_abstain,
            "precision": round(precision, 2),
            "coverage": round(coverage, 2),
            "false_verification_rate": round(fvr, 2),
            "ece": calib["ece"],
            "mce": calib["mce"],
            "brier": calib["brier"],
        }
        sweep_results.append(row)
        print(
            f"T={T:4.1f} | Verified: {n_verified:2d} | Exact: {n_exact:2d} | "
            f"False: {n_false:2d} | Abstain: {n_abstain:2d} | "
            f"Prec: {precision:6.2f}% | Cov: {coverage:5.2f}% | "
            f"ECE: {calib['ece']:.4f} | Brier: {calib['brier']:.4f}"
        )

    out_file = RESULTS_DIR / "calibration_sweep.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "cohort": "Cohort J (Development + Calibration)",
                "total_docs": total_docs,
                "total_fields": total_fields,
                "frozen_baseline_threshold": 70.0,
                "sweep": sweep_results,
            },
            f,
            indent=2,
        )
    print(f"\nSaved sweep results to {out_file}")


if __name__ == "__main__":
    run_calibration_sweep()
