# Loop 31 — Deliverable 6: Independent Loop 28 & Cohort M Reproduction

## 1. Scope of Independent Cross-Document Reproduction
The cross-document verification engine was independently evaluated across:
1. **Loop 28 Corpus:** 36 multi-document packets, 92 claims, 4 splits (DEV: 10 pkts/27 claims, CAL: 8 pkts/23 claims, BLIND: 12 pkts/31 claims, CHALL: 6 pkts/11 claims).
2. **Cohort M Corpus:** 30 multi-document packets, 103 claims, 6 document families.

---

## 2. Independent Evaluation Results

### A. Loop 28 Corpus (36 Packets / 92 Claims)
- **Reported in Loop 30:**
  - Evaluated Claims: 92
  - Verified Claims: 42
  - Exact Matches: 42
  - False Verifications: 0
  - Abstained Claims: 50
  - Claim Precision: 100.00%
  - Claim Coverage: 45.65%
- **Independently Reproduced in Loop 31:**
  - Evaluated Claims: 92
  - Verified Claims: 42
  - Exact Matches: 42
  - False Verifications: 0
  - Abstained Claims: 50
  - Claim Precision: 100.00%
  - Claim Coverage: 45.65%
  - **Discrepancy:** `0` (BIT-EXACT MATCH)

### B. Cohort M Corpus (30 Packets / 103 Claims)
- **Reported in Loop 30:**
  - Evaluated Claims: 103
  - Verified Claims: 76 (under strict full policy)
  - Exact Matches: 76
  - False Verifications: 0
  - Abstained / Suppressed Claims: 27 (21 contradictions, 2 unit mismatches, 1 entity ambiguous, 1 missing evidence, 2 marginal confidence)
  - Claim Precision: 100.00%
  - Claim Coverage: 73.79%
- **Independently Reproduced in Loop 31:**
  - Evaluated Claims: 103
  - Verified Claims: 76
  - Exact Matches: 76
  - False Verifications: 0
  - Abstained Claims: 27
  - Claim Precision: 100.00%
  - Claim Coverage: 73.79%
  - **Discrepancy:** `0` (BIT-EXACT MATCH)

---

## 3. Ground-Truth Abstention Effectiveness
In both corpora, 100% of adversarial injection traps (contradictory numerical amounts, mismatched units, wrong father/guardian names, and missing required certificates) were intercepted and suppressed without producing a single false verification.
