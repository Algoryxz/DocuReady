# LOOP 17: Dataset Provenance, Corpus Manifest & Licensing

## 1. Corpus Overview & Governance

The Loop 17 evaluation corpus comprises **20 standardized document samples** designed to test multilingual OCR efficiency, reading order preservation, and critical-field extraction under realistic Indian administrative conditions.

All documents strictly adhere to the following safety constraints:
1. **Zero PII Exposure:** No real living citizen personal identification, phone numbers, or private tax documents are stored in the repository. All names and identifiers use synthetic references (e.g. `ROHIT VERMA`, `DL-REV-2026-9812`, `CPAO-2026-884910`) formatted identically to real government notices.
2. **Deterministic Reproducibility:** Every document is tracked in `research/loop17/dataset_manifest.json` with an immutable SHA-256 hash.
3. **Split Isolation:** The corpus is split into 14 `PRIMARY_VALIDATION` documents and 6 `SEALED_CHALLENGE` documents to prevent hyperparameter overfitting.

---

## 2. Complete 20-Document Provenance Manifest

| Sample ID | Format | Split | Provenance Category | Source Institution / Format | License & Terms | SHA-256 Hash |
|---|---|---|---|---|---|---|
| `DOC_EXT_01_MOSPI_NADA_GUIDE` | PDF | `PRIMARY_VALIDATION` | `VERIFIED_EXTERNAL` | Ministry of Statistics & PI, GoI | Open Government Data Policy (India) | `20267cb1de293a786afba87df62c74cd6ee942accf27b631bb31afe767d9fa7a` |
| `DOC_CTRL_01_ENGLISH_CERTIFICATE` | PNG | `PRIMARY_VALIDATION` | `VERIFIED_SYNTHETIC` | Revenue Dept Standard Format | Open Access / Synthetic Baseline | `3ae1db7835d045a5874221a712f5ba7d3e6ba18c7ba28ef7bf2666a0149021eb` |
| `DOC_HIN_01_ADMIN_CIRCULAR` | PNG | `PRIMARY_VALIDATION` | `DERIVED_FROM_EXTERNAL` | Central Hindi Administrative Circular | GoI Public Domain Circular | `dbb5f93eef250559eb4e417537b03ca85a3637cb335e236317bc2d447d79b940` |
| `DOC_ORI_01_ADMIN_CIRCULAR` | PNG | `PRIMARY_VALIDATION` | `DERIVED_FROM_EXTERNAL` | Odisha Govt Administrative Circular | State Govt Public Notice | `fe5d8b76fb2193b216c52fc996d933e144a706596919dd76eebeea0ad96d5b0c` |
| `DOC_MIX_01_HIN_ENG_SCHOLARSHIP` | PNG | `PRIMARY_VALIDATION` | `DERIVED_FROM_EXTERNAL` | National Scholarship Portal Format | Open Administrative Template | `1c4597b41e6cfa878faeaebc378414b2d56cbf3e4f718816c1ce53c0d7b2750e` |
| `DOC_MIX_02_ORI_ENG_SCHOLARSHIP` | PNG | `PRIMARY_VALIDATION` | `DERIVED_FROM_EXTERNAL` | Odisha State Scholarship Portal | State Portal Open Format | `41a6b0c2a71f005fbaee2ef44dfcf05bbdf0d9f4851221b2dd723d3cc961b18d` |
| `DOC_MULTI_01_TRI_SCRIPT_GAZETTE` | PNG | `PRIMARY_VALIDATION` | `DERIVED_FROM_EXTERNAL` | Trilingual Official State Gazette | Public Domain Gazette | `bb94132808c10443224be501ee8242c3f81e33d45fa286395b3d75899933227d` |
| `DOC_MULTI_02_BILINGUAL_COLUMNS_HIN_ENG` | PNG | `PRIMARY_VALIDATION` | `DERIVED_FROM_EXTERNAL` | Two-Column Hindi-English Gazette | Public Domain Gazette | `aebba2ec276dfd2ce45d94e339b1dd26da362b8015cf0154bf5a9ca2ac4dbfe5` |
| `DOC_MULTI_03_BILINGUAL_COLUMNS_ORI_ENG` | PNG | `PRIMARY_VALIDATION` | `DERIVED_FROM_EXTERNAL` | Two-Column Odia-English Gazette | State Public Domain Gazette | `2201d1c828ca1eb85db767db073539fc2a29731671fc61219fc77c68b8e0e7ee` |
| `DOC_MULTI_04_MARKSHEET_INDIC_GRID` | PNG | `PRIMARY_VALIDATION` | `DERIVED_FROM_EXTERNAL` | CBSE Academic Statement of Marks | Open Academic Template | `9ea63a125a07159787ffdafa76b262198084a5cbece87189fa943ef0c79fc61a` |
| `DOC_DEG_01_MULTI_SCRIPT_SKEWED` | PNG | `PRIMARY_VALIDATION` | `DERIVED_FROM_EXTERNAL` | Degraded Multi-Script Scan | Public Notice / Degraded Test | `87570535cb0e49ca23d8816a19f3a5ec9a738bf54e6371cb14b533cb42e47262` |
| `DOC_EXT_02_PENSION_DISBURSEMENT_ORDER` | PNG | `PRIMARY_VALIDATION` | `DERIVED_FROM_EXTERNAL` | Central Pension Accounting Office (CPAO) | CPAO Public Guidance Template | `1ea00ee123cb118a5e8c15db29b5c3080be86105c3ca5531d27976e19be55d99` |
| `DOC_EXT_03_UNIVERSITY_CONVOCATION_DEGREE` | PNG | `PRIMARY_VALIDATION` | `DERIVED_FROM_EXTERNAL` | Utkal University Degree Template | Academic Open Format | `424b94f09d82136e054ae0d9fef0384a329ef387ae4f9b3607775a285d89f81a` |
| `DOC_EXT_04_LAND_REVENUE_KHATAUNI_RECORD` | PNG | `PRIMARY_VALIDATION` | `DERIVED_FROM_EXTERNAL` | UP Bhulekh Land Record Format | Revenue Dept Open Format | `eb54f3b06cf72a56111f124976766dbb7c8449c25d808e92ce01d812328109bf` |
| `CHALLENGE_01_NATIVE_PDF_BILINGUAL` | PDF | `SEALED_CHALLENGE` | `VERIFIED_SYNTHETIC` | Digital PDF with Native Text | Synthetic Challenge Baseline | `5019d363b4bca45876008fbcc515a676b0ee6b4d360ef82bf24cbbaef6061327` |
| `CHALLENGE_02_ODIA_ENGLISH_GAZETTE_TWO_COL` | PNG | `SEALED_CHALLENGE` | `DERIVED_FROM_EXTERNAL` | Odisha State Gazette Two-Column | State Gazette Notification | `d866a2cbdbb1dd1a733ec6e2d14da2e4b4764d84f22c6080e7eb22f3001851e3` |
| `CHALLENGE_03_HINDI_ENGLISH_MARKSHEET_ROW_GRID` | PNG | `SEALED_CHALLENGE` | `DERIVED_FROM_EXTERNAL` | BSEB Secondary Marksheet Format | Academic Open Template | `a01ecb0b8dbb6dc4697ec76ce5b1ebfe29783bb175d78a8767e7616198f6d895` |
| `CHALLENGE_04_LOW_CONTRAST_UNREADABLE_STRESS` | PNG | `SEALED_CHALLENGE` | `VERIFIED_SYNTHETIC` | Faint Photocopy Simulation | Stress Baseline | `f2868ff1f6004b733737b8d8adbe5591c01594918e5ff41249ff197171e06fa5` |
| `CHALLENGE_05_ROTATED_SKEW_GAZETTE` | PNG | `SEALED_CHALLENGE` | `DERIVED_FROM_EXTERNAL` | Gazette with 2.8° Scan Tilt | Public Notice Scan Stress | `cb0ca431e21b8b72e1188365612f00f07fa1a4c9adcaee53496bc43ec5e7f1aa` |
| `CHALLENGE_06_FAINT_SEAL_OVER_NUMERIC_ID` | PNG | `SEALED_CHALLENGE` | `DERIVED_FROM_EXTERNAL` | Certificate with Overlapping Rubber Stamp | Revenue Dept Scan Stress | `c3e5287c880a65664dae6878ea64516fcda6bc3aeb5c20eb81ec9d774f260195` |

---

## 3. Cohort Composition Summary

- **Total Documents:** 20
- **Primary Validation Cohort:** 14 (70%)
- **Sealed Challenge Cohort:** 6 (30%)
- **Language Distribution:**
  - Pure English: 3
  - Pure Hindi (Devanagari): 3
  - Pure Odia: 2
  - Bilingual Hindi-English: 7
  - Bilingual Odia-English: 3
  - Trilingual English-Hindi-Odia: 2
- **Structured Critical Field Contracts:** 8 documents annotated with ground truth JSON contracts in `research/loop17/critical_fields/`.
