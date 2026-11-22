"""
Loop 16 Test Suite: Adaptive OCR Strategy Selection, Accuracy Optimization & Latency Reduction.

Validates:
1. Deterministic document profiling (contrast, ink density, quiet gutters, script counts).
2. Strategy resolution logic (fast-path English, monolingual Indic, table/grid compounds,
   multi-column region routing, and unreadable abstention gate).
3. End-to-end adaptive execution returning valid OCR data and StrategyDecisionRecord.
4. Dataset manifest and provenance integrity.
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
CORPUS_DIR = ROOT / "research" / "loop16" / "corpus"
MANIFEST_PATH = ROOT / "research" / "loop16" / "dataset_manifest.json"


@pytest.fixture(scope="session", autouse=True)
def setup_tesseract():
    configure_pytesseract()


def _load_page_image(doc_id: str) -> Image.Image:
    """Helper to load the first page of a corpus document as a PIL Image."""
    pdf_path = CORPUS_DIR / f"{doc_id}.pdf"
    png_path = CORPUS_DIR / f"{doc_id}.png"
    if pdf_path.exists():
        doc = fitz.open(str(pdf_path))
        page = doc[0]
        pix = page.get_pixmap(dpi=300)
        return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    elif png_path.exists():
        return Image.open(png_path).convert("RGB")
    else:
        raise FileNotFoundError(f"Neither {pdf_path} nor {png_path} found.")


def test_manifest_and_provenance():
    """Verify that the dataset manifest exists and defines 15 valid samples."""
    assert MANIFEST_PATH.exists(), "Manifest file missing"
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["version"] == "1.0"
    assert manifest["loop"] == "16"
    assert manifest["total_samples"] == 15
    assert manifest["split_counts"]["PRIMARY_VALIDATION"] == 11
    assert manifest["split_counts"]["SEALED_CHALLENGE"] == 4
    assert len(manifest["samples"]) == 15

    for s in manifest["samples"]:
        assert s["sample_id"]
        assert s["split"] in ("PRIMARY_VALIDATION", "SEALED_CHALLENGE")
        assert s["provenance_category"] in (
            "VERIFIED_EXTERNAL",
            "DERIVED_FROM_EXTERNAL",
            "VERIFIED_SYNTHETIC",
        )
        assert len(s["sha256"]) == 64


def test_fast_path_english():
    """Verify that pure English documents are routed to FAST_PATH_ENG."""
    doc_id = "DOC_CTRL_01_ENGLISH_CERTIFICATE"
    img = _load_page_image(doc_id)
    profile = profile_document(img, native_text="Government of India Income and Assets Certificate English Only")
    decision = select_ocr_strategy(profile)
    assert decision.selected_strategy == "FAST_PATH_ENG"
    assert decision.selected_lang == "eng"
    assert decision.ocr_model_invocations == 1


def test_two_column_region_routing():
    """Verify that documents with a central vertical quiet gutter route to REGION_AWARE_ROUTING."""
    doc_id = "DOC_MULTI_02_BILINGUAL_COLUMNS_HIN_ENG"
    img = _load_page_image(doc_id)
    profile = profile_document(img)
    assert profile.has_column_gutter is True
    decision = select_ocr_strategy(profile)
    assert decision.selected_strategy == "REGION_AWARE_ROUTING"
    assert decision.ocr_model_invocations >= 2


def test_odia_two_column_challenge_routing():
    """Verify that the Odia challenge two-column gazette routes to REGION_AWARE_ROUTING."""
    doc_id = "CHALLENGE_02_ODIA_ENGLISH_GAZETTE_TWO_COL"
    img = _load_page_image(doc_id)
    profile = profile_document(img)
    assert profile.has_column_gutter is True
    decision = select_ocr_strategy(profile)
    assert decision.selected_strategy == "REGION_AWARE_ROUTING"


def test_monolingual_hindi_routing():
    """Verify that monolingual Hindi circulars route to MONOLINGUAL_HIN."""
    doc_id = "DOC_HIN_01_ADMIN_CIRCULAR"
    img = _load_page_image(doc_id)
    profile = profile_document(img)
    decision = select_ocr_strategy(profile)
    assert decision.selected_strategy in ("MONOLINGUAL_HIN", "GLOBAL_MULTILINGUAL")
    assert "hin" in decision.selected_lang


def test_monolingual_odia_routing():
    """Verify that monolingual Odia circulars route to MONOLINGUAL_ORI or compound with Odia."""
    doc_id = "DOC_ORI_01_ADMIN_CIRCULAR"
    img = _load_page_image(doc_id)
    profile = profile_document(img)
    decision = select_ocr_strategy(profile)
    assert decision.selected_strategy in ("MONOLINGUAL_ORI", "GLOBAL_MULTILINGUAL")
    assert "ori" in decision.selected_lang


def test_table_marksheet_compound_routing():
    """Verify that marksheet grids route to GLOBAL_MULTILINGUAL single pass."""
    doc_id = "CHALLENGE_03_HINDI_ENGLISH_MARKSHEET_ROW_GRID"
    img = _load_page_image(doc_id)
    profile = profile_document(img)
    decision = select_ocr_strategy(profile)
    assert decision.selected_strategy == "GLOBAL_MULTILINGUAL"
    assert "hin" in decision.selected_lang
    assert decision.ocr_model_invocations == 1


def test_unreadable_scan_abstention():
    """Verify that severely degraded, low-contrast scans trigger ABSTAIN_UNREADABLE."""
    doc_id = "CHALLENGE_04_LOW_CONTRAST_UNREADABLE_STRESS"
    img = _load_page_image(doc_id)
    profile = profile_document(img)
    assert profile.is_unreadable is True or profile.ink_density < 0.005
    decision = select_ocr_strategy(profile)
    assert decision.selected_strategy == "ABSTAIN_UNREADABLE"
    assert decision.ocr_model_invocations == 0

    # Execute adaptive OCR on unreadable scan: must return empty dict without invoking OCR
    data, dec = execute_adaptive_ocr(img)
    assert dec.selected_strategy == "ABSTAIN_UNREADABLE"
    valid_words = [w for w in data.get("text", []) if str(w).strip()]
    assert len(valid_words) == 0


def test_profiling_determinism():
    """Verify that profiling produces identical metrics across repeated runs."""
    doc_id = "DOC_MULTI_02_BILINGUAL_COLUMNS_HIN_ENG"
    img = _load_page_image(doc_id)
    p1 = profile_document(img)
    p2 = profile_document(img)
    assert p1.has_column_gutter == p2.has_column_gutter
    assert p1.split_x == p2.split_x
    assert np.isclose(p1.ink_density, p2.ink_density, atol=1e-4)
    assert p1.primary_script == p2.primary_script
    assert p1.is_mixed_script == p2.is_mixed_script


def test_end_to_end_adaptive_execution():
    """Verify that execute_adaptive_ocr executes cleanly and returns recognition data."""
    doc_id = "DOC_CTRL_01_ENGLISH_CERTIFICATE"
    img = _load_page_image(doc_id)
    data, decision = execute_adaptive_ocr(img)

    assert isinstance(decision, StrategyDecisionRecord)
    assert decision.selected_strategy in ("FAST_PATH_ENG", "GLOBAL_MULTILINGUAL")
    words = [str(w).strip() for w in data.get("text", []) if str(w).strip()]
    assert len(words) > 0
    full_text = " ".join(words).upper()
    assert "INCOME" in full_text or "CERTIFICATE" in full_text
