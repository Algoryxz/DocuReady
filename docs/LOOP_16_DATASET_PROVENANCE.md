# DOCUREADY — LOOP 16 DATASET PROVENANCE REPORT
## Dataset Provenance, Cohort Tracking & Sealed Challenge Partitioning

**Project:** DocuReady — HackNation 2026  
**Engineering Loop:** 16  
**Date:** November 2026  
**Status:** AUDITED, REGISTERED & PARTITIONED  

---

## 1. Compliance, Ethical Standards & Data Safety

In conformance with the HackNation 2026 competition charter and the Digital Personal Data Protection Act (DPDPA 2023):
1. **Zero Private PII:** All evaluation documents are either official open government documentation, public statutory gazette formats, or controlled adversarial fixtures. No private individual's tax records, Aadhaar numbers, or bank account statements are present.
2. **Explicit Cohort Separation:** Every sample is registered with its provenance cohort (`VERIFIED_EXTERNAL`, `DERIVED_FROM_EXTERNAL`, `VERIFIED_SYNTHETIC`).
3. **Partitioning between Validation & Sealed Challenge:**
   - **`PRIMARY_VALIDATION` Split (11 samples):** Used for strategy benchmarking, profiling, and comparative analysis against Loop 15.
   - **`SEALED_CHALLENGE` Split (4 samples):** Kept strictly isolated during selector threshold tuning to prevent benchmark leakage and test overfitting.

---

## 2. Dataset Partitioning & Cohort Breakdown

Registered in `research/loop16/dataset_manifest.json`:

```
+-----------------------------------------------------------------------------------------+
| TOTAL CORPUS SAMPLES: 15                                                                |
+-----------------------------------------------------------------------------------------+
| [A] SPLIT PARTITIONS:                                                                   |
|     - PRIMARY_VALIDATION: 11 samples (73.3%)                                            |
|     - SEALED_CHALLENGE:    4 samples (26.7%)                                            |
|                                                                                         |
| [B] PROVENANCE COHORTS:                                                                 |
|     - VERIFIED_EXTERNAL:    1 sample  (6.7%)  (MoSPI NADA Guide PDF)                    |
|     - DERIVED_FROM_EXTERNAL: 11 samples (73.3%) (Statutory Gazette & Marksheet Formats) |
|     - VERIFIED_SYNTHETIC:    3 samples (20.0%) (Control Certificates & Stress Fixtures) |
+-----------------------------------------------------------------------------------------+
```

---

## 3. Challenge Split Verification

The sealed challenge split evaluates critical operational edge cases:
1. **`CHALLENGE_01_NATIVE_PDF_BILINGUAL`:** Digital vector PDF testing zero-raster-OCR fast-path extraction.
2. **`CHALLENGE_02_ODIA_ENGLISH_GAZETTE_TWO_COL`:** Two-column Odia/English parallel gazette testing spatial de-interleaving.
3. **`CHALLENGE_03_HINDI_ENGLISH_MARKSHEET_ROW_GRID`:** Complex tabular secondary education marksheet testing intra-cell bilingualism.
4. **`CHALLENGE_04_LOW_CONTRAST_UNREADABLE_STRESS`:** Adversarial low-contrast thermal/carbon copy scan testing unreadable abstention gates.

Every sample has an audited SHA-256 hash and verifiable statutory basis.
