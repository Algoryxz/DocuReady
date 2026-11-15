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
