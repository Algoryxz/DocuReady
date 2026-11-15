"""Pure V2 resolver for evidence-calibrated finding outcomes."""

from dataclasses import dataclass
from typing import Iterable, Optional, Union

from docuready.domain.enums import (
    EvidenceState,
    ExitCode,
    MatchGrade,
    MaxSeverity,
    Raw,
    Readiness,
    ReasonCode,
    Status,
    normalize_evidence_state,
)


@dataclass(frozen=True)
class ResolvedOutcome:
    """Immutable result of resolving one raw rule result."""

    status: Status
    reason_code: str
    message: str


def _coerce_enum(value, enum_type, field_name):
    if isinstance(value, enum_type):
        return value
    try:
        return enum_type(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Unsupported {field_name}: {value!r}") from exc


def resolve_outcome(
    raw: Raw,
    weakest_evidence: Optional[EvidenceState],
    max_severity: Optional[MaxSeverity] = None,
    match_grade: Optional[MatchGrade] = None,
    exemption_reason: Optional[str] = None,
    slot_mismatch: bool = False,
) -> ResolvedOutcome:
    """Resolve a raw result using the V2 Section 6 truth table.

    Missing evidence fails closed to UNCERTAIN. DOC_ABSENT and EXEMPT are
    structural outcomes and do not require extracted evidence. Severity caps
    constrain adverse rule findings; they do not turn a missing mandatory
    document into a pass.
    """
    raw = _coerce_enum(raw, Raw, "raw result")

    if raw is Raw.DOC_ABSENT:
        return ResolvedOutcome(
            Status.MISSING,
            ReasonCode.DOC_ABSENT.value,
            "A required document is absent from the packet.",
        )

    if raw is Raw.EXEMPT:
        reason = (exemption_reason or "CATEGORY_EXEMPTION").strip()
        safe_reason = reason.upper().replace(" ", "_") or "CATEGORY_EXEMPTION"
        return ResolvedOutcome(
            Status.NOT_APPLICABLE,
            f"EXEMPT:{safe_reason}",
            "This rule does not apply to the supplied applicant category.",
        )

    if slot_mismatch:
        evidence = normalize_evidence_state(weakest_evidence)
        if raw is Raw.VIOLATED and evidence is EvidenceState.VERIFIED:
            return ResolvedOutcome(
                Status.REVIEW,
                ReasonCode.WRONG_DOCUMENT_TYPE.value,
                "The uploaded document does not match the required document slot.",
            )
        return ResolvedOutcome(
            Status.REVIEW,
            ReasonCode.EVIDENCE_UNCERTAIN.value,
            "The uploaded document could not be verified for this slot.",
        )

    if raw is Raw.INDETERMINATE:
        return ResolvedOutcome(
            Status.REVIEW,
            ReasonCode.INSUFFICIENT_DATA.value,
            "There is insufficient or ambiguous evidence to resolve this rule.",
        )

    evidence = normalize_evidence_state(weakest_evidence)
    grade = None if match_grade is None else _coerce_enum(
        match_grade, MatchGrade, "match grade"
    )
    cap = None if max_severity is None else _coerce_enum(
        max_severity, MaxSeverity, "maximum severity"
    )

    # Ambiguity overrides either apparent agreement or disagreement.
    if grade is MatchGrade.AMBIGUOUS:
        return ResolvedOutcome(
            Status.REVIEW,
            ReasonCode.EVIDENCE_UNCERTAIN.value,
            "The match is ambiguous and requires human review.",
        )

    if raw is Raw.VIOLATED:
        if evidence is EvidenceState.VERIFIED:
            status = Status.FAIL
            reason_code = ReasonCode.DEFECT_CONFIRMED.value
            message = "A discrepancy is supported by verified evidence."
        elif evidence is EvidenceState.PROVISIONAL:
            status = Status.WARN
            reason_code = ReasonCode.DEFECT_PROBABLE.value
            message = "A discrepancy is probable on provisional evidence; re-check the source."
        else:
            status = Status.REVIEW
            reason_code = ReasonCode.EVIDENCE_UNCERTAIN.value
            message = "A discrepancy is indicated, but the evidence is uncertain."

        # A compatible match cannot produce a hard failure.
        if grade is MatchGrade.COMPATIBLE and status is Status.FAIL:
            status = Status.WARN
            reason_code = ReasonCode.DEFECT_PROBABLE.value
            message = "A compatible variation requires checking; it is not a confirmed defect."

    elif raw is Raw.SATISFIED:
        if grade is MatchGrade.CONFLICT:
            # Contradictory raw and match-grade inputs are an inconsistent
            # evaluation record. Fail closed instead of turning it into PASS.
            status = Status.REVIEW
            reason_code = ReasonCode.EVIDENCE_UNCERTAIN.value
            message = "The raw result conflicts with the match grade; human review is required."
        elif grade is MatchGrade.COMPATIBLE:
            if evidence is EvidenceState.VERIFIED:
                status = Status.WARN
                reason_code = ReasonCode.DEFECT_PROBABLE.value
                message = "A compatible variation was found; check the difference before relying on this match."
            else:
                status = Status.REVIEW
                reason_code = ReasonCode.CANNOT_CONFIRM.value
                message = "A compatible variation is present, but its evidence is not strong enough to confirm."
        elif evidence is EvidenceState.VERIFIED:
            status = Status.PASS
            reason_code = ReasonCode.CONFIRMED_OK.value
            message = "No issue was found on verified evidence."
        else:
            status = Status.REVIEW
            reason_code = ReasonCode.CANNOT_CONFIRM.value
            message = "The check appears satisfied, but the evidence is not strong enough to confirm it."

    else:
        # Defensive branch for future enum additions.
        return ResolvedOutcome(
            Status.REVIEW,
            ReasonCode.INSUFFICIENT_DATA.value,
            "The rule result could not be resolved safely.",
        )

    # Apply a pack-level cap after evidence and match-grade constraints.
    # The cap may only make the result less severe, never more severe.
    if cap is MaxSeverity.WARN and status is Status.FAIL:
        status = Status.WARN
        reason_code = ReasonCode.ADVISORY_RULE_CAP.value
        message = "The finding is capped at WARN by the rule's maximum severity."
    elif cap is MaxSeverity.REVIEW and status in (Status.FAIL, Status.WARN):
        status = Status.REVIEW
        reason_code = ReasonCode.ADVISORY_RULE_CAP.value
        message = "The finding is capped at REVIEW by the rule's maximum severity."

    return ResolvedOutcome(status, reason_code, message)



def resolve_readiness(statuses: Iterable[Union[Status, str]]) -> Readiness:
    """Derive packet readiness from the complete set of finding statuses.

    NOT_APPLICABLE findings are visible but do not affect readiness. An empty
    result set, or a set containing only NOT_APPLICABLE findings, returns
    NEEDS_CHECKS rather than a false-green NO_ISSUES_FOUND.
    """
    normalized = []
    for value in statuses:
        normalized.append(_coerce_enum(value, Status, "finding status"))

    if any(value in (Status.FAIL, Status.MISSING) for value in normalized):
        return Readiness.NOT_READY
    if any(value in (Status.WARN, Status.REVIEW) for value in normalized):
        return Readiness.NEEDS_CHECKS

    applicable = [value for value in normalized if value is not Status.NOT_APPLICABLE]
    if not applicable:
        return Readiness.NEEDS_CHECKS
    if all(value is Status.PASS for value in applicable):
        return Readiness.NO_ISSUES_FOUND
    return Readiness.NEEDS_CHECKS

def weakest_evidence(states: Iterable[Optional[EvidenceState]]) -> Optional[EvidenceState]:
    """Return the least certain normalized evidence state, or None if empty."""
    normalized = [normalize_evidence_state(state) for state in states]
    if not normalized:
        return None
    if EvidenceState.UNCERTAIN in normalized:
        return EvidenceState.UNCERTAIN
    if EvidenceState.PROVISIONAL in normalized:
        return EvidenceState.PROVISIONAL
    return EvidenceState.VERIFIED


def exit_code_for_readiness(readiness: Readiness) -> ExitCode:
    """Map packet readiness to the stable public CLI contract."""
    readiness = _coerce_enum(readiness, Readiness, "readiness")
    return {
        Readiness.NO_ISSUES_FOUND: ExitCode.NO_ISSUES,
        Readiness.NEEDS_CHECKS: ExitCode.NEEDS_CHECKS,
        Readiness.NOT_READY: ExitCode.NOT_READY,
    }[readiness]
