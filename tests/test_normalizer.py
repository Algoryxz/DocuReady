"""
Unit tests for deterministic normalizers (names, dates, amounts, Verhoeff checksum, IFSC).
"""

from datetime import date
from docuready.normalize.normalizer import (
    normalize_name, compare_names, parse_and_normalize_date,
    normalize_income, validate_ifsc_code, validate_verhoeff,
    generate_verhoeff_12
)


def test_verhoeff_checksum():
    valid_aadhaar = generate_verhoeff_12("81001234501")
    assert validate_verhoeff(valid_aadhaar) is True
    # Tamper with last digit
    corrupted = valid_aadhaar[:-1] + ("1" if valid_aadhaar[-1] != "1" else "2")
    assert validate_verhoeff(corrupted) is False
    assert validate_verhoeff("1234") is False
    assert validate_verhoeff("") is False


def test_name_normalization_and_comparison():
    assert normalize_name("Mr. Smruti Ranjan Nayak") == "SMRUTI RANJAN NAYAK"
    assert normalize_name("SHRI S. R. NAYAK") == "S R NAYAK"

    # Exact match
    res = compare_names("Smruti Ranjan Nayak", "Mr. Smruti Ranjan Nayak")
    assert res["status"] == "PASS"

    # Token permutation (reordered)
    res = compare_names("Nayak Smruti Ranjan", "Smruti Ranjan Nayak")
    assert res["status"] == "PASS"
    assert res["type"] == "TOKEN_PERMUTATION"

    # Initials expansion
    res = compare_names("S R Nayak", "Smruti Ranjan Nayak")
    assert res["status"] == "REVIEW"
    assert res["type"] == "INITIALS_EXPANSION"

    # Minor typo / transliteration
    res = compare_names("Smrutiranjan Nayak", "Smruti Ranjan Nayak")
    assert res["status"] == "REVIEW"

    # Distinct conflict
    res = compare_names("Rajesh Kumar Patel", "Smruti Ranjan Nayak")
    assert res["status"] == "FAIL"


def test_date_parsing_and_ambiguity():
    # Standard format
    dt, status, amb = parse_and_normalize_date("14/05/2003")
    assert dt == date(2003, 5, 14)
    assert status == "VALID"
    assert amb is False

    # Ambiguous format (day <= 12 and month <= 12)
    dt, status, amb = parse_and_normalize_date("04/05/2003")
    assert dt is not None
    assert status == "VALID"
    assert amb is True

    # Malformed date
    dt, status, amb = parse_and_normalize_date("not-a-date")
    assert dt is None
    assert status == "INVALID_FORMAT"

    # Unreadable date with masks
    dt, status, amb = parse_and_normalize_date("14/XX/2003")
    assert dt is None
    assert status == "UNREADABLE"


def test_income_normalization():
    assert normalize_income("Rs. 1,80,000/-") == 180000.0
    assert normalize_income("1.8 LPA") == 180000.0
    assert normalize_income("2.5 Lakh") == 250000.0
    assert normalize_income(240000) == 240000.0
    assert normalize_income("INVALID") is None


def test_ifsc_code_validation():
    assert validate_ifsc_code("SBIN0001234") is True
    assert validate_ifsc_code("HDFC0000123") is True
    assert validate_ifsc_code("SBI0001234") is False  # 3 letters instead of 4
    assert validate_ifsc_code("SBIN1001234") is False  # 5th char not zero
    assert validate_ifsc_code("") is False
