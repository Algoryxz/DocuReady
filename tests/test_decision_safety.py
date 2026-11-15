"""
Decision Safety & Evidence Sufficiency Test Suite (Track B)
Adversarial test coverage verifying that:
1. No unsupported PASS can pass through the safety firewall (no provenance, single source, low confidence, ambiguous, unreadable/not found).
2. Legitimate evidence-backed PASS is preserved without regression.
3. No unsupported FAIL can trigger illegal rejection (single source, low confidence, ambiguous, unreadable).
4. Truly absent mandatory documents under active schemes correctly fail statutory validation.
5. AuditResult readiness scores and summary counts accurately reflect safety-downgraded findings.
"""

import pytest
from datetime import date
from docuready.domain.models import (
    DocumentType, ExtractedDocument, ExtractedField, EvidenceProvenance,
    Finding, FindingStatus, Severity, EvidenceState, ExtractionMethod
)
from docuready.outcome.safety_layer import DecisionSafetyLayer
from docuready.rules.validator import DocuReadyValidator, SchemeConfig


@pytest.fixture
def safety_layer():
    return DecisionSafetyLayer(strict_mode=True)


# ----------------- 1. A PASS finding with no provenance -----------------
def test_pass_with_no_provenance_downgrades_to_unknown(safety_layer):
    """A PASS finding with empty evidence must be intercepted and downgraded to UNKNOWN."""
    finding = Finding(
        rule_id="RULE-NAME-PASS",
        rule_name="Cross-Document Applicant Name Consistency",
        status=FindingStatus.PASS,
        severity=Severity.INFO,
        penalty=0,
        field="APPLICANT_NAME",
        documents_involved=[DocumentType.APPLICATION_FORM.value, DocumentType.INCOME_CERT.value],
        message="Names match across documents.",
        evidence=[],  # No provenance!
        remediation="No action required.",
        statutory_reference="MeitY Standards 2023"
    )

    doc_app = ExtractedDocument(
        doc_type=DocumentType.APPLICATION_FORM,
        file_path="app.pdf",
        status="VALID",
        fields={"applicant_name": ExtractedField(field_name="applicant_name", raw_value="SMRUTI NAYAK")}
    )
    docs = {DocumentType.APPLICATION_FORM: doc_app}

    res = safety_layer.audit_findings([finding], docs, "Test Scheme")
    assert len(res) == 1
    assert res[0].status == FindingStatus.REVIEW
    assert res[0].penalty > 0
    assert "lacks supporting evidence provenance" in res[0].message


# ----------------- 2. A cross-document PASS supported by only one source document -----------------
def test_cross_doc_pass_single_source_downgrades_to_unknown(safety_layer):
    """A cross-document comparison PASS supported by only 1 source document cannot establish consistency."""
    ev_app = EvidenceProvenance(
        document_type=DocumentType.APPLICATION_FORM.value,
        file_name="app.pdf",
        extracted_field="applicant_name",
        raw_snippet="SMRUTI NAYAK"
    )
    finding = Finding(
        rule_id="RULE-NAME-PASS",
        rule_name="Cross-Document Applicant Name Consistency",
        status=FindingStatus.PASS,
        severity=Severity.INFO,
        penalty=0,
        field="APPLICANT_NAME",
        documents_involved=[DocumentType.APPLICATION_FORM.value, DocumentType.INCOME_CERT.value],
        message="Names match.",
        evidence=[ev_app],  # Only ONE document in evidence!
        remediation="None",
        statutory_reference="MeitY Standards 2023"
    )

    doc_app = ExtractedDocument(
        doc_type=DocumentType.APPLICATION_FORM,
        file_path="app.pdf",
        status="VALID",
        fields={"applicant_name": ExtractedField(field_name="applicant_name", raw_value="SMRUTI NAYAK", provenance=ev_app)}
    )
    docs = {DocumentType.APPLICATION_FORM: doc_app}

    res = safety_layer.audit_findings([finding], docs, "Test Scheme")
    assert len(res) == 1
    assert res[0].status == FindingStatus.REVIEW
    assert res[0].rule_id == "RULE-NAME-PASS-SINGLE-SOURCE"
    assert "Cannot establish cross-document consistency without dual-document evidence" in res[0].message


# ----------------- 3. A PASS relying on a LOW_CONFIDENCE field -----------------
def test_pass_relying_on_low_confidence_field_downgrades_to_review(safety_layer):
    """A PASS finding substantiated by a field with low OCR confidence must downgrade to REVIEW."""
    ev_inc = EvidenceProvenance(
        document_type=DocumentType.INCOME_CERT.value,
        file_name="inc.pdf",
        extracted_field="annual_income",
        raw_snippet="Rs 1,50,000",
        ocr_confidence=0.45
    )
    finding = Finding(
        rule_id="RULE-INC-CEIL-PASS",
        rule_name="Statutory Income Ceiling Compliance",
        status=FindingStatus.PASS,
        severity=Severity.INFO,
        penalty=0,
        field="INCOME_CEILING",
        documents_involved=[DocumentType.INCOME_CERT.value],
        message="Certified income is within statutory ceiling.",
        evidence=[ev_inc],
        remediation="No action required.",
        statutory_reference="Post-Matric Guidelines Clause 5.2"
    )

    doc_inc = ExtractedDocument(
        doc_type=DocumentType.INCOME_CERT,
        file_path="inc.pdf",
        status="VALID",
        fields={
            "annual_income": ExtractedField(
                field_name="annual_income",
                raw_value="Rs 1,50,000",
                normalized_value=150000.0,
                evidence_state=EvidenceState.LOW_CONFIDENCE,
                calibrated_confidence=0.45,
                is_uncertain=True,
                uncertainty_reason="Low OCR confidence (45.0%)",
                provenance=ev_inc
            )
        }
    )
    docs = {DocumentType.INCOME_CERT: doc_inc}

    res = safety_layer.audit_findings([finding], docs, "Test Scheme")
    assert len(res) == 1
    assert res[0].status == FindingStatus.REVIEW
    assert "low confidence" in res[0].message.lower()
    assert res[0].penalty == 10


# ----------------- 4. A PASS relying on an AMBIGUOUS field -----------------
def test_pass_relying_on_ambiguous_field_downgrades_to_review(safety_layer):
    """A PASS finding relying on an ambiguous date of birth must downgrade to REVIEW."""
    ev_app = EvidenceProvenance(
        document_type=DocumentType.APPLICATION_FORM.value,
        file_name="app.pdf",
        extracted_field="dob",
        raw_snippet="05/06/2003"
    )
    ev_mark = EvidenceProvenance(
        document_type=DocumentType.MARKSHEET.value,
        file_name="mark.pdf",
        extracted_field="dob",
        raw_snippet="05/06/2003"
    )
    finding = Finding(
        rule_id="RULE-DOB-PASS",
        rule_name="Date of Birth Consistency",
        status=FindingStatus.PASS,
        severity=Severity.INFO,
        penalty=0,
        field="DATE_OF_BIRTH",
        documents_involved=[DocumentType.APPLICATION_FORM.value, DocumentType.MARKSHEET.value],
        message="DOB matches.",
        evidence=[ev_app, ev_mark],
        remediation="None",
        statutory_reference="HSC Board Verification Guidelines"
    )

    doc_app = ExtractedDocument(
        doc_type=DocumentType.APPLICATION_FORM,
        file_path="app.pdf",
        status="VALID",
        fields={
            "dob": ExtractedField(
                field_name="dob",
                raw_value="05/06/2003",
                evidence_state=EvidenceState.AMBIGUOUS,
                calibrated_confidence=0.95,
                is_uncertain=True,
                uncertainty_reason="Date format ambiguity (DD/MM vs MM/DD)",
                provenance=ev_app
            )
        }
    )
    doc_mark = ExtractedDocument(
        doc_type=DocumentType.MARKSHEET,
        file_path="mark.pdf",
        status="VALID",
        fields={
            "dob": ExtractedField(
                field_name="dob",
                raw_value="05/06/2003",
                evidence_state=EvidenceState.VERIFIED_TEXT,
                calibrated_confidence=0.98,
                is_uncertain=False,
                provenance=ev_mark
            )
        }
    )
    docs = {DocumentType.APPLICATION_FORM: doc_app, DocumentType.MARKSHEET: doc_mark}

    res = safety_layer.audit_findings([finding], docs, "Test Scheme")
    assert len(res) == 1
    assert res[0].status == FindingStatus.REVIEW
    assert "ambiguous" in res[0].message.lower()


# ----------------- 5. A PASS relying on an UNREADABLE or NOT_FOUND field -----------------
def test_pass_relying_on_unreadable_or_missing_field_downgrades_to_unknown(safety_layer):
    """A PASS finding where a required supporting field is UNREADABLE or NOT_FOUND must downgrade to UNKNOWN."""
    ev_dom = EvidenceProvenance(
        document_type=DocumentType.RESIDENCE_CERT.value,
        file_name="res.pdf",
        extracted_field="state",
        raw_snippet="[UNREADABLE]"
    )
    finding = Finding(
        rule_id="RULE-DOM-PASS",
        rule_name="State Domicile Requirement",
        status=FindingStatus.PASS,
        severity=Severity.INFO,
        penalty=0,
        field="DOMICILE_STATE",
        documents_involved=[DocumentType.RESIDENCE_CERT.value],
        message="State matches requirement.",
        evidence=[ev_dom],
        remediation="None",
        statutory_reference="State Scholarship Rules Clause 2(a)"
    )

    doc_res = ExtractedDocument(
        doc_type=DocumentType.RESIDENCE_CERT,
        file_path="res.pdf",
        status="VALID",
        fields={
            "state": ExtractedField(
                field_name="state",
                raw_value="",
                evidence_state=EvidenceState.UNREADABLE,
                calibrated_confidence=0.0,
                is_uncertain=True,
                provenance=ev_dom
            )
        }
    )
    docs = {DocumentType.RESIDENCE_CERT: doc_res}

    res = safety_layer.audit_findings([finding], docs, "Test Scheme")
    assert len(res) == 1
    assert res[0].status == FindingStatus.REVIEW
    assert "unreadable" in res[0].message.lower() or "missing" in res[0].message.lower()


# ----------------- 6. A valid PASS supported by sufficient evidence -----------------
def test_valid_pass_supported_by_sufficient_evidence_preserved(safety_layer):
    """A valid PASS finding supported by dual-document verified evidence is preserved with zero penalty."""
    ev_app = EvidenceProvenance(
        document_type=DocumentType.APPLICATION_FORM.value,
        file_name="app.pdf",
        extracted_field="applicant_name",
        raw_snippet="SMRUTI RANJAN NAYAK"
    )
    ev_inc = EvidenceProvenance(
        document_type=DocumentType.INCOME_CERT.value,
        file_name="inc.pdf",
        extracted_field="applicant_name",
        raw_snippet="SMRUTI RANJAN NAYAK"
    )
    finding = Finding(
        rule_id="RULE-NAME-PASS",
        rule_name="Cross-Document Applicant Name Consistency",
        status=FindingStatus.PASS,
        severity=Severity.INFO,
        penalty=0,
        field="APPLICANT_NAME",
        documents_involved=[DocumentType.APPLICATION_FORM.value, DocumentType.INCOME_CERT.value],
        message="Applicant name matches consistently across all verified documents.",
        evidence=[ev_app, ev_inc],
        remediation="No action required.",
        statutory_reference="MeitY Demographic Verification Standards 2023"
    )

    doc_app = ExtractedDocument(
        doc_type=DocumentType.APPLICATION_FORM,
        file_path="app.pdf",
        status="VALID",
        fields={
            "applicant_name": ExtractedField(
                field_name="applicant_name",
                raw_value="SMRUTI RANJAN NAYAK",
                evidence_state=EvidenceState.VERIFIED_TEXT,
                calibrated_confidence=0.99,
                is_uncertain=False,
                provenance=ev_app
            )
        }
    )
    doc_inc = ExtractedDocument(
        doc_type=DocumentType.INCOME_CERT,
        file_path="inc.pdf",
        status="VALID",
        fields={
            "applicant_name": ExtractedField(
                field_name="applicant_name",
                raw_value="SMRUTI RANJAN NAYAK",
                evidence_state=EvidenceState.VERIFIED_TEXT,
                calibrated_confidence=0.99,
                is_uncertain=False,
                provenance=ev_inc
            )
        }
    )
    docs = {DocumentType.APPLICATION_FORM: doc_app, DocumentType.INCOME_CERT: doc_inc}

    res = safety_layer.audit_findings([finding], docs, "Test Scheme")
    assert len(res) == 1
    assert res[0].status == FindingStatus.PASS
    assert res[0].penalty == 0
    assert res[0].rule_id == "RULE-NAME-PASS"


# ----------------- 7. A cross-document FAIL with only one supporting document -----------------
def test_cross_doc_fail_single_source_downgrades_to_unknown(safety_layer):
    """A cross-document contradiction FAIL with only 1 source document must downgrade to UNKNOWN."""
    ev_app = EvidenceProvenance(
        document_type=DocumentType.APPLICATION_FORM.value,
        file_name="app.pdf",
        extracted_field="dob",
        raw_snippet="14/05/2003"
    )
    finding = Finding(
        rule_id="RULE-DOB-01",
        rule_name="Cross-Document Date of Birth Consistency",
        status=FindingStatus.FAIL,
        severity=Severity.CRITICAL,
        penalty=25,
        field="DATE_OF_BIRTH",
        documents_involved=[DocumentType.APPLICATION_FORM.value, DocumentType.MARKSHEET.value],
        message="Date of birth contradiction alleged.",
        evidence=[ev_app],  # Only 1 document provided!
        remediation="Verify documents.",
        statutory_reference="UIDAI Regulation Clause 7"
    )
    doc_app = ExtractedDocument(
        doc_type=DocumentType.APPLICATION_FORM,
        file_path="app.pdf",
        status="VALID",
        fields={"dob": ExtractedField(field_name="dob", raw_value="14/05/2003", provenance=ev_app)}
    )
    docs = {DocumentType.APPLICATION_FORM: doc_app}

    res = safety_layer.audit_findings([finding], docs, "Test Scheme")
    assert len(res) == 1
    assert res[0].status == FindingStatus.REVIEW
    assert res[0].rule_id == "RULE-DOB-01-SINGLE-SOURCE"
    assert "Cannot establish contradiction without dual-document evidence" in res[0].message


# ----------------- 8. A FAIL based on unreadable or ambiguous evidence -----------------
def test_fail_based_on_unreadable_or_ambiguous_evidence_downgrades_to_review(safety_layer):
    """A statutory FAIL based on an unreadable or low-confidence field must downgrade to REVIEW."""
    ev_inc = EvidenceProvenance(
        document_type=DocumentType.INCOME_CERT.value,
        file_name="inc.pdf",
        extracted_field="annual_income",
        raw_snippet="Rs 3,00,000"
    )
    finding = Finding(
        rule_id="RULE-INC-01",
        rule_name="Statutory Income Ceiling Compliance",
        status=FindingStatus.FAIL,
        severity=Severity.FATAL,
        penalty=35,
        field="INCOME_CEILING",
        documents_involved=[DocumentType.INCOME_CERT.value],
        message="Income ₹3,00,000 exceeds ceiling ₹2,50,000.",
        evidence=[ev_inc],
        remediation="Submit fresh cert.",
        statutory_reference="Post-Matric Scholarship Scheme Guidelines Clause 5.2"
    )
    doc_inc = ExtractedDocument(
        doc_type=DocumentType.INCOME_CERT,
        file_path="inc.pdf",
        status="VALID",
        fields={
            "annual_income": ExtractedField(
                field_name="annual_income",
                raw_value="Rs 3,00,000",
                evidence_state=EvidenceState.LOW_CONFIDENCE,
                calibrated_confidence=0.48,
                is_uncertain=True,
                provenance=ev_inc
            )
        }
    )
    docs = {DocumentType.INCOME_CERT: doc_inc}

    res = safety_layer.audit_findings([finding], docs, "Test Scheme")
    assert len(res) == 1
    assert res[0].status == FindingStatus.REVIEW
    assert "Direct applicant rejection is legally impermissible on unconfirmed evidence" in res[0].message
    assert res[0].penalty <= 10


# ----------------- 9. A genuinely absent mandatory document under an explicitly configured rule -----------------
def test_genuinely_absent_mandatory_document_fails_cleanly():
    """A missing mandatory document under an active scheme produces FAIL without improper downgrade."""
    scheme = SchemeConfig(
        name="Test Mandatory Scheme",
        mandatory_documents=[DocumentType.CASTE_CERT, DocumentType.APPLICATION_FORM]
    )
    validator = DocuReadyValidator(scheme_config=scheme)

    # Packet has APPLICATION_FORM, but genuinely lacks CASTE_CERT
    ev_app = EvidenceProvenance(document_type="APPLICATION_FORM", file_name="app.pdf", raw_snippet="SMRUTI")
    doc_app = ExtractedDocument(
        doc_type=DocumentType.APPLICATION_FORM,
        file_path="app.pdf",
        status="VALID",
        fields={
            "applicant_name": ExtractedField(field_name="applicant_name", raw_value="SMRUTI", evidence_state=EvidenceState.VERIFIED_TEXT, provenance=ev_app),
            "annual_income": ExtractedField(field_name="annual_income", raw_value="150000", normalized_value=150000.0, evidence_state=EvidenceState.VERIFIED_TEXT),
            "caste_category": ExtractedField(field_name="caste_category", raw_value="SC", evidence_state=EvidenceState.VERIFIED_TEXT)
        }
    )
    docs = {DocumentType.APPLICATION_FORM: doc_app}

    audit_res = validator.validate_packet("TEST_MISSING_MANDATORY", docs)

    # CASTE_CERT is explicitly mandatory, so RULE-DOC-01 MUST remain FAIL
    missing_doc_findings = [f for f in audit_res.findings if f.rule_id == "RULE-DOC-01"]
    assert len(missing_doc_findings) == 1
    assert missing_doc_findings[0].status == FindingStatus.FAIL
    assert missing_doc_findings[0].severity == Severity.FATAL
    assert "CASTE_CERT" in missing_doc_findings[0].documents_involved
    assert audit_res.summary_counts["FAIL"] >= 1
    assert audit_res.readiness.value == "NOT_READY"


# ----------------- 10. Correct summary counts and readiness score after a safety downgrade -----------------
def test_summary_counts_and_score_reflect_safety_downgrade():
    """When a raw finding is downgraded by the safety layer, AuditResult score and counts must update."""
    scheme = SchemeConfig(
        name="Test Score Scheme",
        mandatory_documents=[DocumentType.INCOME_CERT]
    )
    validator = DocuReadyValidator(scheme_config=scheme)

    # Income certificate with low OCR confidence annual_income that would have triggered raw FAIL
    ev_inc = EvidenceProvenance(
        document_type="INCOME_CERT",
        file_name="inc.pdf",
        extracted_field="annual_income",
        raw_snippet="Rs 3,50,000",
        ocr_confidence=0.42
    )
    doc_inc = ExtractedDocument(
        doc_type=DocumentType.INCOME_CERT,
        file_path="inc.pdf",
        status="VALID",
        fields={
            "applicant_name": ExtractedField(field_name="applicant_name", raw_value="SMRUTI NAYAK", evidence_state=EvidenceState.VERIFIED_TEXT),
            "annual_income": ExtractedField(
                field_name="annual_income",
                raw_value="Rs 3,50,000",
                normalized_value=350000.0,
                evidence_state=EvidenceState.LOW_CONFIDENCE,
                calibrated_confidence=0.42,
                is_uncertain=True,
                provenance=ev_inc
            ),
            "issue_date": ExtractedField(field_name="issue_date", raw_value="10/01/2025", normalized_value="2025-01-10", evidence_state=EvidenceState.VERIFIED_TEXT),
            "certificate_no": ExtractedField(field_name="certificate_no", raw_value="E-INC/2025/1", evidence_state=EvidenceState.VERIFIED_TEXT)
        }
    )
    docs = {DocumentType.INCOME_CERT: doc_inc}

    audit_res = validator.validate_packet("TEST_SCORE_DOWNGRADE", docs)

    # Raw income ceiling FAIL (penalty 35) must be downgraded to REVIEW (penalty 10)
    inc_findings = [f for f in audit_res.findings if "INCOME_CEILING" in f.field]
    assert len(inc_findings) == 1
    assert inc_findings[0].status == FindingStatus.REVIEW
    assert inc_findings[0].penalty == 10

    # Summary counts must correctly record 0 FAIL and at least 1 REVIEW
    assert audit_res.summary_counts["FAIL"] == 0
    assert audit_res.summary_counts["REVIEW"] >= 1

    # Readiness score must reflect the downgraded penalty (score should be 100 - penalties)
    total_penalty = sum(f.penalty for f in audit_res.findings)
    assert audit_res.readiness_score == max(0, 100 - total_penalty)
    assert audit_res.readiness_score == 90  # 100 - 10 (only the REVIEW penalty)
