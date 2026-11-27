"""
scripts/build_skew_corpus.py

Generates a controlled, reproducible non-orthogonal skew benchmark corpus for DocuReady Loop 03.
Creates fixtures with precise ground-truth rotation angles:
- Angles: 0°, ±2°, ±3°, ±5°, ±7°, ±10°, ±12°, ±15°, ±20°, ±25°, ±30°, ±35°, ±45°
- Modalities: Clean scan, Low-DPI, Shadow gradient, Table with rules
- Metadata manifest: synthetic_data/skew_corpus/SKEW_CORPUS_MANIFEST.json
"""
import io
import json
import os
from pathlib import Path
from typing import Dict, Any, List

import PIL.Image
import PIL.ImageDraw
import pymupdf

SKEW_CORPUS_DIR = Path("synthetic_data/skew_corpus")
SKEW_CORPUS_DIR.mkdir(parents=True, exist_ok=True)

CORPUS_DIR = Path("synthetic_data/realistic_corpus_60")
CLEAN_BASE = CORPUS_DIR / "smp_11_raster_scan.pdf"
LOW_DPI_BASE = CORPUS_DIR / "smp_25_low_dpi.pdf"
SHADOW_BASE = CORPUS_DIR / "smp_37_shadow_gradient.pdf"

ANGLES = [
    0.0,
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
    45.0, -45.0,
]


def _render_pdf(path: Path, dpi: int = 200) -> PIL.Image.Image:
    doc = pymupdf.open(str(path))
    pix = doc[0].get_pixmap(dpi=dpi)
    img = PIL.Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    doc.close()
    return img


def _save_as_pdf(img: PIL.Image.Image, output_path: Path):
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    buf.seek(0)
    doc = pymupdf.open()
    rect = pymupdf.Rect(0, 0, img.width * 72.0 / 200.0, img.height * 72.0 / 200.0)
    page = doc.new_page(width=rect.width, height=rect.height)
    page.insert_image(rect, stream=buf.getvalue())
    doc.save(str(output_path))
    doc.close()


def generate_skew_corpus():
    print(f"Generating skew corpus in {SKEW_CORPUS_DIR}...")
    clean_img = _render_pdf(CLEAN_BASE, dpi=200)
    low_dpi_img = _render_pdf(LOW_DPI_BASE, dpi=200)
    shadow_img = _render_pdf(SHADOW_BASE, dpi=200)

    # Table template
    w, h = clean_img.size
    table_img = PIL.Image.new("RGB", (w, h), (255, 255, 255))
    draw_t = PIL.ImageDraw.Draw(table_img)
    draw_t.text((150, 150), "GOVERNMENT OF ODISHA - REVENUE DEPARTMENT", fill=(0, 0, 0))
    draw_t.text((150, 200), "ANNUAL INCOME SCHEDULE ASSESSMENT TABLE", fill=(0, 0, 0))
    for r in range(10):
        ry = 280 + r * 90
        draw_t.line([(100, ry), (w - 100, ry)], fill=(0, 0, 0), width=3)
        draw_t.text((120, ry + 20), f"SCHEDULE ROW {r+1}: VERIFIED ANNUAL CITIZEN ASSESSMENT VALUE", fill=(0, 0, 0))
    for c in [100, 350, 750, 1150, w - 100]:
        draw_t.line([(c, 280), (c, 280 + 9 * 90)], fill=(0, 0, 0), width=3)

    manifest: Dict[str, Any] = {}

    # 1. Angle sweep on clean scan
    for angle in ANGLES:
        sign_str = "p" if angle >= 0 else "m"
        fn = f"skew_clean_{sign_str}{abs(int(angle)):02d}deg.pdf"
        out_p = SKEW_CORPUS_DIR / fn

        if angle == 0.0:
            rot_img = clean_img.copy()
        else:
            # PIL rotate: counter-clockwise positive
            rot_img = clean_img.rotate(angle, expand=True, fillcolor=(255, 255, 255))

        _save_as_pdf(rot_img, out_p)
        manifest[fn] = {
            "file_name": fn,
            "category": "clean_scan",
            "ground_truth_skew_degrees": angle,
            "width_px": rot_img.width,
            "height_px": rot_img.height,
            "expected_fields": {
                "applicant_name": "Smruti Ranjan Nayak",
                "father_name": "Ramesh Chandra Nayak",
                "annual_income": "Rs. 1,80,000/-",
                "certificate_no": "E-INC/2025/104928"
            }
        }

    # 2. Modality tests at critical angles (±5°, ±10°, ±15°)
    modality_configs = [
        ("low_dpi", low_dpi_img),
        ("shadow", shadow_img),
        ("table", table_img)
    ]
    critical_angles = [5.0, -5.0, 10.0, -10.0, 15.0, -15.0]

    for mod_name, base_i in modality_configs:
        for angle in critical_angles:
            sign_str = "p" if angle >= 0 else "m"
            fn = f"skew_{mod_name}_{sign_str}{abs(int(angle)):02d}deg.pdf"
            out_p = SKEW_CORPUS_DIR / fn
            rot_img = base_i.rotate(angle, expand=True, fillcolor=(255, 255, 255))
            _save_as_pdf(rot_img, out_p)
            manifest[fn] = {
                "file_name": fn,
                "category": mod_name,
                "ground_truth_skew_degrees": angle,
                "width_px": rot_img.width,
                "height_px": rot_img.height,
                "expected_fields": {
                    "applicant_name": "Smruti Ranjan Nayak"
                } if mod_name != "table" else {}
            }

    manifest_path = SKEW_CORPUS_DIR / "SKEW_CORPUS_MANIFEST.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"Generated {len(manifest)} skew fixtures. Manifest written to {manifest_path}")


if __name__ == "__main__":
    generate_skew_corpus()
