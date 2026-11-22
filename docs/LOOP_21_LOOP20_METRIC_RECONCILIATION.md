# LOOP 21: Loop 20 Metric Reconciliation & Field Outcome Ledger

## 1. Governance & Problem Statement

Section 4 of the Loop 21 Engineering Directive identified an apparent mathematical inconsistency in the reported Loop 20 metrics:
- Reported: 65 eligible critical fields, 54 spatial exact matches, 61 verified fields, 7 false verifications, 88.52% precision, 93.85% coverage, and 10.77% abstention.
- Discrepancy: $61/65 = 93.85\%$ implies $4/65 = 6.15\%$ abstentions, yet reported abstention was $7/65 = 10.77\%$. Furthermore, $65 - 54 = 11$ non-exact fields, whereas only 7 were classified as false verifications.

An exhaustive audit of all 65 field records in `research/loop20/results/benchmark_results.json` was conducted to reconcile the exact outcome of every critical field.

---

## 2. Mutually Exclusive & Exhaustive Field Outcome Ledger

Every eligible critical field ($N = 65$) belongs to exactly one outcome category:

| Category Code | Description | Count | % of Corpus | System Action | Verification State |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **`VERIFIED_CORRECT`** | Text, row, and column match ground truth exactly. | **51** | 78.46% | Verified | `is_verified = True`, `sem_pass = True` |
| **`VERIFIED_WRONG_COORD`** | Text matches, but row or column coordinate shifted. | **2** | 3.08% | Falsely Verified | `is_verified = True`, `sem_pass = False` |
| **`VERIFIED_MISMATCH`** | Wrong text or corrupted value extracted. | **5** | 7.69% | Falsely Verified | `is_verified = True`, `sem_pass = False` |
| **`ABSTAIN_EMPTY_CORRECT`** | Empty cell correctly identified without value inheritance. | **3** | 4.62% | Correctly Abstained | `is_verified = False`, `sem_pass = True` |
| **`ABSTAIN_AMBIGUOUS`** | Ambiguity flagged (type mismatch / multi-row collision). | **2** | 3.08% | Correctly Abstained | `is_verified = False`, `sem_pass = False` |
| **`ABSTAIN_UNEXTRACTED`** | No candidate cell identified for pattern. | **2** | 3.08% | Abstained | `is_verified = False`, `sem_pass = False` |
| **Total Corpus** | **All Evaluated Critical Fields** | **65** | **100.00%** | — | — |

---

## 3. Detailed Audit of the 14 Non-Standard Fields

Of the 65 fields, 51 were standard spatial exact matches (`VERIFIED_CORRECT`). The remaining 14 fields were audited individually:

| Document ID | Field Name | Status in Loop 20 | Value / Got | Ledger Outcome | Root Cause |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `VAL_05_MULTI_ROW_SUMMARY` | `drip_q2_actual` | `FAIL_WRONG_COORDINATE` | `84500` (row 3 vs exp 1) | **`VERIFIED_WRONG_COORD`** | Super-header row shifted data row index by +1 |
| `VAL_05_MULTI_ROW_SUMMARY` | `seed_q1_budget` | `FAIL_WRONG_COORDINATE` | `40000` (row 2 vs exp 0) | **`VERIFIED_WRONG_COORD`** | Super-header row shifted data row index by +1 |
| `BLIND_06_CLINICAL_LAB_REPORT` | `hba1c_result` | `FAIL_MISMATCH` | `56` (expected `5.6`) | **`VERIFIED_MISMATCH`** | OCR dropped single-pixel decimal point |
| `BLIND_08_UNIVERSITY_TRANSCRIPT` | `networks_grade` | `FAIL_MISMATCH` | `fe}` (expected `O`) | **`VERIFIED_MISMATCH`** | OCR glyph misrecognition on single-letter grade |
| `BLIND_09_TRANSPORT_MANIFEST` | `jindal_weight` | `FAIL_MISMATCH` | `54000` (expected `18.5`) | **`VERIFIED_MISMATCH`** | Wrong column association in multi-column layout |
| `CHALL_01_IDENTICAL_AMOUNT` | `penalty_levy_881` | `FAIL_MISMATCH` | `70000` (expected `25000`) | **`VERIFIED_MISMATCH`** | Column coordinate bound to Net Release (col 4) |
| `CHALL_05_EMPTY_AMOUNT_CELL` | `hold_401_current` | `FAIL_MISMATCH` | `15000 1500` | **`VERIFIED_MISMATCH`** | Column gutter bleed between columns 2 and 3 |
| `VAL_06_PARTIALLY_FILLED_FORM` | `joint_name_empty` | `PASS_EMPTY_CORRECT` | `""` (expected `""`) | **`ABSTAIN_EMPTY_CORRECT`** | Empty cell correctly preserved |
| `CHALL_05_EMPTY_AMOUNT_CELL` | `hold_401_arrears` | `PASS_EMPTY_CORRECT` | `""` (expected `""`) | **`ABSTAIN_EMPTY_CORRECT`** | Empty cell correctly preserved |
| `CHALL_06_LABEL_AS_VALUE_TRAP`| `app_901_verification_date`| `PASS_EMPTY_CORRECT` | `""` (expected `""`) | **`ABSTAIN_EMPTY_CORRECT`** | Header echo rejected; blank cell preserved |
| `BLIND_02_CUSTOMS_DECLARATION` | `sensors_duty` | `ABSTAIN_AMBIGUOUS` | `""` | **`ABSTAIN_AMBIGUOUS`** | Ambiguity flagged in spatial extraction |
| `BLIND_09_TRANSPORT_MANIFEST` | `vedanta_freight` | `ABSTAIN_AMBIGUOUS` | `"In Transit"` | **`ABSTAIN_AMBIGUOUS`** | Syntactic rejection: text in numeric amount column |
| `BLIND_02_CUSTOMS_DECLARATION` | `converters_cif` | `FAIL_NOT_EXTRACTED` | `""` | **`ABSTAIN_UNEXTRACTED`** | No candidate cell identified |
| `VAL_03_BORDERLESS_PAYSLIP` | `gross_earnings` | `FAIL_NOT_EXTRACTED` | `""` | **`ABSTAIN_UNEXTRACTED`** | Borderless row anchor not found |

---

## 4. Reconciled Metrics & Mathematical Proof

### 4.1 Total Verified Claims ($V$)
A field is "verified" if the system emitted a positive value claim:
$$V = \text{VERIFIED\_CORRECT} + \text{VERIFIED\_WRONG\_COORD} + \text{VERIFIED\_MISMATCH} = 51 + 2 + 5 = 58$$

### 4.2 Total Abstained Fields ($A$)
A field is "abstained" if the system refused to emit a positive verified value:
$$A = \text{ABSTAIN\_EMPTY\_CORRECT} + \text{ABSTAIN\_AMBIGUOUS} + \text{ABSTAIN\_UNEXTRACTED} = 3 + 2 + 2 = 7$$

### 4.3 Total Corpus ($N$)
$$V + A = 58 + 7 = 65 \quad (\mathbf{100.00\%})$$

---

## 5. Recalculated Metric Comparison

| Metric | Historical Loop 20 Formula & Value | Reconciled Loop 21 Formula & Value | Variance Explanation |
| :--- | :---: | :---: | :--- |
| **Spatial Exact Match (SEM)** | $\frac{51 + 3}{65} = \mathbf{83.08\%}$ | $\frac{51 + 3}{65} = \mathbf{83.08\%}$ | **Exact Match**: Correctly counts 51 verified matches + 3 correctly preserved empty cells. |
| **Verification Coverage** | $\frac{54 + 7}{65} = \mathbf{93.85\%}$ | $\frac{58}{65} = \mathbf{89.23\%}$ | Corrected: Historical formula erroneously included 3 empty abstentions in the numerator. |
| **Abstention Rate** | $\frac{7}{65} = \mathbf{10.77\%}$ | $\frac{7}{65} = \mathbf{10.77\%}$ | **Exact Match**: $89.23\% + 10.77\% = 100.00\%$. |
| **Critical Field Precision (CFP)** | $\frac{54}{61} = \mathbf{88.52\%}$ | $\frac{51}{58} = \mathbf{87.93\%}$ | Corrected: True precision over positive verification claims ($51 / 58$). |
| **False Verification Rate (FVR)** | $\frac{7}{61} = \mathbf{11.48\%}$ | $\frac{7}{58} = \mathbf{12.07\%}$ | Corrected: True false verification rate over positive claims ($7 / 58$). Notice: $\text{CFP} + \text{FVR} = 100.0\%$. |
| **False Verification Count (FVC)**| **7** | **7** | **Exact Match**: 2 wrong coordinate + 5 value mismatch. |

---

## 6. Conclusion

The apparent discrepancies in Loop 20 arose because the benchmark runner grouped the 3 `PASS_EMPTY_CORRECT` fields under `total_sem_passes` when computing precision and coverage, while simultaneously counting them as abstentions. 

The reconciled ledger above provides a mathematically sealed, 100% mutually exclusive baseline for Loop 21 evaluations.
