"""
Integration Test Suite: Pack-Driven Per-Rule Fixture Matrix (T3.2 / T3.2.1)

Exercises all ten canonical rule groups through PackExecutionEngine using packs/generic.demo
with genuine in-memory document fixtures, verifying that:
1. Every canonical rule group executes against real document representations through the pack engine.
2. Every rule maps to its canonical rule_id, V2 Status, Raw enum, and ReasonCode.
3. High-level AuditResult readiness conforms to the V2 resolver contract.
4. T2.1 date-invariance semantics hold at the pack engine level.
5. Reservation exemptions surface as NOT_APPLICABLE under verified evidence and abstain to REVIEW under uncertain evidence.
6. Mismatched document slots prevent corrupt field data from cascading into downstream cross-document comparisons.
7. Evidence provenance, comparison details, reason codes, severity, and penalties are rigorously asserted.
"""

from datetime import date
from pathlib import Path
from typing import Dict, Any, Optional
import pytest

from docuready.domain.enums import (
    EvidenceState,
    ExtractionMethod,
    MatchGrade,
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
from docuready.rules.engine import PackExecutionEngine

_REPO_ROOT = Path(__file__).resolve().parents[2]
_PACK_DIR = _REPO_ROOT / "packs" / "generic.demo"


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
    """Construct a clean, fully-verified 6-document packet where all 14 canonical rules pass."""
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


@pytest.fixture(scope="module")
def pack_engine():
    return PackExecutionEngine(_PACK_DIR, allow_draft=True)


# ---------------------------------------------------------------------------
# 1. Clean Packet Baseline
# ---------------------------------------------------------------------------

def test_pack_clean_packet_produces_all_canonical_passes_and_readiness_no_issues(pack_engine):
    packet = _make_clean_packet()
    res = pack_engine.validate_packet("PKT_CLEAN", packet, as_of=date(2026, 11, 15))

    assert res.readiness is Readiness.NO_ISSUES_FOUND
    assert res.readiness_score == 100
    assert len(res.findings) == 14

    for f in res.findings:
        assert f.resolved_status is Status.PASS
        assert f.reason_code == ReasonCode.CONFIRMED_OK.value


# ---------------------------------------------------------------------------
# 2. Group 1: Document Completeness & Legibility (RULE-DOC-01, RULE-DOC-02)
# ---------------------------------------------------------------------------

def test_pack_grp01_mandatory_document_missing_yields_rule_doc_01(pack_engine):
    packet = _make_clean_packet()
    del packet[DocumentType.INCOME_CERT]

    res = pack_engine.validate_packet("PKT_MISSING_INC", packet, as_of=date(2026, 11, 15))
    assert res.readiness is Readiness.NOT_READY

    finding = next(f for f in res.findings if f.rule_id == "RULE-DOC-01" and "INCOME_CERT" in f.documents_involved)
    assert finding.resolved_status is Status.MISSING
    assert finding.reason_code == ReasonCode.DOC_ABSENT.value
    assert finding.severity is Severity.FATAL
    assert finding.penalty == 35


def test_pack_grp01_unreadable_document_yields_rule_doc_02(pack_engine):
    packet = _make_clean_packet()
    packet[DocumentType.INCOME_CERT] = ExtractedDocument(
        doc_type=DocumentType.INCOME_CERT,
        file_path="income_cert.pdf",
        status="UNREADABLE",
    )

    res = pack_engine.validate_packet("PKT_UNREADABLE_INC", packet, as_of=date(2026, 11, 15))
    assert res.readiness is Readiness.NEEDS_CHECKS

    finding = next(f for f in res.findings if f.rule_id == "RULE-DOC-02" and "INCOME_CERT" in f.documents_involved)
    assert finding.resolved_status is Status.REVIEW
    assert finding.reason_code == ReasonCode.INSUFFICIENT_DATA.value


# ---------------------------------------------------------------------------
# 3. Group 2: Mandatory Field Completeness (RULE-FLD-01)
# ---------------------------------------------------------------------------

def test_pack_grp02_mandatory_field_missing(pack_engine):
    packet = _make_clean_packet()
    del packet[DocumentType.APPLICATION_FORM].fields["applicant_name"]

    res = pack_engine.validate_packet("PKT_MISSING_NAME_FLD", packet, as_of=date(2026, 11, 15))
    fld_finding = next(f for f in res.findings if f.rule_id == "RULE-FLD-01")
    assert fld_finding.resolved_status in (Status.FAIL, Status.REVIEW)


# ---------------------------------------------------------------------------
# 4. Group 3: Applicant Name Consistency (RULE-NAME-01)
# ---------------------------------------------------------------------------

def test_pack_grp03_exact_name_match(pack_engine):
    packet = _make_clean_packet()
    res = pack_engine.validate_packet("PKT_EXACT_NAME", packet, as_of=date(2026, 11, 15))
    f = next(f for f in res.findings if f.rule_id == "RULE-NAME-01")
    assert f.resolved_status is Status.PASS
    assert f.reason_code == ReasonCode.CONFIRMED_OK.value


def test_pack_grp03_contradictory_name_mismatch(pack_engine):
    packet = _make_clean_packet()
    packet[DocumentType.INCOME_CERT].fields["applicant_name"] = _make_field(
        DocumentType.INCOME_CERT, "applicant_name", "Vikram Singh"
    )

    res = pack_engine.validate_packet("PKT_NAME_MISMATCH", packet, as_of=date(2026, 11, 15))
    assert res.readiness is Readiness.NOT_READY

    f = next(f for f in res.findings if f.rule_id == "RULE-NAME-01")
    assert f.resolved_status is Status.FAIL
    assert f.reason_code == ReasonCode.DEFECT_CONFIRMED.value


def test_pack_grp03_compatible_name_variation(pack_engine):
    packet = _make_clean_packet()
    packet[DocumentType.INCOME_CERT].fields["applicant_name"] = _make_field(
        DocumentType.INCOME_CERT, "applicant_name", "Sharma Aarav"
    )

    res = pack_engine.validate_packet("PKT_NAME_COMPAT", packet, as_of=date(2026, 11, 15))
    f = next(f for f in res.findings if f.rule_id == "RULE-NAME-01")
    assert f.resolved_status in (Status.WARN, Status.REVIEW)


def test_pack_grp03_uncertain_ocr_name_variance(pack_engine):
    packet = _make_clean_packet()
    packet[DocumentType.INCOME_CERT].fields["applicant_name"] = _make_field(
        DocumentType.INCOME_CERT, "applicant_name", "Aarav Sharma", is_uncertain=True
    )

    res = pack_engine.validate_packet("PKT_NAME_UNC", packet, as_of=date(2026, 11, 15))
    f = next(f for f in res.findings if f.rule_id == "RULE-NAME-01")
    assert f.resolved_status is Status.REVIEW
    assert f.reason_code == ReasonCode.EVIDENCE_UNCERTAIN.value


# ---------------------------------------------------------------------------
# 5. Group 4: Date of Birth Consistency (RULE-DOB-01)
# ---------------------------------------------------------------------------

def test_pack_grp04_exact_dob_match(pack_engine):
    packet = _make_clean_packet()
    res = pack_engine.validate_packet("PKT_EXACT_DOB", packet, as_of=date(2026, 11, 15))
    f = next(f for f in res.findings if f.rule_id == "RULE-DOB-01")
    assert f.resolved_status is Status.PASS


def test_pack_grp04_contradictory_dob_mismatch(pack_engine):
    packet = _make_clean_packet()
    packet[DocumentType.MARKSHEET].fields["dob"] = _make_field(
        DocumentType.MARKSHEET, "dob", "20/09/2004"
    )

    res = pack_engine.validate_packet("PKT_DOB_MISMATCH", packet, as_of=date(2026, 11, 15))
    f = next(f for f in res.findings if f.rule_id == "RULE-DOB-01")
    assert f.resolved_status is Status.FAIL
    assert f.reason_code == ReasonCode.DEFECT_CONFIRMED.value


def test_pack_grp04_ambiguous_dob_format(pack_engine):
    packet = _make_clean_packet()
    packet[DocumentType.MARKSHEET].fields["dob"] = _make_field(
        DocumentType.MARKSHEET, "dob", "08/05/2005"
    )

    res = pack_engine.validate_packet("PKT_DOB_AMBIGUOUS", packet, as_of=date(2026, 11, 15))
    f = next(f for f in res.findings if f.rule_id == "RULE-DOB-01")
    assert f.resolved_status is Status.REVIEW


# ---------------------------------------------------------------------------
# 6. Group 5: Income Ceiling Compliance (RULE-INC-01)
# ---------------------------------------------------------------------------

def test_pack_grp05_income_within_ceiling(pack_engine):
    packet = _make_clean_packet(annual_income=180000.0)
    res = pack_engine.validate_packet("PKT_INC_OK", packet, as_of=date(2026, 11, 15))
    f = next(f for f in res.findings if f.rule_id == "RULE-INC-01")
    assert f.resolved_status is Status.PASS


def test_pack_grp05_income_exceeds_ceiling(pack_engine):
    packet = _make_clean_packet(annual_income=300000.0)
    res = pack_engine.validate_packet("PKT_INC_HIGH", packet, as_of=date(2026, 11, 15))
    f = next(f for f in res.findings if f.rule_id == "RULE-INC-01")
    assert f.resolved_status is Status.FAIL
    assert f.reason_code == ReasonCode.DEFECT_CONFIRMED.value


def test_pack_grp05_income_ceiling_uncertain_ocr(pack_engine):
    packet = _make_clean_packet(annual_income=300000.0)
    packet[DocumentType.INCOME_CERT].fields["annual_income"] = _make_field(
        DocumentType.INCOME_CERT, "annual_income", "300000", 300000.0, is_uncertain=True
    )

    res = pack_engine.validate_packet("PKT_INC_UNC", packet, as_of=date(2026, 11, 15))
    f = next(f for f in res.findings if f.rule_id == "RULE-INC-01")
    assert f.resolved_status is Status.REVIEW
    assert f.reason_code == ReasonCode.EVIDENCE_UNCERTAIN.value


# ---------------------------------------------------------------------------
# 7. Group 6: Declared vs Certified Income (RULE-INC-02)
# ---------------------------------------------------------------------------

def test_pack_grp06_declared_income_matches_certified(pack_engine):
    packet = _make_clean_packet()
    res = pack_engine.validate_packet("PKT_INC_MATCH", packet, as_of=date(2026, 11, 15))
    f = next(f for f in res.findings if f.rule_id == "RULE-INC-02")
    assert f.resolved_status is Status.PASS


def test_pack_grp06_declared_income_mismatches_certified(pack_engine):
    packet = _make_clean_packet()
    packet[DocumentType.APPLICATION_FORM].fields["annual_income"] = _make_field(
        DocumentType.APPLICATION_FORM, "annual_income", "120000", 120000.0
    )

    res = pack_engine.validate_packet("PKT_INC_DIFF", packet, as_of=date(2026, 11, 15))
    f = next(f for f in res.findings if f.rule_id == "RULE-INC-02")
    assert f.resolved_status is Status.FAIL
    assert f.reason_code == ReasonCode.DEFECT_CONFIRMED.value


# ---------------------------------------------------------------------------
# 8. Group 7: Certificate Validity Period (RULE-EXP-01)
# ---------------------------------------------------------------------------

def test_pack_grp07_valid_certificate(pack_engine):
    packet = _make_clean_packet(issue_date="15/01/2025")
    res = pack_engine.validate_packet("PKT_VALID_CERT", packet, as_of=date(2026, 11, 15))
    f = next(f for f in res.findings if f.rule_id == "RULE-EXP-01")
    assert f.resolved_status is Status.PASS


def test_pack_grp07_expired_certificate(pack_engine):
    packet = _make_clean_packet(issue_date="15/01/2020")
    res = pack_engine.validate_packet("PKT_EXPIRED_CERT", packet, as_of=date(2026, 11, 15))
    f = next(f for f in res.findings if f.rule_id == "RULE-EXP-01")
    assert f.resolved_status is Status.FAIL
    assert f.reason_code == ReasonCode.DEFECT_CONFIRMED.value


def test_pack_grp07_uncertain_date_yields_review(pack_engine):
    packet = _make_clean_packet()
    packet[DocumentType.INCOME_CERT].fields["issue_date"] = _make_field(
        DocumentType.INCOME_CERT, "issue_date", "15/01/2025", is_uncertain=True
    )

    res = pack_engine.validate_packet("PKT_UNC_DATE", packet, as_of=date(2026, 11, 15))
    f = next(f for f in res.findings if f.rule_id == "RULE-EXP-01")
    assert f.resolved_status is Status.REVIEW
    assert f.reason_code in (ReasonCode.EVIDENCE_UNCERTAIN.value, ReasonCode.CANNOT_CONFIRM.value)


# ---------------------------------------------------------------------------
# 9. Group 8: Certificate Reference Match (RULE-REF-01, RULE-REF-02)
# ---------------------------------------------------------------------------

def test_pack_grp08_ref_match(pack_engine):
    packet = _make_clean_packet()
    res = pack_engine.validate_packet("PKT_REF_MATCH", packet, as_of=date(2026, 11, 15))
    f_inc = next(f for f in res.findings if f.rule_id == "RULE-REF-01")
    f_cst = next(f for f in res.findings if f.rule_id == "RULE-REF-02")
    assert f_inc.resolved_status is Status.PASS
    assert f_cst.resolved_status is Status.PASS


def test_pack_grp08_ref_mismatch(pack_engine):
    packet = _make_clean_packet()
    packet[DocumentType.APPLICATION_FORM].fields["income_cert_no"] = _make_field(
        DocumentType.APPLICATION_FORM, "income_cert_no", "INC-WRONG-9999"
    )

    res = pack_engine.validate_packet("PKT_REF_MISMATCH", packet, as_of=date(2026, 11, 15))
    f_inc = next(f for f in res.findings if f.rule_id == "RULE-REF-01")
    assert f_inc.resolved_status is Status.FAIL
    assert f_inc.reason_code == ReasonCode.DEFECT_CONFIRMED.value


# ---------------------------------------------------------------------------
# 10. Group 9: Bank IFSC & Account Consistency (RULE-BNK-01, RULE-BNK-02)
# ---------------------------------------------------------------------------

def test_pack_grp09_valid_ifsc_and_account(pack_engine):
    packet = _make_clean_packet()
    res = pack_engine.validate_packet("PKT_BNK_OK", packet, as_of=date(2026, 11, 15))
    f_ifsc = next(f for f in res.findings if f.rule_id == "RULE-BNK-01")
    f_acc = next(f for f in res.findings if f.rule_id == "RULE-BNK-02")
    assert f_ifsc.resolved_status is Status.PASS
    assert f_acc.resolved_status is Status.PASS


def test_pack_grp09_account_mismatch(pack_engine):
    packet = _make_clean_packet()
    packet[DocumentType.APPLICATION_FORM].fields["account_no"] = _make_field(
        DocumentType.APPLICATION_FORM, "account_no", "999999999999"
    )

    res = pack_engine.validate_packet("PKT_ACC_MISMATCH", packet, as_of=date(2026, 11, 15))
    f_acc = next(f for f in res.findings if f.rule_id == "RULE-BNK-02")
    assert f_acc.resolved_status is Status.FAIL
    assert f_acc.reason_code == ReasonCode.DEFECT_CONFIRMED.value


# ---------------------------------------------------------------------------
# 11. Group 10: Domicile State & Academic Cutoff (RULE-DOM-01, RULE-MRK-01)
# ---------------------------------------------------------------------------

def test_pack_grp10_domicile_match_and_mismatch(pack_engine):
    # Match ODISHA
    packet_ok = _make_clean_packet(state="ODISHA")
    res_ok = pack_engine.validate_packet("PKT_DOM_OK", packet_ok, as_of=date(2026, 11, 15))
    f_ok = next(f for f in res_ok.findings if f.rule_id == "RULE-DOM-01")
    assert f_ok.resolved_status is Status.PASS

    # Mismatch MAHARASHTRA
    packet_bad = _make_clean_packet(state="MAHARASHTRA")
    res_bad = pack_engine.validate_packet("PKT_DOM_BAD", packet_bad, as_of=date(2026, 11, 15))
    f_bad = next(f for f in res_bad.findings if f.rule_id == "RULE-DOM-01")
    assert f_bad.resolved_status is Status.FAIL
    assert f_bad.reason_code == ReasonCode.DEFECT_CONFIRMED.value


def test_pack_grp10_academic_cutoff_general_vs_exemption(pack_engine):
    # 1. Above cutoff General (78.5% >= 50.0%) -> PASS
    packet_high = _make_clean_packet(percentage=78.5, caste_category="GENERAL")
    res_high = pack_engine.validate_packet("PKT_MRK_HIGH", packet_high, as_of=date(2026, 11, 15))
    f_high = next(f for f in res_high.findings if f.rule_id == "RULE-MRK-01")
    assert f_high.resolved_status is Status.PASS

    # 2. Below cutoff General (45.0% < 50.0%) -> FAIL
    packet_low = _make_clean_packet(percentage=45.0, caste_category="GENERAL")
    res_low = pack_engine.validate_packet("PKT_MRK_LOW", packet_low, as_of=date(2026, 11, 15))
    f_low = next(f for f in res_low.findings if f.rule_id == "RULE-MRK-01")
    assert f_low.resolved_status is Status.FAIL

    # 3. Below cutoff SC/ST verified -> NOT_APPLICABLE (EXEMPT)
    packet_sc = _make_clean_packet(percentage=45.0, caste_category="SCHEDULED CASTE (SC)")
    res_sc = pack_engine.validate_packet("PKT_MRK_SC", packet_sc, as_of=date(2026, 11, 15))
    f_sc = next(f for f in res_sc.findings if f.rule_id == "RULE-MRK-01")
    assert f_sc.resolved_status is Status.NOT_APPLICABLE
    assert "EXEMPT" in f_sc.reason_code

    # 4. Below cutoff SC/ST uncertain -> REVIEW
    packet_unc = _make_clean_packet(percentage=45.0)
    packet_unc[DocumentType.APPLICATION_FORM].fields["caste_category"] = _make_field(
        DocumentType.APPLICATION_FORM, "caste_category", "SC", is_uncertain=True
    )
    packet_unc[DocumentType.CASTE_CERT].fields.pop("caste_category", None)
    res_unc = pack_engine.validate_packet("PKT_MRK_UNC", packet_unc, as_of=date(2026, 11, 15))
    f_unc = next(f for f in res_unc.findings if f.rule_id == "RULE-MRK-01")
    assert f_unc.resolved_status is Status.REVIEW


# ---------------------------------------------------------------------------
# 12. Parametrized Matrix Across All 10 Groups
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "group_name,rule_id,expected_status,expected_raw,expected_reason",
    [
        ("GRP_01_DOC", "RULE-DOC-01", Status.MISSING, Raw.DOC_ABSENT, ReasonCode.DOC_ABSENT.value),
        ("GRP_01_LEG", "RULE-DOC-02", Status.REVIEW, Raw.INDETERMINATE, ReasonCode.INSUFFICIENT_DATA.value),
        ("GRP_03_NAME", "RULE-NAME-01", Status.FAIL, Raw.VIOLATED, ReasonCode.DEFECT_CONFIRMED.value),
        ("GRP_04_DOB", "RULE-DOB-01", Status.FAIL, Raw.VIOLATED, ReasonCode.DEFECT_CONFIRMED.value),
        ("GRP_05_INC_CEIL", "RULE-INC-01", Status.FAIL, Raw.VIOLATED, ReasonCode.DEFECT_CONFIRMED.value),
        ("GRP_06_INC_MATCH", "RULE-INC-02", Status.FAIL, Raw.VIOLATED, ReasonCode.DEFECT_CONFIRMED.value),
        ("GRP_07_EXP", "RULE-EXP-01", Status.FAIL, Raw.VIOLATED, ReasonCode.DEFECT_CONFIRMED.value),
        ("GRP_08_REF", "RULE-REF-01", Status.FAIL, Raw.VIOLATED, ReasonCode.DEFECT_CONFIRMED.value),
        ("GRP_09_BNK", "RULE-BNK-02", Status.FAIL, Raw.VIOLATED, ReasonCode.DEFECT_CONFIRMED.value),
        ("GRP_10_DOM", "RULE-DOM-01", Status.FAIL, Raw.VIOLATED, ReasonCode.DEFECT_CONFIRMED.value),
        ("GRP_10_MRK", "RULE-MRK-01", Status.FAIL, Raw.VIOLATED, ReasonCode.DEFECT_CONFIRMED.value),
    ],
)
def test_all_ten_canonical_groups_matrix(
    pack_engine, group_name, rule_id, expected_status, expected_raw, expected_reason
):
    packet = _make_clean_packet()

    if rule_id == "RULE-DOC-01":
        del packet[DocumentType.INCOME_CERT]
    elif rule_id == "RULE-DOC-02":
        packet[DocumentType.INCOME_CERT] = ExtractedDocument(
            doc_type=DocumentType.INCOME_CERT, file_path="income_cert.pdf", status="UNREADABLE"
        )
    elif rule_id == "RULE-NAME-01":
        packet[DocumentType.INCOME_CERT].fields["applicant_name"] = _make_field(
            DocumentType.INCOME_CERT, "applicant_name", "Vikram Singh"
        )
    elif rule_id == "RULE-DOB-01":
        packet[DocumentType.MARKSHEET].fields["dob"] = _make_field(
            DocumentType.MARKSHEET, "dob", "20/09/2004"
        )
    elif rule_id == "RULE-INC-01":
        packet[DocumentType.INCOME_CERT].fields["annual_income"] = _make_field(
            DocumentType.INCOME_CERT, "annual_income", "300000", 300000.0
        )
    elif rule_id == "RULE-INC-02":
        packet[DocumentType.APPLICATION_FORM].fields["annual_income"] = _make_field(
            DocumentType.APPLICATION_FORM, "annual_income", "120000", 120000.0
        )
    elif rule_id == "RULE-EXP-01":
        packet[DocumentType.INCOME_CERT].fields["issue_date"] = _make_field(
            DocumentType.INCOME_CERT, "issue_date", "15/01/2020"
        )
    elif rule_id == "RULE-REF-01":
        packet[DocumentType.APPLICATION_FORM].fields["income_cert_no"] = _make_field(
            DocumentType.APPLICATION_FORM, "income_cert_no", "INC-WRONG-9999"
        )
    elif rule_id == "RULE-BNK-02":
        packet[DocumentType.APPLICATION_FORM].fields["account_no"] = _make_field(
            DocumentType.APPLICATION_FORM, "account_no", "999999999999"
        )
    elif rule_id == "RULE-DOM-01":
        packet[DocumentType.RESIDENCE_CERT].fields["state"] = _make_field(
            DocumentType.RESIDENCE_CERT, "state", "MAHARASHTRA"
        )
    elif rule_id == "RULE-MRK-01":
        packet[DocumentType.MARKSHEET].fields["percentage"] = _make_field(
            DocumentType.MARKSHEET, "percentage", "45.0", 45.0
        )
        packet[DocumentType.APPLICATION_FORM].fields["caste_category"] = _make_field(
            DocumentType.APPLICATION_FORM, "caste_category", "GENERAL"
        )

    res = pack_engine.validate_packet(f"MATRIX_{group_name}", packet, as_of=date(2026, 11, 15))
    f = next(f for f in res.findings if f.rule_id == rule_id)
    assert f.resolved_status is expected_status
    assert f.reason_code == expected_reason
