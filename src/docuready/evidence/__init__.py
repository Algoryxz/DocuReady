"""Evidence provenance, 9-feature logistic calibration, and tri-state discretization."""

from docuready.evidence.calibrator import ConfidenceCalibrator, validate_field_syntax
from docuready.evidence.features import (
    FEATURE_NAMES,
    CalibrationFeatureVector,
    compute_nine_features,
)
from docuready.evidence.states import discretize_probability, to_canonical_state

__all__ = [
    "ConfidenceCalibrator",
    "validate_field_syntax",
    "FEATURE_NAMES",
    "CalibrationFeatureVector",
    "compute_nine_features",
    "discretize_probability",
    "to_canonical_state",
]
