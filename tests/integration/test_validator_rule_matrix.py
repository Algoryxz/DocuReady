"""
Integration Test Suite: Validator-Level Per-Rule Fixture Matrix (T2.2)

Exercises all ten canonical rule groups through DocuReadyValidator.validate_packet()
with genuine in-memory document fixtures, verifying that:
1. Every canonical rule group executes against real document representations.
2. Every rule maps to its canonical rule_id, V2 Status, Raw enum, and ReasonCode.
3. High-level AuditResult readiness conforms to the V2 resolver contract.
4. T2.1 date-invariance semantics (invariant PASS, invariant FAIL, mixed review, OCR exclusion)
   hold at the validator level.
5. Reservation exemptions surface as NOT_APPLICABLE under verified evidence and abstain to REVIEW
   under uncertain evidence.
6. Pack severity caps monotonically reduce severity without mutating core finding classifications.
"""

from datetime import date
from typing import Dict, Optional, Any
import pytest

from docuready.domain.enums import (
    EvidenceState,
    ExtractionMethod,
    MaxSeverity,
    Raw,
    Readiness,
    ReasonCode,
    Status,
)
from docuready.domain.models import (
    DocumentType,
    EvidenceProvenance,
    ExtractedDocument,
    ExtractedField,
    FindingStatus,
    Severity,
)
from docuready.rules.validator import DocuReadyValidator, SchemeConfig


# ---------------------------------------------------------------------------
# FIXTURE BUILDERS FOR IN-MEMORY DOCUMENT PACKETS
# ---------------------------------------------------------------------------

_UNSET = object()


def _make_field(
    doc_type: DocumentType,
    field_name: str,
    raw_value: str,
    normalized_value: Any = _UNSET,
    evidence_state: EvidenceState = EvidenceState.VERIFIED_TEXT,
    extraction_method: ExtractionMethod = ExtractionMethod.NATIVE_VECTOR,
    is_uncertain: bool = False,
    uncertainty_reason: Optional[str] = None,
    candidate_count: int = 1,
) -> ExtractedField:
    """Construct an ExtractedField with complete provenance and evidence metadata."""
    norm = raw_value if normalized_value is _UNSET else normalized_value
    return ExtractedField(
        field_name=field_name,
        raw_value=raw_value,
        normalized_value=norm,
        evidence_state=evidence_state,
        extraction_method=extraction_method,
        is_uncertain=is_uncertain,
        uncertainty_reason=uncertainty_reason,
        candidate_count=candidate_count,
        provenance=EvidenceProvenance(
            document_type=doc_type.value,
            file_name=f"{doc_type.value.lower()}.pdf",
            extracted_field=field_name,
            raw_snippet=raw_value,
            extraction_method=extraction_method.value,
        ),
    )


def _make_clean_packet(
    audit_date: date = date(2026, 11, 15),
    applicant_name: str = "Aarav Sharma",
    annual_income: float = 180000.0,
    caste_category: str = "GENERAL",
    dob: str = "15/08/2005",
    income_cert_no: str = "INC-2025-00123",
    caste_cert_no: str = "CST-2025-00456",
    residence_cert_no: str = "RES-2025-00789",
    state: str = "ODISHA",
    percentage: float = 78.5,
    ifsc: str = "SBIN0001234",
    account_no: str = "123456789012",
    issue_date: str = "15/01/2025",
) -> Dict[DocumentType, ExtractedDocument]:
    """Construct a clean, fully-verified 6-document packet where all 10 canonical rules pass."""
    return {
        DocumentType.APPLICATION_FORM: ExtractedDocument(
            doc_type=DocumentType.APPLICATION_FORM,
            file_path="application_form.pdf",
            status="VALID",
            fields={
                "applicant_name": _make_field(DocumentType.APPLICATION_FORM, "applicant_name", applicant_name),
                "annual_income": _make_field(DocumentType.APPLICATION_FORM, "annual_income", str(int(annual_income)), annual_income),
                "caste_category": _make_field(DocumentType.APPLICATION_FORM, "caste_category", caste_category),
                "dob": _make_field(DocumentType.APPLICATION_FORM, "dob", dob),
                "income_cert_no": _make_field(DocumentType.APPLICATION_FORM, "income_cert_no", income_cert_no),
                "caste_cert_no": _make_field(DocumentType.APPLICATION_FORM, "caste_cert_no", caste_cert_no),
                "ifsc": _make_field(DocumentType.APPLICATION_FORM, "ifsc", ifsc),
                "account_no": _make_field(DocumentType.APPLICATION_FORM, "account_no", account_no),
            },
        ),
        DocumentType.INCOME_CERT: ExtractedDocument(
            doc_type=DocumentType.INCOME_CERT,
            file_path="income_cert.pdf",
            status="VALID",
            fields={
                "applicant_name": _make_field(DocumentType.INCOME_CERT, "applicant_name", applicant_name),
                "annual_income": _make_field(DocumentType.INCOME_CERT, "annual_income", str(int(annual_income)), annual_income),
                "issue_date": _make_field(DocumentType.INCOME_CERT, "issue_date", issue_date),
                "certificate_no": _make_field(DocumentType.INCOME_CERT, "certificate_no", income_cert_no),
            },
        ),
        DocumentType.CASTE_CERT: ExtractedDocument(
            doc_type=DocumentType.CASTE_CERT,
            file_path="caste_cert.pdf",
            status="VALID",
            fields={
                "applicant_name": _make_field(DocumentType.CASTE_CERT, "applicant_name", applicant_name),
                "caste_category": _make_field(DocumentType.CASTE_CERT, "caste_category", caste_category),
                "certificate_no": _make_field(DocumentType.CASTE_CERT, "certificate_no", caste_cert_no),
            },
        ),
        DocumentType.RESIDENCE_CERT: ExtractedDocument(
            doc_type=DocumentType.RESIDENCE_CERT,
            file_path="residence_cert.pdf",
            status="VALID",
            fields={
                "applicant_name": _make_field(DocumentType.RESIDENCE_CERT, "applicant_name", applicant_name),
                "state": _make_field(DocumentType.RESIDENCE_CERT, "state", state),
                "certificate_no": _make_field(DocumentType.RESIDENCE_CERT, "certificate_no", residence_cert_no),
            },
        ),
        DocumentType.MARKSHEET: ExtractedDocument(
            doc_type=DocumentType.MARKSHEET,
            file_path="marksheet.pdf",
            status="VALID",
            fields={
                "applicant_name": _make_field(DocumentType.MARKSHEET, "applicant_name", applicant_name),
                "dob": _make_field(DocumentType.MARKSHEET, "dob", dob),
                "percentage": _make_field(DocumentType.MARKSHEET, "percentage", str(percentage), percentage),
            },
        ),
        DocumentType.BANK_PASSBOOK: ExtractedDocument(
            doc_type=DocumentType.BANK_PASSBOOK,
            file_path="bank_passbook.pdf",
            status="VALID",
            fields={
                "applicant_name": _make_field(DocumentType.BANK_PASSBOOK, "applicant_name", applicant_name),
                "account_no": _make_field(DocumentType.BANK_PASSBOOK, "account_no", account_no),
                "ifsc": _make_field(DocumentType.BANK_PASSBOOK, "ifsc", ifsc),
            },
        ),
    }


def _find_finding(findings, rule_id: str):
    """Find single finding by rule_id or None."""
    matches = [f for f in findings if f.rule_id == rule_id]
    return matches[0] if matches else None


# ---------------------------------------------------------------------------
# BASELINE VERIFICATION: CLEAN PACKET PRODUCES NO ISSUES
# ---------------------------------------------------------------------------

def test_clean_packet_produces_all_canonical_passes_and_readiness_no_issues():
    """Verify that a fully conforming packet passes all 10 canonical rule groups with NO_ISSUES_FOUND."""
    validator = DocuReadyValidator(SchemeConfig(), audit_date=date(2026, 11, 15))
    result = validator.validate_packet("CLEAN_PACKET_001", _make_clean_packet())

    assert result.readiness is Readiness.NO_ISSUES_FOUND
    assert result.overall_status is Readiness.NO_ISSUES_FOUND
    assert result.readiness_score == 100

    expected_passes = [
        "RULE-NAME-PASS",
        "RULE-DOB-PASS",
        "RULE-INC-CEIL-PASS",
        "RULE-INC-MATCH-PASS",
        "RULE-EXP-PASS",
        "RULE-REF-INC-PASS",
        "RULE-REF-CST-PASS",
        "RULE-BNK-IFSC-PASS",
        "RULE-DOM-PASS",
        "RULE-MRK-PASS",
    ]
    rule_ids = [f.rule_id for f in result.findings]
    for exp_rule in expected_passes:
        assert exp_rule in rule_ids, f"Expected {exp_rule} in clean packet findings"
        f = _find_finding(result.findings, exp_rule)
        assert f.status is Status.PASS
        assert f.raw_result is Raw.SATISFIED
        assert f.reason_code == ReasonCode.CONFIRMED_OK.value


# ---------------------------------------------------------------------------
# GROUP 1: RULE_GRP_01_DOC_COMPLETENESS
# ---------------------------------------------------------------------------

def test_grp01_mandatory_document_missing_yields_rule_doc_01_missing_and_not_ready():
    """Omitting CASTE_CERT from packet produces RULE-DOC-01 with Status.MISSING and Readiness.NOT_READY."""
    packet = _make_clean_packet()
    del packet[DocumentType.CASTE_CERT]

    validator = DocuReadyValidator(SchemeConfig(), audit_date=date(2026, 11, 15))
    result = validator.validate_packet("GRP01_MISSING_DOC", packet)

    f = _find_finding(result.findings, "RULE-DOC-01")
    assert f is not None
    assert f.status is Status.MISSING
    assert f.raw_result is Raw.DOC_ABSENT
    assert f.reason_code == ReasonCode.DOC_ABSENT.value
    assert DocumentType.CASTE_CERT.value in f.documents_involved
    assert result.readiness is Readiness.NOT_READY


def test_grp01_unreadable_or_corrupted_document_yields_rule_doc_02_review():
    """Marking MARKSHEET as UNREADABLE produces RULE-DOC-02 with Status.REVIEW and Readiness.NEEDS_CHECKS."""
    packet = _make_clean_packet()
    packet[DocumentType.MARKSHEET].status = "UNREADABLE"

    validator = DocuReadyValidator(SchemeConfig(), audit_date=date(2026, 11, 15))
    result = validator.validate_packet("GRP01_UNREADABLE_DOC", packet)

    f = _find_finding(result.findings, "RULE-DOC-02")
    assert f is not None
    assert f.status is Status.REVIEW
    assert f.raw_result is Raw.INDETERMINATE
    assert f.reason_code == ReasonCode.INSUFFICIENT_DATA.value
    assert DocumentType.MARKSHEET.value in f.documents_involved
    assert result.readiness in (Readiness.NEEDS_CHECKS, Readiness.NOT_READY)


# ---------------------------------------------------------------------------
# GROUP 2: RULE_GRP_02_FLD_COMPLETENESS
# ---------------------------------------------------------------------------

def test_grp02_mandatory_field_missing_yields_rule_fld_01_review():
    """Deleting annual_income from INCOME_CERT triggers RULE-FLD-01 and resolves to REVIEW via safety layer."""
    packet = _make_clean_packet()
    del packet[DocumentType.INCOME_CERT].fields["annual_income"]

    validator = DocuReadyValidator(SchemeConfig(), audit_date=date(2026, 11, 15))
    result = validator.validate_packet("GRP02_MISSING_FIELD", packet)

    f = _find_finding(result.findings, "RULE-FLD-01")
    assert f is not None
    assert f.field == "ANNUAL_INCOME"
    assert f.status is Status.REVIEW
    assert f.raw_result is Raw.VIOLATED
    assert f.reason_code == ReasonCode.EVIDENCE_UNCERTAIN.value


# ---------------------------------------------------------------------------
# GROUP 3: RULE_GRP_03_NAME_CONSISTENCY
# ---------------------------------------------------------------------------

def test_grp03_exact_name_match_across_all_documents_yields_pass():
    """Uniform verified name across all documents triggers RULE-NAME-PASS with Status.PASS."""
    packet = _make_clean_packet()
    validator = DocuReadyValidator(SchemeConfig(), audit_date=date(2026, 11, 15))
    result = validator.validate_packet("GRP03_NAME_MATCH", packet)

    f = _find_finding(result.findings, "RULE-NAME-PASS")
    assert f is not None
    assert f.status is Status.PASS
    assert f.raw_result is Raw.SATISFIED
    assert f.reason_code == ReasonCode.CONFIRMED_OK.value


def test_grp03_contradictory_name_mismatch_yields_rule_name_01_fail_and_not_ready():
    """Conflicting legal name on CASTE_CERT triggers RULE-NAME-01 with Status.FAIL and Readiness.NOT_READY."""
    packet = _make_clean_packet()
    packet[DocumentType.CASTE_CERT].fields["applicant_name"] = _make_field(
        DocumentType.CASTE_CERT, "applicant_name", "Rohan Gupta"
    )

    validator = DocuReadyValidator(SchemeConfig(), audit_date=date(2026, 11, 15))
    result = validator.validate_packet("GRP03_NAME_FAIL", packet)

    f = _find_finding(result.findings, "RULE-NAME-01")
    assert f is not None
    assert f.status is Status.FAIL
    assert f.raw_result is Raw.VIOLATED
    assert f.reason_code == ReasonCode.DEFECT_CONFIRMED.value
    assert result.readiness is Readiness.NOT_READY


def test_grp03_compatible_name_variation_yields_rule_name_02_review():
    """Initial / abbreviation name variance produces RULE-NAME-02 with Status.REVIEW (cannot hard FAIL)."""
    packet = _make_clean_packet()
    packet[DocumentType.INCOME_CERT].fields["applicant_name"] = _make_field(
        DocumentType.INCOME_CERT, "applicant_name", "A. Sharma"
    )

    validator = DocuReadyValidator(SchemeConfig(), audit_date=date(2026, 11, 15))
    result = validator.validate_packet("GRP03_NAME_VARIATION", packet)

    f = _find_finding(result.findings, "RULE-NAME-02")
    assert f is not None
    assert f.status is Status.REVIEW
    assert f.raw_result is Raw.INDETERMINATE
    assert result.readiness is Readiness.NEEDS_CHECKS


def test_grp03_uncertain_ocr_name_variance_yields_rule_name_uncertain_review():
    """Name variance with low-confidence OCR evidence yields RULE-NAME-UNCERTAIN with Status.REVIEW."""
    packet = _make_clean_packet()
    packet[DocumentType.INCOME_CERT].fields["applicant_name"] = _make_field(
        DocumentType.INCOME_CERT,
        "applicant_name",
        "Rohan Gupta",
        evidence_state=EvidenceState.UNCERTAIN,
        extraction_method=ExtractionMethod.LOCAL_OCR,
        is_uncertain=True,
    )

    validator = DocuReadyValidator(SchemeConfig(), audit_date=date(2026, 11, 15))
    result = validator.validate_packet("GRP03_NAME_UNCERTAIN", packet)

    f = _find_finding(result.findings, "RULE-NAME-UNCERTAIN")
    assert f is not None
    assert f.status is Status.REVIEW
    assert f.raw_result is Raw.INDETERMINATE
    assert result.readiness is Readiness.NEEDS_CHECKS


# ---------------------------------------------------------------------------
# GROUP 4: RULE_GRP_04_DOB_CONSISTENCY
# ---------------------------------------------------------------------------

def test_grp04_exact_dob_match_yields_rule_dob_pass():
    """Matching DOB on application and marksheet yields RULE-DOB-PASS with Status.PASS."""
    packet = _make_clean_packet()
    validator = DocuReadyValidator(SchemeConfig(), audit_date=date(2026, 11, 15))
    result = validator.validate_packet("GRP04_DOB_MATCH", packet)

    f = _find_finding(result.findings, "RULE-DOB-PASS")
    assert f is not None
    assert f.status is Status.PASS
    assert f.raw_result is Raw.SATISFIED


def test_grp04_contradictory_dob_mismatch_yields_rule_dob_01_fail():
    """Contradictory unambiguous DOB on marksheet yields RULE-DOB-01 with Status.FAIL and Readiness.NOT_READY."""
    packet = _make_clean_packet()
    packet[DocumentType.MARKSHEET].fields["dob"] = _make_field(
        DocumentType.MARKSHEET, "dob", "25/08/2004"
    )

    validator = DocuReadyValidator(SchemeConfig(), audit_date=date(2026, 11, 15))
    result = validator.validate_packet("GRP04_DOB_FAIL", packet)

    f = _find_finding(result.findings, "RULE-DOB-01")
    assert f is not None
    assert f.status is Status.FAIL
    assert f.raw_result is Raw.VIOLATED
    assert f.reason_code == ReasonCode.DEFECT_CONFIRMED.value
    assert result.readiness is Readiness.NOT_READY


def test_grp04_ambiguous_dob_format_yields_rule_dob_02_review():
    """Ambiguous date representation (05/06/2005 vs 06/05/2005) yields RULE-DOB-02 with Status.REVIEW."""
    packet = _make_clean_packet()
    packet[DocumentType.APPLICATION_FORM].fields["dob"] = _make_field(
        DocumentType.APPLICATION_FORM, "dob", "05/06/2005"
    )
    packet[DocumentType.MARKSHEET].fields["dob"] = _make_field(
        DocumentType.MARKSHEET, "dob", "06/05/2005"
    )

    validator = DocuReadyValidator(SchemeConfig(), audit_date=date(2026, 11, 15))
    result = validator.validate_packet("GRP04_DOB_AMBIGUOUS", packet)

    f = _find_finding(result.findings, "RULE-DOB-02")
    assert f is not None
    assert f.status is Status.REVIEW
    assert f.raw_result is Raw.INDETERMINATE


def test_grp04_malformed_dob_format_yields_rule_dob_03_fail():
    """Malformed DOB on marksheet yields RULE-DOB-03 with Status.FAIL."""
    packet = _make_clean_packet()
    packet[DocumentType.MARKSHEET].fields["dob"] = _make_field(
        DocumentType.MARKSHEET, "dob", "INVALID_DOB_STRING"
    )

    validator = DocuReadyValidator(SchemeConfig(), audit_date=date(2026, 11, 15))
    result = validator.validate_packet("GRP04_DOB_MALFORMED", packet)

    f = _find_finding(result.findings, "RULE-DOB-03")
    assert f is not None
    assert f.status is Status.FAIL
    assert f.raw_result is Raw.VIOLATED


def test_grp04_uncertain_ocr_dob_mismatch_yields_rule_dob_uncertain_review():
    """Conflicting unambiguous DOB with uncertain OCR yields RULE-DOB-UNCERTAIN with Status.REVIEW."""
    packet = _make_clean_packet()
    packet[DocumentType.MARKSHEET].fields["dob"] = _make_field(
        DocumentType.MARKSHEET,
        "dob",
        "25/08/2004",
        evidence_state=EvidenceState.UNCERTAIN,
        extraction_method=ExtractionMethod.LOCAL_OCR,
        is_uncertain=True,
    )

    validator = DocuReadyValidator(SchemeConfig(), audit_date=date(2026, 11, 15))
    result = validator.validate_packet("GRP04_DOB_UNCERTAIN", packet)

    f = _find_finding(result.findings, "RULE-DOB-UNCERTAIN")
    assert f is not None
    assert f.status is Status.REVIEW
    assert f.raw_result is Raw.INDETERMINATE


# ---------------------------------------------------------------------------
# GROUP 5: RULE_GRP_05_INC_CEILING
# ---------------------------------------------------------------------------

def test_grp05_income_within_statutory_ceiling_yields_rule_inc_ceil_pass():
    """Certified income 180,000 <= 250,000 ceiling yields RULE-INC-CEIL-PASS with Status.PASS."""
    packet = _make_clean_packet(annual_income=180000.0)
    validator = DocuReadyValidator(SchemeConfig(), audit_date=date(2026, 11, 15))
    result = validator.validate_packet("GRP05_INC_PASS", packet)

    f = _find_finding(result.findings, "RULE-INC-CEIL-PASS")
    assert f is not None
    assert f.status is Status.PASS
    assert f.raw_result is Raw.SATISFIED


def test_grp05_income_exceeds_statutory_ceiling_yields_rule_inc_01_fail():
    """Certified income 350,000 > 250,000 ceiling yields RULE-INC-01 with Status.FAIL and NOT_READY."""
    packet = _make_clean_packet(annual_income=350000.0)
    validator = DocuReadyValidator(SchemeConfig(), audit_date=date(2026, 11, 15))
    result = validator.validate_packet("GRP05_INC_FAIL", packet)

    f = _find_finding(result.findings, "RULE-INC-01")
    assert f is not None
    assert f.status is Status.FAIL
    assert f.raw_result is Raw.VIOLATED
    assert f.reason_code == ReasonCode.DEFECT_CONFIRMED.value
    assert result.readiness is Readiness.NOT_READY


def test_grp05_income_exceeds_ceiling_with_uncertain_ocr_yields_rule_inc_ceil_uncertain_review():
    """Certified income exceeding ceiling with low OCR confidence yields RULE-INC-CEIL-UNCERTAIN with Status.REVIEW."""
    packet = _make_clean_packet(annual_income=350000.0)
    packet[DocumentType.INCOME_CERT].fields["annual_income"] = _make_field(
        DocumentType.INCOME_CERT,
        "annual_income",
        "350000",
        normalized_value=350000.0,
        evidence_state=EvidenceState.UNCERTAIN,
        extraction_method=ExtractionMethod.LOCAL_OCR,
        is_uncertain=True,
    )

    validator = DocuReadyValidator(SchemeConfig(), audit_date=date(2026, 11, 15))
    result = validator.validate_packet("GRP05_INC_UNCERTAIN", packet)

    f = _find_finding(result.findings, "RULE-INC-CEIL-UNCERTAIN")
    assert f is not None
    assert f.status is Status.REVIEW
    assert f.raw_result is Raw.INDETERMINATE


def test_grp05_unparseable_income_value_yields_rule_inc_03_review():
    """Unparseable income string on Income Certificate yields RULE-INC-03 with Status.REVIEW."""
    packet = _make_clean_packet()
    packet[DocumentType.INCOME_CERT].fields["annual_income"] = _make_field(
        DocumentType.INCOME_CERT,
        "annual_income",
        "NOT_A_NUMBER",
        normalized_value=None,
    )

    validator = DocuReadyValidator(SchemeConfig(), audit_date=date(2026, 11, 15))
    result = validator.validate_packet("GRP05_INC_UNPARSEABLE", packet)

    f = _find_finding(result.findings, "RULE-INC-03")
    assert f is not None
    assert f.status is Status.REVIEW
    assert f.raw_result is Raw.INDETERMINATE


# ---------------------------------------------------------------------------
# GROUP 6: RULE_GRP_06_INC_MATCH
# ---------------------------------------------------------------------------

def test_grp06_declared_income_matches_certified_yields_rule_inc_match_pass():
    """Declared income 180,000 matches certified income exactly, yielding RULE-INC-MATCH-PASS with Status.PASS."""
    packet = _make_clean_packet(annual_income=180000.0)
    validator = DocuReadyValidator(SchemeConfig(), audit_date=date(2026, 11, 15))
    result = validator.validate_packet("GRP06_INC_MATCH_PASS", packet)

    f = _find_finding(result.findings, "RULE-INC-MATCH-PASS")
    assert f is not None
    assert f.status is Status.PASS
    assert f.raw_result is Raw.SATISFIED


def test_grp06_declared_income_mismatches_certified_yields_rule_inc_02_fail():
    """Declared income (180,000) mismatches certified income (220,000), yielding RULE-INC-02 with Status.FAIL."""
    packet = _make_clean_packet()
    packet[DocumentType.INCOME_CERT].fields["annual_income"] = _make_field(
        DocumentType.INCOME_CERT, "annual_income", "220000", normalized_value=220000.0
    )

    validator = DocuReadyValidator(SchemeConfig(), audit_date=date(2026, 11, 15))
    result = validator.validate_packet("GRP06_INC_MISMATCH_FAIL", packet)

    f = _find_finding(result.findings, "RULE-INC-02")
    assert f is not None
    assert f.status is Status.FAIL
    assert f.raw_result is Raw.VIOLATED
    assert f.reason_code == ReasonCode.DEFECT_CONFIRMED.value
    assert result.readiness is Readiness.NOT_READY


def test_grp06_income_mismatch_with_uncertain_ocr_yields_rule_inc_mismatch_uncertain_review():
    """Income mismatch with uncertain OCR on certificate yields RULE-INC-MISMATCH-UNCERTAIN with Status.REVIEW."""
    packet = _make_clean_packet()
    packet[DocumentType.INCOME_CERT].fields["annual_income"] = _make_field(
        DocumentType.INCOME_CERT,
        "annual_income",
        "220000",
        normalized_value=220000.0,
        evidence_state=EvidenceState.UNCERTAIN,
        extraction_method=ExtractionMethod.LOCAL_OCR,
        is_uncertain=True,
    )

    validator = DocuReadyValidator(SchemeConfig(), audit_date=date(2026, 11, 15))
    result = validator.validate_packet("GRP06_INC_MISMATCH_UNCERTAIN", packet)

    f = _find_finding(result.findings, "RULE-INC-MISMATCH-UNCERTAIN")
    assert f is not None
    assert f.status is Status.REVIEW
    assert f.raw_result is Raw.INDETERMINATE


# ---------------------------------------------------------------------------
# GROUP 7: RULE_GRP_07_EXP_VALIDITY (Includes T2.1 Date Invariance Semantics)
# ---------------------------------------------------------------------------

def test_grp07_unambiguous_valid_certificate_yields_rule_exp_pass():
    """Unambiguous issue date within 3-year validity period yields RULE-EXP-PASS with Status.PASS."""
    packet = _make_clean_packet(issue_date="15/01/2025")
    validator = DocuReadyValidator(SchemeConfig(income_cert_validity_years=3), audit_date=date(2026, 11, 15))
    result = validator.validate_packet("GRP07_VALID_DATE", packet)

    f = _find_finding(result.findings, "RULE-EXP-PASS")
    assert f is not None
    assert f.status is Status.PASS
    assert f.raw_result is Raw.SATISFIED


def test_grp07_unambiguous_expired_certificate_yields_rule_exp_01_fail():
    """Unambiguous issue date older than 3 years yields RULE-EXP-01 with Status.FAIL and Readiness.NOT_READY."""
    packet = _make_clean_packet(issue_date="15/01/2020")
    validator = DocuReadyValidator(SchemeConfig(income_cert_validity_years=3), audit_date=date(2026, 11, 15))
    result = validator.validate_packet("GRP07_EXPIRED_DATE", packet)

    f = _find_finding(result.findings, "RULE-EXP-01")
    assert f is not None
    assert f.status is Status.FAIL
    assert f.raw_result is Raw.VIOLATED
    assert f.reason_code == ReasonCode.DEFECT_CONFIRMED.value
    assert result.readiness is Readiness.NOT_READY


def test_grp07_date_invariance_pass_both_interpretations_valid_yields_pass():
    """T2.1: Native vector ambiguous date '10/01/2025' is invariant PASS (both DD/MM and MM/DD are valid)."""
    packet = _make_clean_packet()
    packet[DocumentType.INCOME_CERT].fields["issue_date"] = _make_field(
        DocumentType.INCOME_CERT,
        "issue_date",
        "10/01/2025",
        evidence_state=EvidenceState.AMBIGUOUS,
        extraction_method=ExtractionMethod.NATIVE_VECTOR,
        is_uncertain=True,
        uncertainty_reason="Ambiguous date format: could be DD/MM or MM/DD",
        candidate_count=1,
    )

    validator = DocuReadyValidator(SchemeConfig(income_cert_validity_years=3), audit_date=date(2026, 11, 15))
    result = validator.validate_packet("GRP07_INVARIANT_PASS", packet)

    f = _find_finding(result.findings, "RULE-EXP-PASS")
    assert f is not None
    assert f.status is Status.PASS
    assert f.raw_result is Raw.SATISFIED
    assert f.reason_code == ReasonCode.CONFIRMED_OK.value


def test_grp07_date_invariance_fail_both_interpretations_expired_yields_fail():
    """T2.1: Native vector ambiguous date '10/01/2020' is invariant FAIL (both DD/MM and MM/DD are expired)."""
    packet = _make_clean_packet()
    packet[DocumentType.INCOME_CERT].fields["issue_date"] = _make_field(
        DocumentType.INCOME_CERT,
        "issue_date",
        "10/01/2020",
        evidence_state=EvidenceState.AMBIGUOUS,
        extraction_method=ExtractionMethod.NATIVE_VECTOR,
        is_uncertain=True,
        uncertainty_reason="Ambiguous date format: could be DD/MM or MM/DD",
        candidate_count=1,
    )

    validator = DocuReadyValidator(SchemeConfig(income_cert_validity_years=3), audit_date=date(2026, 11, 15))
    result = validator.validate_packet("GRP07_INVARIANT_FAIL", packet)

    f = _find_finding(result.findings, "RULE-EXP-01")
    assert f is not None
    assert f.status is Status.FAIL
    assert f.raw_result is Raw.VIOLATED
    assert f.reason_code == ReasonCode.DEFECT_CONFIRMED.value
    assert result.readiness is Readiness.NOT_READY


def test_grp07_mixed_candidates_boundary_yields_review():
    """T2.1: Date '04/06/2023' at audit date 2026-05-15 (one candidate valid, one expired) resolves to Status.REVIEW."""
    packet = _make_clean_packet()
    packet[DocumentType.INCOME_CERT].fields["issue_date"] = _make_field(
        DocumentType.INCOME_CERT,
        "issue_date",
        "04/06/2023",
        evidence_state=EvidenceState.AMBIGUOUS,
        extraction_method=ExtractionMethod.NATIVE_VECTOR,
        is_uncertain=True,
        uncertainty_reason="Ambiguous date format: could be DD/MM or MM/DD",
        candidate_count=1,
    )

    validator = DocuReadyValidator(SchemeConfig(income_cert_validity_years=3), audit_date=date(2026, 5, 15))
    result = validator.validate_packet("GRP07_MIXED_CANDIDATES", packet)

    f = _find_finding(result.findings, "RULE-EXP-PASS")
    assert f is not None
    assert f.status is Status.REVIEW
    assert f.raw_result is Raw.INDETERMINATE


def test_grp07_ambiguous_date_with_ocr_extraction_yields_review():
    """T2.1: Ambiguous date '10/01/2025' with LOCAL_OCR extraction cannot claim native invariance and resolves to REVIEW."""
    packet = _make_clean_packet()
    packet[DocumentType.INCOME_CERT].fields["issue_date"] = _make_field(
        DocumentType.INCOME_CERT,
        "issue_date",
        "10/01/2025",
        evidence_state=EvidenceState.AMBIGUOUS,
        extraction_method=ExtractionMethod.LOCAL_OCR,
        is_uncertain=True,
        uncertainty_reason="Ambiguous date format: could be DD/MM or MM/DD",
        candidate_count=1,
    )

    validator = DocuReadyValidator(SchemeConfig(income_cert_validity_years=3), audit_date=date(2026, 11, 15))
    result = validator.validate_packet("GRP07_OCR_AMBIGUOUS", packet)

    f = _find_finding(result.findings, "RULE-EXP-PASS")
    assert f is not None
    assert f.status is Status.REVIEW
    assert f.raw_result is Raw.INDETERMINATE


def test_grp07_unparseable_date_yields_rule_exp_02_review():
    """Unparseable certificate date yields RULE-EXP-02 with Status.REVIEW."""
    packet = _make_clean_packet()
    packet[DocumentType.INCOME_CERT].fields["issue_date"] = _make_field(
        DocumentType.INCOME_CERT, "issue_date", "INVALID_DATE_STAMP"
    )

    validator = DocuReadyValidator(SchemeConfig(income_cert_validity_years=3), audit_date=date(2026, 11, 15))
    result = validator.validate_packet("GRP07_DATE_PARSE_FAIL", packet)

    f = _find_finding(result.findings, "RULE-EXP-02")
    assert f is not None
    assert f.status is Status.REVIEW
    assert f.raw_result is Raw.INDETERMINATE


# ---------------------------------------------------------------------------
# GROUP 8: RULE_GRP_08_REF_MATCH
# ---------------------------------------------------------------------------

def test_grp08_income_cert_number_match_yields_rule_ref_inc_pass():
    """Income certificate reference match yields RULE-REF-INC-PASS with Status.PASS."""
    packet = _make_clean_packet(income_cert_no="INC-2025-00123")
    validator = DocuReadyValidator(SchemeConfig(), audit_date=date(2026, 11, 15))
    result = validator.validate_packet("GRP08_INC_REF_MATCH", packet)

    f = _find_finding(result.findings, "RULE-REF-INC-PASS")
    assert f is not None
    assert f.status is Status.PASS
    assert f.raw_result is Raw.SATISFIED


def test_grp08_income_cert_number_mismatch_yields_rule_ref_01_fail():
    """Income certificate reference number mismatch yields RULE-REF-01 with Status.FAIL and NOT_READY."""
    packet = _make_clean_packet()
    packet[DocumentType.INCOME_CERT].fields["certificate_no"] = _make_field(
        DocumentType.INCOME_CERT, "certificate_no", "INC-9999-DIFFERENT"
    )

    validator = DocuReadyValidator(SchemeConfig(), audit_date=date(2026, 11, 15))
    result = validator.validate_packet("GRP08_INC_REF_MISMATCH", packet)

    f = _find_finding(result.findings, "RULE-REF-01")
    assert f is not None
    assert f.status is Status.FAIL
    assert f.raw_result is Raw.VIOLATED
    assert f.reason_code == ReasonCode.DEFECT_CONFIRMED.value
    assert result.readiness is Readiness.NOT_READY


def test_grp08_caste_cert_number_match_yields_rule_ref_cst_pass():
    """Caste certificate reference match yields RULE-REF-CST-PASS with Status.PASS."""
    packet = _make_clean_packet(caste_cert_no="CST-2025-00456")
    validator = DocuReadyValidator(SchemeConfig(), audit_date=date(2026, 11, 15))
    result = validator.validate_packet("GRP08_CST_REF_MATCH", packet)

    f = _find_finding(result.findings, "RULE-REF-CST-PASS")
    assert f is not None
    assert f.status is Status.PASS
    assert f.raw_result is Raw.SATISFIED


def test_grp08_caste_cert_number_mismatch_yields_rule_ref_02_fail():
    """Caste certificate reference number mismatch yields RULE-REF-02 with Status.FAIL and NOT_READY."""
    packet = _make_clean_packet()
    packet[DocumentType.CASTE_CERT].fields["certificate_no"] = _make_field(
        DocumentType.CASTE_CERT, "certificate_no", "CST-9999-DIFFERENT"
    )

    validator = DocuReadyValidator(SchemeConfig(), audit_date=date(2026, 11, 15))
    result = validator.validate_packet("GRP08_CST_REF_MISMATCH", packet)

    f = _find_finding(result.findings, "RULE-REF-02")
    assert f is not None
    assert f.status is Status.FAIL
    assert f.raw_result is Raw.VIOLATED
    assert f.reason_code == ReasonCode.DEFECT_CONFIRMED.value
    assert result.readiness is Readiness.NOT_READY


# ---------------------------------------------------------------------------
# GROUP 9: RULE_GRP_09_BNK_VALIDATION
# ---------------------------------------------------------------------------

def test_grp09_valid_rbi_ifsc_yields_rule_bnk_ifsc_pass():
    """Valid RBI IFSC code 'SBIN0001234' yields RULE-BNK-IFSC-PASS with Status.PASS."""
    packet = _make_clean_packet(ifsc="SBIN0001234")
    validator = DocuReadyValidator(SchemeConfig(), audit_date=date(2026, 11, 15))
    result = validator.validate_packet("GRP09_IFSC_PASS", packet)

    f = _find_finding(result.findings, "RULE-BNK-IFSC-PASS")
    assert f is not None
    assert f.status is Status.PASS
    assert f.raw_result is Raw.SATISFIED


def test_grp09_malformed_ifsc_yields_rule_bnk_01_fail():
    """Malformed IFSC code 'INVALID_IFSC' yields RULE-BNK-01 with Status.FAIL."""
    packet = _make_clean_packet()
    packet[DocumentType.BANK_PASSBOOK].fields["ifsc"] = _make_field(
        DocumentType.BANK_PASSBOOK, "ifsc", "INVALID_IFSC"
    )

    validator = DocuReadyValidator(SchemeConfig(), audit_date=date(2026, 11, 15))
    result = validator.validate_packet("GRP09_IFSC_MALFORMED", packet)

    f = _find_finding(result.findings, "RULE-BNK-01")
    assert f is not None
    assert f.status is Status.FAIL
    assert f.raw_result is Raw.VIOLATED


def test_grp09_bank_account_mismatch_yields_rule_bnk_02_fail():
    """Bank account mismatch between passbook and form yields RULE-BNK-02 with Status.FAIL and NOT_READY."""
    packet = _make_clean_packet()
    packet[DocumentType.APPLICATION_FORM].fields["account_no"] = _make_field(
        DocumentType.APPLICATION_FORM, "account_no", "987654321098"
    )

    validator = DocuReadyValidator(SchemeConfig(), audit_date=date(2026, 11, 15))
    result = validator.validate_packet("GRP09_ACC_MISMATCH", packet)

    f = _find_finding(result.findings, "RULE-BNK-02")
    assert f is not None
    assert f.status is Status.FAIL
    assert f.raw_result is Raw.VIOLATED
    assert f.reason_code == ReasonCode.DEFECT_CONFIRMED.value
    assert result.readiness is Readiness.NOT_READY


# ---------------------------------------------------------------------------
# GROUP 10: RULE_GRP_10_DOM_MRK_COMPLIANCE (Domicile, Marksheet, and Exemption)
# ---------------------------------------------------------------------------

def test_grp10_matching_domicile_state_yields_rule_dom_pass():
    """Residence state 'ODISHA' matching target state yields RULE-DOM-PASS with Status.PASS."""
    packet = _make_clean_packet(state="ODISHA")
    validator = DocuReadyValidator(SchemeConfig(target_state="ODISHA"), audit_date=date(2026, 11, 15))
    result = validator.validate_packet("GRP10_DOM_MATCH", packet)

    f = _find_finding(result.findings, "RULE-DOM-PASS")
    assert f is not None
    assert f.status is Status.PASS
    assert f.raw_result is Raw.SATISFIED


def test_grp10_mismatched_domicile_state_yields_rule_dom_01_fail():
    """Residence state 'DELHI' differing from target 'ODISHA' yields RULE-DOM-01 with Status.FAIL and NOT_READY."""
    packet = _make_clean_packet(state="DELHI")
    validator = DocuReadyValidator(SchemeConfig(target_state="ODISHA"), audit_date=date(2026, 11, 15))
    result = validator.validate_packet("GRP10_DOM_FAIL", packet)

    f = _find_finding(result.findings, "RULE-DOM-01")
    assert f is not None
    assert f.status is Status.FAIL
    assert f.raw_result is Raw.VIOLATED
    assert f.reason_code == ReasonCode.DEFECT_CONFIRMED.value
    assert result.readiness is Readiness.NOT_READY


def test_grp10_academic_percentage_above_cutoff_yields_rule_mrk_pass():
    """General candidate with 78.5% >= 50% cutoff yields RULE-MRK-PASS with Status.PASS."""
    packet = _make_clean_packet(caste_category="GENERAL", percentage=78.5)
    validator = DocuReadyValidator(SchemeConfig(min_academic_percentage=50.0), audit_date=date(2026, 11, 15))
    result = validator.validate_packet("GRP10_MRK_PASS", packet)

    f = _find_finding(result.findings, "RULE-MRK-PASS")
    assert f is not None
    assert f.status is Status.PASS
    assert f.raw_result is Raw.SATISFIED


def test_grp10_academic_percentage_below_cutoff_general_yields_rule_mrk_01_fail():
    """General candidate with 42.0% < 50% cutoff yields RULE-MRK-01 with Status.FAIL and NOT_READY."""
    packet = _make_clean_packet(caste_category="GENERAL", percentage=42.0)
    validator = DocuReadyValidator(SchemeConfig(min_academic_percentage=50.0), audit_date=date(2026, 11, 15))
    result = validator.validate_packet("GRP10_MRK_FAIL", packet)

    f = _find_finding(result.findings, "RULE-MRK-01")
    assert f is not None
    assert f.status is Status.FAIL
    assert f.raw_result is Raw.VIOLATED
    assert f.reason_code == ReasonCode.DEFECT_CONFIRMED.value
    assert result.readiness is Readiness.NOT_READY


def test_grp10_academic_percentage_below_cutoff_sc_st_verified_yields_not_applicable():
    """SC candidate with 42.0% under PASS_ONLY policy produces RULE-MRK-RELAX-PASS with Status.NOT_APPLICABLE and zero penalty."""
    packet = _make_clean_packet(caste_category="SCHEDULED CASTE (SC)", percentage=42.0)
    validator = DocuReadyValidator(
        SchemeConfig(min_academic_percentage=50.0, sc_st_cutoff_policy="PASS_ONLY"),
        audit_date=date(2026, 11, 15),
    )
    result = validator.validate_packet("GRP10_SC_EXEMPTION_VERIFIED", packet)

    f = _find_finding(result.findings, "RULE-MRK-RELAX-PASS")
    assert f is not None
    assert f.status is Status.NOT_APPLICABLE
    assert f.raw_result is Raw.EXEMPT
    assert f.reason_code == "EXEMPT:CATEGORY_EXEMPTION"
    assert f.penalty == 0


def test_grp10_academic_percentage_sc_st_uncertain_category_yields_review():
    """SC candidate with 42.0% but UNCERTAIN category evidence causes safety layer to abstain to Status.REVIEW."""
    packet = _make_clean_packet(caste_category="SCHEDULED CASTE (SC)", percentage=42.0)
    packet[DocumentType.APPLICATION_FORM].fields["caste_category"] = _make_field(
        DocumentType.APPLICATION_FORM,
        "caste_category",
        "SCHEDULED CASTE (SC)",
        evidence_state=EvidenceState.UNCERTAIN,
        extraction_method=ExtractionMethod.LOCAL_OCR,
        is_uncertain=True,
    )
    packet[DocumentType.CASTE_CERT].fields["caste_category"] = _make_field(
        DocumentType.CASTE_CERT,
        "caste_category",
        "SCHEDULED CASTE (SC)",
        evidence_state=EvidenceState.UNCERTAIN,
        extraction_method=ExtractionMethod.LOCAL_OCR,
        is_uncertain=True,
    )

    validator = DocuReadyValidator(
        SchemeConfig(min_academic_percentage=50.0, sc_st_cutoff_policy="PASS_ONLY"),
        audit_date=date(2026, 11, 15),
    )
    result = validator.validate_packet("GRP10_SC_EXEMPTION_UNCERTAIN", packet)

    f = _find_finding(result.findings, "RULE-MRK-RELAX-PASS")
    assert f is not None
    assert f.status is Status.REVIEW
    assert f.raw_result is Raw.INDETERMINATE


# ---------------------------------------------------------------------------
# PACK SEVERITY CAPS & MONOTONICITY
# ---------------------------------------------------------------------------

def test_pack_severity_cap_reduces_income_breach_fail_to_warn():
    """Pack-level cap rule_max_severity={'RULE-INC-01': MaxSeverity.WARN} reduces Status.FAIL to Status.WARN."""
    packet = _make_clean_packet(annual_income=350000.0)
    config = SchemeConfig(
        income_ceiling=250000.0,
        rule_max_severity={"RULE-INC-01": MaxSeverity.WARN},
    )
    validator = DocuReadyValidator(config, audit_date=date(2026, 11, 15))
    result = validator.validate_packet("CAP_INCOME_WARN", packet)

    f = _find_finding(result.findings, "RULE-INC-01")
    assert f is not None
    assert f.status is Status.WARN
    assert f.raw_result is Raw.VIOLATED
    assert f.reason_code == ReasonCode.ADVISORY_RULE_CAP.value
    assert result.readiness is Readiness.NEEDS_CHECKS


def test_pack_severity_cap_reduces_domicile_breach_fail_to_review():
    """Pack-level cap rule_max_severity={'RULE-DOM-01': MaxSeverity.REVIEW} reduces Status.FAIL to Status.REVIEW."""
    packet = _make_clean_packet(state="DELHI")
    config = SchemeConfig(
        target_state="ODISHA",
        rule_max_severity={"RULE-DOM-01": MaxSeverity.REVIEW},
    )
    validator = DocuReadyValidator(config, audit_date=date(2026, 11, 15))
    result = validator.validate_packet("CAP_DOMICILE_REVIEW", packet)

    f = _find_finding(result.findings, "RULE-DOM-01")
    assert f is not None
    assert f.status is Status.REVIEW
    assert f.raw_result is Raw.VIOLATED
    assert f.reason_code == ReasonCode.ADVISORY_RULE_CAP.value


# ---------------------------------------------------------------------------
# PARAMETRIZED CANONICAL TEN RULE GROUP MATRIX
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "group_id, mutated_rule_id, expected_status, expected_raw, expected_readiness",
    [
        (
            "RULE_GRP_01_DOC_COMPLETENESS",
            "RULE-DOC-01",
            Status.MISSING,
            Raw.DOC_ABSENT,
            Readiness.NOT_READY,
        ),
        (
            "RULE_GRP_02_FLD_COMPLETENESS",
            "RULE-FLD-01",
            Status.REVIEW,
            Raw.VIOLATED,
            Readiness.NEEDS_CHECKS,
        ),
        (
            "RULE_GRP_03_NAME_CONSISTENCY",
            "RULE-NAME-01",
            Status.FAIL,
            Raw.VIOLATED,
            Readiness.NOT_READY,
        ),
        (
            "RULE_GRP_04_DOB_CONSISTENCY",
            "RULE-DOB-01",
            Status.FAIL,
            Raw.VIOLATED,
            Readiness.NOT_READY,
        ),
        (
            "RULE_GRP_05_INC_CEILING",
            "RULE-INC-01",
            Status.FAIL,
            Raw.VIOLATED,
            Readiness.NOT_READY,
        ),
        (
            "RULE_GRP_06_INC_MATCH",
            "RULE-INC-02",
            Status.FAIL,
            Raw.VIOLATED,
            Readiness.NOT_READY,
        ),
        (
            "RULE_GRP_07_EXP_VALIDITY",
            "RULE-EXP-01",
            Status.FAIL,
            Raw.VIOLATED,
            Readiness.NOT_READY,
        ),
        (
            "RULE_GRP_08_REF_MATCH",
            "RULE-REF-01",
            Status.FAIL,
            Raw.VIOLATED,
            Readiness.NOT_READY,
        ),
        (
            "RULE_GRP_09_BNK_VALIDATION",
            "RULE-BNK-01",
            Status.FAIL,
            Raw.VIOLATED,
            Readiness.NOT_READY,
        ),
        (
            "RULE_GRP_10_DOM_MRK_COMPLIANCE",
            "RULE-DOM-01",
            Status.FAIL,
            Raw.VIOLATED,
            Readiness.NOT_READY,
        ),
    ],
)
def test_all_ten_canonical_groups_matrix(
    group_id: str,
    mutated_rule_id: str,
    expected_status: Status,
    expected_raw: Raw,
    expected_readiness: Readiness,
):
    """Parametrized execution ensuring every canonical rule group executes through validate_packet."""
    packet = _make_clean_packet()

    if mutated_rule_id == "RULE-DOC-01":
        del packet[DocumentType.CASTE_CERT]
    elif mutated_rule_id == "RULE-FLD-01":
        del packet[DocumentType.INCOME_CERT].fields["annual_income"]
    elif mutated_rule_id == "RULE-NAME-01":
        packet[DocumentType.CASTE_CERT].fields["applicant_name"] = _make_field(
            DocumentType.CASTE_CERT, "applicant_name", "Rohan Gupta"
        )
    elif mutated_rule_id == "RULE-DOB-01":
        packet[DocumentType.MARKSHEET].fields["dob"] = _make_field(
            DocumentType.MARKSHEET, "dob", "25/08/2004"
        )
    elif mutated_rule_id == "RULE-INC-01":
        packet[DocumentType.INCOME_CERT].fields["annual_income"] = _make_field(
            DocumentType.INCOME_CERT, "annual_income", "350000", normalized_value=350000.0
        )
    elif mutated_rule_id == "RULE-INC-02":
        packet[DocumentType.INCOME_CERT].fields["annual_income"] = _make_field(
            DocumentType.INCOME_CERT, "annual_income", "220000", normalized_value=220000.0
        )
    elif mutated_rule_id == "RULE-EXP-01":
        packet[DocumentType.INCOME_CERT].fields["issue_date"] = _make_field(
            DocumentType.INCOME_CERT, "issue_date", "15/01/2020"
        )
    elif mutated_rule_id == "RULE-REF-01":
        packet[DocumentType.INCOME_CERT].fields["certificate_no"] = _make_field(
            DocumentType.INCOME_CERT, "certificate_no", "INC-9999-MISMATCH"
        )
    elif mutated_rule_id == "RULE-BNK-01":
        packet[DocumentType.BANK_PASSBOOK].fields["ifsc"] = _make_field(
            DocumentType.BANK_PASSBOOK, "ifsc", "INVALID_IFSC"
        )
    elif mutated_rule_id == "RULE-DOM-01":
        packet[DocumentType.RESIDENCE_CERT].fields["state"] = _make_field(
            DocumentType.RESIDENCE_CERT, "state", "DELHI"
        )

    validator = DocuReadyValidator(SchemeConfig(), audit_date=date(2026, 11, 15))
    result = validator.validate_packet(f"MATRIX_{group_id}", packet)

    finding = _find_finding(result.findings, mutated_rule_id)
    assert finding is not None, f"Rule {mutated_rule_id} for {group_id} was not triggered"
    assert finding.status is expected_status, (
        f"Rule {mutated_rule_id} expected status {expected_status}, got {finding.status}"
    )
    assert finding.raw_result is expected_raw, (
        f"Rule {mutated_rule_id} expected raw {expected_raw}, got {finding.raw_result}"
    )
    assert result.readiness is expected_readiness, (
        f"Matrix run for {group_id} expected readiness {expected_readiness}, got {result.readiness}"
    )
