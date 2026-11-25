# DOCUREADY — LOOP 33 DATE & CHRONOLOGY RULES AUDIT (FAMILY B)

**Milestone:** Loop 33 — Domain Rules & Decision Integrity  
**Component:** `src/docuready/normalize/normalizer.py`, `src/docuready/outcome/safety_layer.py`, `src/docuready/rules/validator.py`  
**Operating Thresholds:** $T^* = 70.0$, $T_{\text{fuzzy}} = 75.0$  
**Evaluation Date:** 2026-11-25  

---

## 1. Scope & Objectives

Rule Family B governs temporal and chronological validation:
- **Date Normalization:** Canonicalization of diverse date formats to ISO 8601 `YYYY-MM-DD`.
- **Date of Birth Consistency:** `RULE-DOB-01`, `RULE-DOB-02`, `RULE-DOB-03` cross-document consistency between Application Form and Marksheet/High School Certificate.
- **Certificate Validity & Expiration:** `RULE-EXP-01`, `RULE-EXP-02` checking whether revenue certificates (e.g. Income Certificate) are within statutory validity (typically 1–3 years) as of the audit date.
- **Calendar Boundary & Leap Year Auditing:** Accurate leap-year day validation (e.g., February 29).
- **Ambiguous Date Representations:** Handling slash dates where day $\le 12$ and month $\le 12$ (e.g. `05/06/2024`).

---

## 2. Invariant Analysis & Date Normalization

### 2.1 Canonical ISO Internal Representation
`parse_and_normalize_date()` converts all recognized formats into standard ISO `YYYY-MM-DD` while preserving the original raw string in evidence provenance:
- Supported input patterns:
  - `YYYY-MM-DD`, `DD/MM/YYYY`, `MM/DD/YYYY`
  - `DD-MM-YYYY`, `DD.MM.YYYY`, `DD Month YYYY`, `Month DD, YYYY`
- Calendar verification:
  - Validates dates through strict `datetime.date(year, month, day)` construction.
  - Invalid calendar dates (e.g. `31/04/2024`, `29/02/2025`) fail parsing or abstain.
  - Leap year `29/02/2024` cleanly parses to `2024-02-29`.

### 2.2 Slash Date Ambiguity & Conservative Abstention
When an ambiguous slash date like `05/06/2024` is encountered:
- If day $\le 12$ and month $\le 12$ and day $\neq$ month, the date can be interpreted as either 5th June 2024 or 6th May 2024.
- In `src/docuready/normalize/normalizer.py`:
  - `is_ambiguous_date_format()` flags this ambiguity.
  - `compare_dates()` returns `MatchGrade.AMBIGUOUS` with status `Status.REVIEW` (`ReasonCode.DATE_AMBIGUOUS_FORMAT`).

### 2.3 Decision-Invariant Date Expiration (Invariant 3)
Under `src/docuready/outcome/safety_layer.py`:
- `is_expiration_date_invariant_pass()` and `is_expiration_date_invariant_fail()`:
  - If an issue date is ambiguous (e.g. `05/06/2024` vs `06/05/2024`), the safety layer checks both candidate interpretations against the certificate validity ceiling.
  - If **both** interpretations are within the validity period as of `audit_date`, the certificate is **decision-invariant valid (PASS)**.
  - If **both** interpretations are expired as of `audit_date`, the certificate is **decision-invariant expired (FAIL)**.
  - Only when one interpretation is valid and the other is expired does the engine strictly abstain with `REVIEW`.

---

## 3. Date of Birth Statutory Standards (CBSE Rule 69.2)
- CBSE Bye-laws declare the High School Examination Certificate / Marksheet as the primary authoritative record of birth.
- When Application Form DOB differs from Marksheet DOB:
  - Direct mismatch results in statutory `FAIL` (`RULE-DOB-01`).
  - Low confidence or unreadable DOB on either document results in `REVIEW` (`RULE-DOB-UNCERTAIN`), preventing unsupported rejection.

**Audit Status:** APPROVED. Family B rules correctly enforce ISO canonicalization, calendar validation, and decision-invariant abstention.
