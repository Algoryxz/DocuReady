"""
Loop 20 - Blind Generalization, Table Association Reliability & False-Verification Audit
Unit & Integration Test Suite
"""

import json
from pathlib import Path
import pytest
from PIL import Image
import pytesseract

from docuready.ingest.tesseract_discovery import configure_pytesseract
from docuready.ingest.table_association import (
    TableCell,
    TableGrid,
    FieldEvidence,
    build_table_grid,
    extract_field_by_spatial_association,
    extract_cell_by_intersection,
    verify_cross_document_evidence,
)
from docuready.ingest.script_router import detect_unicode_script, resolve_optimal_ocr_language

ROOT = Path(__file__).resolve().parents[1]
TABLES_DIR = ROOT / "research" / "loop20" / "tables"
MANIFEST_PATH = ROOT / "research" / "loop20" / "dataset_manifest.json"


@pytest.fixture(scope="module", autouse=True)
def setup_ocr():
    configure_pytesseract()


def test_loop20_manifest_integrity():
    assert MANIFEST_PATH.exists(), "Loop 20 manifest must exist"
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["total_documents"] == 34, f"Expected 34 documents, got {data['total_documents']}"
    assert len(data["documents"]) == 34
    for doc_id, meta in data["documents"].items():
        img_p = TABLES_DIR / f"{doc_id}.png"
        assert img_p.exists(), f"Image {img_p} missing"
        assert len(meta["sha256"]) == 64


def test_cohort_a_development_accuracy():
    img_path = TABLES_DIR / "DEV_01_ACCOUNTING_INVOICE.png"
    img = Image.open(img_path)
    ocr_data = pytesseract.image_to_data(img, lang="eng", output_type=pytesseract.Output.DICT)
    grid = build_table_grid(ocr_data, img.width, img.height)

    # invoice_total in Grand Invoice Total row, col 5
    ev = extract_field_by_spatial_association(
        grid=grid,
        field_name="invoice_total",
        target_pattern="Grand Invoice Total",
        col_idx=5,
        expected_type="amount",
    )
    assert ev is not None
    assert ev.value == "110000"
    assert not ev.is_ambiguous
    assert ev.col_idx == 5


def test_cohort_c_blind_evaluation_generalization():
    # Test on unseen BLIND_01 Salary Slip
    img_path = TABLES_DIR / "BLIND_01_SALARY_SLIP.png"
    img = Image.open(img_path)
    ocr_data = pytesseract.image_to_data(img, lang="eng", output_type=pytesseract.Output.DICT)
    grid = build_table_grid(ocr_data, img.width, img.height)

    # Net Pay Disbursed in col 1
    ev_net = extract_field_by_spatial_association(
        grid=grid,
        field_name="net_pay",
        target_pattern="Net Pay Disbursed",
        col_idx=1,
        expected_type="amount",
    )
    assert ev_net is not None
    assert ev_net.value == "107000"
    assert not ev_net.is_ambiguous

    # PF Contribution in col 3
    ev_pf = extract_field_by_spatial_association(
        grid=grid,
        field_name="pf_contrib",
        target_pattern="Basic Pay", # row 0 has PF Contribution in col 3
        col_idx=3,
        expected_type="amount",
    )
    assert ev_pf is not None
    assert ev_pf.value == "8160"


def test_adversarial_adjacent_similar_names_isolation():
    # CHALL_02: Ramesh Kumar Sahoo (score 92) vs Ramesh Chand Sahoo (score 45)
    img_path = TABLES_DIR / "CHALL_02_WRONG_PERSON_ADJACENT_ROWS.png"
    img = Image.open(img_path)
    ocr_data = pytesseract.image_to_data(img, lang="eng", output_type=pytesseract.Output.DICT)
    grid = build_table_grid(ocr_data, img.width, img.height)

    ev_kumar = extract_field_by_spatial_association(
        grid=grid,
        field_name="ramesh_kumar_score",
        target_pattern="Ramesh Kumar Sahoo",
        col_idx=2,
        expected_type="marks",
    )
    assert ev_kumar is not None
    assert ev_kumar.value == "92"

    ev_chand = extract_field_by_spatial_association(
        grid=grid,
        field_name="ramesh_chand_score",
        target_pattern="Ramesh Chand Sahoo",
        col_idx=2,
        expected_type="marks",
    )
    assert ev_chand is not None
    assert ev_chand.value == "45"


def test_adversarial_empty_cell_preservation():
    # CHALL_05: HOLD-401 has blank Arrears and 15000 Current Demand
    img_path = TABLES_DIR / "CHALL_05_EMPTY_AMOUNT_CELL.png"
    img = Image.open(img_path)
    ocr_data = pytesseract.image_to_data(img, lang="eng", output_type=pytesseract.Output.DICT)
    grid = build_table_grid(ocr_data, img.width, img.height)

    ev_arrears = extract_field_by_spatial_association(
        grid=grid,
        field_name="hold_401_arrears",
        target_pattern="HOLD-401",
        col_idx=1,
        expected_type="empty",
    )
    assert ev_arrears is not None
    assert ev_arrears.value == ""
    assert len(ev_arrears.provenance["raw_tokens"]) == 0


def test_adversarial_label_echo_rejection():
    # CHALL_06: Form Date vs Verification Date (blank)
    img_path = TABLES_DIR / "CHALL_06_LABEL_AS_VALUE_TRAP.png"
    img = Image.open(img_path)
    ocr_data = pytesseract.image_to_data(img, lang="eng", output_type=pytesseract.Output.DICT)
    grid = build_table_grid(ocr_data, img.width, img.height)

    ev_blank = extract_field_by_spatial_association(
        grid=grid,
        field_name="app_901_verification_date",
        target_pattern="APP-901",
        col_idx=2,
        expected_type="empty",
    )
    assert ev_blank is not None
    assert ev_blank.value != "Verification Date"
    assert ev_blank.value == ""


def test_cross_document_verification_contract():
    # Construct synthetic evidence objects
    ev1 = FieldEvidence(
        field_name="total_amount",
        value="75400",
        raw_text="75400",
        bbox=(100, 200, 180, 220),
        row_idx=1,
        col_idx=3,
        col_header="Amount",
        confidence=95.0,
        is_ambiguous=False,
        provenance={"doc": "INV_A"},
    )
    ev2_match = FieldEvidence(
        field_name="total_amount",
        value="₹ 75,400",
        raw_text="₹ 75,400",
        bbox=(100, 200, 180, 220),
        row_idx=1,
        col_idx=3,
        col_header="Amount",
        confidence=96.0,
        is_ambiguous=False,
        provenance={"doc": "INV_B"},
    )
    ev2_mismatch = FieldEvidence(
        field_name="total_amount",
        value="78400",
        raw_text="78400",
        bbox=(100, 200, 180, 220),
        row_idx=1,
        col_idx=3,
        col_header="Amount",
        confidence=94.0,
        is_ambiguous=False,
        provenance={"doc": "INV_C"},
    )
    ev_ambig = FieldEvidence(
        field_name="total_amount",
        value="75400",
        raw_text="75400",
        bbox=(100, 200, 180, 220),
        row_idx=1,
        col_idx=3,
        col_header="Amount",
        confidence=95.0,
        is_ambiguous=True,
        provenance={"doc": "INV_D"},
    )

    # 1. Agreement
    res_agree = verify_cross_document_evidence(ev1, ev2_match, "amount")
    assert res_agree["status"] == "AGREEMENT"
    assert res_agree["is_verified"] is True

    # 2. Mismatch
    res_mismatch = verify_cross_document_evidence(ev1, ev2_mismatch, "amount")
    assert res_mismatch["status"] == "MISMATCH"
    assert res_mismatch["is_verified"] is False

    # 3. Ambiguous Association
    res_ambig = verify_cross_document_evidence(ev1, ev_ambig, "amount")
    assert res_ambig["status"] == "AMBIGUOUS_ASSOCIATION"
    assert res_ambig["is_verified"] is False

    # 4. Missing
    res_missing = verify_cross_document_evidence(ev1, None, "amount")
    assert res_missing["status"] == "MISSING"
    assert res_missing["is_verified"] is False


def test_script_routing_letter_gating():
    # Punctuation/numeric stroke noise should NOT route to Hindi or Odia
    res_noise = detect_unicode_script("VOUCHER NO 101 | 221700 - 194300 / 08/01/2026 ===")
    assert res_noise["detected_lang"] == "eng"
    assert not res_noise["is_mixed"]

    # Genuine Devanagari should route to hin
    res_hin = detect_unicode_script("कार्यालय जिलाधीश, कटक")
    assert res_hin["detected_lang"] == "hin"

    # Genuine Odia should route to ori
    res_ori = detect_unicode_script("ଜିଲ୍ଲାପାଳଙ୍କ କାର୍ଯ୍ୟାଳୟ, କଟକ")
    assert res_ori["detected_lang"] == "ori"
