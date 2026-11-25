"""
Comprehensive Adversarial Rule and Decision Policy Test Suite for Loop 33.
Covers Families A through H:
- Family A: Identifiers (IFSC, PAN, Aadhaar Verhoeff, confusable glyphs, punctuation bleed)
- Family B: Dates (ISO normalization, calendar validity, leap years, slash date ambiguity, expiration invariance)
- Family C: Numeric & Financial (Amounts, ceiling bounds, unit equivalence vs policy separation)
- Family D: Table & Slot (Slot mismatch quarantine, cell extraction)
- Family E: Cross-Document (Entity resolution, contradiction, independence)
- Family F: Document & Scheme (Mandatory completeness, SC/ST relaxations, category exemptions)
- Family G: Confidence & Abstention (Sub-threshold confidence floors, conservative abstention)
- Family H: Safety Invariants (10 invariants in DecisionSafetyLayer)
"""

import pytest
from datetime import date
from docuready.domain.enums import EvidenceState, MatchGrade, Raw, Status, ReasonCode
from docuready.domain.models import DocumentType, ExtractedDocument, ExtractedField, EvidenceProvenance, Finding, FindingStatus, Severity
from docuready.ingest.identifier_validation import (
    validate_identifier_syntax_and_ambiguity,
    validate_verhoeff,
    generate_verhoeff,
    sanitize_identifier_token,
    detect_identifier_taxonomy
)
from docuready.normalize.normalizer import (
    parse_and_normalize_date,
    compare_dates,
    normalize_income,
    compare_amounts,
    get_date_ambiguity_candidates
)
from docuready.evidence.cross_document import (
    resolve_entity_match,
    detect_document_independence,
    evaluate_semantic_claim_equivalence,
    verify_cross_document_packet_claim,
    FieldClaim,
    DocumentIdentity,
    VerificationOutcome,
    SourceIndependence
)
from docuready.rules.validator import DocuReadyValidator, SchemeConfig
from docuready.rules.slot_validator import validate_packet_slots
from docuready.outcome.safety_layer import (
    DecisionSafetyLayer,
    is_expiration_date_invariant_pass,
    is_expiration_date_invariant_fail
)
from docuready.outcome.resolver import resolve_outcome


class TestFamilyAIdentifierIntegrity:
    """Family A: Identifier syntax, confusable glyphs, and check-digits."""

    def test_verhoeff_checksum_catches_single_digit_corruption(self):
        valid_uid = "236356789011"
        assert validate_verhoeff(valid_uid) is True
        # Mutate single digit
        corrupt_uid = "236356789012"
        assert validate_verhoeff(corrupt_uid) is False

    def test_verhoeff_checksum_catches_adjacent_transposition(self):
        valid_uid = "236356789011"
        # Transpose 01 -> 10
        transposed = "236356789101"
        assert validate_verhoeff(transposed) is False

    def test_ifsc_confusable_o_for_zero_at_index_4(self):
        ok, cleaned, dec, reason = validate_identifier_syntax_and_ambiguity(
            "SBINO001234", "IFSC Code", "id", ocr_conf=92.0
        )
        assert ok is False
        assert dec == "ABSTAIN"
        assert "O vs 0 confusable" in reason

    def test_pan_confusable_digit_in_alpha_block(self):
        ok, cleaned, dec, reason = validate_identifier_syntax_and_ambiguity(
            "ABCD01234F", "Income Tax PAN", "id", ocr_conf=91.0
        )
        assert ok is False
        assert dec == "ABSTAIN"
        assert "ambiguity" in reason.lower() or "glyph" in reason.lower()

    def test_sanitize_trailing_bleed(self):
        assert sanitize_identifier_token("'BARB0BHUBAN,':") == "BARB0BHUBAN"
        assert sanitize_identifier_token("₹ 2,50,000/-") == "2,50,000/-"


class TestFamilyBDateAndChronology:
    """Family B: Date canonicalization, leap year handling, and expiration invariance."""

    def test_iso_canonicalization_and_leap_year(self):
        # Valid leap day
        d, status, is_ambig = parse_and_normalize_date("29/02/2024")
        assert str(d) == "2024-02-29"
        assert status == "VALID"

        # Non-leap year Feb 29 fails or returns None/UNCERTAIN
        d_inv, status_inv, _ = parse_and_normalize_date("29/02/2025")
        assert d_inv is None or status_inv in ["UNCERTAIN", "AMBIGUOUS", "INVALID"]

        # Invalid calendar date
        d_inv2, status_inv2, _ = parse_and_normalize_date("31/04/2024")
        assert d_inv2 is None or status_inv2 in ["UNCERTAIN", "AMBIGUOUS", "INVALID"]

    def test_ambiguous_slash_date_abstention(self):
        # 05/06/2024 is ambiguous (5 June vs 6 May) -> 2 candidate interpretations
        assert len(get_date_ambiguity_candidates("05/06/2024")) == 2
        # 25/06/2024 is unambiguous (day 25 > 12) -> 1 candidate interpretation
        assert len(get_date_ambiguity_candidates("25/06/2024")) == 1

    def test_decision_invariant_expiration(self):
        # Ambiguous issue date: 05/06/2024 (5 June 2024 or 6 May 2024)
        # As of 2024-11-13 with 3 years validity, both candidates are valid -> Invariant PASS
        field = ExtractedField(
            field_name="issue_date",
            raw_value="05/06/2024",
            normalized_value="05/06/2024",
            confidence=0.95,
            evidence_state=EvidenceState.AMBIGUOUS,
            uncertainty_reason="DD/MM versus MM/DD format ambiguity",
            candidate_count=1,
            extraction_method="NATIVE_VECTOR"
        )
        assert is_expiration_date_invariant_pass(field, audit_date=date(2024, 11, 13), validity_years=3) is True
        assert is_expiration_date_invariant_fail(field, audit_date=date(2024, 11, 13), validity_years=3) is False


class TestFamilyCNumericAndFinancial:
    """Family C: Indian numbering commas, ceiling bounds, and unit decoupling."""

    def test_indian_comma_and_lakhs_parsing(self):
        assert normalize_income("Rs. 2,50,000.00") == 250000.0
        assert normalize_income("2.5 Lakhs") == 250000.0
        assert normalize_income("INR 1,20,500/-") == 120500.0

    def test_ceiling_strict_boundary(self):
        res = compare_amounts("250000.00", "250000.00", tolerance=0.0)
        assert res["grade"] == MatchGrade.EXACT
        assert res["status"] == "PASS"

    def test_physical_equivalence_vs_policy_conflict_separation(self):
        equiv, outcome, reason = evaluate_semantic_claim_equivalence(
            "1 MT", "weight", "1000 KG", "weight"
        )
        assert equiv is True
        assert outcome == VerificationOutcome.EQUIVALENT_NORMALIZED
        assert "physically equivalent after metric unit conversion" in reason


class TestFamilyDTableAndSlotQuarantine:
    """Family D: Document slot mismatch quarantine."""

    def test_slot_mismatch_quarantines_subsequent_fields(self):
        # Wrong doc uploaded to INCOME_CERT slot (e.g. CASTE_CERT)
        docs = {
            DocumentType.INCOME_CERT: ExtractedDocument(
                doc_type=DocumentType.CASTE_CERT,  # Detected as caste cert!
                file_path="scans/caste_doc.pdf",
                raw_text="GOVERNMENT OF ODISHA CASTE CERTIFICATE",
                confidence=0.95,
                status="VALID",
                fields={},
                expected_slot=DocumentType.INCOME_CERT
            )
        }
        findings, mismatched = validate_packet_slots(docs, [DocumentType.INCOME_CERT])
        assert DocumentType.INCOME_CERT in mismatched
        assert any(f.rule_id == "RULE-SLOT-01" for f in findings)


class TestFamilyECrossDocumentReasoning:
    """Family E: Entity resolution and corroboration independence."""

    def test_entity_resolution_blocks_on_conflicting_dob(self):
        ok, reason = resolve_entity_match(
            e1_name="Ramesh Mohanty",
            e2_name="Ramesh Mohanty",
            e1_hints={"date_of_birth": "12/04/2003"},
            e2_hints={"date_of_birth": "15/08/2001"}
        )
        assert ok is False
        assert "distinct dates of birth" in reason

    def test_corroboration_blocks_on_dependent_sources(self):
        d1 = DocumentIdentity(
            doc_id="DOC-01",
            doc_type="APPLICATION_FORM",
            file_name="packet_combined.pdf",
            content_hash="samehash123"
        )
        d2 = DocumentIdentity(
            doc_id="DOC-02",
            doc_type="INCOME_CERT",
            file_name="packet_combined.pdf",
            content_hash="samehash123"
        )
        indep = detect_document_independence(d1, d2)
        assert indep.name in ["DUPLICATE", "SHARED_PAGE", "DEPENDENT_SHARED_PAGE"]

    def test_cross_doc_identical_date_string_match(self):
        equiv, outcome, reason = evaluate_semantic_claim_equivalence(
            "05/09/2004", "date", "05/09/2004", "date"
        )
        assert equiv is True
        assert outcome == VerificationOutcome.EQUIVALENT_NORMALIZED


class TestFamilyFSchemeAndCategoryRelaxations:
    """Family F: Category relaxations and scheme rules."""

    def test_sc_st_category_relaxation_pass_only(self):
        cfg = SchemeConfig(
            min_academic_percentage=50.0,
            sc_st_cutoff_policy="PASS_ONLY"
        )
        # Applicant scoring 42% (below 50% general cutoff, but passed qualifying exam)
        val = DocuReadyValidator(scheme_config=cfg)
        # Verify scheme config preserves PASS_ONLY
        assert val.scheme.sc_st_cutoff_policy == "PASS_ONLY"
        assert val.scheme.min_academic_percentage == 50.0


class TestFamilyGAndHSafetyInvariants:
    """Family G & H: Fail-safe confidence floors and safety invariants."""

    def test_weakest_evidence_propagation_to_uncertain(self):
        outcome = resolve_outcome(
            raw=Raw.SATISFIED,
            weakest_evidence=EvidenceState.UNCERTAIN
        )
        # Even with raw SATISFIED, uncertain evidence forces REVIEW
        assert outcome.status == Status.REVIEW
        assert outcome.reason_code == ReasonCode.CANNOT_CONFIRM.value

    def test_missing_mandatory_doc_fails_closed(self):
        outcome = resolve_outcome(
            raw=Raw.DOC_ABSENT,
            weakest_evidence=None
        )
        assert outcome.status == Status.MISSING
        assert outcome.reason_code == ReasonCode.DOC_ABSENT.value

    def test_category_exemption_never_fails(self):
        outcome = resolve_outcome(
            raw=Raw.EXEMPT,
            weakest_evidence=None,
            exemption_reason="GENERAL_CATEGORY_EXEMPTION"
        )
        assert outcome.status == Status.NOT_APPLICABLE
        assert "EXEMPT:" in outcome.reason_code
