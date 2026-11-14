"""
tests/test_warning_policy.py

Verifies that the package-scoped warning filter (error:::docuready.*) treats
warnings originating from docuready as test errors while preserving standard
behavior for third-party external dependencies.
"""

import warnings
import pytest


def test_docuready_internal_warning_treated_as_error():
    """
    Verifies that a warning emitted with a docuready.* module identifier
    is converted into an exception under the scoped warning policy.
    """
    with pytest.raises(UserWarning, match="DocuReady internal warning"):
        warnings.warn_explicit(
            "DocuReady internal warning",
            UserWarning,
            filename="src/docuready/example.py",
            lineno=1,
            module="docuready.example",
        )


def test_third_party_warning_not_treated_as_error():
    """
    Verifies that external third-party warnings are NOT turned into test errors,
    preventing spurious test failures from third-party libraries.
    """
    with warnings.catch_warnings(record=True) as recorded:
        warnings.warn_explicit(
            "External third-party notice",
            UserWarning,
            filename="site-packages/external/pkg.py",
            lineno=42,
            module="external.pkg",
        )
        assert len(recorded) == 1
        assert "External third-party notice" in str(recorded[0].message)
