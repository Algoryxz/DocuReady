"""Finite-domain property checks for resolver invariants.

The input space is small and explicitly enumerated, so these tests exercise
every supported evidence state, match grade, and severity cap without adding
a new runtime or test dependency.
"""

from itertools import product

from docuready.domain.enums import (
    EvidenceState,
    MatchGrade,
    MaxSeverity,
    Raw,
    Readiness,
    Status,
)
from docuready.outcome.resolver import resolve_outcome, resolve_readiness


def test_satisfied_non_verified_evidence_never_resolves_to_pass():
    caps = [None, *list(MaxSeverity)]
    grades = [None, *list(MatchGrade)]
    for evidence, cap, grade in product(EvidenceState, caps, grades):
        if evidence in (EvidenceState.VERIFIED, EvidenceState.VERIFIED_TEXT):
            continue
        outcome = resolve_outcome(
            Raw.SATISFIED,
            weakest_evidence=evidence,
            max_severity=cap,
            match_grade=grade,
        )
        assert outcome.status is not Status.PASS, (
            evidence, cap, grade, outcome
        )
        assert outcome.status is Status.REVIEW


def test_uncertain_or_absent_evidence_never_confirms_a_violation():
    for evidence in (
        None,
        EvidenceState.UNCERTAIN,
        EvidenceState.AMBIGUOUS,
        EvidenceState.LOW_CONFIDENCE,
        EvidenceState.NOT_FOUND,
        EvidenceState.UNREADABLE,
        EvidenceState.CONFLICTING,
    ):
        outcome = resolve_outcome(Raw.VIOLATED, weakest_evidence=evidence)
        assert outcome.status is Status.REVIEW


def test_readiness_precedence_for_all_status_combinations():
    statuses = list(Status)
    for combination in product(statuses, repeat=3):
        readiness = resolve_readiness(combination)
        if any(s in (Status.FAIL, Status.MISSING) for s in combination):
            assert readiness is Readiness.NOT_READY
        elif any(s in (Status.WARN, Status.REVIEW) for s in combination):
            assert readiness is Readiness.NEEDS_CHECKS
        elif all(s is Status.NOT_APPLICABLE for s in combination):
            assert readiness is Readiness.NEEDS_CHECKS
        else:
            assert readiness is Readiness.NO_ISSUES_FOUND


def test_cli_exit_codes_follow_packet_readiness():
    from docuready.domain.enums import ExitCode
    from docuready.outcome.resolver import exit_code_for_readiness

    assert exit_code_for_readiness(Readiness.NO_ISSUES_FOUND) is ExitCode.NO_ISSUES
    assert exit_code_for_readiness(Readiness.NEEDS_CHECKS) is ExitCode.NEEDS_CHECKS
    assert exit_code_for_readiness(Readiness.NOT_READY) is ExitCode.NOT_READY
