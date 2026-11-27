"""
Unit and integration tests for Loop 27:
Identifier Integrity, Character-Level OCR Ambiguity & False-Verification Prevention
"""

import pytest
from docuready.ingest.identifier_validation import (
    validate_identifier_syntax_and_ambiguity,
    validate_verhoeff,
    generate_verhoeff,
    sanitize_identifier_token,
    detect_identifier_taxonomy,
)
from docuready.ingest.table_association import (
    TableCell,
    TableGrid,
    extract_field_by_spatial_association,
    extract_cell_by_intersection,
)


class TestIdentifierTaxonomyAndSanitization:
    def test_taxonomy_detection(self):
        assert detect_identifier_taxonomy("State Bank IFSC", "id", "BARB0BHUBAN") == "IFSC_CODE"
        assert detect_identifier_taxonomy("Income Tax PAN", "id", "ABCDE1234F") == "PAN_CARD"
        assert detect_identifier_taxonomy("Beneficiary Account", "id", "1234567890") == "BANK_ACCOUNT"
        assert detect_identifier_taxonomy("GSTIN Number", "id", "07AAAAA0000A1Z5") == "GSTIN"
        assert detect_identifier_taxonomy("Aadhaar Card", "id", "236356789012") == "AADHAAR_NUMBER"
        assert detect_identifier_taxonomy("Receipt Date", "date", "10/10/2026") == "DATE"
        assert detect_identifier_taxonomy("Tax Invoice", "id", "INV-2026-001") == "INVOICE_RECEIPT_ID"

    def test_sanitize_identifier_token(self):
        assert sanitize_identifier_token("INV-2026/099,") == "INV-2026/099"
        assert sanitize_identifier_token("'BARB0BHUBAN'") == "BARB0BHUBAN"
        assert sanitize_identifier_token("10/10/2026:") == "10/10/2026"
        assert sanitize_identifier_token("₹ 1,500.00") == "1,500.00"


class TestIFSCValidation:
    def test_valid_ifsc(self):
        ok, cleaned, dec, reason = validate_identifier_syntax_and_ambiguity(
            "BARB0BHUBAN", "State Bank IFSC", "id", ocr_conf=93.0
        )
        assert ok is True
        assert cleaned == "BARB0BHUBAN"
        assert dec == "VERIFY"
        assert reason is None

    def test_ifsc_o_for_zero_ambiguity_abstains(self):
        # Case from Loop 26 false verifications
        ok, cleaned, dec, reason = validate_identifier_syntax_and_ambiguity(
            "BARBOBHUBAN", "State Bank IFSC", "id", ocr_conf=93.0
        )
        assert ok is False
        assert dec == "ABSTAIN"
        assert "O vs 0 confusable at index 4" in reason

    def test_sbin_ifsc_o_for_zero_ambiguity_abstains(self):
        ok, cleaned, dec, reason = validate_identifier_syntax_and_ambiguity(
            "SBINO001234", "Bank IFSC Branch Code", "id", ocr_conf=71.0
        )
        assert ok is False
        assert dec == "ABSTAIN"
        assert "O vs 0 confusable at index 4" in reason

    def test_truncated_ifsc_abstains(self):
        ok, cleaned, dec, reason = validate_identifier_syntax_and_ambiguity(
            "BARB0BHU", "State Bank IFSC", "id", ocr_conf=90.0
        )
        assert ok is False
        assert dec == "ABSTAIN"
        assert "Invalid IFSC length" in reason


class TestPANValidation:
    def test_valid_pan(self):
        ok, cleaned, dec, reason = validate_identifier_syntax_and_ambiguity(
            "ABCDE1234F", "PAN Number", "id", ocr_conf=95.0
        )
        assert ok is True
        assert dec == "VERIFY"

    def test_pan_digit_in_prefix_abstains(self):
        ok, cleaned, dec, reason = validate_identifier_syntax_and_ambiguity(
            "AB0DE1234F", "PAN Number", "id", ocr_conf=90.0
        )
        assert ok is False
        assert dec == "ABSTAIN"
        assert "Digit glyphs" in reason

    def test_pan_letter_in_numeric_abstains(self):
        ok, cleaned, dec, reason = validate_identifier_syntax_and_ambiguity(
            "ABCDEI234F", "Income Tax PAN", "id", ocr_conf=88.0
        )
        assert ok is False
        assert dec == "ABSTAIN"
        assert "Letter glyphs" in reason


class TestBankAccountValidation:
    def test_valid_account(self):
        ok, cleaned, dec, reason = validate_identifier_syntax_and_ambiguity(
            "123456789012", "Account Number", "id", ocr_conf=92.0
        )
        assert ok is True
        assert dec == "VERIFY"

    def test_account_alpha_substitution_abstains(self):
        ok, cleaned, dec, reason = validate_identifier_syntax_and_ambiguity(
            "12345O789012", "Account Number", "id", ocr_conf=92.0
        )
        assert ok is False
        assert dec == "ABSTAIN"
        assert "alphabetic glyphs" in reason


class TestVerhoeffCheckDigit:
    def test_verhoeff_generation_and_validation(self):
        base = "236"
        with_chk = generate_verhoeff(base)
        assert with_chk == "2363"
        assert validate_verhoeff(with_chk) is True
        # Single digit substitution error
        assert validate_verhoeff("2365") is False
        # Transposition error
        assert validate_verhoeff("2633") is False


class TestDateTrailingPunctuation:
    def test_date_trailing_comma_sanitization(self):
        ok, cleaned, dec, reason = validate_identifier_syntax_and_ambiguity(
            "10/10/2026,", "date", "date", ocr_conf=89.5
        )
        assert ok is True
        assert cleaned == "10/10/2026"
        assert dec == "VERIFY"
