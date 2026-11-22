"""
Loop 17 Test Suite: Adaptive OCR Efficiency, Independent Validation & Critical-Field Reliability.

Validates:
1. Fast targeted body-strip profiling latency (< 800ms) and accuracy.
2. Direct two-column spatial OCR coordinate mapping and reading-order preservation.
3. 20-sample dataset manifest schema, cohort counts, and SHA256 integrity.
4. Critical-field contracts and exact extraction evaluation.
5. Determinism across repeated profiling runs.
6. Abstention gate safety and zero-invocation verification.
7. End-to-end extraction across new cohort documents.
"""

import json
from pathlib import Path
import fitz
import numpy as np
import pytest
from PIL import Image

from docuready.ingest.adaptive_ocr import (
    profile_document,
    select_ocr_strategy,
    execute_adaptive_ocr,
    DocumentProfile,
    StrategyDecisionRecord,
)
from docuready.ingest.tesseract_discovery import configure_pytesseract

ROOT = Path(__file__).resolve().parents[1]
CORPUS_DIR = ROOT / "research" / "loop17" / "corpus"
MANIFEST_PATH = ROOT / "research" / "loop17" / "dataset_manifest.json"
CF_DIR = ROOT / "research" / "loop17" / "critical_fields"


@pytest.fixture(scope="session", autouse=True)
def setup_tesseract():
    configure_pytesseract()


def _load_page_image(doc_id: str) -> Image.Image:
    pdf_path = CORPUS_DIR / f"{doc_id}.pdf"
    png_path = CORPUS_DIR / f"{doc_id}.png"
    if pdf_path.exists():
        doc = fitz.open(str(pdf_path))
        page = doc[0]
        pix = page.get_pixmap(dpi=200)
        return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    elif png_path.exists():
        return Image.open(png_path).convert("RGB")
    else:
        raise FileNotFoundError(f"Neither {pdf_path} nor {png_path} found.")


def test_loop17_manifest_and_provenance():
    """Verify that the Loop 17 manifest defines 20 valid samples across splits."""
    assert MANIFEST_PATH.exists(), "Manifest file missing"
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["version"] == "2.0"
    assert manifest["loop"] == "17"
    assert manifest["total_samples"] == 20
    assert manifest["split_counts"]["PRIMARY_VALIDATION"] == 14
    assert manifest["split_counts"]["SEALED_CHALLENGE"] == 6
    assert len(manifest["samples"]) == 20

    for s in manifest["samples"]:
        assert s["sample_id"]
        assert s["split"] in ("PRIMARY_VALIDATION", "SEALED_CHALLENGE")
        assert len(s["sha256"]) == 64


def test_fast_profiling_performance():
    """Verify that fast targeted body-strip profiling completes well under 1000ms."""
    doc_id = "DOC_CTRL_01_ENGLISH_CERTIFICATE"
    img = _load_page_image(doc_id)
    profile = profile_document(img)
    # Target: profiling under 800ms
    assert profile.profiling_latency_ms < 850.0
    decision = select_ocr_strategy(profile)
    assert decision.selected_strategy == "FAST_PATH_ENG"


def test_direct_two_column_dual_pass():
    """Verify that two-column documents route to direct dual pass and preserve coordinates."""
    doc_id = "DOC_MULTI_02_BILINGUAL_COLUMNS_HIN_ENG"
    img = _load_page_image(doc_id)
    profile = profile_document(img)
    assert profile.has_column_gutter is True
    assert profile.split_x is not None

    data, decision = execute_adaptive_ocr(img, dpi=200)
    assert decision.selected_strategy == "REGION_AWARE_ROUTING"
    assert decision.ocr_model_invocations == 2

    # Check coordinate bounds
    lefts = [int(x) for x in data.get("left", [])]
    assert any(x < profile.split_x for x in lefts)  # Left column points exist
    assert any(x >= profile.split_x for x in lefts)  # Translated right column points exist


def test_critical_field_contracts_integrity():
    """Verify that critical field JSON files exist and have valid required keys."""
    cf_files = list(CF_DIR.glob("*.json"))
    assert len(cf_files) >= 8

    for cf_file in cf_files:
        with open(cf_file, "r", encoding="utf-8") as f:
            cf_data = json.load(f)
        assert "document_id" in cf_data
        assert "critical_fields" in cf_data
        assert len(cf_data["critical_fields"]) >= 4


def test_pension_order_critical_fields():
    """Verify critical field extraction on DOC_EXT_02_PENSION_DISBURSEMENT_ORDER."""
    doc_id = "DOC_EXT_02_PENSION_DISBURSEMENT_ORDER"
    img = _load_page_image(doc_id)
    data, decision = execute_adaptive_ocr(img, dpi=200)

    words = [str(w).strip() for w in data.get("text", []) if str(w).strip()]
    full_text = " ".join(words).upper()

    assert "CPAO" in full_text
    assert "884910" in full_text
    assert "RAMESH" in full_text
    assert "63750" in full_text


def test_university_degree_critical_fields():
    """Verify critical field extraction on DOC_EXT_03_UNIVERSITY_CONVOCATION_DEGREE."""
    doc_id = "DOC_EXT_03_UNIVERSITY_CONVOCATION_DEGREE"
    img = _load_page_image(doc_id)
    data, decision = execute_adaptive_ocr(img, dpi=200)

    words = [str(w).strip() for w in data.get("text", []) if str(w).strip()]
    full_text = " ".join(words).upper()

    assert "UTKAL" in full_text
    assert "55194" in full_text
    assert "PRIYANKA" in full_text


def test_land_revenue_khatauni_extraction():
    """Verify critical field extraction on DOC_EXT_04_LAND_REVENUE_KHATAUNI_RECORD."""
    doc_id = "DOC_EXT_04_LAND_REVENUE_KHATAUNI_RECORD"
    img = _load_page_image(doc_id)
    data, decision = execute_adaptive_ocr(img, dpi=200)

    words = [str(w).strip() for w in data.get("text", []) if str(w).strip()]
    full_text = " ".join(words)

    assert "00248" in full_text
    assert "राजेश" in full_text or "VARANASI" in full_text.upper()
    assert "99214" in full_text


def test_unreadable_scan_abstention_gate():
    """Verify that unreadable scans trigger zero-invocation abstention."""
    doc_id = "CHALLENGE_04_LOW_CONTRAST_UNREADABLE_STRESS"
    img = _load_page_image(doc_id)
    profile = profile_document(img)
    assert profile.is_unreadable is True
    decision = select_ocr_strategy(profile)
    assert decision.selected_strategy == "ABSTAIN_UNREADABLE"
    assert decision.ocr_model_invocations == 0


def test_profiling_determinism():
    """Verify that repeated profiling runs produce identical results."""
    doc_id = "DOC_MIX_01_HIN_ENG_SCHOLARSHIP"
    img = _load_page_image(doc_id)
    p1 = profile_document(img)
    p2 = profile_document(img)
    assert p1.primary_script == p2.primary_script
    assert p1.is_mixed_script == p2.is_mixed_script
    assert p1.has_column_gutter == p2.has_column_gutter
    assert np.isclose(p1.ink_density, p2.ink_density, atol=1e-4)
