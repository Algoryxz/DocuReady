"""Truth-table checks for the V2 outcome resolver (ARCHITECTURE_V2 §6)."""

import pytest

from docuready.domain.enums import (
    EvidenceState,
    MatchGrade,
    MaxSeverity,
    Raw,
    ReasonCode,
    Status,
)
from docuready.outcome.resolver import resolve_outcome, resolve_readiness
from docuready.domain.enums import Readiness


@pytest.mark.parametrize(
    "raw,evidence,cap,grade,expected_status,expected_reason",
    [
        (Raw.VIOLATED, EvidenceState.VERIFIED, None, None, Status.FAIL, ReasonCode.DEFECT_CONFIRMED.value),
        (Raw.VIOLATED, EvidenceState.PROVISIONAL, None, None, Status.WARN, ReasonCode.DEFECT_PROBABLE.value),
        (Raw.VIOLATED, EvidenceState.UNCERTAIN, None, None, Status.REVIEW, ReasonCode.EVIDENCE_UNCERTAIN.value),
        (Raw.VIOLATED, None, None, None, Status.REVIEW, ReasonCode.EVIDENCE_UNCERTAIN.value),
        (Raw.SATISFIED, EvidenceState.VERIFIED, None, None, Status.PASS, ReasonCode.CONFIRMED_OK.value),
        (Raw.SATISFIED, EvidenceState.PROVISIONAL, None, None, Status.REVIEW, ReasonCode.CANNOT_CONFIRM.value),
        (Raw.SATISFIED, EvidenceState.UNCERTAIN, None, None, Status.REVIEW, ReasonCode.CANNOT_CONFIRM.value),
        (Raw.INDETERMINATE, EvidenceState.VERIFIED, None, None, Status.REVIEW, ReasonCode.INSUFFICIENT_DATA.value),
        (Raw.DOC_ABSENT, None, None, None, Status.MISSING, ReasonCode.DOC_ABSENT.value),
        (Raw.EXEMPT, None, None, None, Status.NOT_APPLICABLE, "EXEMPT:CATEGORY_EXEMPTION"),
        (Raw.VIOLATED, EvidenceState.VERIFIED, None, MatchGrade.COMPATIBLE, Status.WARN, ReasonCode.DEFECT_PROBABLE.value),
        (Raw.VIOLATED, EvidenceState.VERIFIED, MaxSeverity.WARN, None, Status.WARN, ReasonCode.ADVISORY_RULE_CAP.value),
        (Raw.VIOLATED, EvidenceState.PROVISIONAL, MaxSeverity.REVIEW, None, Status.REVIEW, ReasonCode.ADVISORY_RULE_CAP.value),
        (Raw.VIOLATED, EvidenceState.VERIFIED, None, MatchGrade.AMBIGUOUS, Status.REVIEW, ReasonCode.EVIDENCE_UNCERTAIN.value),
        (Raw.SATISFIED, EvidenceState.VERIFIED, None, MatchGrade.COMPATIBLE, Status.WARN, ReasonCode.DEFECT_PROBABLE.value),
        (Raw.SATISFIED, EvidenceState.PROVISIONAL, None, MatchGrade.COMPATIBLE, Status.REVIEW, ReasonCode.CANNOT_CONFIRM.value),
        (Raw.SATISFIED, EvidenceState.VERIFIED, None, MatchGrade.CONFLICT, Status.REVIEW, ReasonCode.EVIDENCE_UNCERTAIN.value),
        (Raw.SATISFIED, EvidenceState.VERIFIED, MaxSeverity.REVIEW, MatchGrade.COMPATIBLE, Status.REVIEW, ReasonCode.ADVISORY_RULE_CAP.value),
    ],
)
def test_resolver_truth_table(
    raw, evidence, cap, grade, expected_status, expected_reason
):
    outcome = resolve_outcome(
        raw,
        weakest_evidence=evidence,
        max_severity=cap,
        match_grade=grade,
    )
    assert outcome.status is expected_status
    assert outcome.reason_code == expected_reason


@pytest.mark.parametrize(
    "legacy,canonical",
    [
        (EvidenceState.VERIFIED_TEXT, EvidenceState.VERIFIED),
        (EvidenceState.OCR_EXTRACTED, EvidenceState.PROVISIONAL),
        (EvidenceState.AMBIGUOUS, EvidenceState.UNCERTAIN),
        (EvidenceState.LOW_CONFIDENCE, EvidenceState.UNCERTAIN),
        (EvidenceState.NOT_FOUND, EvidenceState.UNCERTAIN),
        (EvidenceState.UNREADABLE, EvidenceState.UNCERTAIN),
        (EvidenceState.CONFLICTING, EvidenceState.UNCERTAIN),
    ],
)
def test_legacy_evidence_values_normalize_explicitly(legacy, canonical):
    from docuready.domain.enums import normalize_evidence_state

    assert normalize_evidence_state(legacy) is canonical


@pytest.mark.parametrize(
    "statuses,expected",
    [
        ([Status.PASS], Readiness.NO_ISSUES_FOUND),
        ([Status.PASS, Status.NOT_APPLICABLE], Readiness.NO_ISSUES_FOUND),
        ([Status.REVIEW], Readiness.NEEDS_CHECKS),
        ([Status.WARN, Status.PASS], Readiness.NEEDS_CHECKS),
        ([Status.FAIL, Status.REVIEW], Readiness.NOT_READY),
        ([Status.MISSING], Readiness.NOT_READY),
        ([Status.NOT_APPLICABLE], Readiness.NEEDS_CHECKS),
        ([], Readiness.NEEDS_CHECKS),
    ],
)
def test_packet_readiness(statuses, expected):
    assert resolve_readiness(statuses) is expected


def test_readiness_enum_canonical_equality_and_hashing():
    """Verify standard enum equality, value comparison, and hashing contract (T2.1 Phase 1)."""
    assert Readiness.NOT_READY == Readiness.NOT_READY
    assert Readiness.NOT_READY == "NOT_READY"
    assert Readiness.NOT_READY != Readiness.NEEDS_CHECKS
    assert Readiness.NOT_READY != Readiness.NO_ISSUES_FOUND
    assert Readiness.NEEDS_CHECKS == "NEEDS_CHECKS"
    assert Readiness.NO_ISSUES_FOUND == "NO_ISSUES_FOUND"

    # Hashing and set membership
    s = {Readiness.NOT_READY, Readiness.NEEDS_CHECKS, Readiness.NO_ISSUES_FOUND}
    assert len(s) == 3
    assert Readiness.NOT_READY in s
    assert hash(Readiness.NOT_READY) == hash("NOT_READY")

    # Dict key behavior for str Enum
    d = {Readiness.NOT_READY: 1, Readiness.NEEDS_CHECKS: 2}
    assert d[Readiness.NOT_READY] == 1
    assert d["NOT_READY"] == 1


def test_readiness_enum_rejects_legacy_string_alias_equality():
    """Verify that canonical V2 Readiness enum does not consider legacy status strings equal."""
    # Legacy strings must not be equal to canonical V2 enum members
    assert Readiness.NO_ISSUES_FOUND != "READY_TO_SUBMIT"
    assert Readiness.NEEDS_CHECKS != "REVIEW_RECOMMENDED"
    assert Readiness.NEEDS_CHECKS != "UNREADABLE_PACKET"
    assert Readiness.NOT_READY != "ACTION_REQUIRED"
    assert Readiness.NOT_READY != "REJECT_PRECHECK"
    assert "READY_TO_SUBMIT" != Readiness.NO_ISSUES_FOUND
    assert "ACTION_REQUIRED" != Readiness.NOT_READY
