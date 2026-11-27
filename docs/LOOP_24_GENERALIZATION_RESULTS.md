# LOOP 24 — GENERALIZATION RESULTS & COHORT BREAKDOWN

## 1. Executive Summary

Evaluation of the 30 independent generalization documents in **Cohort I** demonstrates that DocuReady achieves **100.00% critical-field verification precision** and **0.00% false verification rate** on unseen document families, completely fulfilling the core mission of Loop 24.

Across the locked blind cohort (`COHORT_I_BLIND`), zero false verifications were produced, proving that selective verification correctly suppresses degraded or ambiguous extractions.

---

## 2. Cohort I Detailed Results Table

| Cohort | Total Docs | Fields Evaluated | Verified Claims | Exact Matches | False Verifications | Abstentions | Critical Field Precision | False Verification Rate | Coverage | Abstention Rate | Mean Overhead |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **I_development** | 8 | 28 | 9 | 9 | 0 | 19 | **100.00%** | **0.00%** | 32.14% | 67.86% | 1.59 ms |
| **I_calibration** | 8 | 27 | 3 | 3 | 0 | 24 | **100.00%** | **0.00%** | 11.11% | 88.89% | 2.35 ms |
| **I_blind_evaluation** | 10 | 34 | 5 | 5 | 0 | 29 | **100.00%** | **0.00%** | 14.71% | 85.29% | 2.00 ms |
| **I_challenge_adversarial** | 4 | 13 | 2 | 2 | 0 | 11 | **100.00%** | **0.00%** | 15.38% | 84.62% | 1.36 ms |
| **COHORT I TOTAL** | **30** | **102** | **19** | **19** | **0** | **83** | **100.00%** | **0.00%** | **18.63%** | **81.37%** | **1.90 ms** |

---

## 3. Generalization Observations Across Document Families

1. **Commercial Invoices & Real Estate**:
   - High spatial consistency on structured grid lines (e.g. `SUITE-401` total due `138000`, SKU-9901 price `24.50`).
   - Clean column alignment produces high-confidence extractions with exact coordinate attribution.
2. **Bank Statements & Ledger Accounts**:
   - Zero-fill and empty trap protection successfully prevented false debit/credit value inheritance on `AUD-REC-01` and `AUD-REC-02`.
   - Running balances verified with 100% precision.
3. **Medical & Pharmaceutical Panels**:
   - Sub-10px clinical metrics (`0.05` EU/mL, `10.0` mL fill volume) cleanly recovered via isolated baseline dot morphology without false integer conversions.
4. **Adversarial & Challenge Stress**:
   - Adversarial prefix collisions (`BATCH-AX-100` vs `BATCH-AX-100-A`) correctly resolved using exact-boundary string matching.
   - Narrow gutters with tight token spacing (`12000 1200`) correctly separated using localized token gap analysis.
