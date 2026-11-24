"""
Unit and integration tests for Loop 28:
Cross-Document Verification Reliability, Entity Resolution & Contradiction Detection.
"""

import pytest
from docuready.evidence.cross_document import (
    DocumentIdentity,
    EntityIdentity,
    FieldClaim,
    PacketVerificationResult,
    VerificationOutcome,
    SourceIndependence,
    resolve_entity_match,
    detect_document_independence,
    verify_cross_document_packet_claim,
    compute_string_content_hash,
)


class TestEntityResolutionSafety:
    def test_same_name_different_dob_rejected(self):
        """Rule: A matching name alone does NOT establish identity if DOB conflicts."""
        ok, reason = resolve_entity_match(
            e1_name="Rohit Verma",
            e2_name="Rohit Verma",
            e1_hints={"date_of_birth": "05/09/2004", "father_name": "Suresh Verma"},
            e2_hints={"date_of_birth": "12/11/1998", "father_name": "Suresh Verma"},
        )
        assert ok is False
        assert "distinct dates of birth" in reason

    def test_same_name_different_parent_rejected(self):
        """Rule: Same name with different parent names is an entity conflict."""
        ok, reason = resolve_entity_match(
            e1_name="Rohit Verma",
            e2_name="Rohit Verma",
            e1_hints={"father_name": "Suresh Verma"},
            e2_hints={"father_name": "Ramesh Chandra Verma"},
        )
        assert ok is False
        assert "distinct parent/guardian names" in reason

    def test_same_name_different_pan_rejected(self):
        """Rule: Distinct tax IDs strictly reject entity matching."""
        ok, reason = resolve_entity_match(
            e1_name="Priya Mohapatra",
            e2_name="Priya Mohapatra",
            e1_hints={"tax_id": "ABCDE1234F"},
            e2_hints={"tax_id": "XYZPR9876K"},
        )
        assert ok is False
        assert "distinct identification numbers" in reason

    def test_spelling_variation_with_anchor_resolved(self):
        """Rule: Minor spelling variation (Rohit Verma vs Rohit Varma) resolved if anchor matches."""
        ok, reason = resolve_entity_match(
            e1_name="Rohit Verma",
            e2_name="Rohit Varma",
            e1_hints={"date_of_birth": "05/09/2004"},
            e2_hints={"date_of_birth": "05/09/2004"},
        )
        assert ok is True
        assert "Spelling variation resolved" in reason

    def test_spelling_variation_without_anchor_rejected(self):
        """Rule: Minor spelling variation WITHOUT anchor must abstain / reject."""
        ok, reason = resolve_entity_match(
            e1_name="Rohit Verma",
            e2_name="Rohit Varma",
            e1_hints={},
            e2_hints={},
        )
        assert ok is False
        assert "without corroborating identifier" in reason


class TestSourceIndependence:
    def test_exact_content_hash_duplicate_detected(self):
        """Rule: Duplicate files must be flagged as DUPLICATE, not independent."""
        text = "Directorate of Higher Education Intake Form"
        h = compute_string_content_hash(text)
        d1 = DocumentIdentity("DOC_01", "APPLICATION", "scan1.png", h, raw_text=text)
        d2 = DocumentIdentity("DOC_02", "APPLICATION", "scan1_copy.png", h, raw_text=text)
        assert detect_document_independence(d1, d2) == SourceIndependence.DUPLICATE

    def test_different_documents_independent(self):
        d1 = DocumentIdentity("DOC_01", "APPLICATION", "app.png", "hash1", raw_text="Application form details")
        d2 = DocumentIdentity("DOC_02", "INCOME_CERT", "cert.png", "hash2", raw_text="Income certificate details")
        assert detect_document_independence(d1, d2) == SourceIndependence.INDEPENDENT


class TestCrossDocumentVerificationPolicy:
    @pytest.fixture
    def target_entity(self):
        return EntityIdentity(
            entity_id="ENT_01",
            canonical_name="Rohit Verma",
            father_or_guardian_name="Suresh Verma",
            date_of_birth="05/09/2004",
            tax_id="ABCDE1234F",
        )

    def test_exact_agreement_verified(self, target_entity):
        docs = {
            "DOC_01": DocumentIdentity("DOC_01", "SALARY_SLIP", "slip.png", "h1"),
            "DOC_02": DocumentIdentity("DOC_02", "BANK_STATEMENT", "bank.png", "h2"),
        }
        claims = [
            FieldClaim("C1", "DOC_01", "net_salary", "amount", "55,000.00", "55000", 95.0, entity_hints={"name": "Rohit Verma", "tax_id": "ABCDE1234F"}),
            FieldClaim("C2", "DOC_02", "net_salary", "amount", "INR 55000", "55000", 92.0, entity_hints={"name": "Rohit Verma", "tax_id": "ABCDE1234F"}),
        ]
        res = verify_cross_document_packet_claim("net_salary", target_entity, claims, docs)
        assert res.outcome == VerificationOutcome.VERIFIED
        assert res.is_verified is True
        assert res.verified_value == "55000.00"
        assert len(res.supporting_doc_ids) == 2

    def test_numeric_contradiction_detected(self, target_entity):
        docs = {
            "DOC_01": DocumentIdentity("DOC_01", "SALARY_SLIP", "slip.png", "h1"),
            "DOC_02": DocumentIdentity("DOC_02", "TAX_RETURN", "itr.png", "h2"),
        }
        claims = [
            FieldClaim("C1", "DOC_01", "annual_income", "amount", "600000", "600000", 94.0, entity_hints={"name": "Rohit Verma"}),
            FieldClaim("C2", "DOC_02", "annual_income", "amount", "750000", "750000", 91.0, entity_hints={"name": "Rohit Verma"}),
        ]
        res = verify_cross_document_packet_claim("annual_income", target_entity, claims, docs)
        assert res.outcome == VerificationOutcome.CONTRADICTION
        assert res.is_verified is False
        assert "factual contradiction detected" in res.reason

    def test_date_contradiction_detected(self, target_entity):
        docs = {
            "DOC_01": DocumentIdentity("DOC_01", "INVOICE", "inv.png", "h1"),
            "DOC_02": DocumentIdentity("DOC_02", "RECEIPT", "rcpt.png", "h2"),
        }
        claims = [
            FieldClaim("C1", "DOC_01", "transaction_date", "date", "10/10/2026", "10/10/2026", 90.0, entity_hints={"name": "Rohit Verma"}),
            FieldClaim("C2", "DOC_02", "transaction_date", "date", "15/10/2026", "15/10/2026", 88.0, entity_hints={"name": "Rohit Verma"}),
        ]
        res = verify_cross_document_packet_claim("transaction_date", target_entity, claims, docs)
        assert res.outcome == VerificationOutcome.CONTRADICTION
        assert res.is_verified is False

    def test_missing_mandatory_attachment_abstained(self, target_entity):
        docs = {
            "DOC_01": DocumentIdentity("DOC_01", "APPLICATION_FORM", "app.png", "h1"),
            # Missing mandatory INCOME_CERTIFICATE
        }
        claims = [
            FieldClaim("C1", "DOC_01", "family_income", "amount", "220000", "220000", 95.0, entity_hints={"name": "Rohit Verma"}),
        ]
        res = verify_cross_document_packet_claim(
            "family_income", target_entity, claims, docs, required_doc_types=["APPLICATION_FORM", "INCOME_CERT"]
        )
        assert res.outcome == VerificationOutcome.MISSING_EVIDENCE
        assert res.is_verified is False
        assert "Mandatory supporting document type(s) missing" in res.reason

    def test_unrelated_entity_with_same_amount_not_confused(self, target_entity):
        """Rule: A different person with the same amount must be rejected as an entity mismatch."""
        docs = {
            "DOC_01": DocumentIdentity("DOC_01", "APPLICATION", "app.png", "h1"),
            "DOC_02": DocumentIdentity("DOC_02", "OTHER_APPLICATION", "other.png", "h2"),
        }
        claims = [
            FieldClaim("C1", "DOC_01", "fee_paid", "amount", "5000", "5000", 90.0, entity_hints={"name": "Rohit Verma"}),
            # Document 2 is for an unrelated person Suresh Mohanty who also paid 5000
            FieldClaim("C2", "DOC_02", "fee_paid", "amount", "5000", "5000", 90.0, entity_hints={"name": "Suresh Mohanty"}),
        ]
        res = verify_cross_document_packet_claim("fee_paid", target_entity, claims, docs)
        # Should verify solely based on Rohit Verma's document, without claiming Suresh Mohanty's doc as corroboration
        assert res.outcome == VerificationOutcome.VERIFIED
        assert res.supporting_doc_ids == ["DOC_01"]
        assert "DOC_02" not in res.supporting_doc_ids
