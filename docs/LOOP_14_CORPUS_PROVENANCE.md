# DOCUREADY — LOOP 14
## Corpus Provenance Governance & Manifest Report

**Manifest Location:** `research/loop14/dataset_manifest.json`  
**Storage Directory:** `research/loop14/corpus/`  
**Ground Truth Directory:** `research/loop14/ground_truth/`  
**Standard:** Strict Multi-Tier Provenance Classification  

---

### 1. Provenance Classification Framework

To overcome the synthetic-benchmark limitations exposed in Loop 12, Loop 14 enforces rigorous, mutually exclusive provenance labels for every document in the evaluation corpus:

1. `VERIFIED_EXTERNAL`:
   Genuine documents acquired directly from third-party public repositories or official government portals without modification by DocuReady.
2. `DERIVED_FROM_EXTERNAL`:
   Documents whose textual content, fields, and structural layouts are reconstructed directly from authentic published government circulars, gazettes, and state application formats.
3. `VERIFIED_SYNTHETIC`:
   Programmatically generated stress documents designed to test mathematical edge cases (e.g. baseline angle sweeps).
4. `MANUALLY_ANNOTATED`:
   External or derived documents where ground truth was transcribed or independently audited by a human reviewer.
5. `UNKNOWN_PROVENANCE`:
   Any document whose origin cannot be deterministically verified (prohibited from qualification scoring).

---

### 2. Corpus Composition Breakdown

The Loop 14 corpus contains **15 standardized document samples** spanning five primary language cohorts, four layout archetypes, and three dataset splits:

```
Total Samples: 15
├── By Provenance Category:
│   ├── VERIFIED_EXTERNAL:      1 sample  (6.7%)  [Authentic MoSPI NADA PDF]
│   └── DERIVED_FROM_EXTERNAL: 14 samples (93.3%) [Authentic Government Guidelines & Formats]
│
├── By Language Cohort:
│   ├── English:              5 samples (33.3%)
│   ├── Hindi (Devanagari):   4 samples (26.7%)
│   ├── Odia:                 4 samples (26.7%)
│   ├── Mixed English/Hindi:  1 sample  (6.7%)
│   └── Mixed English/Odia:   1 sample  (6.7%)
│
├── By Layout Archetype:
│   ├── Single-Column Narrative:        5 samples (33.3%)
│   ├── Key-Value Administrative Form:  5 samples (33.3%)
│   ├── Two-Column Symmetrical Gazette: 3 samples (20.0%)
│   └── 3-Column Data Grid (Marksheet): 2 samples (13.3%)
│
└── By Dataset Split:
    ├── Development (dev):   3 samples (20.0%)
    ├── Validation (val):    8 samples (53.3%)
    └── Challenge (sealed):  4 samples (26.7%)
```

---

### 3. Detailed Document Manifest Registry

| Sample ID | Provenance | Language | Script | Layout Classification | Image Quality | Split | SHA-256 (Prefix) |
| :--- | :---: | :---: | :---: | :--- | :--- | :---: | :--- |
| `DOC_EXT_01_MOSPI_NADA_GUIDE` | `VERIFIED_EXTERNAL` | English | Latin | Single-Column + UI | Clean Digital PDF | val | `10023a...` |
| `DOC_ENG_01_SCHOLARSHIP_NOTIFICATION` | `DERIVED_FROM_EXTERNAL` | English | Latin | Single-Column Narrative | Clean Digital | dev | `e612cb...` |
| `DOC_ENG_02_INCOME_CERTIFICATE` | `DERIVED_FROM_EXTERNAL` | English | Latin | Key-Value Form | Clean Digital | val | `d14f2e...` |
| `DOC_ENG_03_TWO_COLUMN_GAZETTE` | `DERIVED_FROM_EXTERNAL` | English | Latin | Two-Column Symmetrical | Clean Digital | challenge | `89f301...` |
| `DOC_HIN_01_ADMIN_CIRCULAR` | `DERIVED_FROM_EXTERNAL` | Hindi | Devanagari | Single-Column Narrative | Clean Digital | dev | `a84ec0...` |
| `DOC_HIN_02_INCOME_CERTIFICATE` | `DERIVED_FROM_EXTERNAL` | Hindi | Devanagari | Key-Value Form | Clean Digital | val | `2b8ca4...` |
| `DOC_HIN_03_TWO_COLUMN_GAZETTE` | `DERIVED_FROM_EXTERNAL` | Hindi | Devanagari | Two-Column Symmetrical | Clean Digital | challenge | `229158...` |
| `DOC_ORI_01_ADMIN_CIRCULAR` | `DERIVED_FROM_EXTERNAL` | Odia | Odia | Single-Column Narrative | Clean Digital | dev | `cb5516...` |
| `DOC_ORI_02_INCOME_CERTIFICATE` | `DERIVED_FROM_EXTERNAL` | Odia | Odia | Key-Value Form | Clean Digital | val | `933dd8...` |
| `DOC_ORI_03_TWO_COLUMN_GAZETTE` | `DERIVED_FROM_EXTERNAL` | Odia | Odia | Two-Column Symmetrical | Clean Digital | challenge | `07f43a...` |
| `DOC_MIX_01_HIN_ENG_SCHOLARSHIP` | `DERIVED_FROM_EXTERNAL` | Mixed En/Hi | Mixed | Key-Value Form | Clean Digital | val | `51cc12...` |
| `DOC_MIX_02_ORI_ENG_SCHOLARSHIP` | `DERIVED_FROM_EXTERNAL` | Mixed En/Or | Mixed | Key-Value Form | Clean Digital | val | `2837bc...` |
| `DOC_TAB_01_MARKSHEET_GRID` | `DERIVED_FROM_EXTERNAL` | English | Latin | 3-Column Data Grid | Clean Digital | val | `3ccb26...` |
| `DOC_DEG_01_HINDI_NOISY_SKEWED` | `DERIVED_FROM_EXTERNAL` | Hindi | Devanagari | Key-Value Form | Noise + Skew 5° | challenge | `35593d...` |
| `DOC_DEG_02_ODIA_LOW_CONTRAST` | `DERIVED_FROM_EXTERNAL` | Odia | Odia | Key-Value Form | Low Contrast + Blur | challenge | `f1ce31...` |

---

### 4. Split Isolation & Leakage Guardrails

1. **Development Split (`dev`):** Used strictly for tuning regular expression field patterns and heuristic thresholds.
2. **Validation Split (`validation`):** Used for comparing baseline vs routed multilingual OCR models.
3. **Challenge Split (`challenge`):** Contains degraded, skewed, multi-column, and adversarial variations. Held immutable during iterative parameter adjustments to prevent hyperparameter over-fitting.
