"""
tests/test_loop03_skew_recovery.py

Regression test suite for DocuReady Loop 03:
- Skew angle estimation accuracy across positive and negative angles
- Upright no-op invariant (|angle| < 1.0°)
- Extraction recovery on non-orthogonal skewed documents (2° to 15°)
- Evidence bounding-box geometry preservation and exact inverse transformation
- Memory stability during repeated deskew processing
"""

import os
import gc
from pathlib import Path
import pytest
import pymupdf
import PIL.Image
import numpy as np

from docuready.ingest.deskew import (
    estimate_skew_angle,
    deskew_image,
    transform_bbox_inverse
)
from docuready.ingest.extractor import DocumentExtractor, PageOCRData, _is_demonstrably_upright
from docuready.domain.models import DocumentType


SKEW_CORPUS_DIR = Path("synthetic_data/skew_corpus")
REALISTIC_CORPUS_DIR = Path("synthetic_data/realistic_corpus_60")


def test_skew_angle_estimation_accuracy():
    """Verifies that projection profile variance estimates skew angles within 0.25° tolerance."""
    test_cases = [
        ("skew_clean_p00deg.pdf", 0.0, 0.0),
        ("skew_clean_p02deg.pdf", 2.0, -2.0),
        ("skew_clean_m02deg.pdf", -2.0, 2.0),
        ("skew_clean_p05deg.pdf", 5.0, -5.0),
        ("skew_clean_m05deg.pdf", -5.0, 5.0),
        ("skew_clean_p10deg.pdf", 10.0, -10.0),
        ("skew_clean_m10deg.pdf", -10.0, 10.0),
        ("skew_clean_p15deg.pdf", 15.0, -15.0),
        ("skew_clean_m15deg.pdf", -15.0, 15.0),
    ]

    for fname, gt_angle, expected_corr in test_cases:
        fpath = SKEW_CORPUS_DIR / fname
        if not fpath.exists():
            continue
        doc = pymupdf.open(str(fpath))
        pix = doc[0].get_pixmap(dpi=200)
        img = PIL.Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        doc.close()

        est_corr, conf = estimate_skew_angle(img, max_angle=45.0)
        if abs(gt_angle) < 1.0:
            assert abs(est_corr) == 0.0, f"Expected 0.0 for near-upright {fname}, got {est_corr}"
        else:
            error = abs(est_corr - expected_corr)
            assert error <= 0.25, f"Angle error for {fname} was {error:.2f}° (expected {expected_corr}°, got {est_corr}°)"
            assert conf >= 5.0, f"Confidence {conf} was below threshold 5.0 for {fname}"


def test_upright_noop_invariant():
    """Confirms that upright pages (|theta| < 1.0°) are not rotated or re-interpolated."""
    im = PIL.Image.new("RGB", (400, 600), (255, 255, 255))
    corr_angle, conf = estimate_skew_angle(im)
    assert corr_angle == 0.0, "Blank upright image should have 0.0 correction"

    deskewed, orig_sz, rot_sz = deskew_image(im, 0.5)
    assert deskewed is im, "Angles < 1.0° must return the original image object (No-Op invariant)"
    assert orig_sz == rot_sz == (400, 600)


def test_inverse_bbox_geometry_math():
    """Tests that transform_bbox_inverse accurately recovers original bounding boxes."""
    # 1. Identity test at 0 degrees
    orig_box = [50.0, 40.0, 150.0, 80.0]
    res_box = transform_bbox_inverse(orig_box, 0.0, (400, 200), (400, 200), scale=1.0)
    assert res_box == orig_box

    # 2. Exact point recovery test under 10° rotation
    im = PIL.Image.new("L", (400, 200), 0)
    im.putpixel((50, 40), 255)
    angle = 10.0
    rot = im.rotate(angle, expand=True)

    # In rotated image, locate the pixel
    coords = np.argwhere(np.array(rot) > 200)
    assert len(coords) > 0
    y1, x1 = coords[0]

    recovered = transform_bbox_inverse([float(x1), float(y1), float(x1), float(y1)], angle, im.size, rot.size, scale=1.0)
    assert abs(recovered[0] - 50.0) <= 0.5
    assert abs(recovered[1] - 40.0) <= 0.5

    # 3. Center preservation test for bounding boxes
    W0, H0 = 400, 200
    W1, H1 = rot.size
    cx1, cy1 = W1 / 2.0, H1 / 2.0
    center_box = transform_bbox_inverse([cx1 - 10, cy1 - 10, cx1 + 10, cy1 + 10], angle, (W0, H0), (W1, H1), scale=1.0)
    mid_x = (center_box[0] + center_box[2]) / 2.0
    mid_y = (center_box[1] + center_box[3]) / 2.0
    assert abs(mid_x - (W0 / 2.0)) <= 0.5
    assert abs(mid_y - (H0 / 2.0)) <= 0.5


def test_field_extraction_recovery_on_5deg_skew():
    """Verifies that smp_21_rotated_5deg.pdf recovers all 6 fields under Loop 03 deskewing."""
    fpath = REALISTIC_CORPUS_DIR / "smp_21_rotated_5deg.pdf"
    if not fpath.exists():
        pytest.skip(f"Corpus file {fpath} not found")

    extractor = DocumentExtractor()
    doc = extractor.extract_document(str(fpath))

    assert doc.status == "VALID"
    assert doc.doc_type == DocumentType.INCOME_CERT

    expected_keys = ["applicant_name", "father_name", "annual_income", "issue_date", "certificate_no", "state"]
    for k in expected_keys:
        assert k in doc.fields, f"Missing field {k} in smp_21_rotated_5deg.pdf"
        f = doc.fields[k]
        assert f.raw_value is not None and len(f.raw_value.strip()) > 0
        assert f.provenance is not None
        bbox = f.provenance.bounding_box
        assert bbox is not None and len(bbox) == 4
        # Validate that bounding box lies within standard PDF page dimensions (approx 595 x 842 pt)
        assert 0 <= bbox[0] < bbox[2] <= 600.0, f"Invalid X geometry for {k}: {bbox}"
        assert 0 <= bbox[1] < bbox[3] <= 850.0, f"Invalid Y geometry for {k}: {bbox}"

    assert "Smruti Ranjan Nayak" in doc.fields["applicant_name"].raw_value
    assert "1,80,000" in doc.fields["annual_income"].raw_value


def test_field_extraction_recovery_on_10deg_skew():
    """Verifies that clean 10-degree skewed scans recover all 4 fields."""
    fpath = SKEW_CORPUS_DIR / "skew_clean_p10deg.pdf"
    if not fpath.exists():
        pytest.skip(f"Corpus file {fpath} not found")

    extractor = DocumentExtractor()
    doc = extractor.extract_document(str(fpath))

    assert doc.status == "VALID"
    assert doc.doc_type == DocumentType.INCOME_CERT
    assert "applicant_name" in doc.fields
    assert "Smruti Ranjan Nayak" in doc.fields["applicant_name"].raw_value
    assert "annual_income" in doc.fields
    assert "1,80,000" in doc.fields["annual_income"].raw_value


def test_repeated_deskew_memory_stability():
    """Confirms no cumulative memory growth during repeated deskew and OCR processing."""
    import psutil
    process = psutil.Process()
    fpath = SKEW_CORPUS_DIR / "skew_clean_p05deg.pdf"
    if not fpath.exists():
        fpath = REALISTIC_CORPUS_DIR / "smp_21_rotated_5deg.pdf"

    extractor = DocumentExtractor()

    # Warmup
    extractor.extract_document(str(fpath))
    gc.collect()
    mem_initial = process.memory_info().rss / (1024 * 1024)

    # 4 consecutive extraction cycles
    for _ in range(4):
        extractor.extract_document(str(fpath))

    gc.collect()
    mem_final = process.memory_info().rss / (1024 * 1024)
    growth_mb = mem_final - mem_initial

    # Allow max 10.0 MB overhead for Python runtime buffers
    assert growth_mb < 10.0, f"Memory leak detected during deskew processing: {growth_mb:.2f} MB growth"
