"""
tests/test_ocr_performance_and_adversarial.py

Adversarial and regression test suite for DocuReady Loop 01:
- Multi-orientation recovery (0°, 90°, 180°, 270°, skew)
- Conservative OSD fast-path verification (upright pages skip OSD safely)
- Image quality and degradation resilience (low DPI, shadows, noise)
- Controlled failure handling (blank pages, corrupted PDFs, OSD timeouts)
- Coordinate contract preservation and bounding-box accuracy
- Decision safety and confidence calibration invariance
"""
import io
import os
from pathlib import Path
from unittest.mock import patch

import PIL.Image
import PIL.ImageDraw
import pytest
import pymupdf
import pytesseract

from docuready.domain.models import DocumentType, ExtractionMethod
from docuready.ingest.extractor import DocumentExtractor, PageOCRData, _is_demonstrably_upright
from docuready.ingest.tesseract_discovery import configure_pytesseract, get_ocr_runtime_info

configure_pytesseract()

CORPUS_DIR = Path("synthetic_data/realistic_corpus_60")


@pytest.fixture(scope="module")
def tesseract_available() -> bool:
    info = get_ocr_runtime_info()
    return info["available"]


def test_upright_fast_path_gate_correctness(tesseract_available: bool) -> None:
    """Verifies that the conservative fast-path gate correctly accepts upright and rejects rotated scans."""
    if not tesseract_available:
        pytest.skip("Tesseract OCR is not available")

    # 1. Upright clean scan
    doc_upright = pymupdf.open(str(CORPUS_DIR / "smp_11_raster_scan.pdf"))
    pix = doc_upright[0].get_pixmap(dpi=200)
    img_upright = PIL.Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    d_upright = pytesseract.image_to_data(img_upright, output_type=pytesseract.Output.DICT)
    doc_upright.close()
    assert _is_demonstrably_upright(d_upright) is True, "Clean upright scan must pass upright fast path"

    # 2. 90-degree rotated scan
    doc_90 = pymupdf.open(str(CORPUS_DIR / "smp_23_rotated_90deg.pdf"))
    pix = doc_90[0].get_pixmap(dpi=200)
    img_90 = PIL.Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    d_90 = pytesseract.image_to_data(img_90, output_type=pytesseract.Output.DICT)
    doc_90.close()
    assert _is_demonstrably_upright(d_90) is False, "90-degree rotated scan must be rejected by upright fast path"

    # 3. 180-degree rotated scan
    doc_180 = pymupdf.open(str(CORPUS_DIR / "smp_24_rotated_180deg.pdf"))
    pix = doc_180[0].get_pixmap(dpi=200)
    img_180 = PIL.Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    d_180 = pytesseract.image_to_data(img_180, output_type=pytesseract.Output.DICT)
    doc_180.close()
    assert _is_demonstrably_upright(d_180) is False, "180-degree upside down scan must be rejected by upright fast path"

    # 4. Blank scan
    doc_blank = pymupdf.open(str(CORPUS_DIR / "smp_59_blank_scan.pdf"))
    pix = doc_blank[0].get_pixmap(dpi=200)
    img_blank = PIL.Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    d_blank = pytesseract.image_to_data(img_blank, output_type=pytesseract.Output.DICT)
    doc_blank.close()
    assert _is_demonstrably_upright(d_blank) is False, "Blank page must not pass fast path"


def test_upright_document_extraction_skips_osd(tesseract_available: bool) -> None:
    """Verifies that extracting an upright document never calls image_to_osd."""
    if not tesseract_available:
        pytest.skip("Tesseract OCR is not available")

    ext = DocumentExtractor()
    with patch("pytesseract.image_to_osd", side_effect=AssertionError("OSD must not be called on upright scans!")):
        doc = ext.extract_document(str(CORPUS_DIR / "smp_11_raster_scan.pdf"), DocumentType.INCOME_CERT)

    assert doc.status == "VALID"
    assert doc.extraction_method == ExtractionMethod.LOCAL_OCR.value
    assert "applicant_name" in doc.fields
    assert doc.fields["applicant_name"].raw_value == "Smruti Ranjan Nayak"
    assert doc.fields["applicant_name"].confidence >= 0.90


def test_rotated_90_degree_recovery(tesseract_available: bool) -> None:
    """Verifies that a 90° rotated scan is properly detected, rotated upright, and accurately extracted."""
    if not tesseract_available:
        pytest.skip("Tesseract OCR is not available")

    ext = DocumentExtractor()
    doc = ext.extract_document(str(CORPUS_DIR / "smp_23_rotated_90deg.pdf"), DocumentType.INCOME_CERT)

    assert doc.status == "VALID"
    assert doc.extraction_method == ExtractionMethod.LOCAL_OCR.value
    assert "applicant_name" in doc.fields
    assert doc.fields["applicant_name"].raw_value == "Smruti Ranjan Nayak"
    assert "annual_income" in doc.fields
    assert "1,80,000" in doc.fields["annual_income"].raw_value
    assert "certificate_no" in doc.fields
    assert "E-INC/2025/104928" in doc.fields["certificate_no"].raw_value


def test_rotated_180_degree_recovery(tesseract_available: bool) -> None:
    """Verifies that a 180° upside-down scan is detected, rotated, and accurately extracted."""
    if not tesseract_available:
        pytest.skip("Tesseract OCR is not available")

    ext = DocumentExtractor()
    doc = ext.extract_document(str(CORPUS_DIR / "smp_24_rotated_180deg.pdf"), DocumentType.INCOME_CERT)

    assert doc.status == "VALID"
    assert doc.extraction_method == ExtractionMethod.LOCAL_OCR.value
    assert "applicant_name" in doc.fields
    assert doc.fields["applicant_name"].raw_value == "Smruti Ranjan Nayak"
    assert "father_name" in doc.fields
    assert doc.fields["father_name"].raw_value == "Ramesh Chandra Nayak"


def test_rotated_270_degree_recovery(tesseract_available: bool) -> None:
    """Verifies that a 270° rotated scan is detected, rotated, and accurately extracted."""
    if not tesseract_available:
        pytest.skip("Tesseract OCR is not available")

    path_270 = CORPUS_DIR / "smp_61_rotated_270deg.pdf"
    if not path_270.exists():
        pytest.skip("smp_61_rotated_270deg.pdf not present")

    ext = DocumentExtractor()
    doc = ext.extract_document(str(path_270), DocumentType.INCOME_CERT)

    assert doc.status == "VALID"
    assert doc.extraction_method == ExtractionMethod.LOCAL_OCR.value
    assert "applicant_name" in doc.fields
    assert doc.fields["applicant_name"].raw_value == "Smruti Ranjan Nayak"


def test_bounding_box_stability_across_orientations(tesseract_available: bool) -> None:
    """Verifies that bounding boxes of extracted fields match the upright coordinate space."""
    if not tesseract_available:
        pytest.skip("Tesseract OCR is not available")

    ext = DocumentExtractor()
    doc_upright = ext.extract_document(str(CORPUS_DIR / "smp_11_raster_scan.pdf"), DocumentType.INCOME_CERT)
    bbox_upright = doc_upright.fields["applicant_name"].provenance.bounding_box

    doc_90 = ext.extract_document(str(CORPUS_DIR / "smp_23_rotated_90deg.pdf"), DocumentType.INCOME_CERT)
    bbox_90 = doc_90.fields["applicant_name"].provenance.bounding_box

    assert bbox_upright is not None
    assert bbox_90 is not None
    # Coordinates should match within 2.0 points
    for c1, c2 in zip(bbox_upright, bbox_90):
        assert abs(c1 - c2) <= 2.0


def test_low_dpi_and_degraded_document_extraction(tesseract_available: bool) -> None:
    """Verifies that low-DPI and degraded documents extract successfully through the fast path."""
    if not tesseract_available:
        pytest.skip("Tesseract OCR is not available")

    ext = DocumentExtractor()

    # Low DPI
    doc_low_dpi = ext.extract_document(str(CORPUS_DIR / "smp_25_low_dpi.pdf"), DocumentType.INCOME_CERT)
    assert doc_low_dpi.status == "VALID"
    assert "certificate_no" in doc_low_dpi.fields
    assert "annual_income" in doc_low_dpi.fields

    # Shadow gradient
    doc_shadow = ext.extract_document(str(CORPUS_DIR / "smp_37_shadow_gradient.pdf"), DocumentType.INCOME_CERT)
    assert doc_shadow.status == "VALID"
    assert "applicant_name" in doc_shadow.fields


def test_blank_page_produces_unreadable_status(tesseract_available: bool) -> None:
    """Verifies that a blank document produces UNREADABLE status and does not crash."""
    if not tesseract_available:
        pytest.skip("Tesseract OCR is not available")

    ext = DocumentExtractor()
    doc_blank = ext.extract_document(str(CORPUS_DIR / "smp_59_blank_scan.pdf"), DocumentType.INCOME_CERT)
    assert doc_blank.status == "UNREADABLE"
    assert len(doc_blank.fields) == 0


def test_osd_timeout_and_failure_resilience(tesseract_available: bool) -> None:
    """Verifies that if OSD times out or fails on a rotated page, it gracefully falls back without crashing."""
    if not tesseract_available:
        pytest.skip("Tesseract OCR is not available")

    ext = DocumentExtractor()
    with patch("pytesseract.image_to_osd", side_effect=RuntimeError("Simulated OSD timeout")):
        # Must not raise RuntimeError
        doc = ext.extract_document(str(CORPUS_DIR / "smp_23_rotated_90deg.pdf"), DocumentType.INCOME_CERT)
        assert doc is not None
        assert doc.extraction_method == ExtractionMethod.LOCAL_OCR.value


def test_corrupted_pdf_produces_corrupted_status() -> None:
    """Verifies that a corrupted PDF header is safely rejected as CORRUPTED."""
    ext = DocumentExtractor()
    doc = ext.extract_document(str(CORPUS_DIR / "smp_60_corrupted_header.pdf"), DocumentType.INCOME_CERT)
    assert doc.status == "CORRUPTED"
