# Loop 31 — Deliverable 2: 221-Document Transition Ledger

## 1. Document Inventory & Partition Breakdown
All 221 documents evaluated across the multi-cohort benchmark are preserved in [document_transition_ledger.json](file:///c:/Users/smara/Desktop/New folder/research/loop31/reconciliation/document_transition_ledger.json).

| Cohort Family | Origin Loop | Document Count | Critical Fields | Exact Verified | False Verified | Abstained | Partition Role |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Cohort L (DEV)** | Loop 27 | 10 | 30 | 18 | 0 | 12 | Initial ambiguity stress |
| **Cohort L (CAL)** | Loop 27 | 10 | 30 | 17 | 0 | 13 | Confidence calibration |
| **Cohort L (BLIND)** | Loop 27 | 10 | 30 | 14 | 0 | 16 | Held-out blind evaluation |
| **Cohort L (CHALL)** | Loop 27 | 15 | 30 | 2 | 0 | 28 | Adversarial substitution traps |
| **Cohort K (DEV)** | Loop 26 | 15 | 77 | 31 | 0 | 46 | Public scanned documents |
| **Cohort K (CAL)** | Loop 26 | 15 | 77 | 28 | 0 | 49 | Public calibration documents |
| **Cohort K (BLIND)** | Loop 26 | 20 | 100 | 33 | 0 | 67 | Public held-out blind scans |
| **Cohort K (CHALL)** | Loop 26 | 10 | 53 | 11 | 0 | 42 | Heavy skew & low-contrast |
| **Cohort J** | Loop 25 | 60 | 201 | 122 | 0 | 79 | Micro-font & narrow gutters |
| **Cohort I (Combined)**| Loops 23 & 24 | 36 | 120 | 50 | 0 | 70 | 30 Cohort I + 6 Cohort H docs |
| **Historical Loops 20-23**| Loops 20-23 | 20 | 43 | 18 | 0 | 25 | Deduplicated golden core |
| **TOTAL** | — | **221** | **791** | **344** | **0** | **447** | **Zero False Verifications** |

---

## 2. Document Evolution History
1. **Loop 20–23 Historical Baseline:**
   - Evaluated 52 early documents.
   - 20 canonical documents retained as stable golden regression baseline (`HIST_L20_23_*`).
2. **Loop 23 Cohort H Integration:**
   - 6 documents created for micro-font decimal and narrow-gutter stress (`COHORT_H_01` to `_06`).
   - Grouped into the benchmark under partition `Cohort_I_Blind`.
3. **Loop 24 Cohort I Introduction:**
   - 30 documents introduced across DEV (8), CAL (8), BLIND (10), ADV (4).
   - Joined with Cohort H to form the 36-document benchmark partition.
4. **Loop 25 Cohort J Introduction:**
   - 60 documents introduced for large-scale table extraction (DEV: 15, CAL: 15, BLIND: 20, ADV: 10).
5. **Loop 26 Cohort K Introduction:**
   - 60 real-world scanned documents sourced from public datasets (FUNSD, CORD, SROIE, Indian Gazettes).
6. **Loop 27 Cohort L Introduction:**
   - 45 documents added for identifier verification ($O/0$, $I/1$, PAN, IFSC, Aadhaar).
7. **Total Stable Repository Inventory:** Exactly **221 documents**.
