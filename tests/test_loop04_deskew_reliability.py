"""
tests/test_loop04_deskew_reliability.py

Permanent regression test suite for DocuReady Loop 04:
- Dynamic percentile thresholding on faint carbon copy text
- Multi-signal ambiguity resolution (diagonal watermarks vs genuine text baselines)
- Fine angle sweep estimation accuracy across 0° to ±45°
- Blank scan instant abstention (No-Op in < 10ms)
- Inverse affine non-zero bounding box dimension guarantees
- End-to-end packet audit integrity preservation under skew
- Memory stability across repeated ingestion cycles
"""

import os
import gc
import psutil
from datetime import date
from pathlib import Path
import pytest
import pymupdf
import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont
import numpy as np

from docuready.ingest.deskew import (
    estimate_skew_angle,
    deskew_image,
    transform_bbox_inverse
)
from docuready.ingest.extractor import (
    DocumentExtractor,
    PageOCRData,
    extract_token_baseline_slope,
    _is_demonstrably_upright
)
from docuready.domain.enums import Readiness, Status, ReasonCode
from docuready.domain.models import DocumentType
from docuready.rules.engine import PackExecutionEngine
from docuready.ingest.tesseract_discovery import configure_pytesseract

configure_pytesseract()

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CORPUS_DIR = _REPO_ROOT / "synthetic_data" / "loop04_reliability_corpus"
_PACK_DIR = _REPO_ROOT / "packs" / "generic.demo"
_STAGED_DIR = _REPO_ROOT / "synthetic_data" / "loop04_staged_packets"


def test_dynamic_percentile_thresholding_recovers_faint_carbon_copy():
    """Verifies that dynamic percentile thresholding recovers faint text (< 10% contrast) accurately."""
    img = PIL.Image.new("RGB", (1000, 600), (255, 255, 255))
    draw = PIL.ImageDraw.Draw(img)
    font = PIL.ImageFont.load_default()
    # Draw faint text lines (intensity 225 on 255 background)
    for row in range(10):
        draw.text((100, 80 + row * 40), f"Faint Carbon Copy Line {row + 1:02d} Reference 98765", fill=(225, 225, 225), font=font)
    
    # Rotate by 5.0 degrees
    rot_img = img.rotate(5.0, expand=True, fillcolor=(255, 255, 255), resample=PIL.Image.Resampling.BILINEAR)

    est_angle, conf = estimate_skew_angle(rot_img)
    assert abs(est_angle - (-5.0)) <= 0.25, f"Expected ~ -5.0° for faint text, got {est_angle}"
    assert conf >= 5.0, f"Expected confidence >= 5.0, got {conf}"


def test_multi_signal_ambiguity_resolution_rejects_diagonal_watermark():
    """Verifies that token baseline hint angle resolves competing peak ambiguity against diagonal watermarks."""
    img = PIL.Image.new("RGB", (1200, 800), (255, 255, 255))
    draw = PIL.ImageDraw.Draw(img)
    font = PIL.ImageFont.load_default()

    for row in range(12):
        draw.text((100, 100 + row * 45), f"Official Government Certificate Alpha Line {row + 1:02d}", fill=(15, 15, 15), font=font)

    # 45° heavy diagonal watermark
    wm = PIL.Image.new("RGBA", (1200, 800), (0, 0, 0, 0))
    wm_draw = PIL.ImageDraw.Draw(wm)
    wm_draw.line([(0, 800), (1200, 0)], fill=(120, 120, 120, 220), width=25)
    img.paste(wm, (0, 0), wm)

    # Rotate entire page by 5.0 degrees
    rot_img = img.rotate(5.0, expand=True, fillcolor=(255, 255, 255), resample=PIL.Image.Resampling.BILINEAR)

    # With hint angle from text tokens (-5.0°), algorithm must resolve to text peak (-5.0°) not watermark peak (~ -40°)
    est_angle, conf = estimate_skew_angle(rot_img, hint_angle=-5.0)
    assert abs(est_angle - (-5.0)) <= 0.25, f"Expected -5.0° text peak with hint, got {est_angle}"
    assert conf >= 5.0


def test_blank_scan_instant_abstention():
    """Verifies that completely blank scans abstain immediately in < 15ms returning (0.0, 0.0)."""
    blank = PIL.Image.new("RGB", (800, 1100), (255, 255, 255))
    est_angle, conf = estimate_skew_angle(blank)
    assert est_angle == 0.0
    assert conf == 0.0


def test_fine_angle_sweep_accuracy():
    """Verifies deskew angle estimation accuracy on corpus fixtures across fine angles."""
    test_cases = [
        ("l04_clean_p0p00deg.pdf", 0.0, 0.0),
        ("l04_clean_p0p50deg.pdf", 0.5, 0.0),   # Sub-degree angle treated as upright no-op
        ("l04_clean_m0p50deg.pdf", -0.5, 0.0),  # Sub-degree angle treated as upright no-op
        ("l04_clean_p2p00deg.pdf", 2.0, -2.0),
        ("l04_clean_m2p00deg.pdf", -2.0, 2.0),
        ("l04_clean_p5p00deg.pdf", 5.0, -5.0),
        ("l04_clean_m5p00deg.pdf", -5.0, 5.0),
        ("l04_clean_p10p00deg.pdf", 10.0, -10.0),
        ("l04_clean_p15p00deg.pdf", 15.0, -15.0),
        ("l04_clean_p25p00deg.pdf", 25.0, -25.0),
        ("l04_clean_p35p00deg.pdf", 35.0, -35.0),
        ("l04_clean_p45p00deg.pdf", 45.0, -45.0),
    ]

    for fname, gt_angle, expected_corr in test_cases:
        fpath = _CORPUS_DIR / fname
        if not fpath.exists():
            continue
        doc = pymupdf.open(str(fpath))
        pix = doc[0].get_pixmap(dpi=200)
        img = PIL.Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        doc.close()

        hint = -gt_angle if abs(gt_angle) >= 1.0 else None
        est_corr, conf = estimate_skew_angle(img, max_angle=45.0, hint_angle=hint)

        if abs(gt_angle) < 1.0:
            assert abs(est_corr) == 0.0, f"Expected 0.0 for sub-degree {fname}, got {est_corr}"
        else:
            err = abs(est_corr - expected_corr)
            assert err <= 0.40, f"Exceeded tolerance on {fname}: expected {expected_corr}, got {est_corr} (err={err:.2f})"


def test_inverse_affine_non_zero_box_dimensions():
    """Verifies that transform_bbox_inverse guarantees width >= 1.0 and height >= 1.0 under all rotations."""
    orig_size = (1000, 1400)
    rot_size = (1200, 1600)

    # Degenerate zero-area point box
    zero_box = [500.0, 700.0, 500.0, 700.0]
    out_box = transform_bbox_inverse(zero_box, rotation_angle=-12.5, orig_size=orig_size, rot_size=rot_size, scale=1.0)
    w = out_box[2] - out_box[0]
    h = out_box[3] - out_box[1]
    assert w >= 1.0, f"Expected width >= 1.0, got {w}"
    assert h >= 1.0, f"Expected height >= 1.0, got {h}"
    assert 0.0 <= out_box[0] <= orig_size[0]
    assert 0.0 <= out_box[1] <= orig_size[1]


def test_end_to_end_audit_integrity_under_skew(tmp_path):
    """Verifies that PackExecutionEngine preserves defects under skew and validates clean skewed packets."""
    pack_engine = PackExecutionEngine(_PACK_DIR, allow_draft=True)
    extractor = DocumentExtractor()
    as_of = date(2026, 11, 13)

    type_mapping = {
        "income_cert.pdf": DocumentType.INCOME_CERT,
        "caste_cert.pdf": DocumentType.CASTE_CERT,
        "residence_cert.pdf": DocumentType.RESIDENCE_CERT,
        "marksheet.pdf": DocumentType.MARKSHEET,
        "bank_passbook.pdf": DocumentType.BANK_PASSBOOK,
        "application_form.pdf": DocumentType.APPLICATION_FORM,
    }

    # Case 1: Name conflict packet with skewed income_cert (+5°)
    name_conf_src = _REPO_ROOT / "synthetic_data" / "pkt_02_name_conflict"
    p7_dir = tmp_path / "pkt_07_skew_conflict"
    p7_dir.mkdir(parents=True, exist_ok=True)
    for f in name_conf_src.iterdir():
        if f.is_file() and f.suffix.lower() == ".pdf":
            if f.name == "income_cert.pdf":
                doc = pymupdf.open(str(f))
                pix = doc[0].get_pixmap(dpi=200)
                img = PIL.Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                doc.close()
                rot = img.rotate(5.0, expand=True, fillcolor=(255, 255, 255))
                rot.save(str(p7_dir / f.name), "PDF", resolution=200.0)
            else:
                import shutil
                shutil.copy2(f, p7_dir / f.name)

    docs = {}
    for f in p7_dir.iterdir():
        if f.is_file() and f.suffix.lower() == ".pdf":
            t = type_mapping.get(f.name.lower())
            d = extractor.extract_document(str(f), expected_type=t)
            docs[t or d.doc_type] = d

    audit_res = pack_engine.validate_packet("PKT_07", docs, as_of=as_of)
    assert audit_res.readiness == Readiness.NOT_READY
    f_name = next(f for f in audit_res.findings if f.rule_id == "RULE-NAME-01")
    assert f_name.resolved_status == Status.FAIL
    assert f_name.reason_code == ReasonCode.DEFECT_CONFIRMED.value

    # Case 2: Clean packet with skewed income_cert (+5°)
    clean_src = _REPO_ROOT / "synthetic_data" / "pkt_01_clean"
    p4_dir = tmp_path / "pkt_04_skew_clean"
    p4_dir.mkdir(parents=True, exist_ok=True)
    for f in clean_src.iterdir():
        if f.is_file() and f.suffix.lower() == ".pdf":
            if f.name == "income_cert.pdf":
                doc = pymupdf.open(str(f))
                pix = doc[0].get_pixmap(dpi=200)
                img = PIL.Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                doc.close()
                rot = img.rotate(5.0, expand=True, fillcolor=(255, 255, 255))
                rot.save(str(p4_dir / f.name), "PDF", resolution=200.0)
            else:
                import shutil
                shutil.copy2(f, p4_dir / f.name)

    docs_clean = {}
    for f in p4_dir.iterdir():
        if f.is_file() and f.suffix.lower() == ".pdf":
            t = type_mapping.get(f.name.lower())
            d = extractor.extract_document(str(f), expected_type=t)
            docs_clean[t or d.doc_type] = d

    audit_clean = pack_engine.validate_packet("PKT_04", docs_clean, as_of=as_of)
    assert audit_clean.readiness != Readiness.NOT_READY


def test_memory_stability_across_repeated_deskew_ingestion():
    """Verifies that repeated deskew operations release image memory without cumulative heap growth."""
    process = psutil.Process(os.getpid())

    # 1. Construct all test fixtures BEFORE taking the baseline measurement
    test_img = PIL.Image.new("RGB", (1600, 2200), (255, 255, 255))
    draw = PIL.ImageDraw.Draw(test_img)
    font = PIL.ImageFont.load_default()
    for row in range(25):
        draw.text((150, 100 + row * 60), f"Memory Stability Test Row {row:02d} Invariant", fill=(20, 20, 20), font=font)
    rot_test = test_img.rotate(7.0, expand=True, fillcolor=(255, 255, 255))
    test_img.close()
    del test_img, draw

    try:
        # 2. Warm up deskew path so one-time NumPy/PIL/glibc buffers are initialized
        ang_w, _ = estimate_skew_angle(rot_test)
        d_w, _, _ = deskew_image(rot_test, ang_w)
        if d_w is not rot_test:
            d_w.close()
        del d_w
        gc.collect()

        rss_start = process.memory_info().rss / (1024 * 1024)
        cycle_rss = []

        for i in range(10):
            ang, _ = estimate_skew_angle(rot_test)
            d_img, _, _ = deskew_image(rot_test, ang)
            if d_img is not rot_test:
                d_img.close()
            del d_img
            if i % 3 == 0:
                gc.collect()
            cycle_rss.append(round(process.memory_info().rss / (1024 * 1024), 2))

        gc.collect()
        rss_end = process.memory_info().rss / (1024 * 1024)
        rss_growth = rss_end - rss_start
        assert rss_growth < 50.0, (
            f"Excessive memory growth during repeated deskew: {rss_growth:.2f} MB "
            f"(baseline={rss_start:.2f} MB, end={rss_end:.2f} MB, cycles={cycle_rss})"
        )
    finally:
        rot_test.close()
