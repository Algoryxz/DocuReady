"""
Unit tests for Loop 3 Decision Safety Layer
Verifies the non-rejection axioms, statutory reference verification, dual-source contradiction guarantees,
and evidence state safety intercepts.
"""

import pytest
from docuready.domain.enums import Status
from docuready.domain.models import (
    DocumentType, ExtractedDocument, ExtractedField, EvidenceProvenance,
    Finding, FindingStatus, Severity, EvidenceState
)
from docuready.outcome.safety_layer import DecisionSafetyLayer


@pytest.fixture
def safety_layer():
    return DecisionSafetyLayer(strict_mode=True)


def test_safety_layer_pass_through_of_pass_and_review(safety_layer):
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
    doc_app = ExtractedDocument(
        doc_type=DocumentType.APPLICATION_FORM,
        file_path="app.pdf",
        status="VALID",
        fields={
            "applicant_name": ExtractedField(
                field_name="applicant_name",
                raw_value="SMRUTI RANJAN NAYAK",
                evidence_state=EvidenceState.VERIFIED_TEXT,
                calibrated_confidence=0.98,
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
                calibrated_confidence=0.98,
                is_uncertain=False,
                provenance=ev_inc
            )
        }
    )
    docs = {DocumentType.APPLICATION_FORM: doc_app, DocumentType.INCOME_CERT: doc_inc}

    pass_finding = Finding(
        rule_id="RULE-NAME-PASS",
        rule_name="Applicant Name Consistency",
        status=FindingStatus.PASS,
        severity=Severity.INFO,
        penalty=0,
        field="APPLICANT_NAME",
        documents_involved=[DocumentType.APPLICATION_FORM.value, DocumentType.INCOME_CERT.value],
        message="Names match.",
        evidence=[ev_app, ev_inc],
        remediation="None",
        statutory_reference="MoSJE Guidelines Clause 5"
    )
    res = safety_layer.audit_findings([pass_finding], docs, "Test Scheme")
    assert len(res) == 1
    assert res[0].status == FindingStatus.PASS
    assert res[0].rule_id == "RULE-NAME-PASS"

    review_finding = Finding(
        rule_id="RULE-NAME-02",
        rule_name="Applicant Name Variation",
        status=FindingStatus.REVIEW,
        severity=Severity.REVIEW,
        penalty=10,
        field="APPLICANT_NAME_VARIATION",
        documents_involved=[DocumentType.APPLICATION_FORM.value, DocumentType.INCOME_CERT.value],
        message="Minor name variation.",
        evidence=[ev_app, ev_inc],
        remediation="Verify manually.",
        statutory_reference="UIDAI Guidelines"
    )
    res_rev = safety_layer.audit_findings([review_finding], docs, "Test Scheme")
    assert len(res_rev) == 1
    assert res_rev[0].status == FindingStatus.REVIEW


def test_safety_firewall_unverified_statutory_reference(safety_layer):
    """Findings without verified legal citation cannot trigger statutory FAIL."""
    unverified_fail = Finding(
        rule_id="RULE-UNOFFICIAL-01",
        rule_name="Unofficial Cutoff Check",
        status=FindingStatus.FAIL,
        severity=Severity.CRITICAL,
        penalty=25,
        field="MERIT_PERCENTAGE",
        documents_involved=[DocumentType.MARKSHEET.value],
        message="Fails unofficial quota requirement.",
        evidence=[],
        remediation="Contact college.",
        statutory_reference=""  # Missing statutory reference
    )

    doc_mark = ExtractedDocument(
        doc_type=DocumentType.MARKSHEET,
        file_path="mark.pdf",
        fields={"percentage": ExtractedField(field_name="percentage", raw_value="45%")}
    )

    res = safety_layer.audit_findings([unverified_fail], {DocumentType.MARKSHEET: doc_mark}, "Test Scheme")
    assert len(res) == 1
    assert res[0].status == FindingStatus.REVIEW
    assert "SAFETY INTERCEPT" in res[0].message
    assert "lacks verified primary legal citation" in res[0].message


def test_safety_firewall_dual_source_provenance_guarantee(safety_layer):
    """Cross-document contradiction claims require evidence from >= 2 distinct documents."""
    single_source_fail = Finding(
        rule_id="RULE-NAME-01",
        rule_name="Applicant Name Inconsistency",
        status=FindingStatus.FAIL,
        severity=Severity.CRITICAL,
        penalty=25,
        field="APPLICANT_NAME",
        documents_involved=[DocumentType.APPLICATION_FORM.value, DocumentType.BANK_PASSBOOK.value],
        message="Name mismatch alleged.",
        evidence=[
            EvidenceProvenance(document_type="APPLICATION_FORM", file_name="app.pdf", raw_snippet="Smruti Nayak")
            # Bank passbook evidence is missing!
        ],
        remediation="Upload matching docs.",
        statutory_reference="MoSJE Guidelines Clause 5"
    )

    res = safety_layer.audit_findings([single_source_fail], {}, "Test Scheme")
    assert len(res) == 1
    assert res[0].status == Status.REVIEW
    assert "Cannot establish contradiction without dual-document evidence" in res[0].message


def test_safety_firewall_ocr_low_confidence_downgrades_to_review(safety_layer):
    """Statutory FAIL on low confidence field must downgrade to REVIEW."""
    fail_finding = Finding(
        rule_id="RULE-INC-01",
        rule_name="Income Ceiling Compliance",
        status=FindingStatus.FAIL,
        severity=Severity.CRITICAL,
        penalty=35,
        field="INCOME_CEILING",
        documents_involved=[DocumentType.INCOME_CERT.value],
        message="Income ₹2,80,000 exceeds ₹2,50,000 ceiling.",
        evidence=[
            EvidenceProvenance(document_type="INCOME_CERT", file_name="inc.pdf", extracted_field="annual_income", raw_snippet="Rs 2,80,000")
        ],
        remediation="Submit fresh cert.",
        statutory_reference="Odisha Misc Cert Rules 2019"
    )

    doc_inc = ExtractedDocument(
        doc_type=DocumentType.INCOME_CERT,
        file_path="inc.pdf",
        fields={
            "annual_income": ExtractedField(
                field_name="annual_income",
                raw_value="Rs 2,80,000",
                evidence_state=EvidenceState.LOW_CONFIDENCE,
                calibrated_confidence=0.48,
                is_uncertain=True
            )
        }
    )

    res = safety_layer.audit_findings([fail_finding], {DocumentType.INCOME_CERT: doc_inc}, "Test Scheme")
    assert len(res) == 1
    assert res[0].status == FindingStatus.REVIEW
    assert "SAFETY INTERCEPT" in res[0].message
    assert "LOW_CONFIDENCE" in res[0].message
    assert res[0].penalty <= 10


def test_safety_firewall_unrelated_field_uncertainty_does_not_downgrade(safety_layer):
    """An uncertain issue_date in income cert must not downgrade a verified annual_income FAIL."""
    fail_income = Finding(
        rule_id="RULE-INC-01",
        rule_name="Income Ceiling Compliance",
        status=FindingStatus.FAIL,
        severity=Severity.CRITICAL,
        penalty=35,
        field="INCOME_CEILING",
        documents_involved=[DocumentType.INCOME_CERT.value],
        message="Income ₹3,20,000 exceeds ₹2,50,000 ceiling.",
        evidence=[
            EvidenceProvenance(document_type="INCOME_CERT", file_name="inc.pdf", extracted_field="annual_income", raw_snippet="Rs 3,20,000")
        ],
        remediation="Submit fresh cert.",
        statutory_reference="Odisha Misc Cert Rules 2019"
    )

    doc_inc = ExtractedDocument(
        doc_type=DocumentType.INCOME_CERT,
        file_path="inc.pdf",
        fields={
            "annual_income": ExtractedField(
                field_name="annual_income",
                raw_value="Rs 3,20,000",
                evidence_state=EvidenceState.VERIFIED_TEXT,
                calibrated_confidence=0.98,
                is_uncertain=False
            ),
            "issue_date": ExtractedField(
                field_name="issue_date",
                raw_value="10/01/2025",
                evidence_state=EvidenceState.AMBIGUOUS,
                calibrated_confidence=0.98,
                is_uncertain=True
            )
        }
    )

    res = safety_layer.audit_findings([fail_income], {DocumentType.INCOME_CERT: doc_inc}, "Test Scheme")
    assert len(res) == 1
    # Because annual_income is VERIFIED_TEXT, FAIL must NOT be downgraded!
    assert res[0].status == FindingStatus.FAIL
    assert res[0].rule_id == "RULE-INC-01"
