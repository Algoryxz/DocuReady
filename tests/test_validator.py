"""
Unit tests for deterministic validation rules and finding status categorization.
"""

from docuready.domain.models import (
    DocumentType, ExtractedDocument, ExtractedField, FindingStatus, Severity
)
from docuready.rules.validator import DocuReadyValidator, SchemeConfig


def test_validator_mandatory_document_missing():
    validator = DocuReadyValidator()
    # Packet with no documents
    res = validator.validate_packet("TEST_EMPTY", {})
    assert res.readiness.value == "NOT_READY"
    missing_findings = [f for f in res.findings if f.rule_id == "RULE-DOC-01"]
    assert len(missing_findings) == 6
    assert all(f.status == FindingStatus.FAIL for f in missing_findings)
    assert all(f.severity == Severity.FATAL for f in missing_findings)


def test_validator_income_ceiling_breach():
    validator = DocuReadyValidator(SchemeConfig(income_ceiling=250000.0))
    doc_inc = ExtractedDocument(
        doc_type=DocumentType.INCOME_CERT,
        file_path="dummy.pdf",
        status="VALID",
        fields={
            "applicant_name": ExtractedField(field_name="applicant_name", raw_value="Smruti Nayak", normalized_value="SMRUTI NAYAK"),
            "annual_income": ExtractedField(field_name="annual_income", raw_value="350000", normalized_value=350000.0),
            "issue_date": ExtractedField(field_name="issue_date", raw_value="10/01/2025", normalized_value="2025-01-10"),
            "certificate_no": ExtractedField(field_name="certificate_no", raw_value="E-INC/123", normalized_value="EINC123"),
            "state": ExtractedField(field_name="state", raw_value="ODISHA", normalized_value="ODISHA")
        }
    )
    res = validator.validate_packet("TEST_CEILING", {DocumentType.INCOME_CERT: doc_inc})
    ceiling_findings = [f for f in res.findings if f.rule_id == "RULE-INC-01"]
    assert len(ceiling_findings) == 1
    assert ceiling_findings[0].status == FindingStatus.FAIL
    assert ceiling_findings[0].severity == Severity.FATAL
