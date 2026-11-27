# LOOP 19: Cross-Document Evidence Matching & Spatial Integrity

## 1. Executive Summary

DocuReady's core workflow compares evidence across multi-document packets (e.g., verifying that the applicant name, date of birth, and income on an application form match those on the tax return and bank statement).

A major vulnerability exposed prior to Loop 19 was that **misassociated evidence produced false cross-document conflicts**:
- If a table extraction grabbed an amount from the wrong column (e.g. `Tax Inflow` instead of `Grant Inflow`), the decision engine flagged an apparent financial conflict.
- In reality, the document was correct; the OCR association was wrong.

---

## 2. Four-State Cross-Document Verification Logic

Loop 19 formalizes a four-state outcome taxonomy for cross-document field comparison:

```
                  Cross-Document Field Comparison
                                 │
     ┌───────────────────────────┼───────────────────────────┬───────────────────────────┐
     ▼                           ▼                           ▼                           ▼
[1. AGREEMENT]             [2. MISMATCH]             [3. UNCERTAIN]              [4. MISSING]
Both values match          Both values confident     One or both extractions     Field absent
and provenances align.     and spatially bound,      flagged is_ambiguous or     in one or both
-> VERIFIED                but values differ.        conf < 40%.                 packet documents.
                           -> GENUINE CONFLICT       -> MANUAL REVIEW            -> MISSING_EVIDENCE
```

---

## 3. Evaluation on Synthetic Packets

We tested the four-state comparator across standard packet configurations:
1. **Packet 01 (Clean)**: All fields agree across documents -> `STATUS: PASSED (ALL_VERIFIED)`.
2. **Packet 02 (Name Conflict)**: Explicit mismatch between application and ID card -> `STATUS: DEFECT (NAME_MISMATCH)`.
3. **Packet 04 (Income Mismatch)**: Income amount discrepancy -> `STATUS: DEFECT (INCOME_CONFLICT)`.
4. **Packet 08 (Ambiguous Evidence)**: Faint or straddling text -> `STATUS: REVIEW_NEEDED (AMBIGUOUS_EVIDENCE)` — crucially, it is **NOT** classified as an intentional defect or fraud.

### Key Finding
By ensuring that fields retain their spatial `row_idx` and `col_idx`, cross-document comparisons are protected from false mismatches caused by adjacent cell bleed.
