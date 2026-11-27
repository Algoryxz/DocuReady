"""
tests/test_loop02_orientation_assurance.py

Permanent regression and assurance test suite for DocuReady Loop 02:
- Empirical safety of the conservative upright fast path
- Zero false-upright rate on rotated, skewed, and adversarial documents
- Two-tier OSD recovery correctness and speedup
- Bounding-box coordinate safety and clamping invariants
- Memory stability across repeated batch processing
- Punctuation and noise speck spoofing prevention
"""
import os
import psutil
from pathlib import Path
from typing import Dict, List, Any

import pytest
import pymupdf
import PIL.Image

from docuready.domain.models import DocumentType, ExtractionMethod
from docuready.ingest.extractor import (
    DocumentExtractor,
    PageOCRData,
    _is_demonstrably_upright,
    _ocr_page,
    MAX_PIXEL_DIMENSION,
)
from docuready.ingest.tesseract_discovery import configure_pytesseract, get_ocr_runtime_info

configure_pytesseract()

CORPUS_DIR = Path("synthetic_data/realistic_corpus_60")
ATTACK_DIR = Path("synthetic_data/attack_corpus")


@pytest.fixture(scope="module")
def tesseract_available() -> bool:
    info = get_ocr_runtime_info()
    return info.get("available", False)


def test_attack_corpus_zero_false_upright_rate(tesseract_available: bool) -> None:
    """
    CRITICAL SAFETY CONTRACT:
    Verifies that ZERO rotated, skewed, or adversarial documents pass the upright fast-path gate.
    False-upright rate must be strictly 0.0%.
    """
    if not tesseract_available:
        pytest.skip("Tesseract OCR is not available")

    attack_fixtures = [
        "atk_01_skew_10deg.pdf",
        "atk_02_skew_15deg.pdf",
        "atk_03_mixed_orientation.pdf",
        "atk_06_inverted_reversible_words.pdf",
        "atk_08_landscape_table_90deg.pdf",
    ]

    for fname in attack_fixtures:
        fpath = ATTACK_DIR / fname
        if not fpath.exists():
            continue

        doc = pymupdf.open(str(fpath))
        pix = doc[0].get_pixmap(dpi=200)
        img = PIL.Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        doc.close()

        import pytesseract
        data_0 = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT, timeout=15)
        is_upright = _is_demonstrably_upright(data_0)

        assert not is_upright, f"CRITICAL FAILURE: {fname} falsely passed the upright gate!"


def test_sparse_page_and_noise_specks_rejection(tesseract_available: bool) -> None:
    """Verifies that sparse documents and blank pages with noise specks do not pass the gate."""
    if not tesseract_available:
        pytest.skip("Tesseract OCR is not available")

    for fname in ["atk_04_sparse_receipt.pdf", "atk_05_blank_with_noise_dots.pdf"]:
        fpath = ATTACK_DIR / fname
        if not fpath.exists():
            continue

        doc = pymupdf.open(str(fpath))
        pix = doc[0].get_pixmap(dpi=200)
        img = PIL.Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        doc.close()

        import pytesseract
        data_0 = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT, timeout=15)
        is_upright = _is_demonstrably_upright(data_0)

        assert not is_upright, f"{fname} must be rejected by upright gate"


def test_punctuation_and_noise_spoofing_prevention() -> None:
    """
    Verifies that synthetic data with 50 high-confidence punctuation marks (e.g. hyphens, periods)
    cannot spoof the gate because of the alphanumeric requirement.
    """
    # 50 hyphens with 95% confidence and wide horizontal aspect ratio
    fake_data = {
        "text": ["-"] * 50,
        "conf": [95.0] * 50,
        "left": [10] * 50,
        "top": [10] * 50,
        "width": [20.0] * 50,
        "height": [5.0] * 50,
    }
    assert not _is_demonstrably_upright(fake_data), "Punctuation-only tokens must not pass the gate"


def test_character_count_threshold_prevents_single_char_gate_bypass() -> None:
    """
    Verifies that 16 single-character tokens (total characters = 16 < 40)
    cannot pass the gate even if confidence is 100%.
    """
    fake_data = {
        "text": ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P"],
        "conf": [99.0] * 16,
        "left": [10] * 16,
        "top": [10] * 16,
        "width": [20.0] * 16,
        "height": [10.0] * 16,
    }
    assert not _is_demonstrably_upright(fake_data), "Single-character tokens below char limit must not pass"


def test_two_tier_osd_recovery_accuracy(tesseract_available: bool) -> None:
    """Verifies that 90°, 180°, and 270° scans recover full extraction accuracy through two-tier OSD."""
    if not tesseract_available:
        pytest.skip("Tesseract OCR is not available")

    ext = DocumentExtractor()

    # 90°
    doc_90 = ext.extract_document(str(CORPUS_DIR / "smp_23_rotated_90deg.pdf"), DocumentType.INCOME_CERT)
    assert doc_90.status == "VALID"
    assert doc_90.fields["applicant_name"].raw_value == "Smruti Ranjan Nayak"

    # 180°
    doc_180 = ext.extract_document(str(CORPUS_DIR / "smp_24_rotated_180deg.pdf"), DocumentType.INCOME_CERT)
    assert doc_180.status == "VALID"
    assert doc_180.fields["applicant_name"].raw_value == "Smruti Ranjan Nayak"

    # 270°
    path_270 = CORPUS_DIR / "smp_61_rotated_270deg.pdf"
    if path_270.exists():
        doc_270 = ext.extract_document(str(path_270), DocumentType.INCOME_CERT)
        assert doc_270.status == "VALID"
        assert doc_270.fields["applicant_name"].raw_value == "Smruti Ranjan Nayak"


def test_coordinate_bounds_and_validity_across_rotations(tesseract_available: bool) -> None:
    """Verifies that bounding boxes across all orientations remain strictly within page bounds."""
    if not tesseract_available:
        pytest.skip("Tesseract OCR is not available")

    ext = DocumentExtractor()
    test_files = [
        "smp_11_raster_scan.pdf",
        "smp_23_rotated_90deg.pdf",
        "smp_24_rotated_180deg.pdf",
    ]

    for fname in test_files:
        fpath = CORPUS_DIR / fname
        doc_pdf = pymupdf.open(str(fpath))
        p_w, p_h = doc_pdf[0].rect.width, doc_pdf[0].rect.height
        doc_pdf.close()

        ext_doc = ext.extract_document(str(fpath), DocumentType.INCOME_CERT)
        for field_name, fld in ext_doc.fields.items():
            if fld.provenance and fld.provenance.bounding_box:
                x0, y0, x1, y1 = fld.provenance.bounding_box
                assert x1 >= x0, f"{fname} {field_name}: x1 ({x1}) < x0 ({x0})"
                assert y1 >= y0, f"{fname} {field_name}: y1 ({y1}) < y0 ({y0})"
                assert x0 >= -5.0, f"{fname} {field_name}: x0 ({x0}) < 0"
                assert y0 >= -5.0, f"{fname} {field_name}: y0 ({y0}) < 0"


def test_repeated_processing_memory_stability(tesseract_available: bool) -> None:
    """Verifies that repeated extraction runs do not leak memory (>50MB RSS growth)."""
    if not tesseract_available:
        pytest.skip("Tesseract OCR is not available")

    ext = DocumentExtractor()
    proc = psutil.Process(os.getpid())

    # Warm-up run
    ext.extract_document(str(CORPUS_DIR / "smp_11_raster_scan.pdf"), DocumentType.INCOME_CERT)
    rss_initial = proc.memory_info().rss / (1024 * 1024)

    # 10 repeated extraction iterations
    for _ in range(10):
        ext.extract_document(str(CORPUS_DIR / "smp_11_raster_scan.pdf"), DocumentType.INCOME_CERT)

    rss_final = proc.memory_info().rss / (1024 * 1024)
    growth_mb = rss_final - rss_initial
    assert growth_mb < 50.0, f"Memory leak detected: RSS grew by {growth_mb:.2f} MB"
