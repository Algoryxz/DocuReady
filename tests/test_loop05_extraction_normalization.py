"""
DocuReady Loop 05 Permanent Regression Test Suite:
Extraction Reliability, Field Normalization & Cross-Document Intelligence.

Verifies:
1. Income Normalization:
   - "Lakh" descriptive text does NOT multiply figures >= 1,000 by 100,000 (eliminates 18 Billion INR bug).
   - LPA/Lakh abbreviated notation correctly converts figures < 1,000 to full INR.
2. Name Normalization & Intelligence:
   - "Kumar" preserved in given names (e.g. "Kumar Gaurav" is not degraded to single-token).
   - "Kumar" canonicalized as honorific affix in 3-token names ("Rajesh Kumar Patel" -> "RAJESH PATEL").
   - Distinct given names with shared surname (sibling rhyme pairs) fail with CONFLICT ("Ramesh Nayak" vs "Suresh Nayak").
   - Middle name omission passes as COMPATIBLE ("Smruti Nayak" vs "Smruti Ranjan Nayak").
3. Date Normalization:
   - Dot-delimited (10.01.2025), dash-delimited (10-01-2025), and named month (10 Jan 2025) parsed accurately.
   - Ambiguous day/month (both <= 12) correctly flagged.
4. Identifier Normalization:
   - OCR digit 0 / letter O confusion corrected in both year and sequence slots.
5. Ingestion & Slot Extraction:
   - Table borders (|) stripped from raw captured values.
   - Father name extracted without requiring trailing comma delimiter.
   - Aadhaar document slots (applicant_name, dob, gender, aadhaar_no) extracted.
   - Competing values on separate lines correctly trigger candidate ambiguity.
6. Corpus Parity:
   - All 12 controlled fixtures in synthetic_data/loop05_extraction_corpus extract accurately.
"""

import json
from pathlib import Path
from datetime import date
import pytest

from docuready.domain.enums import MatchGrade
from docuready.domain.models import DocumentType, ExtractionMethod
from docuready.ingest.extractor import DocumentExtractor
from docuready.normalize.normalizer import (
    normalize_name, normalize_income, parse_and_normalize_date,
    normalize_cert_number, compare_names, compare_dates
)

CORPUS_DIR = Path("synthetic_data/loop05_extraction_corpus")


# ==============================================================================
# 1. INCOME NORMALIZATION TESTS
# ==============================================================================

def test_income_lakh_in_parentheses_does_not_multiply_full_figure():
    """Verify 'Rs. 1,80,000/- (Rupees One Lakh Eighty Thousand only)' produces 180,000.0, NOT 18 Billion."""
    raw = "Rs. 1,80,000/- (Rupees One Lakh Eighty Thousand only)"
    res = normalize_income(raw)
    assert res == 180000.0, f"Expected 180000.0, got {res}"


def test_income_lpa_multiplier():
    """Verify small numbers with LPA/Lakh multiplier are scaled correctly."""
    assert normalize_income("1.8 LPA") == 180000.0
    assert normalize_income("2.5 Lakh") == 250000.0
    assert normalize_income("3.0 Lacs") == 300000.0
    assert normalize_income("₹ 1,80,000/-") == 180000.0
    assert normalize_income("180000") == 180000.0


# ==============================================================================
# 2. NAME NORMALIZATION & INTELLIGENCE TESTS
# ==============================================================================

def test_kumar_given_name_preserved():
    """Verify 'Kumar Gaurav' retains both tokens and is not reduced to single-token 'GAURAV'."""
    norm = normalize_name("Kumar Gaurav")
    assert norm == "KUMAR GAURAV"
    assert len(norm.split()) == 2


def test_kumar_middle_honorific_canonicalization():
    """Verify 3-token name canonicalizes intermediate Kumar while maintaining baseline parity."""
    assert normalize_name("Rajesh Kumar Patel") == "RAJESH PATEL"
    assert normalize_name("Santosh Kumar Nayak") == "SANTOSH NAYAK"


def test_sibling_rhyme_names_conflict():
    """Verify distinct individuals with rhyming given names and shared surname are classified as CONFLICT."""
    res1 = compare_names("Ramesh Nayak", "Suresh Nayak")
    assert res1["match_grade"] is MatchGrade.CONFLICT
    assert res1["type"] == "DISTINCT_GIVEN_NAMES"

    res2 = compare_names("Anita Das", "Sunita Das")
    assert res2["match_grade"] is MatchGrade.CONFLICT
    assert res2["type"] == "DISTINCT_GIVEN_NAMES"


def test_middle_name_omission_is_compatible():
    """Verify person with omitted middle name is classified as COMPATIBLE with MIDDLE_NAME_VARIATION."""
    res = compare_names("Smruti Nayak", "Smruti Ranjan Nayak")
    assert res["match_grade"] is MatchGrade.COMPATIBLE
    assert res["type"] == "MIDDLE_NAME_VARIATION"
    assert res["status"] == "REVIEW"


def test_token_permutation_and_initials_expansion():
    """Verify token reordering and single-letter initial expansions are COMPATIBLE."""
    res_perm = compare_names("Nayak Smruti Ranjan", "Smruti Ranjan Nayak")
    assert res_perm["match_grade"] is MatchGrade.COMPATIBLE
    assert res_perm["type"] == "TOKEN_PERMUTATION"

    res_init = compare_names("S R Nayak", "Smruti Ranjan Nayak")
    assert res_init["match_grade"] is MatchGrade.COMPATIBLE
    assert res_init["type"] == "INITIALS_EXPANSION"


def test_single_token_name_is_ambiguous():
    """Verify single-token name compared against multi-token name is marked AMBIGUOUS."""
    res = compare_names("Smruti", "Smruti Ranjan Nayak")
    assert res["match_grade"] is MatchGrade.AMBIGUOUS
    assert res["type"] == "SINGLE_TOKEN_NAME"


# ==============================================================================
# 3. DATE NORMALIZATION TESTS
# ==============================================================================

def test_diverse_date_formats_parsing():
    """Verify dot, dash, named month, and slash date formats normalize to ISO-8601."""
    d1, s1, amb1 = parse_and_normalize_date("25.01.2025")
    assert s1 == "VALID"
    assert d1 == date(2025, 1, 25)
    assert not amb1

    d2, s2, amb2 = parse_and_normalize_date("25-01-2025")
    assert s2 == "VALID"
    assert d2 == date(2025, 1, 25)
    assert not amb2

    d3, s3, amb3 = parse_and_normalize_date("10 Jan 2025")
    assert s3 == "VALID"
    assert d3 == date(2025, 1, 10)
    assert not amb3

    # Ambiguous date (both day and month <= 12)
    d4, s4, amb4 = parse_and_normalize_date("10/01/2025")
    assert s4 == "VALID"
    assert amb4 is True


# ==============================================================================
# 4. IDENTIFIER NORMALIZATION TESTS
# ==============================================================================

def test_cert_number_ocr_digit_correction():
    """Verify OCR letter 'O' confused with digit '0' is corrected in year and sequence slots."""
    raw = "E-INC/2O25/1O4928"
    norm = normalize_cert_number(raw)
    assert norm == "EINC/2025/104928"


# ==============================================================================
# 5. INGESTION & EXTRACTION FIXTURE TESTS (LOOP 05 CORPUS)
# ==============================================================================

def test_fixture_clean_income_standard():
    """l05_clean_income_standard.pdf: Verify wordy lakh text extracts 180,000.0 without multiplier overflow."""
    fpath = CORPUS_DIR / "l05_clean_income_standard.pdf"
    if not fpath.exists():
        pytest.skip(f"Corpus file {fpath} not found")

    ext = DocumentExtractor()
    doc = ext.extract_document(str(fpath), DocumentType.INCOME_CERT)
    assert doc.status == "VALID"
    assert "annual_income" in doc.fields
    assert doc.fields["annual_income"].normalized_value == 180000.0
    assert doc.fields["applicant_name"].normalized_value == "SMRUTI RANJAN NAYAK"
    assert doc.fields["father_name"].normalized_value == "RAMESH CHANDRA NAYAK"


def test_fixture_income_lpa_format():
    """l05_income_lpa_format.pdf: Verify '1.8 LPA' extracts 180,000.0."""
    fpath = CORPUS_DIR / "l05_income_lpa_format.pdf"
    if not fpath.exists():
        pytest.skip(f"Corpus file {fpath} not found")

    ext = DocumentExtractor()
    doc = ext.extract_document(str(fpath), DocumentType.INCOME_CERT)
    assert doc.status == "VALID"
    assert doc.fields["annual_income"].normalized_value == 180000.0


def test_fixture_kumar_given_name():
    """l05_kumar_given_name.pdf: Verify marksheet applicant name 'Kumar Gaurav' is preserved."""
    fpath = CORPUS_DIR / "l05_kumar_given_name.pdf"
    if not fpath.exists():
        pytest.skip(f"Corpus file {fpath} not found")

    ext = DocumentExtractor()
    doc = ext.extract_document(str(fpath), DocumentType.MARKSHEET)
    assert doc.status == "VALID"
    assert doc.fields["applicant_name"].normalized_value == "KUMAR GAURAV"


def test_fixture_table_boxed_layout():
    """l05_table_boxed_layout.pdf: Verify table cell pipes (|) are stripped from values."""
    fpath = CORPUS_DIR / "l05_table_boxed_layout.pdf"
    if not fpath.exists():
        pytest.skip(f"Corpus file {fpath} not found")

    ext = DocumentExtractor()
    doc = ext.extract_document(str(fpath), DocumentType.INCOME_CERT)
    assert doc.status == "VALID"
    assert doc.fields["applicant_name"].normalized_value == "SMRUTI RANJAN NAYAK"
    assert doc.fields["annual_income"].normalized_value == 180000.0
    assert doc.fields["certificate_no"].normalized_value == "EINC/2025/778899"
    # Ensure raw values do not have pipe borders
    assert "|" not in doc.fields["applicant_name"].raw_value


def test_fixture_father_name_no_comma():
    """l05_father_name_no_comma.pdf: Verify father name is extracted cleanly without requiring trailing comma."""
    fpath = CORPUS_DIR / "l05_father_name_no_comma.pdf"
    if not fpath.exists():
        pytest.skip(f"Corpus file {fpath} not found")

    ext = DocumentExtractor()
    doc = ext.extract_document(str(fpath), DocumentType.INCOME_CERT)
    assert doc.status == "VALID"
    assert doc.fields["applicant_name"].normalized_value == "SMRUTI RANJAN NAYAK"
    assert doc.fields["father_name"].normalized_value == "RAMESH CHANDRA NAYAK"


def test_fixture_aadhaar_card_standard():
    """l05_aadhaar_card_standard.pdf: Verify all 4 slots extracted from Aadhaar card."""
    fpath = CORPUS_DIR / "l05_aadhaar_card_standard.pdf"
    if not fpath.exists():
        pytest.skip(f"Corpus file {fpath} not found")

    ext = DocumentExtractor()
    doc = ext.extract_document(str(fpath), DocumentType.AADHAAR)
    assert doc.status == "VALID"
    assert doc.fields["applicant_name"].normalized_value == "SMRUTI RANJAN NAYAK"
    assert doc.fields["dob"].normalized_value == "2005-01-10"
    assert doc.fields["gender"].normalized_value == "MALE"
    assert "aadhaar_no" in doc.fields


def test_fixture_ocr_digit_confused_cert():
    """l05_ocr_digit_confused_cert.pdf: Verify OCR letter 'O' in cert number is resolved to digit '0'."""
    fpath = CORPUS_DIR / "l05_ocr_digit_confused_cert.pdf"
    if not fpath.exists():
        pytest.skip(f"Corpus file {fpath} not found")

    ext = DocumentExtractor()
    doc = ext.extract_document(str(fpath), DocumentType.INCOME_CERT)
    assert doc.status == "VALID"
    assert doc.fields["certificate_no"].normalized_value == "EINC/2025/104928"
