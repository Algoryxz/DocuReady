"""Canonical V2 domain vocabulary for findings, evidence, and packet readiness.

The legacy evidence-state values are retained temporarily because extraction
components still emit them. The resolver normalizes those values to the three
V2 evidence states; this keeps the migration explicit and fail-closed.
"""

from enum import Enum, IntEnum
from typing import Optional


class Status(str, Enum):
    """Canonical V2 finding status."""

    FAIL = "FAIL"
    WARN = "WARN"
    REVIEW = "REVIEW"
    PASS = "PASS"
    MISSING = "MISSING"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class Raw(str, Enum):
    """Raw rule evaluation before evidence-aware resolution."""

    SATISFIED = "SATISFIED"
    VIOLATED = "VIOLATED"
    INDETERMINATE = "INDETERMINATE"
    DOC_ABSENT = "DOC_ABSENT"
    EXEMPT = "EXEMPT"


class EvidenceState(str, Enum):
    """Evidence certainty states plus transitional extractor values.

    VERIFIED means the value is sufficiently supported for a deterministic
    rule decision. It does not mean that an issuing authority or certificate
    has been legally authenticated.
    """

    VERIFIED = "VERIFIED"
    PROVISIONAL = "PROVISIONAL"
    UNCERTAIN = "UNCERTAIN"

    # Transitional extraction values. These are normalized by the resolver.
    VERIFIED_TEXT = "VERIFIED_TEXT"
    OCR_EXTRACTED = "OCR_EXTRACTED"
    AMBIGUOUS = "AMBIGUOUS"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    NOT_FOUND = "NOT_FOUND"
    UNREADABLE = "UNREADABLE"
    CONFLICTING = "CONFLICTING"


class MatchGrade(str, Enum):
    """Optional match-quality constraint consumed by the resolver."""

    EXACT = "EXACT"
    COMPATIBLE = "COMPATIBLE"
    CONFLICT = "CONFLICT"
    AMBIGUOUS = "AMBIGUOUS"


class MaxSeverity(str, Enum):
    """Highest adverse status a rule is permitted to emit."""

    FAIL = "FAIL"
    WARN = "WARN"
    REVIEW = "REVIEW"


class ReasonCode(str, Enum):
    DEFECT_CONFIRMED = "DEFECT_CONFIRMED"
    DEFECT_PROBABLE = "DEFECT_PROBABLE"
    EVIDENCE_UNCERTAIN = "EVIDENCE_UNCERTAIN"
    CONFIRMED_OK = "CONFIRMED_OK"
    CANNOT_CONFIRM = "CANNOT_CONFIRM"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    DOC_ABSENT = "DOC_ABSENT"
    ADVISORY_RULE_CAP = "ADVISORY_RULE_CAP"


class Readiness(str, Enum):
    """Packet-level result derived solely from resolved finding statuses."""

    NOT_READY = "NOT_READY"
    NEEDS_CHECKS = "NEEDS_CHECKS"
    NO_ISSUES_FOUND = "NO_ISSUES_FOUND"


class ExitCode(IntEnum):
    NO_ISSUES = 0
    NEEDS_CHECKS = 1
    NOT_READY = 2
    USAGE_ERROR = 64


def normalize_evidence_state(
    evidence_state: Optional[EvidenceState],
) -> EvidenceState:
    """Map legacy extractor states to the canonical V2 evidence vocabulary.

    Unknown or absent evidence is treated as UNCERTAIN, never VERIFIED.
    """
    if evidence_state is None:
        return EvidenceState.UNCERTAIN

    try:
        state = EvidenceState(evidence_state)
    except (TypeError, ValueError):
        return EvidenceState.UNCERTAIN

    if state in (EvidenceState.VERIFIED, EvidenceState.VERIFIED_TEXT):
        return EvidenceState.VERIFIED
    if state in (EvidenceState.PROVISIONAL, EvidenceState.OCR_EXTRACTED):
        return EvidenceState.PROVISIONAL
    return EvidenceState.UNCERTAIN
