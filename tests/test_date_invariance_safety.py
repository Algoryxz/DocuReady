"""
Focused Regression Test Suite for Expiration Date Invariance Safety Logic.

Verifies:
1. Clean packet, native-vector date ambiguity: 10/01/2025, audit date 2026-11-13, validity 3 years.
   Both interpretations are valid -> PKT_01_CLEAN produces NO_ISSUES_FOUND, all 8 findings verified PASS.
2. Mixed interpretation outcome: 10/01/2025, audit date 2027-10-01, validity 2 years.
   One interpretation is expired (2.72 yrs) and the other is valid (2.00 yrs).
   Finding remains REVIEW (CANNOT_CONFIRM), packet readiness is NEEDS_CHECKS (not NO_ISSUES_FOUND, not rejection).
3. OCR multi-candidate date: issue_date with EvidenceState.AMBIGUOUS, LOCAL_OCR, candidate_count > 1
   remains uncertain even with valid year.
4. Unrelated ambiguity: uncertainty reason does not identify DD/MM vs MM/DD date format -> not promoted.
5. Malformed or invalid candidate date -> no verified promotion.
6. Boundary test: date close to validity boundary where interpretations differ -> remains REVIEW.
7. Configured policy test: changing income_cert_validity_years or audit_date dynamically changes the
   decision consistently with the actual rule with zero hardcoded year threshold.
8. Two-digit year handling: exact agreement with parse_and_normalize_date for boundary years 68, 69, 70.
9. Dedicated Invariant FAIL integration regression: both interpretations expired -> confirmed statutory FAIL,
   raw_result VIOLATED, reason_code DEFECT_CONFIRMED, packet readiness NOT_READY.
"""

from __future__ import annotations

import pathlib
from datetime import date
import pytest

from docuready.domain.enums import Status, Raw, Readiness, EvidenceState, ExtractionMethod, ReasonCode
from docuready.domain.models import (
    AuditResult, DocumentType, ExtractedDocument, ExtractedField, EvidenceProvenance,
    Finding, FindingStatus, Severity
)
from docuready.normalize.normalizer import (
    get_date_ambiguity_candidates,
    parse_and_normalize_date,
)
from docuready.outcome.safety_layer import (
    DecisionSafetyLayer,
    is_expiration_date_invariant_pass,
    is_expiration_date_invariant_fail,
)
from docuready.rules.validator import DocuReadyValidator, SchemeConfig
from docuready.pipeline import AuditPipeline

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_SYNTHETIC_DIR = _REPO_ROOT / "synthetic_data"


# ---------------------------------------------------------------------------
# Test 1: Clean packet native-vector date ambiguity (Invariant PASS)
# ---------------------------------------------------------------------------

def test_clean_packet_native_vector_date_ambiguity_invariant_pass():
    """
    10/01/2025, audit date 2026-11-13, validity 3 years.
    Both interpretations (10 Jan 2025 = 1.84 yrs, 1 Oct 2025 = 1.12 yrs) are valid.
    PKT_01_CLEAN must produce NO_ISSUES_FOUND, readiness score 100, and 8 verified PASS findings.
    """
    pipeline = AuditPipeline()
    pkt_dir = _SYNTHETIC_DIR / "pkt_01_clean"
    result, docs = pipeline.load_and_audit_packet(str(pkt_dir), packet_id="PKT_01_CLEAN")

    assert result.overall_status == Readiness.NO_ISSUES_FOUND
    assert result.readiness_score == 100

    exp_finding = next((f for f in result.findings if f.rule_id == "RULE-EXP-PASS"), None)
    assert exp_finding is not None
    assert exp_finding.status == Status.PASS
    assert exp_finding.reason_code == "CONFIRMED_OK"
    assert exp_finding.raw_result == Raw.SATISFIED

    # All 8 findings must be PASS
    assert len(result.findings) == 8
    for f in result.findings:
        assert f.status == Status.PASS
        assert f.reason_code == "CONFIRMED_OK"


# ---------------------------------------------------------------------------
# Test 2: Mixed interpretation outcome (Remains REVIEW, not FAIL or PASS)
# ---------------------------------------------------------------------------

def test_mixed_interpretation_outcome_remains_review():
    """
    Raw date: 10/01/2025
    Interpretation A (DD/MM): 10 January 2025 -> age (2027-10-01 - 2025-01-10) = 994 days = 2.72 years > 2 years (EXPIRED)
    Interpretation B (MM/DD): 1 October 2025 -> age (2027-10-01 - 2025-10-01) = 730 days = 2.00 years <= 2 years (VALID)
    The date interpretation changes the outcome.
    The V2 result must remain REVIEW (CANNOT_CONFIRM), never FAIL or PASS.
    """
    pipeline = AuditPipeline(
        scheme_config=SchemeConfig(income_cert_validity_years=2),
        audit_date=date(2027, 10, 1),
    )
    pkt_dir = _SYNTHETIC_DIR / "pkt_01_clean"
    result, _ = pipeline.load_and_audit_packet(str(pkt_dir), packet_id="PKT_01_MIXED_DATE")

    # Expiration finding must be REVIEW
    exp_findings = [f for f in result.findings if "EXP" in f.rule_id]
    assert len(exp_findings) == 1
    exp_f = exp_findings[0]

    assert exp_f.status == Status.REVIEW, f"Expected REVIEW but got {exp_f.status}"
    assert exp_f.status != Status.FAIL, "Must not be a definitive rejection"
    assert exp_f.status != Status.PASS, "Must not be an unsupported pass"
    assert exp_f.reason_code in ("CANNOT_CONFIRM", "EVIDENCE_UNCERTAIN", "INSUFFICIENT_DATA")

    # Packet readiness must NOT be NO_ISSUES_FOUND
    assert result.overall_status != Readiness.NO_ISSUES_FOUND
    assert result.overall_status == Readiness.NEEDS_CHECKS


# ---------------------------------------------------------------------------
# Test 3: OCR multi-candidate date (Remains UNCERTAIN / REVIEW)
# ---------------------------------------------------------------------------

def test_ocr_multi_candidate_date_remains_uncertain():
    """
    An issue_date extracted via LOCAL_OCR with candidate_count > 1 or OCR ambiguity
    must NOT be promoted to VERIFIED_TEXT, even if the year calculation appears valid.
    """
    field = ExtractedField(
        field_name="issue_date",
        raw_value="10/01/2025",
        normalized_value="2025-01-10",
        extraction_method="LOCAL_OCR",
        candidate_count=2,
        evidence_state=EvidenceState.AMBIGUOUS,
        is_uncertain=True,
        uncertainty_reason="Date format ambiguity (DD/MM vs MM/DD) with multiple OCR candidates",
    )
    doc = ExtractedDocument(
        doc_type=DocumentType.INCOME_CERT,
        file_path="income_cert.pdf",
        fields={"issue_date": field},
    )
    finding = Finding(
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

    safety = DecisionSafetyLayer()
    states = safety._collect_v2_evidence_states(
        finding, {DocumentType.INCOME_CERT: doc}, scheme_config=SchemeConfig(), audit_date=date(2026, 11, 13)
    )
    assert states == [EvidenceState.UNCERTAIN]

    # Directly verify helper function abstains on OCR
    assert is_expiration_date_invariant_pass(field, audit_date=date(2026, 11, 13), validity_years=3) is False

    audited = safety.audit_findings([finding], {DocumentType.INCOME_CERT: doc}, audit_date=date(2026, 11, 13))
    assert audited[0].resolved_status is Status.REVIEW
    assert audited[0].reason_code in ("CANNOT_CONFIRM", "EVIDENCE_UNCERTAIN", "INSUFFICIENT_DATA")


# ---------------------------------------------------------------------------
# Test 4: Unrelated ambiguity not promoted
# ---------------------------------------------------------------------------

def test_unrelated_ambiguity_not_promoted():
    """
    An ambiguous issue_date whose uncertainty reason does not specifically identify
    DD/MM vs MM/DD date format ambiguity must NOT be promoted.
    """
    field = ExtractedField(
        field_name="issue_date",
        raw_value="10/01/2025",
        extraction_method="NATIVE_VECTOR",
        candidate_count=1,
        evidence_state=EvidenceState.AMBIGUOUS,
        is_uncertain=True,
        uncertainty_reason="Layout bounding box overlap conflict",  # Unrelated ambiguity
    )
    is_inv = is_expiration_date_invariant_pass(field, audit_date=date(2026, 11, 13), validity_years=3)
    assert is_inv is False, "Unrelated ambiguity must not be promoted"


# ---------------------------------------------------------------------------
# Test 5: Malformed or invalid candidate date (No verified promotion)
# ---------------------------------------------------------------------------

def test_malformed_or_invalid_candidate_date():
    """
    Malformed date string cannot produce two valid interpretations and must not be promoted.
    """
    candidates = get_date_ambiguity_candidates("99/99/2025")
    assert candidates == []

    field = ExtractedField(
        field_name="issue_date",
        raw_value="99/99/2025",
        extraction_method="NATIVE_VECTOR",
        candidate_count=1,
        evidence_state=EvidenceState.AMBIGUOUS,
        is_uncertain=True,
        uncertainty_reason="Date format ambiguity (DD/MM vs MM/DD)",
    )
    is_inv = is_expiration_date_invariant_pass(field, audit_date=date(2026, 11, 13), validity_years=3)
    assert is_inv is False


# ---------------------------------------------------------------------------
# Test 6: Boundary date ambiguity (Remains REVIEW)
# ---------------------------------------------------------------------------

def test_boundary_date_ambiguity_remains_review():
    """
    Date close enough to the validity boundary that the two interpretations differ:
    Raw date: 02/06/2023, audit date: 2026-05-01, validity: 3 years.
    Interpretation 1 (02 June 2023): age is 1064 days = 2.913 years <= 3 (VALID)
    Interpretation 2 (06 Feb 2023): age is 1180 days = 3.230 years > 3 (EXPIRED)
    Because interpretations differ across the validity boundary, result must remain REVIEW.
    """
    candidates = get_date_ambiguity_candidates("02/06/2023")
    assert len(candidates) == 2
    assert date(2023, 6, 2) in candidates
    assert date(2023, 2, 6) in candidates

    field = ExtractedField(
        field_name="issue_date",
        raw_value="02/06/2023",
        extraction_method="NATIVE_VECTOR",
        candidate_count=1,
        evidence_state=EvidenceState.AMBIGUOUS,
        is_uncertain=True,
        uncertainty_reason="Date format ambiguity (DD/MM vs MM/DD)",
    )
    is_inv = is_expiration_date_invariant_pass(field, audit_date=date(2026, 5, 1), validity_years=3)
    assert is_inv is False, "Boundary date where one interpretation is expired must not be promoted"


# ---------------------------------------------------------------------------
# Test 7: Configured policy responsiveness (No hardcoded year threshold)
# ---------------------------------------------------------------------------

def test_configured_policy_responsiveness_no_hardcoded_year():
    """
    Demonstrate that changing income_cert_validity_years or audit_date changes the decision
    consistently with the actual rule, with no hardcoded year threshold.
    For raw_value = '10/01/2025':
    - With validity=3 years, audit_date=2026-11-13: Both candidates (1.84 and 1.12 yrs) <= 3 -> Invariant PASS.
    - With validity=1 year, audit_date=2026-11-13: Both candidates > 1 yr -> Not promoted (False).
    - With validity=1 year, audit_date=2025-05-01: Candidate Oct 1 2025 is in future (age < 0) -> Not promoted (False).
    """
    field = ExtractedField(
        field_name="issue_date",
        raw_value="10/01/2025",
        extraction_method="NATIVE_VECTOR",
        candidate_count=1,
        evidence_state=EvidenceState.AMBIGUOUS,
        is_uncertain=True,
        uncertainty_reason="Date format ambiguity (DD/MM vs MM/DD)",
    )

    # 1. 3-year validity at 2026-11-13: both valid
    assert is_expiration_date_invariant_pass(field, audit_date=date(2026, 11, 13), validity_years=3) is True

    # 2. 1-year validity at 2026-11-13: both expired
    assert is_expiration_date_invariant_pass(field, audit_date=date(2026, 11, 13), validity_years=1) is False

    # 3. 1-year validity at 2025-05-01: Oct 1 2025 is future date
    assert is_expiration_date_invariant_pass(field, audit_date=date(2025, 5, 1), validity_years=1) is False

    # 4. None audit_date or validity_years: fail-closed False
    assert is_expiration_date_invariant_pass(field, audit_date=None, validity_years=3) is False
    assert is_expiration_date_invariant_pass(field, audit_date=date(2026, 11, 13), validity_years=None) is False


# ---------------------------------------------------------------------------
# Test 8: Two-digit year handling agreement with parser (68, 69, 70)
# ---------------------------------------------------------------------------

def test_two_digit_year_candidate_agreement_with_parser():
    """
    Verifies that get_date_ambiguity_candidates matches the century interpretation
    used by parse_and_normalize_date for boundary years 68, 69, and 70:
    - 68 -> 2068
    - 69 -> 1969
    - 70 -> 1970
    The helper must never infer candidate dates that disagree with the parser.
    """
    for y_str in ("68", "69", "70"):
        date_str = f"10/01/{y_str}"
        dt, status, amb = parse_and_normalize_date(date_str)
        assert status == "VALID"
        assert amb is True

        candidates = get_date_ambiguity_candidates(date_str)
        assert len(candidates) == 2, f"Failed to get 2 candidates for {date_str}"

        # Every candidate must share the exact century/year of the parser
        for c in candidates:
            assert c.year == dt.year, f"Year mismatch for {y_str}: candidate={c.year}, parser={dt.year}"

        if y_str == "68":
            assert dt.year == 2068
            assert date(2068, 1, 10) in candidates
            assert date(2068, 10, 1) in candidates
        elif y_str == "69":
            assert dt.year == 1969
            assert date(1969, 1, 10) in candidates
            assert date(1969, 10, 1) in candidates
        elif y_str == "70":
            assert dt.year == 1970
            assert date(1970, 1, 10) in candidates
            assert date(1970, 10, 1) in candidates


# ---------------------------------------------------------------------------
# Test 9: Dedicated Invariant FAIL integration regression
# ---------------------------------------------------------------------------

def test_invariant_fail_integration_regression():
    """
    Dedicated integration regression for a native-vector ambiguous issue date
    where both interpretations are expired:
    - Date: 10/01/2020 on income_cert.pdf
    - Audit date: 2026-11-13, validity: 3 years.
    - Candidate 1 (10 Jan 2020): age 6.84 yrs > 3 yrs (expired)
    - Candidate 2 (01 Oct 2020): age 6.12 yrs > 3 yrs (expired)
    Both interpretations are expired -> invariant FAIL.
    Must assert:
    - Finding rule_id == 'RULE-EXP-01'
    - raw_result == Raw.VIOLATED
    - status == Status.FAIL
    - reason_code == ReasonCode.DEFECT_CONFIRMED.value
    - packet readiness == Readiness.NOT_READY
    """
    field = ExtractedField(
        field_name="issue_date",
        raw_value="10/01/2020",
        normalized_value="2020-01-10",
        extraction_method=ExtractionMethod.NATIVE_VECTOR,
        candidate_count=1,
        evidence_state=EvidenceState.AMBIGUOUS,
        is_uncertain=True,
        uncertainty_reason="Date format ambiguity (DD/MM vs MM/DD)",
    )
    doc = ExtractedDocument(
        doc_type=DocumentType.INCOME_CERT,
        file_path="income_cert.pdf",
        extraction_method=ExtractionMethod.NATIVE_VECTOR,
        fields={"issue_date": field},
    )
    finding = Finding(
        rule_id="RULE-EXP-01",
        rule_name="Income certificate validity",
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
                extraction_method=ExtractionMethod.NATIVE_VECTOR,
            )
        ],
        remediation="Obtain a valid income certificate issued within the last 3 years.",
        statutory_reference="Odisha Misc Cert Rules 2019, Rule 8(2)",
    )

    scheme = SchemeConfig(income_cert_validity_years=3)
    safety = DecisionSafetyLayer()

    # Step 1: helper function verification
    assert is_expiration_date_invariant_fail(field, audit_date=date(2026, 11, 13), validity_years=3) is True
    assert is_expiration_date_invariant_pass(field, audit_date=date(2026, 11, 13), validity_years=3) is False

    # Step 2: audit findings
    audited = safety.audit_findings(
        [finding],
        {DocumentType.INCOME_CERT: doc},
        scheme_name="Test Scheme",
        scheme_config=scheme,
        audit_date=date(2026, 11, 13),
    )

    assert len(audited) == 1
    f = audited[0]

    # Explicit assertions per Section 4:
    assert f.rule_id == "RULE-EXP-01"
    assert f.raw_result == Raw.VIOLATED
    assert f.status == Status.FAIL
    assert f.reason_code == ReasonCode.DEFECT_CONFIRMED.value

    # Step 3: packet readiness
    audit_res = AuditResult(
        packet_id="PKT_INVARIANT_EXPIRED",
        scheme_name="Test Scheme",
        readiness_score=75,
        overall_status="ACTION_REQUIRED",
        findings=audited,
        summary_counts={"FAIL": 1},
        execution_time_ms=1.0,
        timestamp="2026-11-15T00:00:00",
    )
    assert audit_res.readiness == Readiness.NOT_READY
