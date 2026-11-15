"""Integration checks for the transitional legacy-to-V2 outcome adapter."""

from docuready.domain.enums import (
    EvidenceState,
    ExtractionMethod,
    MaxSeverity,
    Raw,
    Readiness,
    ReasonCode,
    Status,
    normalize_evidence_state,
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


def _expiration_finding():
    return Finding(
        rule_id="RULE-EXP-PASS",
        rule_name="Income certificate validity",
        status=FindingStatus.PASS,
        severity=Severity.INFO,
        field="VALIDITY_PERIOD",
        documents_involved=[DocumentType.INCOME_CERT.value],
        message="Income certificate is valid.",
        evidence=[
            EvidenceProvenance(
                document_type=DocumentType.INCOME_CERT.value,
                file_name="income_cert.pdf",
                extracted_field="issue_date",
            )
        ],
        remediation="No action required.",
        statutory_reference="Odisha Misc Cert Rules 2019, Rule 8(2)",
    )


def test_native_vector_ambiguous_date_with_safe_year_resolves_to_pass():
    """1. Native vector text may remain VERIFIED when date interpretation is genuinely safe (year >= 2024)."""
    finding = _expiration_finding()
    field = ExtractedField(
        field_name="issue_date",
        raw_value="10/01/2025",
        normalized_value="2025-01-10",
        extraction_method=ExtractionMethod.NATIVE_VECTOR,
        evidence_state=EvidenceState.AMBIGUOUS,
        is_uncertain=True,
        uncertainty_reason="Ambiguous date representation",
    )
    doc = ExtractedDocument(
        doc_type=DocumentType.INCOME_CERT,
        file_path="income_cert.pdf",
        extraction_method=ExtractionMethod.NATIVE_VECTOR,
        fields={"issue_date": field},
    )

    audited = DecisionSafetyLayer().audit_findings([finding], {DocumentType.INCOME_CERT: doc})
    assert audited[0].resolved_status is Status.PASS
    assert audited[0].reason_code == ReasonCode.CONFIRMED_OK.value


def test_ocr_extracted_ambiguous_date_remains_provisional_and_resolves_to_review():
    """2. OCR-extracted ambiguous date remains PROVISIONAL and must never be promoted to VERIFIED."""
    finding = _expiration_finding()
    field = ExtractedField(
        field_name="issue_date",
        raw_value="10/01/2025",
        normalized_value="2025-01-10",
        extraction_method=ExtractionMethod.LOCAL_OCR,
        evidence_state=EvidenceState.AMBIGUOUS,
        is_uncertain=True,
        uncertainty_reason="Ambiguous date representation",
    )
    doc = ExtractedDocument(
        doc_type=DocumentType.INCOME_CERT,
        file_path="income_cert.pdf",
        extraction_method=ExtractionMethod.LOCAL_OCR,
        fields={"issue_date": field},
    )

    safety = DecisionSafetyLayer()
    states = safety._collect_v2_evidence_states(finding, {DocumentType.INCOME_CERT: doc})
    assert states == [EvidenceState.OCR_EXTRACTED]
    assert normalize_evidence_state(states[0]) is EvidenceState.PROVISIONAL

    audited = safety.audit_findings([finding], {DocumentType.INCOME_CERT: doc})
    assert audited[0].resolved_status is Status.REVIEW
    assert audited[0].reason_code in (ReasonCode.CANNOT_CONFIRM.value, ReasonCode.INSUFFICIENT_DATA.value)


def test_satisfied_plus_ocr_evidence_produces_review():
    """3. SATISFIED + PROVISIONAL (OCR evidence) must resolve to REVIEW, never PASS."""
    finding = _expiration_finding()
    field = ExtractedField(
        field_name="issue_date",
        raw_value="2025-01-10",
        normalized_value="2025-01-10",
        extraction_method=ExtractionMethod.LOCAL_OCR,
        evidence_state=EvidenceState.OCR_EXTRACTED,
        is_uncertain=False,
    )
    doc = ExtractedDocument(
        doc_type=DocumentType.INCOME_CERT,
        file_path="income_cert.pdf",
        extraction_method=ExtractionMethod.LOCAL_OCR,
        fields={"issue_date": field},
    )

    audited = DecisionSafetyLayer().audit_findings([finding], {DocumentType.INCOME_CERT: doc})
    assert audited[0].raw_result is Raw.SATISFIED
    assert audited[0].resolved_status is Status.REVIEW
    assert audited[0].reason_code == ReasonCode.CANNOT_CONFIRM.value


def test_violated_plus_ocr_evidence_produces_warn():
    """4. VIOLATED + PROVISIONAL (OCR evidence) must resolve to WARN."""
    finding = Finding(
        rule_id="RULE-EXP-01",
        rule_name="Certificate validity",
        status=FindingStatus.FAIL,
        severity=Severity.CRITICAL,
        penalty=25,
        field="VALIDITY_PERIOD",
        documents_involved=[DocumentType.INCOME_CERT.value],
        message="Income certificate is expired.",
        evidence=[
            EvidenceProvenance(
                document_type=DocumentType.INCOME_CERT.value,
                file_name="income_cert.pdf",
                extracted_field="issue_date",
                extraction_method=ExtractionMethod.LOCAL_OCR,
            )
        ],
        remediation="Obtain a valid certificate.",
        statutory_reference="Odisha Misc Cert Rules 2019",
    )
    field = ExtractedField(
        field_name="issue_date",
        raw_value="2021-01-10",
        normalized_value="2021-01-10",
        extraction_method=ExtractionMethod.LOCAL_OCR,
        evidence_state=EvidenceState.OCR_EXTRACTED,
        is_uncertain=False,
    )
    doc = ExtractedDocument(
        doc_type=DocumentType.INCOME_CERT,
        file_path="income_cert.pdf",
        extraction_method=ExtractionMethod.LOCAL_OCR,
        fields={"issue_date": field},
    )

    audited = DecisionSafetyLayer().audit_findings([finding], {DocumentType.INCOME_CERT: doc})
    assert audited[0].raw_result is Raw.VIOLATED
    assert audited[0].resolved_status is Status.WARN
    assert audited[0].reason_code == ReasonCode.DEFECT_PROBABLE.value


def test_uncertain_evidence_never_produces_pass():
    """5. Uncertain evidence must never produce PASS for satisfied or violated checks."""
    # Case A: SATISFIED + UNCERTAIN -> REVIEW (CANNOT_CONFIRM)
    pass_finding = _expiration_finding()
    field_low = ExtractedField(
        field_name="issue_date",
        raw_value="2025-01-10",
        normalized_value="2025-01-10",
        extraction_method=ExtractionMethod.LOCAL_OCR,
        evidence_state=EvidenceState.LOW_CONFIDENCE,
        is_uncertain=True,
        uncertainty_reason="Low OCR confidence (40%)",
    )
    doc_low = ExtractedDocument(
        doc_type=DocumentType.INCOME_CERT,
        file_path="income_cert.pdf",
        fields={"issue_date": field_low},
    )
    audited_pass = DecisionSafetyLayer().audit_findings([pass_finding], {DocumentType.INCOME_CERT: doc_low})
    assert audited_pass[0].resolved_status is Status.REVIEW
    assert audited_pass[0].resolved_status is not Status.PASS

    # Case B: VIOLATED + UNCERTAIN -> REVIEW (EVIDENCE_UNCERTAIN)
    fail_finding = Finding(
        rule_id="RULE-EXP-01",
        rule_name="Certificate validity",
        status=FindingStatus.FAIL,
        severity=Severity.CRITICAL,
        penalty=25,
        field="VALIDITY_PERIOD",
        documents_involved=[DocumentType.INCOME_CERT.value],
        message="Income certificate is expired.",
        evidence=[
            EvidenceProvenance(
                document_type=DocumentType.INCOME_CERT.value,
                file_name="income_cert.pdf",
                extracted_field="issue_date",
            )
        ],
        remediation="Obtain a valid certificate.",
        statutory_reference="Odisha Misc Cert Rules 2019",
    )
    audited_fail = DecisionSafetyLayer().audit_findings([fail_finding], {DocumentType.INCOME_CERT: doc_low})
    assert audited_fail[0].resolved_status is Status.REVIEW
    assert audited_fail[0].resolved_status is not Status.FAIL
    assert audited_fail[0].reason_code in (
        ReasonCode.EVIDENCE_UNCERTAIN.value,
        ReasonCode.CANNOT_CONFIRM.value,
        ReasonCode.INSUFFICIENT_DATA.value,
    )


def test_existing_clean_packet_behavior_remains_correct():
    """6. Clean synthetic packet PKT_01_CLEAN continues to produce NO_ISSUES_FOUND."""
    from pathlib import Path
    from docuready.pipeline import AuditPipeline

    repo_root = Path(__file__).resolve().parents[1]
    pkt_clean_dir = repo_root / "synthetic_data" / "pkt_01_clean"
    pipeline = AuditPipeline()
    result, docs = pipeline.load_and_audit_packet(str(pkt_clean_dir), packet_id="PKT_01_CLEAN")

    assert result.readiness is Readiness.NO_ISSUES_FOUND
    assert result.readiness_score == 100
    assert all(f.status is Status.PASS for f in result.findings)
