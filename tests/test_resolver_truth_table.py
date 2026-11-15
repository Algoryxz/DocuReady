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


def test_compatible_cannot_cause_hard_fail():
    """Verify that match_grade COMPATIBLE cannot cause a hard FAIL under any combination."""
    from itertools import product
    for raw, evidence, cap in product(Raw, EvidenceState, [None, *list(MaxSeverity)]):
        outcome = resolve_outcome(
            raw,
            weakest_evidence=evidence,
            max_severity=cap,
            match_grade=MatchGrade.COMPATIBLE,
        )
        assert outcome.status is not Status.FAIL, (raw, evidence, cap, outcome)


def test_ambiguous_grade_or_evidence_forces_review():
    """Verify that AMBIGUOUS match grade or evidence state forces Status.REVIEW."""
    from itertools import product
    # AMBIGUOUS match grade forces REVIEW on non-absent/non-exempt findings
    for raw in (Raw.SATISFIED, Raw.VIOLATED, Raw.INDETERMINATE):
        for evidence in EvidenceState:
            for cap in [None, *list(MaxSeverity)]:
                outcome = resolve_outcome(
                    raw,
                    weakest_evidence=evidence,
                    max_severity=cap,
                    match_grade=MatchGrade.AMBIGUOUS,
                )
                assert outcome.status is Status.REVIEW, (raw, evidence, cap, outcome)

    # AMBIGUOUS evidence state forces REVIEW on non-absent/non-exempt findings
    for raw in (Raw.SATISFIED, Raw.VIOLATED, Raw.INDETERMINATE):
        for grade in [None, *list(MatchGrade)]:
            for cap in [None, *list(MaxSeverity)]:
                outcome = resolve_outcome(
                    raw,
                    weakest_evidence=EvidenceState.AMBIGUOUS,
                    max_severity=cap,
                    match_grade=grade,
                )
                assert outcome.status is Status.REVIEW, (raw, grade, cap, outcome)


def test_max_severity_only_reduces_severity():
    """Verify that max_severity cap only reduces or preserves severity, never increases it."""
    from itertools import product
    severity_order = {
        Status.PASS: 0,
        Status.NOT_APPLICABLE: 0,
        Status.REVIEW: 1,
        Status.WARN: 2,
        Status.MISSING: 3,
        Status.FAIL: 3,
    }
    for raw, evidence, grade in product(Raw, EvidenceState, [None, *list(MatchGrade)]):
        base_outcome = resolve_outcome(raw, weakest_evidence=evidence, max_severity=None, match_grade=grade)
        base_rank = severity_order[base_outcome.status]
        for cap in MaxSeverity:
            capped_outcome = resolve_outcome(raw, weakest_evidence=evidence, max_severity=cap, match_grade=grade)
            capped_rank = severity_order[capped_outcome.status]
            assert capped_rank <= base_rank, (
                f"max_severity {cap} increased severity from {base_outcome.status} to {capped_outcome.status}"
            )


def test_not_applicable_findings_remain_visible():
    """Verify that all NOT_APPLICABLE findings remain visible in reports and public projections."""
    from docuready.domain.models import Finding, FindingStatus, Severity, AuditResult
    finding = Finding(
        rule_id="RULE-MRK-RELAX-PASS",
        rule_name="Marksheet category relaxation",
        status=FindingStatus.PASS,
        severity=Severity.INFO,
        field="CATEGORY_RELAXATION",
        documents_involved=["marksheet.pdf"],
        message="Exempt from minimum percentage cutoffs.",
        remediation="No action required.",
        statutory_reference="Scheme Guidelines",
    )
    finding.set_resolution(Raw.EXEMPT, Status.NOT_APPLICABLE, "EXEMPT:CATEGORY_EXEMPTION")
    result = AuditResult(
        packet_id="TEST_EXEMPT",
        scheme_name="Test Scheme",
        readiness_score=100,
        overall_status="NO_ISSUES_FOUND",
        findings=[finding],
        summary_counts={"NOT_APPLICABLE": 1},
        execution_time_ms=0.0,
        timestamp="2026-11-15T00:00:00",
    )
    assert len(result.findings) == 1
    assert result.findings[0].status is Status.NOT_APPLICABLE
    public = result.to_public_dict()
    assert len(public["findings"]) == 1
    assert public["findings"][0]["status"] == "NOT_APPLICABLE"


def test_public_output_never_emits_prohibited_terms():
    """Verify that public projection never emits 'eligible', 'approved', or 'ready to submit'."""
    from docuready.domain.models import Finding, FindingStatus, Severity, AuditResult
    finding = Finding(
        rule_id="RULE-TEST-01",
        rule_name="Test Rule",
        status=FindingStatus.PASS,
        severity=Severity.INFO,
        field="TEST",
        documents_involved=["test.pdf"],
        message="Test message",
        remediation="No action required.",
        statutory_reference="Ref",
    )
    finding.set_resolution(Raw.SATISFIED, Status.PASS, ReasonCode.CONFIRMED_OK.value)
    result = AuditResult(
        packet_id="TEST_CLEAN",
        scheme_name="Test Scheme",
        readiness_score=100,
        overall_status="READY_TO_SUBMIT",
        findings=[finding],
        summary_counts={"PASS": 1},
        execution_time_ms=0.0,
        timestamp="2026-11-15T00:00:00",
    )
    public = result.to_public_dict()
    public_str = str(public).lower()
    for prohibited in ("eligible", "approved", "ready to submit"):
        assert prohibited not in public_str, f"Found prohibited term '{prohibited}' in public output"


def test_cli_exit_codes_comprehensive():
    """Verify that CLI exit codes are 0, 1, 2, and 64 for usage errors."""
    from docuready.domain.enums import ExitCode, Readiness
    from docuready.outcome.resolver import exit_code_for_readiness
    assert int(exit_code_for_readiness(Readiness.NO_ISSUES_FOUND)) == 0
    assert int(exit_code_for_readiness(Readiness.NEEDS_CHECKS)) == 1
    assert int(exit_code_for_readiness(Readiness.NOT_READY)) == 2
    assert int(ExitCode.USAGE_ERROR) == 64
