# Loop 30 — Semantic Normalization & Unit Equivalence Audit

## 1. Problem Statement
Cross-document verification frequently encounters evidence expressed in differing units, currencies, or formatting conventions (e.g., `1 Metric Ton` vs `1,000 kg`, or `INR 1,50,000` vs `150000`).
Naively treating these as literal string mismatches causes false contradictions and unwarranted abstentions. Conversely, conflating incompatible units (e.g., `100 USD` vs `100 EUR`) causes false verifications.

`evaluate_semantic_claim_equivalence` resolves this boundary.

---

## 2. Semantic Normalization Rules

| Category | Input Claim A | Input Claim B | Classification | Verification Decision |
| :--- | :--- | :--- | :--- | :--- |
| **Mass Units** | `1 MT` | `1000 KG` | `EQUIVALENT_AFTER_NORMALIZATION` | VERIFY |
| **Mass Units** | `2.5 Quintal` | `250 kg` | `EQUIVALENT_AFTER_NORMALIZATION` | VERIFY |
| **Area Units** | `1 Hectare` | `2.471 Acres` | `EQUIVALENT_AFTER_NORMALIZATION` | VERIFY |
| **Area Units** | `100 Cents` | `1 Acre` | `EQUIVALENT_AFTER_NORMALIZATION` | VERIFY |
| **Currency Formats**| `INR 50,000` | `50000.00` | `EQUIVALENT_AFTER_NORMALIZATION` | VERIFY |
| **Currency Mismatch**| `50,000 USD`| `50,000 EUR` | `UNIT_OR_CURRENCY_MISMATCH` | ABSTAIN / CONTRADICTION |
| **Date Formats** | `2026-03-15` | `15/03/2026` | `EQUIVALENT_AFTER_NORMALIZATION` | VERIFY |
| **Numeric Discrepancy**| `1000 KG` | `1200 KG` | `NUMERICAL_CONTRADICTION` | CONTRADICTION_DETECTED |

---

## 3. Audit Verification
Every unit equivalence and currency mismatch check evaluates deterministically with zero floating-point drift.
All unit tests in `tests/test_loop28_cross_document.py` pass without regression.
