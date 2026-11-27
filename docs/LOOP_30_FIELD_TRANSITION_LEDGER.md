# Loop 30 — Field Transition Ledger & Accounting Reconciliation

## 1. Overview
This ledger traces the provenance, categorization, and transitions of all 791 critical fields evaluated in the DocuReady benchmark across Loops 20 through 30.

- **Ledger Version:** `30.0.0`
- **Total Field Records:** `791`
- **Exact Verified Records:** `344` (`43.49%`)
- **False Verification Records:** `0` (`0.00%`)
- **Abstained Records:** `447` (`56.51%`)

---

## 2. Cohort Field Transition Summary

| Cohort Family | Partition | Document IDs Range | Fields | Exact Verified | Abstained | Primary Abstention Driver |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Cohort L** | DEV | `COHORT_L_DEV_01` to `_10` | 30 | 18 | 12 | Ambiguity filter ($O/0$, $I/1$) |
| **Cohort L** | CAL | `COHORT_L_CAL_01` to `_10` | 30 | 17 | 13 | Confidence floor ($< 70.0$) |
| **Cohort L** | BLIND | `COHORT_L_BLIND_01` to `_10` | 30 | 14 | 16 | Missing evidence / OCR noise |
| **Cohort L** | CHALL | `COHORT_L_CHALL_01` to `_15` | 30 | 2 | 28 | Adversarial substitution traps |
| **Cohort K** | DEV | `COHORT_K_DEV_01` to `_15` | 77 | 31 | 46 | Non-standard layout / Low DPI |
| **Cohort K** | CAL | `COHORT_K_CAL_01` to `_15` | 77 | 28 | 49 | Low OCR confidence |
| **Cohort K** | BLIND | `COHORT_K_BLIND_01` to `_20` | 100 | 33 | 67 | Unseen real-world degradation |
| **Cohort K** | CHALL | `COHORT_K_CHALL_01` to `_10` | 53 | 11 | 42 | Heavy skew / Narrow gutters |
| **Cohort J** | Multi | `COHORT_J_DEV/CAL/BLIND/ADV` | 201 | 122 | 79 | Sub-10px micro-font blur |
| **Cohort I** | Multi | `COHORT_I_DEV/CAL/BLIND/ADV` | 120 | 50 | 70 | Table border absence |
| **Historical**| Golden | `HIST_L20_23_01` to `_20` | 43 | 18 | 25 | Dense numeric columns |
| **TOTAL** | — | **221 Documents** | **791** | **344** | **447** | **Zero False Verifications** |

---

## 3. Transition Mapping from Loop 26/27 to Loop 29/30

```
[Loop 26 Benchmark]
Total: 202 Documents | 723 Critical Fields
  ├── Cohort K (Real-World Public): 60 docs / 307 fields
  └── Historical Cohorts (I, J, 20-23): 142 docs / 416 fields (with overlap)

                     │
                     ▼ (Addition of Cohort L & Deduplication of Historical Core)

[Loop 27 Benchmark]
Total: 221 Documents | 791 Critical Fields
  ├── Cohort K: 60 docs / 307 fields
  ├── Cohort L: 45 docs / 120 fields (initially drafted as 19 docs / 68 fields)
  └── Consolidated Historical (I, J, 20-23): 116 docs / 364 fields (pruned from 416)
        ├── Cohort J: 60 docs / 201 fields
        ├── Cohort I: 36 docs / 120 fields
        └── Historical L20-23 Core: 20 docs / 43 fields

                     │
                     ▼ (Verification & Hardened Ledger)

[Loop 29 / 30 Frozen Audit]
Total: 221 Documents | 791 Critical Fields
  ├── Exact Verified: 344
  ├── False Verified: 0
  └── Abstained: 447
  Invariant: 344 + 0 + 447 = 791 (Verified bit-exact)
```

---

## 4. Abstention Taxonomy Across All 447 Abstained Fields
1. **Confidence Floor ($< T^* = 70.0$):** 214 fields ($47.87\%$). High ambiguity or low OCR certainty.
2. **Character Ambiguity Guard ($O/0, I/1, B/8$):** 98 fields ($21.92\%$). Ambiguous glyphs prevented from false verification.
3. **Missing or Incomplete Field Evidence:** 74 fields ($16.55\%$). Value absent or clipped in document image.
4. **Header / Semantic Contradiction:** 36 fields ($8.05\%$). Extracted token contradicted document semantic type.
5. **Adversarial Noise & Multi-Token Syntax Interference:** 25 fields ($5.59\%$). Deliberately perturbed tokens.

The entire per-field registry is tracked in `research/loop30/reconciliation/reconciliation_ledger.json`.
