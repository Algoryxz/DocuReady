# LOOP 20: Blind Corpus Integrity & Leakage Protection Audit

## 1. Methodological Integrity & Separation

To guarantee genuine generalization and prevent benchmark overfitting, Loop 20 establishes a strict four-cohort separation policy:

```
[Entire Corpus: 34 Documents]
 ├── Cohort A: Development (8 Docs) ── Allowed for error inspection, rule tuning, debugging
 ├── Cohort B: Validation (8 Docs) ── Allowed for parameter tuning, layout stress testing
 ├── Cohort C: Blind Evaluation (10 Docs) ── STRICTLY HELD OUT; zero tuning until code frozen
 └── Cohort D: Challenge & Adversarial (8 Docs) ── False-verification traps, cross-doc conflicts
```

### 1.1 Leakage Protection Rules
1. **Zero Hardcoded Identifiers**: No code may check for fixture IDs (`BLIND_01`, `DEV_02`, etc.) or hardcoded expected string values.
2. **Held-Out Blind Guarantee**: The 10 layouts in Cohort C represent domains never seen during Loop 19 development (customs manifests, electricity tariffs, clinical lab biochemistry, public distribution ration registers, port declarations, court fee registries).
3. **Immutable Ground Truth**: All ground truth annotations in `research/loop20/dataset_manifest.json` are fixed *before* running benchmark evaluations.
4. **Zero-PII Compliance**: Every document utilizes strictly synthetic names, registration numbers, roll codes, and transaction amounts.

---

## 2. Cohort Classification & Provenance Matrix

| Document ID | Cohort | Domain Category | Table Geometry | Language/Script | PII Status | Exposure |
| :--- | :---: | :--- | :--- | :--- | :---: | :---: |
| `DEV_01_ACCOUNTING_INVOICE` | A | Commercial Supply | 6 cols, bordered | English | Synthetic | Open |
| `DEV_02_ACADEMIC_MARKSHEET` | A | Education Examination | 6 cols, bordered | English | Synthetic | Open |
| `DEV_03_GOVT_PENSION_ORDER` | A | Treasury Pension | 6 cols, bordered | English | Synthetic | Open |
| `DEV_04_LAND_KHATAUNI_RECORD` | A | Revenue Land Record | 6 cols, bordered | English | Synthetic | Open |
| `DEV_05_EMPLOYMENT_CERTIFICATE` | A | Municipal Service | 5 cols, bordered | English | Synthetic | Open |
| `DEV_06_RECEIPT_VOUCHER` | A | Urban Body Receipt | 5 cols, bordered | English | Synthetic | Open |
| `DEV_07_ADMINISTRATIVE_CIRCULAR` | A | Recruitment Quota | 6 cols, bordered | English | Synthetic | Open |
| `DEV_08_MEDICAL_BILL` | A | Hospital Discharge | 5 cols, bordered | English | Synthetic | Open |
| `VAL_01_WRAPPED_LINE_ITEMS` | B | Procurement Order | 4 cols, multi-line wrap | English | Synthetic | Validation |
| `VAL_02_DENSE_LEDGER` | B | Bank Ledger | 6 cols, dense numeric | English | Synthetic | Validation |
| `VAL_03_BORDERLESS_PAYSLIP` | B | Salary Slip | 4 cols, borderless | English | Synthetic | Validation |
| `VAL_04_MIXED_SCRIPT_BILINGUAL` | B | Panchayat Register | 4 cols, Odia/English | Bilingual | Synthetic | Validation |
| `VAL_05_MULTI_ROW_SUMMARY` | B | Budget Variance | 5 cols, 2-tier subheader | English | Synthetic | Validation |
| `VAL_06_PARTIALLY_FILLED_FORM` | B | Welfare Application | 4 cols, blank cells | English | Synthetic | Validation |
| `VAL_07_TAX_ASSESSMENT_SCHEDULE`| B | Property Tax Schedule | 6 cols, bordered | English | Synthetic | Validation |
| `VAL_08_SHADOW_NOISE_SCAN` | B | Scholarship Awards | 4 cols, noisy scan | English | Synthetic | Validation |
| `BLIND_01_SALARY_SLIP` | C | Enterprise Payroll | 4 cols, held-out | English | Synthetic | **BLIND** |
| `BLIND_02_CUSTOMS_DECLARATION` | C | Customs Entry | 6 cols, held-out | English | Synthetic | **BLIND** |
| `BLIND_03_UTILITY_ELECTRICITY_BILL`| C | Energy Utility | 6 cols, held-out | English | Synthetic | **BLIND** |
| `BLIND_04_MUNICIPAL_HOLDING_TAX` | C | Municipal Tax | 6 cols, held-out | English | Synthetic | **BLIND** |
| `BLIND_05_BANK_ACCOUNT_STATEMENT`| C | Savings Account | 6 cols, held-out | English | Synthetic | **BLIND** |
| `BLIND_06_CLINICAL_LAB_REPORT` | C | Pathology Lab | 5 cols, held-out | English | Synthetic | **BLIND** |
| `BLIND_07_PUBLIC_DISTRIBUTION_RATION`| C | Food Supplies | 5 cols, held-out | English | Synthetic | **BLIND** |
| `BLIND_08_UNIVERSITY_SEMESTER_TRANSCRIPT`| C | University Grade | 5 cols, held-out | English | Synthetic | **BLIND** |
| `BLIND_09_TRANSPORT_FREIGHT_MANIFEST`| C | Cargo Freight | 6 cols, held-out | English | Synthetic | **BLIND** |
| `BLIND_10_COURT_FEE_REGISTRY` | C | Court Petitions | 5 cols, held-out | English | Synthetic | **BLIND** |
| `CHALL_01_IDENTICAL_AMOUNT_DIFF_COLUMNS`| D | Adversarial Traps | Dual 25000 in row | English | Synthetic | Challenge |
| `CHALL_02_WRONG_PERSON_ADJACENT_ROWS` | D | Adversarial Traps | Adjacent similar names | English | Synthetic | Challenge |
| `CHALL_03_FAINT_COLUMN_BLEED` | D | Adversarial Traps | 12px narrow gutter | English | Synthetic | Challenge |
| `CHALL_04_REPEATED_ACCOUNT_NUMBERS` | D | Adversarial Traps | Same ID in 3 rows | English | Synthetic | Challenge |
| `CHALL_05_EMPTY_AMOUNT_CELL` | D | Adversarial Traps | Blank arrears cell | English | Synthetic | Challenge |
| `CHALL_06_LABEL_AS_VALUE_TRAP` | D | Adversarial Traps | Header over blank cell | English | Synthetic | Challenge |
| `CHALL_07_CROSS_DOC_PAIR_A` | D | Cross-Doc Audit Pair | Invoice (Original) | English | Synthetic | Challenge |
| `CHALL_08_CROSS_DOC_PAIR_B` | D | Cross-Doc Conflict | Site Receipt (Mismatch) | English | Synthetic | Challenge |

---

## 3. Leakage Audit Sign-off

- All 34 images verified generated and hashed with SHA-256.
- Zero source code references to `BLIND_*` or `CHALL_*` exist in `src/docuready/`.
- Evaluation runner scripts read purely from `dataset_manifest.json` and pass image paths into the generic ingestion engine.
