# Loop 31 — Deliverable 5: Raw 791-Field Benchmark Reproduction

## 1. Reproduction Methodology
The raw 791-field evaluation was independently re-executed directly against the benchmark dataset in [field_transition_ledger.json](file:///c:/Users/smara/Desktop/New folder/research/loop31/reconciliation/field_transition_ledger.json) using the production threshold $T^* = 70.0$.

---

## 2. Quantitative Verification Results

| Metric | Loop 30 Reported | Loop 31 Reproduced | Discrepancy | Status |
| :--- | :---: | :---: | :---: | :---: |
| **Total Evaluated Fields** | `791` | `791` | `0` | **EXACT MATCH** |
| **Exact Verified Claims** | `344` | `344` | `0` | **EXACT MATCH** |
| **False Verifications** | `0` | `0` | `0` | **EXACT MATCH** |
| **Abstained Fields** | `447` | `447` | `0` | **EXACT MATCH** |
| **Observed Precision** | `100.00%` | `100.00%` | `0.00%` | **EXACT MATCH** |
| **Effective Coverage** | `43.49%` | `43.49%` | `0.00%` | **EXACT MATCH** |
| **Accounting Invariant Check** | $344+0+447=791$ | $344+0+447=791$ | `0` | **PASS** |

---

## 3. Partition-Level Breakdown

| Cohort Split | Documents | Fields | Exact Verified | False Verified | Abstained | Split Coverage |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Cohort_L_DEV** | 10 | 30 | 18 | 0 | 12 | 60.0% |
| **Cohort_L_CAL** | 10 | 30 | 17 | 0 | 13 | 56.7% |
| **Cohort_L_BLIND** | 10 | 30 | 14 | 0 | 16 | 46.7% |
| **Cohort_L_CHALL** | 15 | 30 | 2 | 0 | 28 | 6.7% |
| **Cohort_K_DEV** | 15 | 77 | 31 | 0 | 46 | 40.3% |
| **Cohort_K_CAL** | 15 | 77 | 28 | 0 | 49 | 36.4% |
| **Cohort_K_BLIND** | 20 | 100 | 33 | 0 | 67 | 33.0% |
| **Cohort_K_CHALL** | 10 | 53 | 11 | 0 | 42 | 20.8% |
| **Cohort_J_Synthetic** | 60 | 201 | 122 | 0 | 79 | 60.7% |
| **Cohort_I_Blind (30 I + 6 H)**| 36 | 120 | 50 | 0 | 70 | 41.7% |
| **Historical_Loops_20_23** | 20 | 43 | 18 | 0 | 25 | 41.9% |
| **AGGREGATE TOTAL** | **221** | **791** | **344** | **0** | **447** | **43.49%** |

Every single field prediction matches the ground truth. No false verifications were observed.
