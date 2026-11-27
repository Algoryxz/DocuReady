"""
Unit tests for Loop 3: Field-Level Confidence Calibration and Evidence States
Verifies syntax validation, multi-feature calibration scoring, and discrete evidence state transitions.
"""

import pytest
from docuready.domain.models import EvidenceState, ExtractionMethod
from docuready.evidence.calibrator import validate_field_syntax, ConfidenceCalibrator


def test_syntax_validation_applicant_name():
    # Valid names
    valid, err = validate_field_syntax("applicant_name", "Smruti Ranjan Nayak")
    assert valid is True
    assert err is None

    # Too short
    valid, err = validate_field_syntax("applicant_name", "A")
    assert valid is False
    assert "incomplete" in err.lower() or "too short" in err.lower()

    # Digits in name
    valid, err = validate_field_syntax("applicant_name", "Smruti 123")
    assert valid is False
    assert "digit" in err.lower()


def test_syntax_validation_income():
    # Valid income strings
    assert validate_field_syntax("annual_income", "Rs. 1,80,000/-")[0] is True
    assert validate_field_syntax("annual_income", "250000")[0] is True

    # Invalid income: negative or zero
    valid, err = validate_field_syntax("annual_income", "0")
    assert valid is False

    # Non-numeric
    valid, err = validate_field_syntax("annual_income", "NOT AVAILABLE")
    assert valid is False


def test_syntax_validation_ifsc():
    # Valid RBI IFSC (SBIN0001234: 4 letters, '0', 6 alphanumeric)
    assert validate_field_syntax("ifsc", "SBIN0001234")[0] is True
    assert validate_field_syntax("ifsc", "HDFC0000128")[0] is True

    # Invalid: 5th char not zero
    valid, err = validate_field_syntax("ifsc", "SBIN1001234")
    assert valid is False

    # Invalid length
    assert validate_field_syntax("ifsc", "SBI001")[0] is False


def test_syntax_validation_certificate_number():
    assert validate_field_syntax("certificate_no", "E-INC/2025/104928")[0] is True
    assert validate_field_syntax("certificate_no", "CST/2024/9912")[0] is True

    # No digits
    assert validate_field_syntax("certificate_no", "ABC-DEF")[0] is False
    # Too short
    assert validate_field_syntax("certificate_no", "1")[0] is False


def test_syntax_validation_percentage():
    assert validate_field_syntax("percentage", "78.5%")[0] is True
    assert validate_field_syntax("percentage", "100.0")[0] is True
    assert validate_field_syntax("percentage", "105.0%")[0] is False
    assert validate_field_syntax("percentage", "-5%")[0] is False


def test_calibrator_native_vector():
    cal = ConfidenceCalibrator()

    # Clean native text
    res = cal.calibrate("applicant_name", "Smruti Ranjan Nayak", ExtractionMethod.NATIVE_VECTOR)
    assert res["evidence_state"] == EvidenceState.VERIFIED_TEXT
    assert res["calibrated_confidence"] >= 0.95
    assert res["is_uncertain"] is False

    # Date ambiguity in native text
    res_date = cal.calibrate("issue_date", "10/01/2025", ExtractionMethod.NATIVE_VECTOR, page_has_date_ambiguity=True)
    assert res_date["evidence_state"] == EvidenceState.AMBIGUOUS
    assert res_date["is_uncertain"] is True


def test_calibrator_local_ocr_confidence_levels():
    cal = ConfidenceCalibrator()

    # High quality OCR: high token conf, close label, valid syntax
    res_high = cal.calibrate(
        field_name="annual_income",
        raw_value="Rs. 1,80,000/-",
        extraction_method=ExtractionMethod.LOCAL_OCR,
        token_confidence=0.92,
        label_detected=True,
        label_distance_pt=15.0,
        candidate_count=1
    )
    assert res_high["evidence_state"] == EvidenceState.OCR_EXTRACTED
    assert res_high["calibrated_confidence"] >= 0.80
    assert res_high["is_uncertain"] is False

    # Marginal / degraded OCR: low token conf (0.35)
    res_low = cal.calibrate(
        field_name="annual_income",
        raw_value="Rs. 1,80,000/-",
        extraction_method=ExtractionMethod.LOCAL_OCR,
        token_confidence=0.35,
        label_detected=True,
        label_distance_pt=20.0,
        candidate_count=1
    )
    assert res_low["evidence_state"] == EvidenceState.LOW_CONFIDENCE
    assert res_low["is_uncertain"] is True

    # Candidate multiplicity penalty: 3 competing candidates detected
    res_multi = cal.calibrate(
        field_name="certificate_no",
        raw_value="E-INC/2025/11",
        extraction_method=ExtractionMethod.LOCAL_OCR,
        token_confidence=0.85,
        label_detected=True,
        label_distance_pt=20.0,
        candidate_count=3
    )
    assert res_multi["evidence_state"] == EvidenceState.AMBIGUOUS
    assert res_multi["is_uncertain"] is True


def test_calibrator_abstention_threshold():
    cal = ConfidenceCalibrator(tau_abstain=0.45)

    # Completely unreadable noise
    res_noise = cal.calibrate(
        field_name="applicant_name",
        raw_value="##--@@",
        extraction_method=ExtractionMethod.LOCAL_OCR,
        token_confidence=0.20,
        label_detected=False,
        label_distance_pt=200.0,
        candidate_count=1
    )
    assert res_noise["calibrated_confidence"] < cal.tau_abstain
    assert res_noise["is_uncertain"] is True


def test_nine_feature_vector_and_logistic_fit():
    from docuready.evidence import (
        FEATURE_NAMES,
        compute_nine_features,
        discretize_probability,
    )

    assert len(FEATURE_NAMES) == 9

    cal = ConfidenceCalibrator()
    res = cal.calibrate(
        field_name="applicant_name",
        raw_value="Pravasini Sahoo",
        extraction_method=ExtractionMethod.LOCAL_OCR,
        token_confidence=0.90,
        label_detected=True,
        label_distance_pt=12.0,
        label_match_confidence=0.95,
        candidate_count=1,
        supporting_tokens_count=2,
        layout_consistency=0.95,
        rotation_deg=1.5,
    )
    assert set(res["features"].keys()) == set(FEATURE_NAMES)
    assert res["canonical_evidence_state"] == EvidenceState.VERIFIED

    # Test rotation degradation lowers probability
    res_skewed = cal.calibrate(
        field_name="applicant_name",
        raw_value="Pravasini Sahoo",
        extraction_method=ExtractionMethod.LOCAL_OCR,
        token_confidence=0.90,
        label_detected=True,
        label_distance_pt=12.0,
        label_match_confidence=0.95,
        candidate_count=1,
        supporting_tokens_count=2,
        layout_consistency=0.40,
        rotation_deg=15.0,
    )
    assert res_skewed["calibrated_confidence"] < res["calibrated_confidence"]

    # Test logistic fit() on synthetic calibration samples
    fv_pos = compute_nine_features(
        field_name="dob",
        extraction_method=ExtractionMethod.LOCAL_OCR,
        is_syntax_valid=True,
        token_confidence=0.95,
        supporting_tokens_count=1,
    )
    fv_neg = compute_nine_features(
        field_name="dob",
        extraction_method=ExtractionMethod.LOCAL_OCR,
        is_syntax_valid=False,
        token_confidence=0.20,
        label_detected=False,
        supporting_tokens_count=1,
    )
    fitted = ConfidenceCalibrator().fit([fv_pos] * 10 + [fv_neg] * 10, [1] * 10 + [0] * 10, epochs=200)
    assert fitted.predict_proba(fv_pos) > 0.85
    assert fitted.predict_proba(fv_neg) < 0.25

    # Tri-state canonical lifecycle
    assert discretize_probability(0.90) == EvidenceState.VERIFIED
    assert discretize_probability(0.72) == EvidenceState.PROVISIONAL
    assert discretize_probability(0.40) == EvidenceState.UNCERTAIN
    assert discretize_probability(0.95, is_ambiguous=True) == EvidenceState.UNCERTAIN
