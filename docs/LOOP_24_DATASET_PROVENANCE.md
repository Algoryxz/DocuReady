# LOOP 24 — DATASET PROVENANCE SPECIFICATION

## 1. Overview and Intent

Loop 24 introduced **Cohort I (Independent Generalization Corpus)**, comprising 30 newly generated document fixtures containing 102 independently annotated critical fields. Cohort I is structurally separated from all historical training, tuning, and prompt artifacts developed in Loops 20 through 23.

The mission of Cohort I is to answer the fundamental generalization question:
> Does DocuReady's spatial table association, decimal point recovery, and evidence-gated selective verification generalize to completely unseen document layouts, semantic domains, and acquisition conditions without false verifications?

---

## 2. Document Taxonomy & Multi-Family Coverage

Cohort I spans 6 distinct document families:

| Document Family | Fixture IDs | Description & Critical Fields |
| :--- | :--- | :--- |
| **Commercial Invoices** | `DEV_01`, `DEV_08`, `CAL_01`, `CAL_08`, `BLIND_01`, `BLIND_08`, `ADV_02` | Line items, unit prices, SKU identifiers, tariff schedules, tax lines, net amounts. |
| **Bank Statements** | `DEV_02`, `CAL_02`, `BLIND_02`, `BLIND_09`, `ADV_01` | Transaction registers, debit/credit columns, running balances, EMI schedules, credit card minimum due. |
| **Tax & Municipal Schedules** | `DEV_03`, `CAL_03`, `BLIND_03`, `BLIND_10`, `ADV_03` | Property holding numbers, assessed values, property tax, education cess, customs duty, water sewerage charges. |
| **Medical & Diagnostic Panels** | `DEV_04`, `CAL_04`, `BLIND_04` | Clinical biochemistry panels (Bilirubin, Creatinine, BUN, Glucose), arterial blood gas (pH, pCO2, pO2, HCO3), thyroid immunoassays (FT3, FT4, TSH). |
| **Pharmaceutical Quality Statements** | `DEV_05`, `CAL_05`, `BLIND_05`, `ADV_04` | Active pharmaceutical ingredient (API) assay purity, moisture content, dissolution release profiles, sterile vial fill volume and endotoxin levels. |
| **Retail Receipts & Delivery Challans**| `DEV_06`, `DEV_07`, `CAL_06`, `CAL_07`, `BLIND_06`, `BLIND_07` | Supermarket item registers, hardware depot POS receipts, pharmacy retail slips, warehouse delivery challans, railway rake coal manifests. |

---

## 3. Acquisition and Rendering Conditions

To evaluate robustness under real-world digitization challenges, documents were rendered under three distinct acquisition conditions:

1. **Clean Digital Vector (`clean`)**:
   - High-contrast synthetic rendering with crisp typography (Arial, Arial Bold).
   - Simulates born-digital PDF and electronic document exchange.
2. **Degraded / Scanned Photocopy (`scan`)**:
   - Gaussian blur filtering ($\sigma = 0.4$), simulated low-contrast toner deposition, and micro-scale character thinning.
   - Evaluates micro-font extraction and noise tolerance.
3. **Thermal POS / Faint Contrast (`thermal`)**:
   - Contrast compression (look-up table transformation scaling pixel values to 92% baseline with 15-intensity elevation).
   - Mimics point-of-sale thermal receipts and faded printer ribbons.

---

## 4. Formal Partitioning & Blinding Safeguards

The 30 documents are formally partitioned into 4 cohorts:

| Partition | Documents | Total Fields | Blinding & Exposure Policy |
| :--- | :---: | :---: | :--- |
| **Cohort A: Development** | 8 | 28 | Unblinded during pipeline inspection and performance profiling. |
| **Cohort B: Calibration** | 8 | 27 | Used exclusively for threshold sweeps and ECE/MCE/Brier score computation. |
| **Cohort C: Locked Independent Blind** | 10 | 34 | **Strictly locked and unexposed** until the decision threshold $T^* = 70.0$ was frozen. |
| **Cohort D: Challenge / Adversarial** | 4 | 13 | Adversarial edge cases: empty traps, prefix collisions, borderless tight gutters, and sub-10px crops. |
| **TOTAL** | **30** | **102** | **100% authoritative machine-readable manifest (`dataset_manifest.json`)** |

All document images are permanently archived in `research/loop24/tables/` and indexed with ground-truth coordinates, expected values, and syntactic data types in `research/loop24/dataset_manifest.json`.
