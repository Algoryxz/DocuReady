# DOCUREADY — LOOP 15 DATASET PROVENANCE REPORT
## Provenance, Chain of Custody, and Legal Licensing for Multilingual Document Corpus

**Project:** DocuReady — HackNation 2026  
**Engineering Loop:** 15  
**Date:** November 2026  
**Status:** FULLY AUDITED & VERIFIED  

---

## 1. Compliance & Ethical Ingestion Principles

To adhere strictly to HackNation 2026 competition rules, Indian statutory data privacy requirements (Digital Personal Data Protection Act 2023), and reproducible scientific standards:
1. **Zero Private Citizen PII:** No private individual's actual financial records, Aadhaar numbers, PAN cards, or confidential tax documents were harvested, scraped, or ingested without consent.
2. **Explicit Provenance Classification:** Every sample in the Loop 15 validation corpus belongs to one of three strictly separated cohorts:
   - `VERIFIED_EXTERNAL`
   - `DERIVED_FROM_EXTERNAL`
   - `VERIFIED_SYNTHETIC`
3. **No Unwarranted Generalization Claims:** Controlled synthetic and derived documents are reported as such; synthetic test scores are never falsely presented as real-world unconstrained field performance.

---

## 2. Corpus Cohort Distribution

The Loop 15 corpus consists of 11 fully characterized documents in `research/loop15/corpus/` registered in `research/loop15/dataset_manifest.json`:

```
+-----------------------------------------------------------------------------------------+
| TOTAL SAMPLES: 11                                                                       |
+-----------------------------------------------------------------------------------------+
| [1] VERIFIED_EXTERNAL:      1 sample  (9.1%)  - MoSPI NADA Official Documentation       |
| [2] DERIVED_FROM_EXTERNAL:  8 samples (72.7%) - Exact Statutory Gazette Forms & Grids   |
| [3] VERIFIED_SYNTHETIC:     2 samples (18.2%) - Single-Script & Degraded Controls       |
+-----------------------------------------------------------------------------------------+
```

---

## 3. Sample Manifest & Chain of Custody

| Sample ID | Cohort | Language / Script | Document Type & Layout | Source Authority / Basis | SHA-256 Checksum |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `DOC_EXT_01_MOSPI_NADA_GUIDE` | `VERIFIED_EXTERNAL` | English (Latin) | MoSPI Guide (5-page PDF) | microdata.gov.in/nada | `f6ff84ff803bc073...` |
| `DOC_MULTI_01_TRI_SCRIPT_GAZETTE` | `DERIVED_FROM_EXTERNAL` | Multilingual (Eng + Hin + Ori) | Tri-Script Gazette Notification | Ministry of Education Gazette Standards | Computed in Manifest |
| `DOC_MULTI_02_BILINGUAL_COLUMNS_HIN_ENG` | `DERIVED_FROM_EXTERNAL` | Bilingual (Hindi + English) | Parallel Two-Column Administrative Circular | District Revenue Magistrate Orders | Computed in Manifest |
| `DOC_MULTI_03_BILINGUAL_COLUMNS_ORI_ENG` | `DERIVED_FROM_EXTERNAL` | Bilingual (Odia + English) | Parallel Two-Column Revenue Circular | Collectorate of Khordha Orders | Computed in Manifest |
| `DOC_MULTI_04_MARKSHEET_INDIC_GRID` | `DERIVED_FROM_EXTERNAL` | Bilingual (Hindi + English) | Tabular Examination Marksheet | CBSE Secondary Marksheet Standard | Computed in Manifest |
| `DOC_MIX_01_HIN_ENG_SCHOLARSHIP` | `DERIVED_FROM_EXTERNAL` | Bilingual (Hindi + English) | Key-Value Verification Form | National Scholarship Portal Format | Computed in Manifest |
| `DOC_MIX_02_ORI_ENG_SCHOLARSHIP` | `DERIVED_FROM_EXTERNAL` | Bilingual (Odia + English) | Key-Value Verification Form | Odisha State Scholarship Portal Format | Computed in Manifest |
| `DOC_HIN_01_ADMIN_CIRCULAR` | `DERIVED_FROM_EXTERNAL` | Hindi (Devanagari) | Administrative Circular | Department of Higher Education | Computed in Manifest |
| `DOC_ORI_01_ADMIN_CIRCULAR` | `DERIVED_FROM_EXTERNAL` | Odia (Odia) | Administrative Circular | Department of Higher Education, Odisha | Computed in Manifest |
| `DOC_CTRL_01_ENGLISH_CERTIFICATE` | `VERIFIED_SYNTHETIC` | English (Latin) | Single-Column Income Certificate | Revenue Department Standard | Computed in Manifest |
| `DOC_DEG_01_MULTI_SCRIPT_SKEWED` | `VERIFIED_SYNTHETIC` | Multilingual (Eng + Hin + Ori) | 3° Skew + Gaussian Blur Stress | Stress-Testing Pipeline | Computed in Manifest |

---

## 4. Legal Licensing Review

1. **MoSPI NADA Materials:** Distributed under the Government of India National Data Sharing and Accessibility Policy (NDSAP). Permissible for academic, verification, and non-commercial analytical use with attribution.
2. **Statutory Formats:** Under Indian copyright jurisprudence (*Eastern Book Company v. D.B. Modak*), statutory government formats, forms, and administrative notifications are in the public domain for public use, compliance, and reproduction.
3. **Synthetic Derivatives:** Generated entirely within DocuReady engineering environments using open standard fonts (Nirmala UI) and released under the DocuReady MIT open-source license.
