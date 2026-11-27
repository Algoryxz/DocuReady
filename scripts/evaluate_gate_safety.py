"""
scripts/evaluate_gate_safety.py

Comprehensive evaluation harness for DocuReady Loop 02:
Evaluates orientation classification safety, false-upright rates, recovery correctness,
and bounding-box validity across both the Realistic 60-Corpus and the Attack Corpus.
Outputs detailed JSON and Markdown summaries.
"""
import io
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List

import pymupdf
import PIL.Image
import pytesseract

from docuready.ingest.tesseract_discovery import configure_pytesseract
from docuready.ingest.extractor import (
    DocumentExtractor,
    PageOCRData,
    _is_demonstrably_upright,
    _ocr_page,
    OSD_FAST_PATH_MIN_TOKENS,
    OSD_FAST_PATH_MIN_MEAN_CONF,
    OSD_FAST_PATH_MIN_HIGH_CONF_RATIO,
    OSD_FAST_PATH_MIN_HORIZ_RATIO,
    OSD_FAST_PATH_HIGH_CONF_THRESH,
)
from docuready.domain.models import DocumentType

configure_pytesseract()

REALISTIC_DIR = Path("synthetic_data/realistic_corpus_60")
ATTACK_DIR = Path("synthetic_data/attack_corpus")
OUT_JSON = Path("docs/04-VALIDATION/LOOP_02_GATE_SAFETY_RESULTS.json")
OUT_MD = Path("docs/04-VALIDATION/LOOP_02_GATE_SAFETY_SUMMARY.md")


def get_ground_truth_orientation(file_name: str) -> int:
    fn = file_name.lower()
    if "90deg" in fn or "skew_10deg" in fn or "skew_15deg" in fn:
        if "90deg" in fn:
            return 90
        elif "10deg" in fn:
            return 10
        elif "15deg" in fn:
            return 15
    if "180deg" in fn or "inverted" in fn:
        return 180
    if "270deg" in fn:
        return 270
    if "mixed" in fn:
        return 999  # Mixed
    return 0


def evaluate_single_fixture(pdf_path: Path, expected_type: DocumentType = DocumentType.INCOME_CERT) -> Dict[str, Any]:
    file_name = pdf_path.name
    gt_rot = get_ground_truth_orientation(file_name)
    is_actually_upright = (gt_rot == 0 or abs(gt_rot) <= 5)

    doc = pymupdf.open(str(pdf_path))
    page = doc[0]
    p_rect = page.rect
    page_w, page_h = p_rect.width, p_rect.height

    # 1. Speculative token OCR at 0°
    pix = page.get_pixmap(dpi=200)
    img = PIL.Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    img_w, img_h = img.size
    pix = None

    t0 = time.perf_counter()
    try:
        data_0 = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT, timeout=15)
    except Exception:
        data_0 = {"text": [], "conf": [], "left": [], "top": [], "width": [], "height": []}
    speculative_ocr_ms = (time.perf_counter() - t0) * 1000.0

    # Token stats
    texts = data_0.get("text", [])
    confs = data_0.get("conf", [])
    widths = data_0.get("width", [])
    heights = data_0.get("height", [])

    valid_tokens = []
    for text, conf, w, h in zip(texts, confs, widths, heights):
        word = str(text).strip()
        c = float(conf)
        if word and c >= 0:
            valid_tokens.append((word, c, float(w), float(h)))

    total_tokens = len(valid_tokens)
    mean_conf = (sum(t[1] for t in valid_tokens) / total_tokens) if total_tokens > 0 else 0.0
    high_conf_count = sum(1 for t in valid_tokens if t[1] >= OSD_FAST_PATH_HIGH_CONF_THRESH)
    high_conf_ratio = (high_conf_count / total_tokens) if total_tokens > 0 else 0.0
    horiz_count = sum(1 for t in valid_tokens if t[2] >= t[3])
    horiz_ratio = (horiz_count / total_tokens) if total_tokens > 0 else 0.0

    # Gate decision
    gate_decision_upright = _is_demonstrably_upright(data_0)

    # Classification matrix classification
    if is_actually_upright:
        if gate_decision_upright:
            classification = "TRUE_UPRIGHT_FAST_PATH"
        else:
            classification = "UPRIGHT_FALLBACK_TO_OSD"
    else:
        if gate_decision_upright:
            classification = "CRITICAL_ROTATED_FALSE_UPRIGHT"
        else:
            classification = "ROTATED_CORRECTLY_REJECTED"

    # End-to-end extraction through production extractor
    ext = DocumentExtractor()
    t0_ext = time.perf_counter()
    extracted_doc = ext.extract_document(str(pdf_path), expected_type=expected_type)
    total_ext_ms = (time.perf_counter() - t0_ext) * 1000.0

    # Bounding box validity
    bbox_valid = True
    for f_name, f_val in extracted_doc.fields.items():
        if f_val.provenance and f_val.provenance.bounding_box:
            bx = f_val.provenance.bounding_box
            # Check within bounds
            if bx[0] < -5.0 or bx[1] < -5.0 or bx[2] > page_w + 5.0 or bx[3] > page_h + 5.0:
                bbox_valid = False
            if bx[0] > bx[2] or bx[1] > bx[3]:
                bbox_valid = False

    doc.close()

    return {
        "file_name": file_name,
        "path": str(pdf_path),
        "ground_truth_orientation": gt_rot,
        "is_actually_upright": is_actually_upright,
        "page_dimensions_pt": [round(page_w, 1), round(page_h, 1)],
        "raster_dimensions_px": [img_w, img_h],
        "speculative_ocr_ms": round(speculative_ocr_ms, 2),
        "total_extraction_ms": round(total_ext_ms, 2),
        "token_metrics": {
            "total_tokens": total_tokens,
            "mean_confidence": round(mean_conf, 2),
            "high_confidence_ratio": round(high_conf_ratio, 3),
            "horizontal_token_ratio": round(horiz_ratio, 3),
        },
        "gate_decision_upright": gate_decision_upright,
        "classification": classification,
        "extraction_status": extracted_doc.status,
        "fields_extracted_count": len(extracted_doc.fields),
        "extracted_fields": list(extracted_doc.fields.keys()),
        "bounding_box_valid": bbox_valid,
    }


def run_evaluation():
    print("=" * 70)
    print("DOCUREADY LOOP 02 — GATE SAFETY & RECOVERY EVALUATION")
    print("=" * 70)

    # Collect fixtures
    realistic_files = sorted(list(REALISTIC_DIR.glob("*.pdf")))
    attack_files = sorted(list(ATTACK_DIR.glob("*.pdf")))

    all_fixtures = [("realistic", f) for f in realistic_files if not f.name.startswith("smp_60")] + [("attack", f) for f in attack_files]

    results = []
    print(f"Evaluating {len(all_fixtures)} document fixtures...")

    for category, fpath in all_fixtures:
        res = evaluate_single_fixture(fpath)
        res["corpus_category"] = category
        results.append(res)
        mark = "✓" if res["classification"] != "CRITICAL_ROTATED_FALSE_UPRIGHT" else "FAIL"
        print(f"[{mark}] {res['file_name']:<35} | GT={res['ground_truth_orientation']}° | Gate={res['gate_decision_upright']} | {res['classification']} | {res['total_extraction_ms']} ms")

    # Aggregate Statistics
    total_count = len(results)
    true_uprights = [r for r in results if r["is_actually_upright"]]
    rotated_docs = [r for r in results if not r["is_actually_upright"]]

    upright_fast_path_count = sum(1 for r in true_uprights if r["gate_decision_upright"])
    upright_fallback_count = sum(1 for r in true_uprights if not r["gate_decision_upright"])
    rotated_false_upright_count = sum(1 for r in rotated_docs if r["gate_decision_upright"])
    rotated_rejected_count = sum(1 for r in rotated_docs if not r["gate_decision_upright"])

    upright_fast_path_rate = (upright_fast_path_count / len(true_uprights)) * 100.0 if true_uprights else 0.0
    rotated_false_upright_rate = (rotated_false_upright_count / len(rotated_docs)) * 100.0 if rotated_docs else 0.0

    print("\n" + "=" * 70)
    print("GATE SAFETY SUMMARY STATISTICS:")
    print("=" * 70)
    print(f"Total Evaluated Fixtures: {total_count}")
    print(f"Actual Upright Documents: {len(true_uprights)}")
    print(f"  -> Upright Fast-Path (Accepted): {upright_fast_path_count} ({upright_fast_path_rate:.1f}%)")
    print(f"  -> Upright Safe Fallback (OSD):  {upright_fallback_count}")
    print(f"Actual Rotated / Adversarial: {len(rotated_docs)}")
    print(f"  -> Correctly Rejected (OSD/Fail): {rotated_rejected_count}")
    print(f"  -> CRITICAL False-Upright:       {rotated_false_upright_count} ({rotated_false_upright_rate:.2f}%)")

    output_data = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "summary": {
            "total_fixtures": total_count,
            "actual_upright_count": len(true_uprights),
            "upright_fast_path_rate_pct": round(upright_fast_path_rate, 2),
            "actual_rotated_count": len(rotated_docs),
            "rotated_false_upright_count": rotated_false_upright_count,
            "rotated_false_upright_rate_pct": round(rotated_false_upright_rate, 2),
            "rotated_correctly_rejected_count": rotated_rejected_count,
        },
        "critical_failures": [r for r in results if r["classification"] == "CRITICAL_ROTATED_FALSE_UPRIGHT"],
        "fixtures": results,
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)
    print(f"\nDetailed evaluation written to {OUT_JSON}")


if __name__ == "__main__":
    run_evaluation()
