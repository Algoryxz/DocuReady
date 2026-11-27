"""Synthetic Document Generator v2 (T4.3)."""

from eval.generators.generator_v2 import (
    ALL_LAYOUTS,
    DEV_CALIB_LAYOUTS,
    TEST_ONLY_LAYOUTS,
    PERTURBATIONS,
    NEGATIVE_CONTROLS,
    SyntheticGeneratorV2,
    generate_split_dataset,
)

__all__ = [
    "ALL_LAYOUTS",
    "DEV_CALIB_LAYOUTS",
    "TEST_ONLY_LAYOUTS",
    "PERTURBATIONS",
    "NEGATIVE_CONTROLS",
    "SyntheticGeneratorV2",
    "generate_split_dataset",
]
