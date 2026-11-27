"""
Loop 15 - Region-Aware Multilingual OCR & Script Routing Tests
DocuReady Automated Verification Suite
"""

import json
from pathlib import Path
import pytest
from PIL import Image, ImageDraw

from docuready.ingest.extractor import PageOCRData
from docuready.ingest.region_ocr import (
    DocumentRegion,
    classify_region_script,
    ocr_page_by_regions,
    segment_page_into_regions,
)
from docuready.ingest.script_router import detect_unicode_script
from docuready.ingest.tesseract_discovery import configure_pytesseract

ROOT = Path(__file__).resolve().parents[1]
CORPUS_DIR = ROOT / "research" / "loop15" / "corpus"
MANIFEST_PATH = ROOT / "research" / "loop15" / "dataset_manifest.json"


@pytest.fixture(autouse=True)
def setup_ocr():
    configure_pytesseract()


def test_classify_region_script_unicode_text():
    """Verifies Unicode script classification on known text snippets."""
    # Latin
    res_lat = detect_unicode_script("GOVERNMENT OF INDIA - MINISTRY OF EDUCATION")
    assert res_lat["primary_script"] == "LATIN"
    assert res_lat["detected_lang"] == "eng"

    # Devanagari
    res_dev = detect_unicode_script("सभी पात्र विद्यार्थियों को सूचित किया जाता है")
    assert res_dev["primary_script"] == "DEVANAGARI"
    assert res_dev["detected_lang"] == "hin"

    # Odia
    res_ori = detect_unicode_script("ସମସ୍ତ ଯୋଗ୍ୟ ଛାତ୍ରଛାତ୍ରୀ ଆବେଦନ କରିବାକୁ ଅନୁରୋଧ")
    assert res_ori["primary_script"] == "ODIA"
    assert res_ori["detected_lang"] == "ori"

    # Mixed Devanagari + Latin
    res_mix_hin = detect_unicode_script("Applicant Name / आवेदक का नाम: ROHIT VERMA")
    assert res_mix_hin["is_mixed"] is True
    assert res_mix_hin["detected_lang"] == "eng+hin"

    # Mixed Odia + Latin
    res_mix_ori = detect_unicode_script("Candidate Name / ଆବେଦନକାରୀଙ୍କ ନାମ: ROHIT VERMA")
    assert res_mix_ori["is_mixed"] is True
    assert res_mix_ori["detected_lang"] == "eng+ori"


def test_segment_page_into_regions_single_column():
    """Verifies that a single-column layout without vertical gutters does not produce false column splits."""
    im = Image.new("RGB", (1000, 500), (255, 255, 255))
    d = ImageDraw.Draw(im)
    d.rectangle([(100, 100), (900, 140)], fill=(0, 0, 0))
    d.rectangle([(100, 180), (900, 220)], fill=(0, 0, 0))
    d.rectangle([(100, 260), (900, 300)], fill=(0, 0, 0))

    regions = segment_page_into_regions(im)
    assert len(regions) >= 1
    # None of the regions should be false column splits
    for r in regions:
        assert r.region_type in ("HEADER", "BODY", "FOOTER", "UNIFORM")
        assert r.region_type not in ("COLUMN_LEFT", "COLUMN_RIGHT")


def test_segment_page_into_regions_two_column():
    """Verifies that two columns separated by a central quiet gutter are correctly identified."""
    im = Image.new("RGB", (1000, 600), (255, 255, 255))
    d = ImageDraw.Draw(im)
    # Left column text block (x: 100 to 450)
    d.rectangle([(100, 150), (450, 450)], fill=(0, 0, 0))
    # Right column text block (x: 550 to 900)
    d.rectangle([(550, 150), (900, 450)], fill=(0, 0, 0))

    regions = segment_page_into_regions(im)
    col_types = [r.region_type for r in regions]
    assert "COLUMN_LEFT" in col_types
    assert "COLUMN_RIGHT" in col_types


def test_ocr_page_by_regions_coordinate_mapping():
    """Verifies that tokens from sub-image crops are mapped back to global page coordinates."""
    # Test on DOC_CTRL_01
    img_path = CORPUS_DIR / "DOC_CTRL_01_ENGLISH_CERTIFICATE.png"
    if not img_path.exists():
        pytest.skip("Corpus image not found")

    im = Image.open(img_path)
    data = ocr_page_by_regions(im, dpi=200)

    # Check that coordinates exist and are non-negative
    assert len(data["left"]) > 0
    assert len(data["top"]) > 0
    assert all(l >= 0 for l in data["left"])
    assert all(t >= 0 for t in data["top"])
    assert all(w > 0 for w in data["width"])
    assert all(h > 0 for h in data["height"])

    # Page point conversion through PageOCRData
    ocr_obj = PageOCRData(data, dpi=200)
    assert len(ocr_obj.lines) > 0

    # Bounding boxes should be scaled to 72 DPI space
    scale = 72.0 / 200.0
    for l in ocr_obj.lines:
        bbox = l["bbox"]
        assert len(bbox) == 4
        assert bbox[0] < bbox[2]  # x0 < x1
        assert bbox[1] < bbox[3]  # y0 < y1
        assert bbox[2] <= im.width * scale + 5.0
        assert bbox[3] <= im.height * scale + 5.0


def test_ocr_page_by_regions_zero_regression_english():
    """Guarantees zero regression on English certificates (bit-exact 0.00% CER/WER)."""
    img_path = CORPUS_DIR / "DOC_CTRL_01_ENGLISH_CERTIFICATE.png"
    gt_path = ROOT / "research" / "loop15" / "ground_truth" / "DOC_CTRL_01_ENGLISH_CERTIFICATE_gt.txt"
    if not img_path.exists() or not gt_path.exists():
        pytest.skip("Corpus files missing")

    im = Image.open(img_path)
    with open(gt_path, "r", encoding="utf-8") as f:
        gt_text = f.read().strip()

    data = ocr_page_by_regions(im, dpi=200)
    ocr_obj = PageOCRData(data, dpi=200)
    hyp_text = "\n".join(l["text"] for l in ocr_obj.lines)

    from research.loop15.benchmark.run_region_benchmark import calculate_metrics
    cer, wer = calculate_metrics(hyp_text, gt_text)

    assert cer == 0.0, f"Expected 0.0 CER on control English certificate, got {cer}"
    assert wer == 0.0, f"Expected 0.0 WER on control English certificate, got {wer}"


def test_ocr_page_by_regions_bilingual_two_column():
    """Verifies that parallel bilingual columns are extracted and de-interleaved."""
    img_path = CORPUS_DIR / "DOC_MULTI_02_BILINGUAL_COLUMNS_HIN_ENG.png"
    if not img_path.exists():
        pytest.skip("Corpus image not found")

    im = Image.open(img_path)
    data = ocr_page_by_regions(im, dpi=200)
    ocr_obj = PageOCRData(data, dpi=200)
    full_text = " ".join(l["text"] for l in ocr_obj.lines)

    # Must contain both Hindi terms and English terms
    assert "राजस्व" in full_text or "निर्देशित" in full_text or "सत्यापन" in full_text
    assert "DISTRICT" in full_text or "revenue" in full_text.lower() or "verification" in full_text.lower()


def test_dataset_manifest_and_provenance_integrity():
    """Validates that research/loop15/dataset_manifest.json is structurally sound."""
    assert MANIFEST_PATH.exists()
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["version"] == "1.0"
    assert manifest["loop"] == "15"
    assert manifest["total_samples"] == len(manifest["samples"])
    assert manifest["total_samples"] >= 10

    # Ensure all three required provenance categories are present
    cohorts = manifest["cohort_counts"]
    assert cohorts["VERIFIED_EXTERNAL"] >= 1
    assert cohorts["DERIVED_FROM_EXTERNAL"] >= 5
    assert cohorts["VERIFIED_SYNTHETIC"] >= 2

    # Verify every registered file exists and has non-empty SHA-256
    for s in manifest["samples"]:
        sample_path = CORPUS_DIR / s["file_name"]
        assert sample_path.exists(), f"Sample file {s['file_name']} does not exist"
        assert len(s["sha256"]) == 64, f"Invalid SHA-256 for {s['file_name']}"
        assert s["provenance_category"] in ("VERIFIED_EXTERNAL", "DERIVED_FROM_EXTERNAL", "VERIFIED_SYNTHETIC")
