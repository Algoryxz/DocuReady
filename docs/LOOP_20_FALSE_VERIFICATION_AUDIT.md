# LOOP 20: False-Verification Audit & Substring Fallacy Analysis

## 1. Governance & Core Mission

A core objective of Loop 20 is to audit and eliminate **False Verification**:
> **A confidently wrong verification is worse than a transparent abstention.**

In statutory document audits, falsely verifying an incorrect income, incorrect pension, or wrong beneficiary name leads to unauthorized benefits or compliance violations. A transparent abstention ("Uncertain cell context — refer to human review") preserves audit safety.

---

## 2. False Verification Metrics Definition

1. **False Verification Count (FVC)**: Number of fields marked `is_verified = True` whose extracted value or row/column coordinates do not match ground truth.
2. **False Verification Rate (FVR)**:
   $$\text{FVR} = \frac{\text{Incorrectly Verified Fields}}{\text{All Fields Verified by System}} = \frac{7}{61} = 11.48\%$$
3. **Critical Field Precision (CFP)**:
   $$\text{CFP} = \frac{\text{Correctly Verified Critical Fields}}{\text{All Fields Verified by System}} = \frac{54}{61} = 88.52\%$$
4. **Verification Coverage**:
   $$\text{Coverage} = \frac{\text{Verified Fields}}{\text{Total Eligible Fields}} = \frac{61}{65} = 93.85\%$$
5. **Abstention Rate**:
   $$\text{Abstention Rate} = \frac{\text{Abstained Fields}}{\text{Total Eligible Fields}} = \frac{7}{65} = 10.77\%$$

---

## 3. Cohort-Specific False Verification Audit

| Cohort | Total Fields | Exact Matches | False Verifications | Abstained | FVR (%) | Precision (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Cohort A (Development)** | 16 | 16 | **0** | 0 | **0.00%** | **100.00%** |
| **Cohort B (Validation)** | 16 | 13 | **2** | 1 | **13.33%** | **86.67%** |
| **Cohort C (Blind Evaluation)** | 20 | 14 | **3** | 3 | **17.65%** | **82.35%** |
| **Cohort D (Challenge / Traps)**| 13 | 11 | **2** | 1 | **15.38%** | **84.62%** |
| **Total Benchmark** | **65** | **54** | **7** | **7** | **11.48%** | **88.52%** |

---

## 4. The Substring Presence Fallacy Audit

In Loop 18, baseline scoring tested whether `expected_val in page_text`.

We audited this fallacy across the 34 documents:
- **Baseline Substring Match (BSM) Rate**: **95.38%** (62/65 fields were present as raw substrings somewhere on the page).
- **Spatial Exact Match (SEM) Rate**: **83.08%** (54/65 fields were in the correct cell, row, and column).
- **The Fallacy Gap**: **12.30 percentage points** of apparent accuracy in naive substring checking were actually false associations!
- In `CHALL_01` (Dual ₹25,000 in Advance and Penalty), naive substring matching reports 100% pass for both fields, masking the fact that the two values belong to completely different statutory ledger columns.
- In `CHALL_05` (Empty Arrears), naive substring matching ignores the empty cell entirely because `15000` is on the page.

DocuReady Loop 20 completely rejects page-wide substring matching in favor of bound `FieldEvidence`.
