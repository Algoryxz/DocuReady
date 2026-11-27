# Loop 30 — Raw Reproduction & Verification Audit

## 1. Scope & Objective
This audit establishes whether the raw evaluation results reported in Loop 29 can be independently reproduced from the underlying datasets and algorithm implementations without discrepancies.

Evaluated Corpora:
1. **Loop 28 Cross-Document Corpus:** 36 multi-document packets, 92 claims, 4 splits (DEV, CAL, BLIND, CHALL).
2. **Cohort M Generalization Suite:** 30 multi-document packets, 103 claims, 6 document families.
3. **Aggregate Multi-Cohort Benchmark:** 221 documents, 791 critical fields.

---

## 2. Reproduction Results

### A. Loop 28 Cross-Document Benchmark (36 Packets / 92 Claims)
- **Reported in Loop 29:**
  - Evaluated Claims: 92
  - Verified Claims: 42
  - Exact Matches: 42
  - False Verifications: 0
  - Claim Precision: 100.0%
  - Claim Coverage: 45.65%
- **Independently Reproduced in Loop 30:**
  - Evaluated Claims: 92
  - Verified Claims: 42
  - Exact Matches: 42
  - False Verifications: 0
  - Claim Precision: 100.00%
  - Claim Coverage: 45.65%
  - **Discrepancy:** `0` (BIT-EXACT MATCH)

### B. Cohort M Generalization Suite (30 Packets / 103 Claims)
- **Reported in Loop 29:**
  - Evaluated Claims: 103
  - Verified Claims: 78
  - Exact Matches: 78
  - False Verifications: 0
  - Suppressed Discrepant Claims: 25 (21 contradictions, 2 unit mismatches, 1 ambiguous entity, 1 missing evidence)
  - Claim Precision: 100.0%
  - Claim Coverage: 75.73%
- **Independently Reproduced in Loop 30:**
  - Evaluated Claims: 103
  - Verified Claims: 78
  - Exact Matches: 78
  - False Verifications: 0
  - Suppressed Discrepant Claims: 25
  - Claim Precision: 100.00%
  - Claim Coverage: 75.73%
  - **Discrepancy:** `0` (BIT-EXACT MATCH)

### C. 791-Field Multi-Cohort Benchmark
- **Reported in Loop 29:**
  - Total Fields: 791
  - Exact Verified: 344
  - False Verified: 0
  - Abstained: 447
  - Precision: 100.0%
  - Coverage: 43.49%
- **Independently Reproduced in Loop 30:**
  - Total Fields: 791
  - Exact Verified: 344
  - False Verified: 0
  - Abstained: 447
  - Precision: 100.00%
  - Coverage: 43.49%
  - **Discrepancy:** `0` (BIT-EXACT MATCH)

---

## 3. Reproduction Audit Verdict
All primary evaluation numbers across candidate-level, packet-level, and benchmark-level suites replicate bit-for-bit.
No parameter drifting or manual outcome selection is present in the codebase.
