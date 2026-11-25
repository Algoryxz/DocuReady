"""
Loop 32 Bug Reproduction & Regression Test Suite.
Verifies reproducible defects discovered across DocuReady subsystems:
- BUG-032-001: Vector field extraction tuple bounding box crash
- BUG-032-002: ISO date normalization false contradiction
- BUG-032-003: Premature unit contradiction suppressing metric equivalence
- BUG-032-005: Corrupted Verhoeff tables in normalizer.py
"""

import pytest
from docuready.ingest.extractor import _find_field_in_page_vector
from docuready.evidence.cross_document import (
    evaluate_semantic_claim_equivalence,
    normalize_claim_value,
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
    """BUG-032-002: YYYY-MM-DD and DD/MM/YYYY representing same day must be equivalent."""
    d_iso = "2026-03-15"
    d_in = "15/03/2026"
    assert normalize_claim_value(d_iso, "date") == "15/03/2026"
    assert normalize_claim_value(d_in, "date") == "15/03/2026"

    ok, outcome, msg = evaluate_semantic_claim_equivalence(d_iso, "date", d_in, "date")
    assert ok is True
    assert outcome == VerificationOutcome.EQUIVALENT_NORMALIZED


def test_bug_032_003_metric_unit_cross_doc_verification():
    """BUG-032-003: evaluate_semantic_claim_equivalence evaluates 1 MT == 1000 KG, while packet verification conservatively flags unharmonized units."""
    ok, outcome, msg = evaluate_semantic_claim_equivalence("1 MT", "weight", "1000 KG", "weight")
    assert ok is True
    assert outcome == VerificationOutcome.EQUIVALENT_NORMALIZED

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


def test_bug_032_005_verhoeff_table_parity():
    """BUG-032-005: normalizer.py and identifier_validation.py must share standard Verhoeff tables."""
    test_aadhaar = "234567890124"
    assert ident_validate_verhoeff(test_aadhaar) is True
    assert norm_validate_verhoeff(test_aadhaar) is True
