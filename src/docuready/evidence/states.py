"""Canonical tri-state evidence discretization helpers."""

from __future__ import annotations

from docuready.domain.enums import EvidenceState, normalize_evidence_state


def discretize_probability(
    calibrated_prob: float,
    *,
    verified_threshold: float = 0.85,
    provisional_threshold: float = 0.60,
    is_ambiguous: bool = False,
) -> EvidenceState:
    """Map calibrated probability P(Correct | x) to canonical EvidenceState.

    Lifecycle: VERIFIED -> PROVISIONAL -> UNCERTAIN.
    Ambiguous extractions always fail closed to UNCERTAIN.
    """
    if is_ambiguous or calibrated_prob < provisional_threshold:
        return EvidenceState.UNCERTAIN
    if calibrated_prob >= verified_threshold:
        return EvidenceState.VERIFIED
    return EvidenceState.PROVISIONAL


def to_canonical_state(state: EvidenceState) -> EvidenceState:
    """Normalize transitional extractor states into canonical V2 EvidenceState."""
    return normalize_evidence_state(state)
