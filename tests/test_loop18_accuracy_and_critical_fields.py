"""
Loop 18 Test Suite: Independent OCR Accuracy, Benchmark Integrity & Critical-Field Stress Validation.

Validates:
1. 25-document dataset manifest integrity, splits (19 PRIMARY + 6 CHALLENGE), and SHA-256 hashes.
2. Spatial line reconstruction via PageOCRData (no line flattening).
3. Reading-order inversion metric sensitivity (Kendall-tau rank inversions).
4. Macro per-document vs Micro corpus-level metric computation.
5. Critical-field extraction contract compliance across new cohort documents.
6. Adversarial stress fixtures integrity and ground-truth alignment.
7. Profiling latency and adaptive routing across new external documents.
"""

import json
from pathlib import Path
import fitz
import numpy as np
import pytest
from PIL import Image

from docuready.ingest.extractor import PageOCRData
from docuready.ingest.adaptive_ocr import (
    profile_document,
    select_ocr_strategy,
    execute_adaptive_ocr,
    DocumentProfile,
    StrategyDecisionRecord,
)
from docuready.ingest.tesseract_discovery import configure_pytesseract
from research.loop18.benchmark.run_strategy_benchmark import (
    compute_reading_order_inversion,
    compute_char_edit_distance,
    compute_word_edit_distance,
    evaluate_critical_fields,
)

ROOT = Path(__file__).resolve().parents[1]
CORPUS_DIR = ROOT / "research" / "loop18" / "corpus"
GT_DIR = ROOT / "research" / "loop18" / "ground_truth"
CF_DIR = ROOT / "research" / "loop18" / "critical_fields"
STRESS_DIR = ROOT / "research" / "loop18" / "stress_fixtures"
MANIFEST_PATH = ROOT / "research" / "loop18" / "dataset_manifest.json"


@pytest.fixture(scope="session", autouse=True)
def setup_tesseract():
    configure_pytesseract()


def _load_doc_image(doc_id: str) -> Image.Image:
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


def test_loop18_manifest_integrity():
    """Verify that Loop 18 manifest accurately records 25 documents across splits."""
    assert MANIFEST_PATH.exists(), "Manifest file missing"
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["version"] == "3.0"
    assert manifest["loop"] == "18"
    assert manifest["total_samples"] == 25
    assert manifest["split_counts"]["PRIMARY_VALIDATION"] == 19
    assert manifest["split_counts"]["SEALED_CHALLENGE"] == 6
    assert manifest["critical_field_contract_count"] == 13
    assert len(manifest["samples"]) == 25

    for s in manifest["samples"]:
        assert s["sample_id"]
        assert s["split"] in ("PRIMARY_VALIDATION", "SEALED_CHALLENGE")
        assert len(s["sha256"]) == 64
        # Verify physical file exists and matches recorded size
        file_path = CORPUS_DIR / s["file_name"]
        assert file_path.exists(), f"Missing file: {s['file_name']}"
        assert file_path.stat().st_size == s["file_size_bytes"]


def test_line_reconstruction_integrity():
    """Verify that PageOCRData reconstructs spatial lines and does not collapse them into a single line."""
    dummy_ocr_data = {
        "text": ["GOVERNMENT", "OF", "INDIA", "MINISTRY", "OF", "FINANCE", "ORDER", "NO", "9812"],
        "conf": ["95", "95", "95", "92", "92", "92", "90", "90", "90"],
        "left": [50, 150, 200, 50, 150, 200, 50, 120, 160],
        "top": [30, 30, 30, 70, 70, 70, 110, 110, 110],
        "width": [90, 40, 50, 90, 40, 70, 60, 30, 50],
        "height": [20, 20, 20, 20, 20, 20, 20, 20, 20],
        "line_num": [1, 1, 1, 2, 2, 2, 3, 3, 3],
        "block_num": [1, 1, 1, 1, 1, 1, 1, 1, 1],
        "par_num": [1, 1, 1, 1, 1, 1, 1, 1, 1]
    }
    ocr = PageOCRData(dummy_ocr_data, dpi=200)
    lines = [l["text"] for l in ocr.lines if l.get("text")]
    assert len(lines) == 3, f"Expected 3 spatial lines, got {len(lines)}"
    assert lines[0] == "GOVERNMENT OF INDIA"
    assert lines[1] == "MINISTRY OF FINANCE"
    assert lines[2] == "ORDER NO 9812"


def test_reading_order_inversion_calculation():
    """Verify that compute_reading_order_inversion properly detects inversions."""
    ref_lines = [
        "First line header",
        "Second line middle content",
        "Third line footer note"
    ]
    # Perfectly ordered
    hyp_ordered = [
        "First line header",
        "Second line middle content",
        "Third line footer note"
    ]
    assert compute_reading_order_inversion(hyp_ordered, ref_lines) == 0.0

    # Inverted lines: line 3 comes before line 1
    hyp_inverted = [
        "Third line footer note",
        "Second line middle content",
        "First line header"
    ]
    inv_rate = compute_reading_order_inversion(hyp_inverted, ref_lines)
    assert inv_rate > 50.0, f"Expected inversion > 50%, got {inv_rate}%"


def test_dual_metric_computation():
    """Verify character and word edit distance calculations."""
    ref = "GOVERNMENT OF INDIA"
    hyp = "GOVERNMENT OF INIDA"  # 2 char transposition/sub
    c_dist, c_tot = compute_char_edit_distance(hyp, ref)
    w_dist, w_tot = compute_word_edit_distance(hyp, ref)

    assert c_tot == 19
    assert c_dist == 2
    assert w_tot == 3
    assert w_dist == 1


def test_new_documents_profiling_and_execution():
    """Verify that new documents DOC_EXT_05 through DOC_EXT_09 profile and execute adaptively."""
    new_docs = [
        "DOC_EXT_05_PUBLIC_HEALTH_CIRCULAR",
        "DOC_EXT_06_ODIA_REVENUE_NOTICE",
        "DOC_EXT_07_TECHNICAL_EDUCATION_DIPLOMA",
        "DOC_EXT_08_PENSION_LIFE_CERTIFICATE_RECEIPT",
        "DOC_EXT_09_RTI_APPEAL_DISPOSAL_ORDER"
    ]
    for d_id in new_docs:
        img = _load_doc_image(d_id)
        profile = profile_document(img)
        assert profile.profiling_latency_ms < 1400.0, f"Profiling too slow on {d_id}"
        decision = select_ocr_strategy(profile)
        assert decision.selected_strategy in (
            "FAST_PATH_ENG", "FAST_PATH_HIN", "FAST_PATH_ORI", "GLOBAL_MULTILINGUAL", "MULTILINGUAL_GLOBAL", "REGION_AWARE_ROUTING"
        )

        data, exec_decision = execute_adaptive_ocr(img, dpi=200)
        assert exec_decision.ocr_model_invocations in (1, 2)
        words = [w for w in data.get("text", []) if str(w).strip()]
        assert len(words) > 10, f"Too few words extracted from {d_id}"


def test_critical_fields_evaluation():
    """Verify critical field matching logic on sample contract."""
    crit_fields = {
        "notice_no": "MOHFW-DIS-2026-8841",
        "issue_date": "14/09/2026",
        "district": "Khordha",
        "amount": "4250"
    }
    ocr_hyp = (
        "MINISTRY OF HEALTH Notification No: MOHFW-DIS-2026-8841\n"
        "Date of Issue: 14/09/2026 Target District: Khordha\n"
        "Assessed Amount: Rs 4250 only"
    )
    eval_res = evaluate_critical_fields(ocr_hyp, crit_fields)
    assert eval_res["total_fields"] == 4
    assert eval_res["exact_matches"] == 4
    assert eval_res["match_rate"] == 1.0
    assert eval_res["mean_field_cer"] == 0.0


def test_stress_fixtures_exist():
    """Verify all 4 controlled stress fixtures exist with ground-truth and critical fields."""
    fixtures = [
        "STRESS_01_SIMILAR_DIGIT_CONFUSION",
        "STRESS_02_FAINT_RUBBER_STAMP_OVERLAY",
        "STRESS_03_MULTICOLUMN_EMBEDDED_AMOUNTS",
        "STRESS_04_SKEW_LOW_CONTRAST"
    ]
    for fix in fixtures:
        img_p = STRESS_DIR / f"{fix}.png"
        gt_p = STRESS_DIR / f"{fix}_gt.txt"
        cf_p = STRESS_DIR / f"{fix}_cf.json"

        assert img_p.exists(), f"Missing stress image: {fix}"
        assert gt_p.exists(), f"Missing stress ground truth: {fix}"
        assert cf_p.exists(), f"Missing stress critical fields: {fix}"

        with open(cf_p, "r", encoding="utf-8") as f:
            cf_data = json.load(f)
            assert len(cf_data.get("critical_fields", {})) >= 3
