"""Integration checks for the transitional legacy-to-V2 outcome adapter."""

from docuready.domain.enums import (
    EvidenceState,
    MaxSeverity,
    Raw,
    Readiness,
    ReasonCode,
    Status,
)
from docuready.domain.models import (
    AuditResult,
    DocumentType,
    EvidenceProvenance,
    ExtractedDocument,
    ExtractedField,
    Finding,
    FindingStatus,
    Severity,
)
from docuready.outcome.safety_layer import DecisionSafetyLayer
from docuready.rules.validator import SchemeConfig


def _document(doc_type, evidence_state):
    field = ExtractedField(
        field_name="applicant_name",
        raw_value="SAMPLE APPLICANT",
        evidence_state=evidence_state,
    )
    return ExtractedDocument(
        doc_type=doc_type,
        file_path=f"{doc_type.value.lower()}.pdf",
        fields={"applicant_name": field},
    )


def _cross_document_pass():
    return Finding(
        rule_id="RULE-NAME-PASS",
        rule_name="Cross-document applicant-name consistency",
        status=FindingStatus.PASS,
        severity=Severity.INFO,
        field="APPLICANT_NAME",
        documents_involved=[
            DocumentType.APPLICATION_FORM.value,
            DocumentType.INCOME_CERT.value,
        ],
        message="The extracted names match.",
        evidence=[
            EvidenceProvenance(
                document_type=DocumentType.APPLICATION_FORM.value,
                file_name="application_form.pdf",
                extracted_field="applicant_name",
            ),
            EvidenceProvenance(
                document_type=DocumentType.INCOME_CERT.value,
                file_name="income_cert.pdf",
                extracted_field="applicant_name",
            ),
        ],
        remediation="No action required.",
        statutory_reference="Verified demonstration rule",
    )


def test_verified_cross_document_pass_resolves_to_v2_pass():
    finding = _cross_document_pass()
    documents = {
        DocumentType.APPLICATION_FORM: _document(
            DocumentType.APPLICATION_FORM, EvidenceState.VERIFIED_TEXT
        ),
        DocumentType.INCOME_CERT: _document(
            DocumentType.INCOME_CERT, EvidenceState.VERIFIED_TEXT
        ),
    }

    audited = DecisionSafetyLayer().audit_findings([finding], documents)
    assert audited[0].status is Status.PASS
    assert audited[0].resolved_status is Status.PASS
    assert audited[0].raw_result is Raw.SATISFIED
    assert audited[0].reason_code == ReasonCode.CONFIRMED_OK.value


def test_ocr_supported_pass_is_review_in_v2_even_when_legacy_filter_preserves_it():
    finding = _cross_document_pass()
    documents = {
        DocumentType.APPLICATION_FORM: _document(
            DocumentType.APPLICATION_FORM, EvidenceState.OCR_EXTRACTED
        ),
        DocumentType.INCOME_CERT: _document(
            DocumentType.INCOME_CERT, EvidenceState.OCR_EXTRACTED
        ),
    }

    audited = DecisionSafetyLayer().audit_findings([finding], documents)
    assert audited[0].resolved_status is Status.REVIEW
    assert audited[0].reason_code == ReasonCode.CANNOT_CONFIRM.value


def test_missing_mandatory_document_becomes_missing_not_generic_fail():
    finding = Finding(
        rule_id="RULE-DOC-01",
        rule_name="Mandatory document completeness",
        status=FindingStatus.FAIL,
        severity=Severity.FATAL,
        penalty=35,
        field="MANDATORY_DOCUMENT",
        documents_involved=[DocumentType.INCOME_CERT.value],
        message="Mandatory income certificate is absent.",
        evidence=[],
        remediation="Add the required document.",
        statutory_reference="Verified scheme document checklist",
    )

    audited = DecisionSafetyLayer().audit_findings([finding], {})
    assert audited[0].resolved_status is Status.MISSING
    assert audited[0].reason_code == ReasonCode.DOC_ABSENT.value
    result = AuditResult(
        packet_id="SYNTHETIC_MISSING",
        scheme_name="Test Scheme",
        readiness_score=65,
        overall_status="REJECT_PRECHECK",
        findings=audited,
        summary_counts={"FAIL": 1},
        execution_time_ms=0.0,
        timestamp="2026-11-15T00:00:00",
    )
    assert result.readiness is Readiness.NOT_READY


def test_scheme_config_severity_cap_is_applied_by_safety_layer():
    finding = Finding(
        rule_id="RULE-INC-01",
        rule_name="Income ceiling check",
        status=FindingStatus.FAIL,
        severity=Severity.CRITICAL,
        penalty=25,
        field="INCOME_VALUE",
        documents_involved=[DocumentType.INCOME_CERT.value],
        message="Income is above the configured ceiling.",
        evidence=[
            EvidenceProvenance(
                document_type=DocumentType.INCOME_CERT.value,
                file_name="income_cert.pdf",
                extracted_field="annual_income",
            )
        ],
        remediation="Verify the source value.",
        statutory_reference="Verified scheme income rule",
    )
    document = ExtractedDocument(
        doc_type=DocumentType.INCOME_CERT,
        file_path="income_cert.pdf",
        fields={
            "annual_income": ExtractedField(
                field_name="annual_income",
                raw_value="300000",
                evidence_state=EvidenceState.VERIFIED_TEXT,
            )
        },
    )
    config = SchemeConfig(rule_max_severity={"RULE-INC-01": MaxSeverity.REVIEW})

    audited = DecisionSafetyLayer().audit_findings(
        [finding],
        {DocumentType.INCOME_CERT: document},
        scheme_config=config,
    )
    assert audited[0].resolved_status is Status.REVIEW
    assert audited[0].reason_code == ReasonCode.ADVISORY_RULE_CAP.value


def test_public_projection_uses_v2_readiness_and_status_without_changing_legacy_dump():
    finding = _cross_document_pass()
    finding.set_resolution(Raw.SATISFIED, Status.PASS, ReasonCode.CONFIRMED_OK.value)
    result = AuditResult(
        packet_id="SYNTHETIC_CLEAN",
        scheme_name="Test Scheme",
        readiness_score=100,
        overall_status="READY_TO_SUBMIT",
        findings=[finding],
        summary_counts={"PASS": 1},
        execution_time_ms=0.0,
        timestamp="2026-11-15T00:00:00",
    )

    legacy = result.model_dump(mode="json")
    public = result.to_public_dict()
    assert legacy["overall_status"] == "READY_TO_SUBMIT"
    assert "reason_code" not in legacy["findings"][0]
    assert public["overall_status"] == "NO_ISSUES_FOUND"
    assert public["readiness"] == "NO_ISSUES_FOUND"
    assert public["findings"][0]["status"] == "PASS"
    assert public["findings"][0]["reason_code"] == ReasonCode.CONFIRMED_OK.value
