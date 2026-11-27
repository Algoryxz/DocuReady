# DocuReady Loop 05 Extraction, Normalization & Cross-Document Intelligence Benchmark

**Date:** 2026-11-22  
**Corpus Fixtures:** 12 / 12 (100.0%)  
**Name Matching Intelligence:** 9 / 9 (100.0%)  
**Date Normalization Accuracy:** 6 / 6 (100.0%)  

---

## 1. Controlled Extraction Corpus Results (12 Fixtures)

| ID | Category | Doc Type | Status | Extracted Fields | Timing (ms) |
|---|---|---|:---:|---|:---:|
| l05_clean_income_standard.pdf | lakh_text_in_parentheses | INCOME_CERT | PASS | `applicant_name`, `father_name`, `annual_income`, `issue_date`, `certificate_no` | 19.95 |
| l05_kumar_middle_name.pdf | kumar_middle_name | INCOME_CERT | PASS | `applicant_name`, `father_name`, `annual_income`, `issue_date` | 8.14 |
| l05_kumar_given_name.pdf | kumar_given_name | MARKSHEET | PASS | `applicant_name`, `father_name`, `dob`, `roll_no`, `percentage` | 7.73 |
| l05_date_dot_delimited.pdf | date_dot_delimited | RESIDENCE_CERT | PASS | `applicant_name`, `father_name`, `issue_date`, `state` | 8.38 |
| l05_date_named_month.pdf | date_named_month | RESIDENCE_CERT | PASS | `applicant_name`, `issue_date` | 8.07 |
| l05_date_dash_delimited.pdf | date_dash_delimited | CASTE_CERT | PASS | `applicant_name`, `issue_date`, `caste_category` | 9.59 |
| l05_table_boxed_layout.pdf | table_pipe_layout | INCOME_CERT | PASS | `applicant_name`, `father_name`, `annual_income`, `certificate_no` | 10.41 |
| l05_competing_amounts_conflict.pdf | competing_amounts_ambiguity | INCOME_CERT | PASS | `applicant_name`, `annual_income` | 9.03 |
| l05_father_name_no_comma.pdf | father_name_so_no_comma | INCOME_CERT | PASS | `applicant_name`, `father_name`, `annual_income` | 8.81 |
| l05_aadhaar_card_standard.pdf | aadhaar_card_extraction | AADHAAR | PASS | `applicant_name`, `dob`, `gender`, `aadhaar_no` | 8.7 |
| l05_income_lpa_format.pdf | income_lpa_multiplier | INCOME_CERT | PASS | `applicant_name`, `annual_income` | 8.71 |
| l05_ocr_digit_confused_cert.pdf | ocr_digit_confused_cert | INCOME_CERT | PASS | `applicant_name`, `certificate_no` | 11.78 |

## 2. Cross-Document Name Intelligence Matrix

| Test Case | Name 1 | Name 2 | Expected Grade | Actual Grade | Type | Status |
|---|---|---|---|---|---|:---:|
| EXACT | Smruti Ranjan Nayak | Smruti Ranjan Nayak | EXACT | EXACT | `EXACT_MATCH` | PASS |
| SIBLING_RHYME_1 | Ramesh Nayak | Suresh Nayak | CONFLICT | CONFLICT | `DISTINCT_GIVEN_NAMES` | PASS |
| SIBLING_RHYME_2 | Anita Das | Sunita Das | CONFLICT | CONFLICT | `DISTINCT_GIVEN_NAMES` | PASS |
| MIDDLE_OMITTED | Smruti Nayak | Smruti Ranjan Nayak | COMPATIBLE | COMPATIBLE | `MIDDLE_NAME_VARIATION` | PASS |
| INITIALS_EXP | S R Nayak | Smruti Ranjan Nayak | COMPATIBLE | COMPATIBLE | `INITIALS_EXPANSION` | PASS |
| TOKEN_ORDER | Nayak Smruti Ranjan | Smruti Ranjan Nayak | COMPATIBLE | COMPATIBLE | `TOKEN_PERMUTATION` | PASS |
| TRANSLIT_MINOR | Smruti Nayak | Smruti Naik | COMPATIBLE | COMPATIBLE | `MINOR_TYPO_TRANSLITERATION` | PASS |
| SINGLE_TOKEN | Smruti | Smruti Ranjan Nayak | AMBIGUOUS | AMBIGUOUS | `SINGLE_TOKEN_NAME` | PASS |
| DISTINCT_INDIVIDUAL | Smruti Ranjan Nayak | Rajesh Patel | CONFLICT | CONFLICT | `CONTRADICTORY_NAME` | PASS |

## 3. Date Normalization Matrix

| Format | Raw String | Normalized ISO | Ambiguous Flag | Status |
|---|---|---|:---:|:---:|
| Slash Unambiguous DD/MM/YYYY | `25/01/2025` | `2025-01-25` | `False` | PASS |
| Dot Unambiguous DD.MM.YYYY | `25.01.2025` | `2025-01-25` | `False` | PASS |
| Dash Unambiguous DD-MM-YYYY | `25-01-2025` | `2025-01-25` | `False` | PASS |
| Named Month DD Mon YYYY | `10 Jan 2025` | `2025-01-10` | `False` | PASS |
| Ambiguous Slash DD/MM vs MM/DD | `10/01/2025` | `2025-01-10` | `True` | PASS |
| Ambiguous Dot DD.MM vs MM.DD | `05.06.2025` | `2025-06-05` | `True` | PASS |