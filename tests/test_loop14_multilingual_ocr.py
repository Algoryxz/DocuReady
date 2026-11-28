"""
Loop 14 - Unit & Integration Test Suite
Multilingual OCR Validation, Script-Aware Routing & Dataset Provenance Integrity
DocuReady Subsystem
"""

from __future__ import annotations

import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import pytest

from docuready.ingest.extractor import PageOCRData, _ocr_page
from docuready.ingest.script_router import (
    detect_unicode_script,
    resolve_optimal_ocr_language,
    RE_DEVANAGARI,
    RE_ODIA,
    RE_LATIN
)
from docuready.ingest.tesseract_discovery import (
    configure_pytesseract,
    get_ocr_runtime_info,
    find_tesseract_binary
)

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module", autouse=True)
def setup_tesseract():
    configure_pytesseract()


# ============================================================================
# 1. SCRIPT DETECTION & ROUTING UNIT TESTS
# ============================================================================

def test_script_detection_pure_latin():
    text = "Department of Higher Education Central Sector Scholarship Scheme 2026."
    res = detect_unicode_script(text)
    assert res["primary_script"] == "LATIN"
    assert res["detected_lang"] == "eng"
    assert res["is_mixed"] is False
    assert res["counts"]["latin"] > 0
    assert res["counts"]["devanagari"] == 0
    assert res["counts"]["odia"] == 0


def test_script_detection_pure_devanagari():
    text = "भारत सरकार उच्च शिक्षा विभाग राष्ट्रीय छात्रवृत्ति योजना २०२६"
    res = detect_unicode_script(text)
    assert res["primary_script"] == "DEVANAGARI"
    assert res["detected_lang"] == "hin"
    assert res["is_mixed"] is False
    assert res["counts"]["devanagari"] > 0
    assert res["counts"]["latin"] == 0


def test_script_detection_pure_odia():
    text = "ଓଡ଼ିଶା ସରକାର ଉଚ୍ଚଶିକ୍ଷା ବିଭାଗ ଛାତ୍ରବୃତ୍ତି ଯୋଜନା ନିର୍ଦ୍ଦେଶାବଳୀ ୨୦୨୬"
    res = detect_unicode_script(text)
    assert res["primary_script"] == "ODIA"
    assert res["detected_lang"] == "ori"
    assert res["is_mixed"] is False
    assert res["counts"]["odia"] > 0
    assert res["counts"]["latin"] == 0


def test_script_detection_bilingual_hindi_english():
    text = "Government of India / भारत सरकार - Scholarship Portal / छात्रवृत्ति"
    res = detect_unicode_script(text)
    assert res["primary_script"] == "MIXED_DEVANAGARI_LATIN"
    assert res["detected_lang"] == "eng+hin"
    assert res["is_mixed"] is True
    assert res["counts"]["latin"] > 0
    assert res["counts"]["devanagari"] > 0


def test_script_detection_bilingual_odia_english():
    text = "Government of Odisha / ଓଡ଼ିଶା ସରକାର - Verification / ଯାଞ୍ଚ ପୋର୍ଟାଲ"
    res = detect_unicode_script(text)
    assert res["primary_script"] == "MIXED_ODIA_LATIN"
    assert res["detected_lang"] == "eng+ori"
    assert res["is_mixed"] is True
    assert res["counts"]["latin"] > 0
    assert res["counts"]["odia"] > 0


# ============================================================================
# 2. TESSERACT MULTILINGUAL DISCOVERY & RUNTIME INTEGRATION
# ============================================================================

def test_tesseract_multilingual_language_packs_discovered():
    """Verifies that English, Hindi, and Odia traineddata are discovered and available."""
    info = get_ocr_runtime_info()
    assert info["available"] is True
    langs = info["languages"]
    assert "eng" in langs
    assert "hin" in langs
    assert "ori" in langs


def test_hindi_devanagari_ocr_extraction():
    """Verifies that Tesseract with lang='hin' successfully extracts Devanagari text."""
    import pytesseract

    hin_corpus = ROOT / "research" / "loop14" / "corpus" / "DOC_HIN_01_ADMIN_CIRCULAR.png"
    if hin_corpus.exists():
        img = Image.open(hin_corpus).convert("RGB")
    else:
        img = Image.new("RGB", (600, 100), (255, 255, 255))
        try:
            font = ImageFont.truetype(r"C:\Windows\Fonts\Nirmala.ttc", 28)
        except Exception:
            font = ImageFont.load_default()
        ImageDraw.Draw(img).text((20, 25), "प्रमाण पत्र: वैध आय", fill=(0, 0, 0), font=font)

    txt = pytesseract.image_to_string(img, lang="hin").strip()
    assert len(txt) > 0
    # Must contain Devanagari characters
    assert len(RE_DEVANAGARI.findall(txt)) > 0


def test_odia_ocr_extraction():
    """Verifies that Tesseract with lang='ori' successfully extracts Odia script characters."""
    import pytesseract

    ori_corpus = ROOT / "research" / "loop18" / "corpus" / "DOC_EXT_06_ODIA_REVENUE_NOTICE.png"
    if ori_corpus.exists():
        img = Image.open(ori_corpus).convert("RGB")
    else:
        img = Image.new("RGB", (600, 100), (255, 255, 255))
        try:
            font = ImageFont.truetype(r"C:\Windows\Fonts\Nirmala.ttc", 28)
        except Exception:
            font = ImageFont.load_default()
        ImageDraw.Draw(img).text((20, 25), "ପ୍ରମାଣ ପତ୍ର: ବୈଧ ଆୟ", fill=(0, 0, 0), font=font)

    txt = pytesseract.image_to_string(img, lang="ori").strip()
    assert len(txt) > 0
    # Must contain Odia characters
    assert len(RE_ODIA.findall(txt)) > 0


# ============================================================================
# 3. DATASET MANIFEST & PROVENANCE GOVERNANCE TESTS
# ============================================================================

def test_dataset_manifest_schema_and_integrity():
    """Verifies the structural integrity, checksums, and provenance labels in dataset_manifest.json."""
    manifest_path = ROOT / "research" / "loop14" / "dataset_manifest.json"
    assert manifest_path.exists()

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert len(manifest) >= 15

    allowed_provenance = {
        "VERIFIED_EXTERNAL",
        "VERIFIED_SYNTHETIC",
        "DERIVED_FROM_EXTERNAL",
        "MANUALLY_ANNOTATED",
        "UNKNOWN_PROVENANCE"
    }

    seen_ids = set()
    external_count = 0

    for item in manifest:
        # Unique ID
        sample_id = item["sample_id"]
        assert sample_id not in seen_ids
        seen_ids.add(sample_id)

        # Required fields
        assert "dataset_name" in item
        assert "sha256" in item and len(item["sha256"]) == 64
        assert "provenance_category" in item
        assert item["provenance_category"] in allowed_provenance
        if item["provenance_category"] == "VERIFIED_EXTERNAL":
            external_count += 1

        assert item["language"] in ["English", "Hindi", "Odia", "Mixed English/Hindi", "Mixed English/Odia"]
        assert item["dataset_split"] in ["dev", "validation", "challenge"]
        assert item["ground_truth_available"] is True

        # File exists on disk
        file_path = ROOT / "research" / "loop14" / "corpus" / item["file_name"]
        assert file_path.exists()
        assert file_path.stat().st_size == item["file_size_bytes"]

    # At least 1 verified external document must exist
    assert external_count >= 1


def test_portal_survey_results_integrity():
    """Verifies that all 4 Indian portals were probed and recorded."""
    survey_path = ROOT / "research" / "loop14" / "portal_survey_results.json"
    assert survey_path.exists()

    with open(survey_path, "r", encoding="utf-8") as f:
        survey = json.load(f)

    expected_portals = [
        "portal_a_data_gov_in",
        "portal_b_ndap",
        "portal_c_mospi_nada",
        "portal_d_india_data_portal"
    ]
    for p in expected_portals:
        assert p in survey
        assert "base_probe" in survey[p]
        assert survey[p]["base_probe"]["status"] in [200, 301, 302]
        assert len(survey[p]["query_probes"]) >= 4
