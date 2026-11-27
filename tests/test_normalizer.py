"""
Unit tests for deterministic normalizers (names, dates, amounts, Verhoeff checksum, IFSC, match grades).
"""

from datetime import date
from docuready.domain.enums import MatchGrade
from docuready.normalize.normalizer import (
    normalize_name, compare_names, parse_and_normalize_date,
    normalize_income, validate_ifsc_code, validate_verhoeff,
    generate_verhoeff_12, compare_dates, compare_identifiers, compare_amounts,
    normalize_indic_digits, normalize_cert_number, get_date_ambiguity_candidates,
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
    # Diacritics stripping
    assert normalize_name("Smrūti Ranjan Nāyak") == "SMRUTI RANJAN NAYAK"
    assert normalize_name("Aarāv Sharmā") == "AARAV SHARMA"

    # Exact match (including diacritics invariance)
    res = compare_names("Smruti Ranjan Nayak", "Mr. Smruti Ranjan Nayak")
    assert res["status"] == "PASS"
    assert res["grade"] == MatchGrade.EXACT
    assert res["match_grade"] == MatchGrade.EXACT

    res_diacritic = compare_names("Smrūti Ranjan Nāyak", "Smruti Ranjan Nayak")
    assert res_diacritic["status"] == "PASS"
    assert res_diacritic["grade"] == MatchGrade.EXACT

    # Token permutation (reordered)
    res = compare_names("Nayak Smruti Ranjan", "Smruti Ranjan Nayak")
    assert res["status"] == "PASS"
    assert res["type"] == "TOKEN_PERMUTATION"
    assert res["grade"] == MatchGrade.COMPATIBLE

    # Initials expansion ('S R Nayak' vs 'Smruti Ranjan Nayak', 'A. Sharma' vs 'Aarav Sharma')
    res = compare_names("S R Nayak", "Smruti Ranjan Nayak")
    assert res["status"] == "REVIEW"
    assert res["type"] == "INITIALS_EXPANSION"
    assert res["grade"] == MatchGrade.COMPATIBLE

    res_a = compare_names("A. Sharma", "Aarav Sharma")
    assert res_a["status"] == "REVIEW"
    assert res_a["type"] == "INITIALS_EXPANSION"
    assert res_a["grade"] == MatchGrade.COMPATIBLE

    # Minor typo / transliteration
    res = compare_names("Smrutiranjan Nayak", "Smruti Ranjan Nayak")
    assert res["status"] == "REVIEW"
    assert res["grade"] == MatchGrade.COMPATIBLE

    # Common-name collision (different given name with same surname)
    res_collision = compare_names("Rohan Sharma", "Aarav Sharma")
    assert res_collision["status"] == "FAIL"
    assert res_collision["grade"] == MatchGrade.CONFLICT

    # Single-token variation (one side single token, other multiple)
    res_single = compare_names("Aarav", "Aarav Sharma")
    assert res_single["status"] == "REVIEW"
    assert res_single["type"] == "SINGLE_TOKEN_NAME"
    assert res_single["grade"] == MatchGrade.AMBIGUOUS

    # Distinct conflict
    res = compare_names("Rajesh Kumar Patel", "Smruti Ranjan Nayak")
    assert res["status"] == "FAIL"
    assert res["grade"] == MatchGrade.CONFLICT

    # Empty field
    res_empty = compare_names("", "Aarav Sharma")
    assert res_empty["status"] == "FAIL"
    assert res_empty["grade"] == MatchGrade.AMBIGUOUS


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


def test_compare_dates():
    # Exact match across formats
    res = compare_dates("14/05/2003", "2003-05-14")
    assert res["status"] == "PASS"
    assert res["grade"] == MatchGrade.EXACT
    assert res["type"] == "EXACT_MATCH"

    # Ambiguous format (03/04/2005 read two ways)
    res = compare_dates("03/04/2005", "03/04/2005")
    assert res["status"] == "REVIEW"
    assert res["grade"] == MatchGrade.AMBIGUOUS
    assert res["type"] == "AMBIGUOUS_DATE"

    # Differing dates
    res = compare_dates("14/05/2003", "20/06/2003")
    assert res["status"] == "FAIL"
    assert res["grade"] == MatchGrade.CONFLICT
    assert res["type"] == "DIFFERING_DATE"

    # Missing or unparseable date
    assert compare_dates(None, "14/05/2003")["grade"] == MatchGrade.AMBIGUOUS
    assert compare_dates("not-a-date", "14/05/2003")["grade"] == MatchGrade.AMBIGUOUS


def test_compare_identifiers():
    # Exact match
    res = compare_identifiers("1234 5678 9012", "1234-5678-9012")
    assert res["status"] == "PASS"
    assert res["grade"] == MatchGrade.EXACT

    # Differing digits
    res = compare_identifiers("123456789012", "987654321098")
    assert res["status"] == "FAIL"
    assert res["grade"] == MatchGrade.CONFLICT

    # Aadhaar Verhoeff checksum failure -> AMBIGUOUS (extraction doubt, not identity conflict)
    valid_aadhaar = generate_verhoeff_12("81001234501")
    tampered_aadhaar = valid_aadhaar[:-1] + ("1" if valid_aadhaar[-1] != "1" else "2")
    res = compare_identifiers(valid_aadhaar, tampered_aadhaar, is_aadhaar=True)
    assert res["status"] == "REVIEW"
    assert res["grade"] == MatchGrade.AMBIGUOUS
    assert res["type"] == "CHECKSUM_FAILURE"

    # Extraction uncertainty flag
    res_unc = compare_identifiers("123456789012", "123456789012", is_uncertain=True)
    assert res_unc["grade"] == MatchGrade.AMBIGUOUS

    # Missing identifier
    assert compare_identifiers(None, "123456789012")["grade"] == MatchGrade.AMBIGUOUS


def test_compare_amounts():
    # Exact match
    res = compare_amounts("1.8 LPA", "1,80,000")
    assert res["status"] == "PASS"
    assert res["grade"] == MatchGrade.EXACT

    # Within declared tolerance
    res_tol = compare_amounts("180000", "185000", tolerance=10000.0)
    assert res_tol["status"] == "REVIEW"
    assert res_tol["grade"] == MatchGrade.COMPATIBLE
    assert res_tol["type"] == "WITHIN_TOLERANCE"

    # Outside tolerance
    res_out = compare_amounts("180000", "200000", tolerance=10000.0)
    assert res_out["status"] == "FAIL"
    assert res_out["grade"] == MatchGrade.CONFLICT
    assert res_out["type"] == "OUTSIDE_TOLERANCE"

    # Unparseable / uncertain
    assert compare_amounts("INVALID", "180000")["grade"] == MatchGrade.AMBIGUOUS
    assert compare_amounts("180000", "180000", is_uncertain=True)["grade"] == MatchGrade.AMBIGUOUS


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


def test_indic_digit_normalization():
    # All ten Odia digits
    assert normalize_indic_digits("୦୧୨୩୪୫୬୭୮୯") == "0123456789"
    # All ten Devanagari digits
    assert normalize_indic_digits("०१२३४५६७८९") == "0123456789"
    # ASCII unchanged
    assert normalize_indic_digits("0123456789") == "0123456789"
    # Mixed-script numeral strings with punctuation, separators, currency, whitespace
    mixed = "₹ ୧,८०,000/- (ID: ୨୦୨୪/०५-99)"
    assert normalize_indic_digits(mixed) == "₹ 1,80,000/- (ID: 2024/05-99)"
    # Idempotence
    once = normalize_indic_digits(mixed)
    assert normalize_indic_digits(once) == once
    # Empty and non-string inputs
    assert normalize_indic_digits("") == ""
    assert normalize_indic_digits(None) == ""
    assert normalize_indic_digits(12345) == "12345"
    # Unknown/non-decimal characters are never guessed
    assert normalize_indic_digits("²³X?abc") == "²³X?abc"


def test_indic_dates_amounts_identifiers_and_verhoeff():
    # Odia and Devanagari dates
    dt_ori, st_ori, amb_ori = parse_and_normalize_date("୧୫/୦୫/୧୯୯୦")
    assert dt_ori == date(1990, 5, 15)
    assert st_ori == "VALID"
    assert amb_ori is False

    dt_hin, st_hin, amb_hin = parse_and_normalize_date("१५-०५-१९९०")
    assert dt_hin == date(1990, 5, 15)
    assert st_hin == "VALID"
    assert amb_hin is False

    # Date ambiguity preserved for Indic dates (04/05/2003)
    dt_amb, st_amb, is_amb = parse_and_normalize_date("୦୪/୦୫/୨୦୦୩")
    assert dt_amb is not None and st_amb == "VALID" and is_amb is True
    assert len(get_date_ambiguity_candidates("०४/०५/२००३")) == 2
    assert compare_dates("୦୪/୦୫/୨୦୦୩", "०४/०५/२००३")["grade"] == MatchGrade.AMBIGUOUS
    assert compare_dates("୧୫/୦୫/୧୯୯୦", "15/05/1990")["grade"] == MatchGrade.EXACT

    # Indic-formatted income/amounts
    assert normalize_income("₹ ୧,୮୦,୦୦୦/-") == 180000.0
    assert normalize_income("₹ १,८०,०००/-") == 180000.0
    assert normalize_income("୨.୫ Lakh") == 250000.0
    assert compare_amounts("₹ ୧,୮୦,୦୦୦/-", "180000")["grade"] == MatchGrade.EXACT

    # Certificate-number and identifier normalization
    assert normalize_cert_number("INC-୨୦୨୫-୦୦୧୨୩") == "INC202500123"
    assert normalize_cert_number(None) == ""
    assert normalize_cert_number(123) == ""
    assert compare_identifiers("INC-୨୦୨୫-୦୦୧୨୩", "INC/२०२५/00123")["grade"] == MatchGrade.EXACT

    # Verhoeff validation with Odia and Devanagari digits
    valid_ascii = generate_verhoeff_12("81001234501")
    to_ori = str.maketrans("0123456789", "୦୧୨୩୪୫୬୭୮୯")
    to_hin = str.maketrans("0123456789", "०१२३४५६७८९")
    valid_ori = valid_ascii.translate(to_ori)
    valid_hin = valid_ascii.translate(to_hin)
    assert validate_verhoeff(valid_ori) is True
    assert validate_verhoeff(valid_hin) is True
    assert validate_verhoeff("²" * 12) is False
    assert compare_identifiers(valid_ori, valid_hin, is_aadhaar=True)["grade"] == MatchGrade.EXACT


def test_cross_script_name_matching_boundary():
    """Verify cross-script names yield AMBIGUOUS (never CONFLICT or PASS)."""
    res_ori = compare_names("Pravasini Sahoo", "ପ୍ରଭାସିନୀ ସାହୁ")
    assert res_ori["grade"] == MatchGrade.AMBIGUOUS
    assert res_ori["grade"] != MatchGrade.CONFLICT
    assert res_ori["status"] != "PASS"

    res_hin = compare_names("Pravasini Sahoo", "प्रभासिनी साहू")
    assert res_hin["grade"] == MatchGrade.AMBIGUOUS
    assert res_hin["grade"] != MatchGrade.CONFLICT
    assert res_hin["status"] != "PASS"
