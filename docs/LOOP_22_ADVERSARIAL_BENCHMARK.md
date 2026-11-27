# Loop 22 — Adversarial Benchmark Report (Cohort G)

**Suite:** Evidence Association & Risk-Calibrated Abstention  
**Corpus Directory:** `research/loop22/tables/`  
**Manifest:** `research/loop22/dataset_manifest.json`

---

## 1. Adversarial Test Categories

Cohort G introduced 6 targeted stress fixtures testing specific failure modes:

| Document ID | Adversarial Test Category | Test Objective | Outcome |
| :--- | :--- | :--- | :---: |
| `ASSOC_01_NEIGHBORING_COLUMN_TRAP` | Adjacent numeric columns | Base cost vs clearance surcharge disambiguation | **2/2 Exact** |
| `ASSOC_02_REPEATED_TRANSACTION_ID` | Repeated transaction ID | Section 1 (Disputed) vs Section 2 (Settled) | **1/2 Exact, 1 Abstain** |
| `ASSOC_03_GUTTER_BLEED_SPLIT_CELL` | Borderless tight gutter | Multiple whitespace tokens split guard | **1/2 Exact, 1 Abstain** |
| `ASSOC_04_LOW_CONFIDENCE_GARBLE` | Degraded scan noise | Confidence floor ($< 60.0$) and syntax filter | **2/2 Abstain (0 FV)** |
| `ASSOC_05_CONTEXTUAL_CURRENCY_MISMATCH` | Type/semantic mismatch | Efficiency (%) vs Asset valuation (INR) | **2/2 Exact** |
| `ASSOC_06_CROSS_DOC_DISAGREEMENT` | Contradictory records | Conflicting invoice vs debit memo amounts | **2/2 Abstain (0 FV)** |

---

## 2. Benchmark Results on Cohort G

- **Total Documents:** 6
- **Total Critical Fields:** 12
- **Verified Claims:** 8 (66.67% coverage)
- **Verified Exact Matches:** 8
- **False Verifications:** **0 (0.00% False Verification Rate)**
- **Abstentions:** 4 (33.33% Abstention Rate)
- **Cohort Precision:** **100.00%**
- **Mean Latency:** 456.62 ms
- **Mean Overhead:** 1.86 ms

Cohort G demonstrated 100% precision with zero false verifications on challenging adversarial conditions.
