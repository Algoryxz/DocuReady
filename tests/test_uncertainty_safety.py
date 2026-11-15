"""
Test Suite for Loop 2: Uncertainty Safety and Non-Rejection Guarantees
Verifies that low OCR confidence, ambiguous evidence, and unreadable scans
never convert into automatic statutory rejections (FAIL), and that statutory
relaxation rules (e.g. SC/ST cutoff exemptions) are honored.
"""

import pytest
from docuready.domain.enums import Status, Readiness
from docuready.domain.models import (
    DocumentType, ExtractedDocument, ExtractedField, EvidenceProvenance,
    FindingStatus, Severity, ExtractionMethod
)
from docuready.rules.validator import DocuReadyValidator, SchemeConfig


def test_low_ocr_confidence_downgrades_to_review():
    """Uncertain extraction from low-confidence OCR must produce REVIEW, never FAIL."""
    validator = DocuReadyValidator()

    # Form with high confidence name
    form_f = ExtractedField(
        field_name="applicant_name",
        raw_value="SMRUTI RANJAN NAYAK",
        normalized_value="SMRUTI RANJAN NAYAK",
        confidence=1.0,
        extraction_method=ExtractionMethod.NATIVE_VECTOR.value,
        is_uncertain=False
    )
    doc_form = ExtractedDocument(
        doc_type=DocumentType.APPLICATION_FORM,
        file_path="app.pdf",
        status="VALID",
        fields={"applicant_name": form_f}
    )

    # Scanned certificate where OCR produced completely conflicting text with low confidence
    cert_f = ExtractedField(
        field_name="applicant_name",
        raw_value="RAKESH SHARMA",
        normalized_value="RAKESH SHARMA",
        confidence=0.48,
        extraction_method=ExtractionMethod.LOCAL_OCR.value,
        is_uncertain=True,
        uncertainty_reason="Low OCR confidence (48.0%)",
        provenance=EvidenceProvenance(
            document_type="INCOME_CERT",
            file_name="scanned_cert.pdf",
            extraction_method="LOCAL_OCR",
            ocr_confidence=0.48
        )
    )
    doc_cert = ExtractedDocument(
        doc_type=DocumentType.INCOME_CERT,
        file_path="scanned_cert.pdf",
        status="VALID",
        fields={
            "applicant_name": cert_f,
            "annual_income": ExtractedField(field_name="annual_income", raw_value="1,50,000", normalized_value=150000.0),
            "issue_date": ExtractedField(field_name="issue_date", raw_value="10/01/2025", normalized_value="2025-01-10"),
            "certificate_no": ExtractedField(field_name="certificate_no", raw_value="E-INC/2025/11", normalized_value="EINC/2025/11")
        }
    )

    docs = {
        DocumentType.APPLICATION_FORM: doc_form,
        DocumentType.INCOME_CERT: doc_cert
    }

    res = validator.validate_packet("TEST_UNC_NAME", docs)
    # Check that NO finding with rule_id="RULE-NAME-01" (FAIL) was generated
    fail_name_findings = [f for f in res.findings if f.rule_id == "RULE-NAME-01"]
    assert len(fail_name_findings) == 0, "Uncertain OCR must not trigger confirmed FAIL"

    # Check that REVIEW finding was generated
    unc_findings = [f for f in res.findings if f.rule_id == "RULE-NAME-UNCERTAIN"]
    assert len(unc_findings) == 1
    assert unc_findings[0].status == FindingStatus.REVIEW
    assert "low confidence" in unc_findings[0].message.lower()


def test_date_of_birth_uncertain_ocr_produces_review():
    """DOB discrepancy with low OCR confidence must downgrade to REVIEW."""
    validator = DocuReadyValidator()

    form_dob = ExtractedField(
        field_name="dob",
        raw_value="14/05/2003",
        normalized_value="2003-05-14",
        is_uncertain=False
    )
    mark_dob = ExtractedField(
        field_name="dob",
        raw_value="14/06/2003",
        normalized_value="2003-06-14",
        confidence=0.52,
        is_uncertain=True,
        uncertainty_reason="Low OCR confidence (52.0%)"
    )

    doc_form = ExtractedDocument(
        doc_type=DocumentType.APPLICATION_FORM,
        file_path="app.pdf",
        fields={"applicant_name": ExtractedField(field_name="applicant_name", raw_value="SMRUTI"), "dob": form_dob}
    )
    doc_mark = ExtractedDocument(
        doc_type=DocumentType.MARKSHEET,
        file_path="mark.pdf",
        fields={"applicant_name": ExtractedField(field_name="applicant_name", raw_value="SMRUTI"), "dob": mark_dob, "percentage": ExtractedField(field_name="percentage", raw_value="65%", normalized_value=65.0)}
    )

    docs = {DocumentType.APPLICATION_FORM: doc_form, DocumentType.MARKSHEET: doc_mark}
    res = validator.validate_packet("TEST_UNC_DOB", docs)

    assert not any(f.rule_id == "RULE-DOB-01" for f in res.findings)
    unc_dob = [f for f in res.findings if f.rule_id == "RULE-DOB-UNCERTAIN"]
    assert len(unc_dob) == 1
    assert unc_dob[0].status == FindingStatus.REVIEW


def test_income_ceiling_uncertain_ocr_produces_review():
    """Potential income ceiling breach from low-confidence OCR must produce REVIEW."""
    validator = DocuReadyValidator(SchemeConfig(income_ceiling=250000.0))

    inc_f = ExtractedField(
        field_name="annual_income",
        raw_value="Rs. 2,80,000/-",
        normalized_value=280000.0,
        confidence=0.45,
        is_uncertain=True,
        uncertainty_reason="Low OCR confidence (45.0%)"
    )
    doc_inc = ExtractedDocument(
        doc_type=DocumentType.INCOME_CERT,
        file_path="inc.pdf",
        fields={
            "applicant_name": ExtractedField(field_name="applicant_name", raw_value="SMRUTI"),
            "annual_income": inc_f,
            "issue_date": ExtractedField(field_name="issue_date", raw_value="10/01/2025", normalized_value="2025-01-10"),
            "certificate_no": ExtractedField(field_name="certificate_no", raw_value="E-INC/01", normalized_value="EINC/01")
        }
    )

    docs = {DocumentType.INCOME_CERT: doc_inc}
    res = validator.validate_packet("TEST_UNC_INC", docs)

    assert not any(f.rule_id == "RULE-INC-01" for f in res.findings)
    unc_inc = [f for f in res.findings if f.rule_id == "RULE-INC-CEIL-UNCERTAIN"]
    assert len(unc_inc) == 1
    assert unc_inc[0].status == FindingStatus.REVIEW


def test_sc_st_candidate_exempt_from_academic_cutoff():
    """Under Post-Matric SC/ST Guidelines Clause 4.1, SC/ST candidates are exempt from minimum percentage cutoffs."""
    validator = DocuReadyValidator(SchemeConfig(min_academic_percentage=50.0))

    # Candidate with 42.5% marks (below 50% cutoff) but belonging to Scheduled Caste
    doc_app = ExtractedDocument(
        doc_type=DocumentType.APPLICATION_FORM,
        file_path="app.pdf",
        fields={
            "applicant_name": ExtractedField(field_name="applicant_name", raw_value="SMRUTI"),
            "caste_category": ExtractedField(field_name="caste_category", raw_value="SCHEDULED CASTE (SC)", normalized_value="SCHEDULED CASTE (SC)")
        }
    )
    doc_mark = ExtractedDocument(
        doc_type=DocumentType.MARKSHEET,
        file_path="mark.pdf",
        fields={
            "applicant_name": ExtractedField(field_name="applicant_name", raw_value="SMRUTI"),
            "dob": ExtractedField(field_name="dob", raw_value="14/05/2003", normalized_value="2003-05-14"),
            "percentage": ExtractedField(field_name="percentage", raw_value="42.5%", normalized_value=42.5)
        }
    )

    docs = {DocumentType.APPLICATION_FORM: doc_app, DocumentType.MARKSHEET: doc_mark}
    res = validator.validate_packet("TEST_SC_ST_CUTOFF", docs)

    # Must NOT fail RULE-MRK-01
    assert not any(f.rule_id == "RULE-MRK-01" for f in res.findings), "SC/ST applicant must not fail academic cutoff"
    relax_pass = [f for f in res.findings if f.rule_id == "RULE-MRK-RELAX-PASS"]
    assert len(relax_pass) == 1
    assert relax_pass[0].status == Status.NOT_APPLICABLE
    assert "exempt" in relax_pass[0].message.lower()


def test_unreadable_scan_produces_unknown_not_rejection():
    """Unreadable scan must produce UNKNOWN status rather than statutory ineligibility."""
    validator = DocuReadyValidator()

    doc_unreadable = ExtractedDocument(
        doc_type=DocumentType.INCOME_CERT,
        file_path="smudged.pdf",
        status="UNREADABLE"
    )

    docs = {DocumentType.INCOME_CERT: doc_unreadable}
    res = validator.validate_packet("TEST_UNREADABLE", docs)

    unreadable_findings = [f for f in res.findings if f.rule_id == "RULE-DOC-02"]
    assert len(unreadable_findings) == 1
    assert unreadable_findings[0].status == Status.REVIEW
    assert res.overall_status == Readiness.NOT_READY
