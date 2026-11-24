# Loop 25 - Dataset Provenance & Partitioning

## Overview of Corpus J

Cohort J introduces 60 independent document fixtures (201 critical fields) across 6 document families and 3 acquisition conditions:
- **Commercial Invoices:** Vertex Industrial Hardware, Steel Pipe Fabricators, Solar Power Feed-in, Industrial Valves.
- **Bank Statements:** Gramya Bank Savings Ledger, Current Business Account, Mortgage Escrow Settlement, Clearing Registers.
- **Tax Schedules:** Municipal Commercial Tax Demand, Town Water Supply Bill, Container Customs Import Clearance, Land Assessment.
- **Medical Panels:** Renal Biochemistry Panel, Cardiovascular Lipid Profile, Clinical Chemistry, Blood Gas Panels.
- **Pharma Assays:** Stability Batch Specification, Bulk Chemical Analysis, Antibiotic Potency Bioassays.
- **Retail Receipts:** Daily Mart Convenience Store, Digital Electronics Accessories, Regional Goods Challans.

## Partitioning Strategy

| Partition | Document Count | Critical Fields | Purpose |
|---|---|---|---|
| Development (`J_development`) | 15 | 57 | Algorithm tuning and forensics |
| Calibration (`J_calibration`) | 15 | 52 | Threshold sweep and ECE/MCE/Brier optimization |
| Locked Blind (`J_blind_evaluation`) | 20 | 70 | Unseen out-of-sample evaluation |
| Adversarial Challenge (`J_challenge_adversarial`) | 10 | 22 | Stress tests (empty cells, prefix collisions, tight gutters) |
| **Total Cohort J** | **60** | **201** | |

## Historical Benchmark Preservation

Loops 20-24 benchmark datasets are preserved bit-exactly:
- Loop 20: 40 documents, 83 fields
- Loop 21/22/23: 12 documents, 30 fields
- Loop 24 (Cohort I): 30 documents, 102 fields
- **Total Combined Corpus:** 142 documents, 416 critical fields.
