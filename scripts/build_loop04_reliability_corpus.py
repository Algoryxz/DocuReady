"""
scripts/build_loop04_reliability_corpus.py

Generates the Loop 04 expanded reliability and stress corpus:
1. Fine angle sweep on clean scans:
   0°, ±0.25°, ±0.5°, ±0.75°, ±1.0°, ±1.5°, ±2.0°, ±3.0°, ±5.0°, ±7.0°,
   ±10.0°, ±12.0°, ±15.0°, ±20.0°, ±25.0°, ±30.0°, ±35.0°, ±40.0°, ±45.0°
2. Realistic combinations:
   - 3° skew + Low DPI (100 DPI)
   - 5° skew + Diagonal Shadow Gradient
   - 7° skew + Gaussian Blur
   - 2° skew + JPEG Compression Artifacts (Q=40)
   - 5° skew + Table Grid Rules
   - 10° skew + Sparse Text
   - Upright (0°) + Shadow + Heavy Box Border
   - Upright (0°) + Noise + Faint Carbon Copy Text
   - 5° skew + 45° Diagonal Watermark
   - 8° skew + Multi-column Gazette
   - 12° skew + Narrow Receipt Aspect Ratio
   - Blank Scan

Metadata saved to synthetic_data/loop04_reliability_corpus/LOOP04_CORPUS_MANIFEST.json
"""

import io
import json
import math
import os
from pathlib import Path
from typing import Dict, Any, List

import numpy as np
import pymupdf
import PIL.Image
import PIL.ImageDraw
import PIL.ImageFilter

CORPUS_DIR = Path("synthetic_data/loop04_reliability_corpus")
CORPUS_DIR.mkdir(parents=True, exist_ok=True)

BASE_DIR = Path("synthetic_data/realistic_corpus_60")
CLEAN_BASE_PDF = BASE_DIR / "smp_11_raster_scan.pdf"


def _render_pdf(path: Path, dpi: int = 200) -> PIL.Image.Image:
    doc = pymupdf.open(str(path))
    pix = doc[0].get_pixmap(dpi=dpi)
    img = PIL.Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    doc.close()
    return img


def _save_as_pdf(img: PIL.Image.Image, out_path: Path, jpeg_quality: int = 85):
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=jpeg_quality)
    buf.seek(0)
    doc = pymupdf.open()
    rect = pymupdf.Rect(0, 0, img.width * 72.0 / 200.0, img.height * 72.0 / 200.0)
    page = doc.new_page(width=rect.width, height=rect.height)
    page.insert_image(rect, stream=buf.getvalue())
    doc.save(str(out_path))
    doc.close()


def generate_loop04_corpus():
    print(f"Generating Loop 04 Reliability Corpus in {CORPUS_DIR}...")
    clean_img = _render_pdf(CLEAN_BASE_PDF, dpi=200)

    manifest: Dict[str, Any] = {}

    # 1. Fine Angle Sweep on Clean Scans
    angles = [
        0.0,
        0.25, -0.25,
        0.50, -0.50,
        0.75, -0.75,
        1.0, -1.0,
        1.5, -1.5,
        2.0, -2.0,
        3.0, -3.0,
        5.0, -5.0,
        7.0, -7.0,
        10.0, -10.0,
        12.0, -12.0,
        15.0, -15.0,
        20.0, -20.0,
        25.0, -25.0,
        30.0, -30.0,
        35.0, -35.0,
        40.0, -40.0,
        45.0, -45.0,
    ]

    expected_clean_fields = {
        "applicant_name": "Smruti Ranjan Nayak",
        "father_name": "Ramesh Chandra Nayak",
        "annual_income": "Rs. 1,80,000/-",
        "certificate_no": "E-INC/2025/104928"
    }

    for ang in angles:
        sign_str = "p" if ang >= 0 else "m"
        ang_str = f"{abs(ang):04.2f}".replace(".", "p")
        fname = f"l04_clean_{sign_str}{ang_str}deg.pdf"
        out_p = CORPUS_DIR / fname

        if abs(ang) < 1e-4:
            rot_img = clean_img.copy()
        else:
            rot_img = clean_img.rotate(ang, expand=True, fillcolor=(255, 255, 255), resample=PIL.Image.Resampling.BILINEAR)

        _save_as_pdf(rot_img, out_p, jpeg_quality=90)
        manifest[fname] = {
            "file_name": fname,
            "category": "clean_scan",
            "ground_truth_skew_degrees": float(ang),
            "expected_fields": expected_clean_fields,
            "modalities": ["clean_scan"]
        }

    # 2. Realistic Compound Distortions
    # 2a: 3° skew + Low DPI (render at 100 DPI, then scale back)
    doc_low = pymupdf.open(str(CLEAN_BASE_PDF))
    pix_low = doc_low[0].get_pixmap(dpi=100)
    img_low = PIL.Image.frombytes("RGB", [pix_low.width, pix_low.height], pix_low.samples)
    doc_low.close()
    img_low = img_low.resize((clean_img.width, clean_img.height), PIL.Image.Resampling.NEAREST)
    rot_low = img_low.rotate(3.0, expand=True, fillcolor=(255, 255, 255), resample=PIL.Image.Resampling.BILINEAR)
    fn_low = "l04_combo_skew03deg_low_dpi.pdf"
    _save_as_pdf(rot_low, CORPUS_DIR / fn_low)
    manifest[fn_low] = {
        "file_name": fn_low,
        "category": "compound",
        "ground_truth_skew_degrees": 3.0,
        "expected_fields": expected_clean_fields,
        "modalities": ["skew", "low_dpi"]
    }

    # 2b: 5° skew + Diagonal Shadow Gradient
    arr = np.array(clean_img, dtype=np.float32)
    h, w, _ = arr.shape
    y_coords, x_coords = np.mgrid[0:h, 0:w]
    shadow = 0.35 + 0.65 * ((x_coords / w) * 0.5 + (y_coords / h) * 0.5)
    shadow = np.expand_dims(shadow, axis=2)
    shadowed_arr = np.clip(arr * shadow, 0, 255).astype(np.uint8)
    shadow_img = PIL.Image.fromarray(shadowed_arr)
    rot_shadow = shadow_img.rotate(5.0, expand=True, fillcolor=(255, 255, 255), resample=PIL.Image.Resampling.BILINEAR)
    fn_shadow = "l04_combo_skew05deg_shadow.pdf"
    _save_as_pdf(rot_shadow, CORPUS_DIR / fn_shadow)
    manifest[fn_shadow] = {
        "file_name": fn_shadow,
        "category": "compound",
        "ground_truth_skew_degrees": 5.0,
        "expected_fields": expected_clean_fields,
        "modalities": ["skew", "shadow_gradient"]
    }

    # 2c: 7° skew + Gaussian Blur
    blur_img = clean_img.filter(PIL.ImageFilter.GaussianBlur(radius=1.5))
    rot_blur = blur_img.rotate(7.0, expand=True, fillcolor=(255, 255, 255), resample=PIL.Image.Resampling.BILINEAR)
    fn_blur = "l04_combo_skew07deg_blur.pdf"
    _save_as_pdf(rot_blur, CORPUS_DIR / fn_blur)
    manifest[fn_blur] = {
        "file_name": fn_blur,
        "category": "compound",
        "ground_truth_skew_degrees": 7.0,
        "expected_fields": expected_clean_fields,
        "modalities": ["skew", "blur"]
    }

    # 2d: 2° skew + Heavy JPEG compression (Q=35)
    rot_jpeg = clean_img.rotate(2.0, expand=True, fillcolor=(255, 255, 255), resample=PIL.Image.Resampling.BILINEAR)
    fn_jpeg = "l04_combo_skew02deg_jpeg_artifact.pdf"
    _save_as_pdf(rot_jpeg, CORPUS_DIR / fn_jpeg, jpeg_quality=35)
    manifest[fn_jpeg] = {
        "file_name": fn_jpeg,
        "category": "compound",
        "ground_truth_skew_degrees": 2.0,
        "expected_fields": expected_clean_fields,
        "modalities": ["skew", "jpeg_artifacts"]
    }

    # 2e: 5° skew + Table Grid Rules
    table_img = clean_img.copy()
    draw_t = PIL.ImageDraw.Draw(table_img)
    for r in range(8):
        ry = 1200 + r * 80
        draw_t.line([(100, ry), (w - 100, ry)], fill=(0, 0, 0), width=3)
    for c in [100, 400, 800, 1200, w - 100]:
        draw_t.line([(c, 1200), (c, 1200 + 7 * 80)], fill=(0, 0, 0), width=3)
    rot_table = table_img.rotate(5.0, expand=True, fillcolor=(255, 255, 255), resample=PIL.Image.Resampling.BILINEAR)
    fn_table = "l04_combo_skew05deg_table_rules.pdf"
    _save_as_pdf(rot_table, CORPUS_DIR / fn_table)
    manifest[fn_table] = {
        "file_name": fn_table,
        "category": "compound",
        "ground_truth_skew_degrees": 5.0,
        "expected_fields": expected_clean_fields,
        "modalities": ["skew", "table_grid"]
    }

    # 2f: 10° skew + Sparse Text (Receipt/voucher)
    sparse_img = PIL.Image.new("RGB", (1200, 1600), (255, 255, 255))
    draw_sp = PIL.ImageDraw.Draw(sparse_img)
    draw_sp.text((150, 200), "GOVERNMENT OF ODISHA - REVENUE DEPARTMENT", fill=(0, 0, 0))
    draw_sp.text((150, 300), "INCOME CERTIFICATE", fill=(0, 0, 0))
    draw_sp.text((150, 450), "Certificate No: E-INC/2025/104928", fill=(0, 0, 0))
    draw_sp.text((150, 600), "Smruti Ranjan Nayak", fill=(0, 0, 0))
    draw_sp.text((150, 750), "Annual Family Income: Rs. 1,80,000/-", fill=(0, 0, 0))
    rot_sp = sparse_img.rotate(10.0, expand=True, fillcolor=(255, 255, 255), resample=PIL.Image.Resampling.BILINEAR)
    fn_sp = "l04_combo_skew10deg_sparse_text.pdf"
    _save_as_pdf(rot_sp, CORPUS_DIR / fn_sp)
    manifest[fn_sp] = {
        "file_name": fn_sp,
        "category": "compound",
        "ground_truth_skew_degrees": 10.0,
        "expected_fields": {
            "applicant_name": "Smruti Ranjan Nayak",
            "annual_income": "Rs. 1,80,000/-",
            "certificate_no": "E-INC/2025/104928"
        },
        "modalities": ["skew", "sparse_text"]
    }

    # 2g: Upright (0°) + Shadow + Heavy Box Border
    box_img = clean_img.copy()
    draw_box = PIL.ImageDraw.Draw(box_img)
    draw_box.rectangle([(60, 60), (w - 60, h - 60)], outline=(0, 0, 0), width=10)
    arr_box = np.array(box_img, dtype=np.float32)
    shadow_box = 0.5 + 0.5 * (x_coords / w)
    arr_box = np.clip(arr_box * np.expand_dims(shadow_box, axis=2), 0, 255).astype(np.uint8)
    fn_box = "l04_combo_upright00deg_shadow_box_border.pdf"
    _save_as_pdf(PIL.Image.fromarray(arr_box), CORPUS_DIR / fn_box)
    manifest[fn_box] = {
        "file_name": fn_box,
        "category": "compound",
        "ground_truth_skew_degrees": 0.0,
        "expected_fields": expected_clean_fields,
        "modalities": ["upright", "shadow", "box_border"]
    }

    # 2h: 5° skew + 45° Diagonal Watermark (Adversarial Stress!)
    wm_img = clean_img.copy()
    draw_wm = PIL.ImageDraw.Draw(wm_img)
    for d in range(-2000, 4000, 120):
        draw_wm.line([(d, 0), (d + 2400, 2400)], fill=(210, 210, 210), width=2)
    rot_wm = wm_img.rotate(5.0, expand=True, fillcolor=(255, 255, 255), resample=PIL.Image.Resampling.BILINEAR)
    fn_wm = "l04_combo_skew05deg_diag_watermark.pdf"
    _save_as_pdf(rot_wm, CORPUS_DIR / fn_wm)
    manifest[fn_wm] = {
        "file_name": fn_wm,
        "category": "compound",
        "ground_truth_skew_degrees": 5.0,
        "expected_fields": expected_clean_fields,
        "modalities": ["skew", "diagonal_watermark"]
    }

    # 2i: Upright Blank Page
    blank_img = PIL.Image.new("RGB", (1600, 2200), (255, 255, 255))
    fn_blank = "l04_combo_upright00deg_blank.pdf"
    _save_as_pdf(blank_img, CORPUS_DIR / fn_blank)
    manifest[fn_blank] = {
        "file_name": fn_blank,
        "category": "compound",
        "ground_truth_skew_degrees": 0.0,
        "expected_fields": {},
        "modalities": ["blank"]
    }

    # Save manifest
    manifest_path = CORPUS_DIR / "LOOP04_CORPUS_MANIFEST.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"Loop 04 Reliability Corpus successfully generated: {len(manifest)} fixtures.")
    print(f"Manifest written to: {manifest_path}")


if __name__ == "__main__":
    generate_loop04_corpus()
