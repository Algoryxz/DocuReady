# LOOP 18: Dataset Provenance, Cohort Manifest & Legal Compliance

## 1. Executive Summary & Legal Compliance

Loop 18 expands the DocuReady research evaluation corpus from 20 to 25 representative administrative documents, alongside a dedicated 4-fixture adversarial stress suite.

### Regulatory & Ethics Standards
- **Zero Real PII**: All names, identification numbers (PAN, PPO, roll numbers, khata numbers), and dates correspond to synthetic or public mock identities.
- **Fair Dealing / Open Government Data**: Built from standard templates compliant with Government Open Data guidelines and fair dealing for research and algorithm auditing.
- **Offline & Local**: No external network requests or third-party cloud processing are used at any stage of evaluation.

---

## 2. Dataset Composition (25 Documents)

| Category / Cohort | Count | Description | Primary Scripts |
| :--- | :---: | :--- | :--- |
| **VERIFIED_EXTERNAL** | 1 | Real public administrative PDF (`DOC_EXT_01_MOSPI_NADA_GUIDE.pdf`). | English |
| **DERIVED_FROM_EXTERNAL** | 21 | Authentic layout templates modeled on Indian public forms, land records, degrees, and notices. | English, Devanagari (Hindi), Odia |
| **VERIFIED_SYNTHETIC** | 3 | Pure synthetic reference standards for control and baseline calibration. | Latin, Devanagari, Odia |
| **Total Main Corpus** | **25** | **19 PRIMARY_VALIDATION + 6 SEALED_CHALLENGE** | **Tri-Script Multi-Lingual** |

### Additional Controlled Stress Fixtures (4 Fixtures)
- `STRESS_01_SIMILAR_DIGIT_CONFUSION`: Adversarial character test (0 vs O, 8 vs B, 1 vs I, 5 vs S).
- `STRESS_02_FAINT_RUBBER_STAMP_OVERLAY`: Official treasury circular with semi-transparent official stamp obscuring token serial and amounts.
- `STRESS_03_MULTICOLUMN_EMBEDDED_AMOUNTS`: Dual-column fiscal balance sheet testing column interleaving and number extraction.
- `STRESS_04_SKEW_LOW_CONTRAST`: 2.8° scan tilt combined with 40% contrast reduction simulating degraded civil registry records.

---

## 3. Critical Field Contract Inventory

The critical-field annotation subsystem defines exact key-value contracts for 13 of the 25 corpus documents, totaling **67 annotated critical fields**:
1. `CHALLENGE_03_HINDI_ENGLISH_MARKSHEET_ROW_GRID` (5 fields)
2. `CHALLENGE_06_FAINT_SEAL_OVER_NUMERIC_ID` (4 fields)
3. `DOC_CTRL_01_ENGLISH_CERTIFICATE` (4 fields)
4. `DOC_EXT_02_PENSION_DISBURSEMENT_ORDER` (6 fields)
5. `DOC_EXT_03_UNIVERSITY_CONVOCATION_DEGREE` (6 fields)
6. `DOC_EXT_04_LAND_REVENUE_KHATAUNI_RECORD` (7 fields)
7. `DOC_EXT_05_PUBLIC_HEALTH_CIRCULAR` (4 fields)
8. `DOC_EXT_06_ODIA_REVENUE_NOTICE` (6 fields)
9. `DOC_EXT_07_TECHNICAL_EDUCATION_DIPLOMA` (6 fields)
10. `DOC_EXT_08_PENSION_LIFE_CERTIFICATE_RECEIPT` (5 fields)
11. `DOC_EXT_09_RTI_APPEAL_DISPOSAL_ORDER` (4 fields)
12. `DOC_MIX_01_HIN_ENG_SCHOLARSHIP` (5 fields)
13. `DOC_MULTI_04_MARKSHEET_INDIC_GRID` (5 fields)

The stress fixtures contribute an additional **15 annotated fields** across 4 adversarial documents.

---

## 4. SHA-256 Checksum Manifest

All files, sizes, and cryptographically verified SHA-256 hashes are recorded in `research/loop18/dataset_manifest.json`.
