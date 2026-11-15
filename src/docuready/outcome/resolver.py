"""Pure V2 resolver for evidence-calibrated finding outcomes."""

from dataclasses import dataclass
from typing import Iterable, Optional, Union

from docuready.domain.enums import (
    EvidenceState,
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

        # Apply the pack-level cap only to adverse outcomes. A cap may lower
        # severity, but must never promote REVIEW/WARN to a more severe status.
        if cap is MaxSeverity.WARN and status is Status.FAIL:
            status = Status.WARN
            reason_code = ReasonCode.ADVISORY_RULE_CAP.value
            message = "The finding is capped at WARN by the rule's maximum severity."
        elif cap is MaxSeverity.REVIEW and status in (Status.FAIL, Status.WARN):
            status = Status.REVIEW
            reason_code = ReasonCode.ADVISORY_RULE_CAP.value
            message = "The finding is capped at REVIEW by the rule's maximum severity."

        return ResolvedOutcome(status, reason_code, message)

    if raw is Raw.SATISFIED:
        if evidence is EvidenceState.VERIFIED and grade is not MatchGrade.AMBIGUOUS:
            return ResolvedOutcome(
                Status.PASS,
                ReasonCode.CONFIRMED_OK.value,
                "No issue was found on verified evidence.",
            )
        return ResolvedOutcome(
            Status.REVIEW,
            ReasonCode.CANNOT_CONFIRM.value,
            "The check appears satisfied, but the evidence is not strong enough to confirm it.",
        )

    # Defensive branch for future enum additions.
    return ResolvedOutcome(
        Status.REVIEW,
        ReasonCode.INSUFFICIENT_DATA.value,
        "The rule result could not be resolved safely.",
    )


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
