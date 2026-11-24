# Loop 26 - Dataset Provenance & Cohort Composition

## Cohort K Structure

Cohort K consists of **307 critical fields** across **60 independently sourced documents**, partitioned strictly into four non-overlapping splits:

| Split Partition | Document Count | Critical Fields | Layout Characteristics | Exposure Policy |
|---|---|---|---|---|
| **Development (DEV)** | 15 | 77 | Form key-value, POS receipts, certificates | Exposed for exploratory analysis |
| **Calibration (CAL)** | 15 | 77 | Multi-family receipts, legal forms, tables | Parameter and threshold calibration |
| **Locked Blind (BLIND)** | 20 | 100 | Unseen layouts + Held-out multi-item receipts | Strictly locked; unblinded only at qualification |
| **Challenge (CHALL)** | 10 | 53 | Truncated margins, sub-10px text, heavy noise | Adversarial boundary testing |
| **TOTAL COHORT K** | **60** | **307** | **6 Families / 3 Acquisition Conditions** | **Audited Manifest** |

## Document Families Represented
1. Public-Sector Intake Forms (FUNSD)
2. Commercial Point-of-Sale Receipts (SROIE)
3. Civil & Administrative Certificates (Indic OCR)
4. Freight & Customs Manifests (DocLayNet/Degradation)
5. Multi-Column Tabular Ledgers (DocLayNet)
6. Thermal Dispensary & Retail Slips (SROIE/Degradation)
