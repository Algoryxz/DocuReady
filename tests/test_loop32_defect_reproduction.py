"""
Loop 32 Bug Reproduction & Regression Test Suite.
Verifies reproducible defects discovered across DocuReady subsystems:
- BUG-032-001: Vector field extraction tuple bounding box crash
- BUG-032-002: ISO date normalization, leap year validation, invalid date rejection, ambiguity abstention
- BUG-032-003: Physical metric equivalence vs conservative evidence-policy conflict distinction
- BUG-032-005: Corrupted Verhoeff tables in normalizer.py
"""

import pytest
from datetime import date
from docuready.ingest.extractor import _find_field_in_page_vector
from docuready.evidence.cross_document import (
    evaluate_semantic_claim_equivalence,
    normalize_claim_value,
    is_ambiguous_date_representation,
    verify_cross_document_packet_claim,
    FieldClaim,
    EntityIdentity,
    DocumentIdentity,
    VerificationOutcome
)
from docuready.normalize.normalizer import (
    validate_verhoeff as norm_validate_verhoeff,
    generate_verhoeff_12 as norm_generate_verhoeff
)
from docuready.ingest.identifier_validation import (
    validate_verhoeff as ident_validate_verhoeff,
    generate_verhoeff as ident_generate_verhoeff
)


class MockTuplePage:
    """Simulates a PDF backend returning tuple bounding boxes (e.g. PdfiumPageBackend)."""
    def get_text(self):
        return "ANNUAL REVENUE: 500000\n"

    def search_for(self, needle):
        return [(15.5, 30.2, 120.8, 55.4)]


def test_bug_032_001_tuple_bounding_box_extraction():
    """BUG-032-001: _find_field_in_page_vector must support tuple bounding boxes."""
    page = MockTuplePage()
    val, bbox, snippet = _find_field_in_page_vector(page, [r"ANNUAL REVENUE:\s*(\d+)"])
    assert val == "500000"
    assert bbox == [15.5, 30.2, 120.8, 55.4]


def test_bug_032_002_iso_date_normalization_equivalence():
    """BUG-032-002: YYYY-MM-DD and DD/MM/YYYY canonicalize to ISO and evaluate equivalent."""
    d_iso = "2026-03-15"
    d_in = "15/03/2026"
    assert normalize_claim_value(d_iso, "date") == "2026-03-15"
    assert normalize_claim_value(d_in, "date") == "2026-03-15"

    ok, outcome, msg = evaluate_semantic_claim_equivalence(d_iso, "date", d_in, "date")
    assert ok is True
    assert outcome == VerificationOutcome.EQUIVALENT_NORMALIZED
    assert "2026-03-15" in msg


def test_bug_032_002_supported_date_formats():
    """BUG-032-002: Supported formats (ISO, slash, hyphen, dot) canonicalize to ISO YYYY-MM-DD."""
    assert normalize_claim_value("2026-08-25", "date") == "2026-08-25"
    assert normalize_claim_value("25/08/2026", "date") == "2026-08-25"
    assert normalize_claim_value("25-08-2026", "date") == "2026-08-25"
    assert normalize_claim_value("25.08.2026", "date") == "2026-08-25"


def test_bug_032_002_date_leap_year_validation():
    """BUG-032-002: Leap years validate correctly; invalid leap days return INVALID_DATE and abstain."""
    # 2024 is a leap year
    assert normalize_claim_value("29/02/2024", "date") == "2024-02-29"
    ok, outcome, _ = evaluate_semantic_claim_equivalence("29/02/2024", "date", "2024-02-29", "date")
    assert ok is True
    assert outcome == VerificationOutcome.EQUIVALENT_NORMALIZED

    # 2025 is not a leap year
    assert normalize_claim_value("29/02/2025", "date") == "INVALID_DATE"
    ok, outcome, msg = evaluate_semantic_claim_equivalence("29/02/2025", "date", "28/02/2025", "date")
    assert ok is False
    assert outcome == VerificationOutcome.ABSTAIN
    assert "invalid date" in msg.lower()


def test_bug_032_002_invalid_calendar_dates():
    """BUG-032-002: Non-existent calendar dates (e.g. Feb 31, Apr 31) are marked invalid and abstain."""
    assert normalize_claim_value("31/02/2026", "date") == "INVALID_DATE"
    assert normalize_claim_value("31/04/2026", "date") == "INVALID_DATE"

    ok, outcome, msg = evaluate_semantic_claim_equivalence("31/02/2026", "date", "28/02/2026", "date")
    assert ok is False
    assert outcome == VerificationOutcome.ABSTAIN
    assert "invalid date" in msg.lower()


def test_bug_032_002_ambiguous_date_formats():
    """BUG-032-002: Dates with ambiguous DD/MM vs MM/DD representation abstain across conflicting formats."""
    # 05/06/2026 could be May 6 or June 5; compared against 06/05/2026 it must abstain
    ok, outcome, msg = evaluate_semantic_claim_equivalence("05/06/2026", "date", "06/05/2026", "date")
    assert ok is False
    assert outcome == VerificationOutcome.ABSTAIN
    assert "ambiguous date format" in msg.lower()

    # Unambiguous dates (day > 12) do NOT abstain on ambiguity
    ok, outcome, _ = evaluate_semantic_claim_equivalence("15/03/2026", "date", "2026-03-15", "date")
    assert ok is True
    assert outcome == VerificationOutcome.EQUIVALENT_NORMALIZED


def test_bug_032_003_metric_unit_cross_doc_verification():
    """BUG-032-003: Physical metric equivalence is distinct from conservative evidence-policy conflict."""
    # 1. Physical equivalence evaluation
    ok, outcome, msg = evaluate_semantic_claim_equivalence("1 MT", "weight", "1000 KG", "weight")
    assert ok is True
    assert outcome == VerificationOutcome.EQUIVALENT_NORMALIZED
    assert "physically equivalent" in msg.lower()

    # Physical mismatch evaluation
    ok, outcome, msg = evaluate_semantic_claim_equivalence("1 MT", "weight", "500 KG", "weight")
    assert ok is False
    assert outcome == VerificationOutcome.CONTRADICTION
    assert "physical weight mismatch" in msg.lower()

    # 2. Conservative cross-document packet policy
    target = EntityIdentity(entity_id="E1", canonical_name="ACME LOGISTICS")
    docs = {
        "d1": DocumentIdentity(doc_id="d1", doc_type="INVOICE", file_name="inv.pdf", content_hash="h1"),
        "d2": DocumentIdentity(doc_id="d2", doc_type="SHIPPING", file_name="ship.pdf", content_hash="h2")
    }
    claims = [
        FieldClaim(claim_id="c1", doc_id="d1", field_name="cargo_weight", field_type="weight", claimed_value="1 MT", raw_ocr_value="1 MT", confidence=92.0, unit_or_currency="MT"),
        FieldClaim(claim_id="c2", doc_id="d2", field_name="cargo_weight", field_type="weight", claimed_value="1000 KG", raw_ocr_value="1000 KG", confidence=94.0, unit_or_currency="KG")
    ]

    res = verify_cross_document_packet_claim("cargo_weight", target, claims, docs, operating_threshold=70.0)
    assert res.outcome == VerificationOutcome.CONTRADICTION
    assert res.is_verified is False
    assert "Evidence policy conflict" in res.reason


def test_bug_032_005_verhoeff_table_parity():
    """BUG-032-005: normalizer.py and identifier_validation.py must share standard Verhoeff tables."""
    test_aadhaar = "234567890124"
    assert ident_validate_verhoeff(test_aadhaar) is True
    assert norm_validate_verhoeff(test_aadhaar) is True
