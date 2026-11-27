# Loop 21 Blind Validation Integrity & Failure Attribution Audit

## 1. Overview

A critical principle of DocuReady's engineering philosophy is absolute honesty regarding benchmark integrity. We do not invent successes, nor do we explain away failures without strict forensic evidence.

In Loop 21, the 10 unseen blind documents from Cohort C (`BLIND_01` through `BLIND_10`) were re-audited under the new hierarchical header and decimal retention engines.

---

## 2. Exhaustive Audit of Cohort C (Blind Evaluation)

Cohort C consists of 10 unseen documents comprising 20 critical fields:

| Document ID | Field Name | Expected | Extracted | Loop 20 Status | Loop 21 Status | Forensic Root Cause |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `BLIND_01_SALARY_SLIP` | `basic_salary` | `45000` | `45000` | PASS_SPATIAL_EXACT | **PASS_SPATIAL_EXACT** | Maintained exact match |
| `BLIND_01_SALARY_SLIP` | `net_pay` | `62500` | `62500` | PASS_SPATIAL_EXACT | **PASS_SPATIAL_EXACT** | Maintained exact match |
| `BLIND_02_CUSTOMS_DECLARATION` | `customs_duty` | `18500` | `Assessment` | ABSTAIN_AMBIGUOUS | **ABSTAIN_AMBIGUOUS** | Borderless form / label collision |
| `BLIND_02_CUSTOMS_DECLARATION` | `igst_cess` | `3700` | `Value` | ABSTAIN_AMBIGUOUS | **ABSTAIN_AMBIGUOUS** | Borderless form / label collision |
| `BLIND_03_UTILITY_ELECTRICITY_BILL` | `current_charges`| `2450` | `Meter: 8491` | FAIL_MISMATCH | **FAIL_MISMATCH** | Two-column interleaved layout |
| `BLIND_03_UTILITY_ELECTRICITY_BILL` | `total_payable` | `2695` | `Arrears: 245`| FAIL_MISMATCH | **FAIL_MISMATCH** | Two-column interleaved layout |
| `BLIND_04_MUNICIPAL_HOLDING_TAX` | `current_demand` | `4200` | `4200` | PASS_SPATIAL_EXACT | **PASS_SPATIAL_EXACT** | Maintained exact match |
| `BLIND_04_MUNICIPAL_HOLDING_TAX` | `arrear_demand` | `1800` | `Penalty: 400`| FAIL_MISMATCH | **FAIL_MISMATCH** | Irregular table row split |
| `BLIND_05_BANK_ACCOUNT_STATEMENT` | `salary_credit` | `62500` | `62500` | PASS_SPATIAL_EXACT | **PASS_SPATIAL_EXACT** | Maintained exact match |
| `BLIND_05_BANK_ACCOUNT_STATEMENT` | `closing_balance`| `84250` | `84250` | PASS_SPATIAL_EXACT | **PASS_SPATIAL_EXACT** | Maintained exact match |
| `BLIND_06_CLINICAL_LAB_REPORT` | `glucose_result` | `98` | `98` | PASS_SPATIAL_EXACT | **PASS_SPATIAL_EXACT** | Maintained exact match |
| `BLIND_06_CLINICAL_LAB_REPORT` | `hba1c_result` | `5.6` | `5.6` | FAIL_MISMATCH ('56') | **PASS_SPATIAL_EXACT** | **RESOLVED by Loop 21 Decimal Retention** |
| `BLIND_07_PUBLIC_DISTRIBUTION_RATION` | `rice_allotment` | `35` | `35` | PASS_SPATIAL_EXACT | **PASS_SPATIAL_EXACT** | Maintained exact match |
| `BLIND_07_PUBLIC_DISTRIBUTION_RATION` | `sugar_allotment`| `2` | `2` | PASS_SPATIAL_EXACT | **PASS_SPATIAL_EXACT** | Maintained exact match |
| `BLIND_08_UNIVERSITY_SEMESTER_TRANSCRIPT` | `compiler_credits`| `4` | `4` | PASS_SPATIAL_EXACT | **PASS_SPATIAL_EXACT** | Maintained exact match |
| `BLIND_08_UNIVERSITY_SEMESTER_TRANSCRIPT` | `networks_grade` | `O` | `fe}` | FAIL_MISMATCH ('fe}')| **FAIL_MISMATCH ('fe}')**| OCR single-character letter misrecognition |
| `BLIND_09_TRANSPORT_FREIGHT_MANIFEST` | `vedanta_freight` | `38000` | `In Transit` | ABSTAIN_AMBIGUOUS | **ABSTAIN_AMBIGUOUS** | Cell boundary ambiguity |
| `BLIND_09_TRANSPORT_FREIGHT_MANIFEST` | `jindal_weight` | `18.5` | `54000` | FAIL_MISMATCH ('54000')| **FAIL_MISMATCH ('54000')**| Manifest Ground-Truth index error (col 3 vs 2) |
| `BLIND_10_COURT_FEE_REGISTRY` | `stamp_duty` | `500` | `500` | PASS_SPATIAL_EXACT | **PASS_SPATIAL_EXACT** | Maintained exact match |
| `BLIND_10_COURT_FEE_REGISTRY` | `advocate_welfare`| `100` | `100` | PASS_SPATIAL_EXACT | **PASS_SPATIAL_EXACT** | Maintained exact match |

---

## 3. Key Forensic Insights

1. **Resolution of `BLIND_06`**:
   The primary defect in Cohort C identified in Loop 20 (`hba1c_result` = `56` vs `5.6`) was fully resolved by Loop 21's pure NumPy decimal morphology. The document now achieves 2/2 exact matches.
2. **Persistence of `BLIND_08` Grade OCR Limitation**:
   The letter grade `O` (Outstanding) continues to be recognized as `fe}` by standard English Tesseract at 12px height. Because DocuReady refuses to invent hallucinated fallback text when OCR fails, this remains an honest OCR failure.
3. **Manifest Index Discrepancy in `BLIND_09`**:
   In `BLIND_09_TRANSPORT_FREIGHT_MANIFEST`, the ground-truth manifest specifies `col: 3` for `jindal_weight`, but in the actual document, `Weight (MT)` is column 2 (`18.5`) and `Freight (INR)` is column 3 (`54000`). The engine correctly extracted column 3 as instructed by `col_idx=3`, yielding `54000`. We preserve this discrepancy to maintain blind evaluation integrity without retrospective ground-truth tampering.
