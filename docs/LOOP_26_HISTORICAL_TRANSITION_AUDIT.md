# Loop 26 - Historical Reconciliation & Transition Audit

## Reconciliation of Historical Verified Claims (Loops 20-23)

Loop 24 reported 71 verified claims among 113 historical fields.
Loop 25 reported 75 verified claims among the same 113 fields.

Forensic audit confirmed exactly **4 historical transitions** from unverified to verified claims:

| Document ID | Field Name | Expected Ground Truth | Loop 24 Status | Loop 25/26 Status | Extracted Value | Confidence | Correctness | Transition Root Cause |
|---|---|---|---|---|---|---|---|---|
| `COHORT_H_02_MICRO_DOSAGE_AUDIT` | `diaz_strength` | `2.4` | `ABSTAIN_NOT_EXTRACTED` | `PASS_EXACT` | `2.4` | 87.4% | **EXACT** | Row-label substitution recovered |
| `DEC_02_COMMODITY_RATES` | `turmeric_settlement` | `138.50` | `ABSTAIN_NOT_EXTRACTED` | `PASS_EXACT` | `138.50` | 84.4% | **EXACT** | Canonical equivalence match |
| `DEC_03_PHARMA_DOSAGE` | `amlodipine_strength` | `2.5` | `ABSTAIN_NOT_EXTRACTED` | `PASS_EXACT` | `2.5` | 75.1% | **EXACT** | Micro-font row recovered |
| `VAL_03_BORDERLESS_PAYSLIP` | `gross_earnings` | `92140` | `ABSTAIN_NOT_EXTRACTED` | `PASS_EXACT` | `92140` | 84.4% | **EXACT** | Borderless payslip row recovered |

## Audit Finding
All 4 transitions are **100% correct and verified exact matches**. No historical test baselines were modified or regenerated; the improvement is entirely attributable to evidence-guided row-label recovery.
