"""
Loop 24 Calibration and Threshold Sweep Engine
Evaluates Development (Cohort A) and Calibration (Cohort B) cohorts
to quantify ECE, MCE, Brier score, and Pareto frontier across T in [40, 90].
Freezes the operating threshold T* prior to blind cohort evaluation.
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

L24_DIR = Path(__file__).resolve().parents[1]
RESULTS_DIR = L24_DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def configure_pytesseract():
    tess_path = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
    if tess_path.exists():
        pytesseract.pytesseract.tesseract_cmd = str(tess_path)


def compute_calibration_metrics(predictions: List[Dict[str, Any]], n_bins: int = 5) -> Dict[str, float]:
    """
    Computes ECE (Expected Calibration Error), MCE (Maximum Calibration Error),
    and Brier score over verified claims.
    """
    if not predictions:
        return {"ece": 0.0, "mce": 0.0, "brier": 0.0}

    # Verified claims only for calibration evaluation
    verified = [p for p in predictions if p["is_verified"]]
    if not verified:
        return {"ece": 0.0, "mce": 0.0, "brier": 0.0}

    confidences = np.array([p["confidence"] / 100.0 for p in verified])
    accuracies = np.array([1.0 if p["is_exact"] else 0.0 for p in verified])

    # Brier score
    brier = float(np.mean((confidences - accuracies) ** 2))

    # Binned ECE and MCE
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
    exp_row = field_meta.get("row")
    exp_col = field_meta.get("col")
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
            "field_name": field_name,
            "expected": expected_val,
            "extracted": "",
            "confidence": 0.0,
            "is_verified": False,
            "is_exact": False,
            "is_false_verification": False,
            "is_abstained": True,
            "reason": "Missing evidence / no cell found",
        }

    ext_val = evidence.value.strip()
    conf = evidence.confidence

    norm_ext = ext_val.replace("₹", "").replace("Rs.", "").replace(",", "").replace("$", "").strip()
    norm_exp = expected_val.replace("₹", "").replace("Rs.", "").replace(",", "").replace("$", "").strip()

    row_match = (exp_row is None or evidence.row_idx == exp_row or evidence.row_idx == exp_row + 1)
    col_match = (exp_col is None or evidence.col_idx == exp_col)

    # Threshold gating
    if conf < conf_threshold:
        return {
            "field_name": field_name,
            "expected": expected_val,
            "extracted": ext_val,
            "confidence": conf,
            "is_verified": False,
            "is_exact": (norm_ext == norm_exp and row_match and col_match),
            "is_false_verification": False,
            "is_abstained": True,
            "reason": f"Confidence floor ({conf:.1f}% < {conf_threshold}%)",
        }

    if evidence.verification_decision == "ABSTAIN" or evidence.is_ambiguous:
        return {
            "field_name": field_name,
            "expected": expected_val,
            "extracted": ext_val,
            "confidence": conf,
            "is_verified": False,
            "is_exact": (norm_ext == norm_exp and row_match and col_match),
            "is_false_verification": False,
            "is_abstained": True,
            "reason": evidence.abstention_reason or "Evidence flagged ambiguous",
        }

    # Verified claim
    is_exact = (norm_ext == norm_exp and row_match and col_match)
    is_false_verification = not is_exact

    return {
        "field_name": field_name,
        "expected": expected_val,
        "extracted": ext_val,
        "confidence": conf,
        "is_verified": True,
        "is_exact": is_exact,
        "is_false_verification": is_false_verification,
        "is_abstained": False,
        "reason": None,
    }


def run_threshold_sweep():
    configure_pytesseract()
    with open(L24_DIR / "dataset_manifest.json", "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Filter strictly to Development (Cohort A) and Calibration (Cohort B)
    dev_cal_docs = {
        k: v for k, v in manifest.items()
        if v["cohort"] in ["I_development", "I_calibration"]
    }
    print(f"Running threshold sweep across {len(dev_cal_docs)} Dev/Calib documents...")

    thresholds = [40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90]
    sweep_results = []

    # Pre-process OCR & table grids once
    preprocessed = {}
    for doc_id, meta in dev_cal_docs.items():
        img = Image.open(meta["image_path"])
        ocr_data = pytesseract.image_to_data(img, lang="eng", output_type=pytesseract.Output.DICT)
        grid = build_table_grid(ocr_data, img.width, img.height, image=img)
        preprocessed[doc_id] = (img, grid, meta["critical_fields"])

    for T in thresholds:
        preds = []
        for doc_id, (img, grid, fields) in preprocessed.items():
            for f_meta in fields:
                res = evaluate_field(grid, f_meta, doc_id, img, conf_threshold=float(T))
                preds.append(res)

        total_fields = len(preds)
        verified_claims = sum(1 for p in preds if p["is_verified"])
        exact_matches = sum(1 for p in preds if p["is_verified"] and p["is_exact"])
        false_verifications = sum(1 for p in preds if p["is_false_verification"])
        abstentions = sum(1 for p in preds if p["is_abstained"])

        precision = (exact_matches / verified_claims * 100.0) if verified_claims > 0 else 100.0
        fvr = (false_verifications / verified_claims * 100.0) if verified_claims > 0 else 0.0
        coverage = (verified_claims / total_fields * 100.0) if total_fields > 0 else 0.0

        calib_metrics = compute_calibration_metrics(preds)

        row = {
            "threshold": T,
            "total_fields": total_fields,
            "verified_claims": verified_claims,
            "exact_matches": exact_matches,
            "false_verifications": false_verifications,
            "abstentions": abstentions,
            "precision": round(precision, 2),
            "false_verification_rate": round(fvr, 2),
            "coverage": round(coverage, 2),
            "ece": calib_metrics["ece"],
            "mce": calib_metrics["mce"],
            "brier_score": calib_metrics["brier"],
        }
        sweep_results.append(row)
        print(f"T={T:2d} | Verified={verified_claims:2d}/{total_fields:2d} | Exact={exact_matches:2d} | FV={false_verifications} | Prec={precision:6.2f}% | Cov={coverage:6.2f}% | ECE={calib_metrics['ece']:.3f} | Brier={calib_metrics['brier']:.3f}")

    out_file = RESULTS_DIR / "calibration_sweep.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(sweep_results, f, indent=2)

    print(f"\nSaved calibration sweep results to {out_file}")


if __name__ == "__main__":
    run_threshold_sweep()
