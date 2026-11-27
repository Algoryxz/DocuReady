# DOCUREADY — LOOP 12 DATASET PROVENANCE AUDIT
## Independent Provenance, Authenticity, Licensing & Generation Forensics

**Project:** DocuReady  
**Loop:** 12  
**Target:** Loop 11 230-Document Benchmark Corpus  
**Audit Date:** 2026-11-22  
**Branch:** `loop-12-benchmark-integrity-audit`  
**Auditor:** DocuReady Benchmark Integrity & Reproducibility Team  

---

## 1. EXECUTIVE PROVENANCE SUMMARY

Loop 11 presented an evaluation across five benchmark suites comprising 230 document files, cataloged under public dataset titles: **FUNSD** (50), **SROIE** (60), **Indic OCR** (40), **DocLayNet** (30), and **DIBCO/Degradation** (50).

This adversarial audit tracked the physical provenance, byte hashes, and generation pathways of all 230 files:

| Suite Name | Claimed Public Baseline | Sample Count | Actual Provenance Category | Provenance Status | Physical Generation Source |
| :--- | :--- | :---: | :--- | :--- | :--- |
| **FUNSD** | ICDAR-OST 2019 Forms | 50 | Category C: Modeled Synthetic Samples | `VERIFIED_SYNTHETIC_MODEL` | `acquire_benchmark_data.py::build_funsd_suite` |
| **SROIE** | ICDAR 2019 Receipts | 60 | Category C: Modeled Synthetic Samples | `VERIFIED_SYNTHETIC_MODEL` | `acquire_benchmark_data.py::build_sroie_suite` |
| **INDIC_OCR** | IIIT-H IndicDLP / ILST | 40 | Category C: Modeled Synthetic Samples | `VERIFIED_SYNTHETIC_MODEL` | `acquire_benchmark_data.py::build_indic_ocr_suite` |
| **DOCLAYNET** | IBM / KDD 2022 Layouts | 30 | Category C: Modeled Synthetic Samples | `VERIFIED_SYNTHETIC_MODEL` | `acquire_benchmark_data.py::build_doclaynet_suite` |
| **DEGRADATION**| DIBCO Binarization | 50 | Category C: Modeled Synthetic Samples | `VERIFIED_SYNTHETIC_MODEL` | `acquire_benchmark_data.py::build_degradation_suite` |
| **TOTAL** | **5 Public Datasets** | **230** | **100% Synthetic Modeled Corpus** | **`VERIFIED_SYNTHETIC_MODEL`** | **Local Python Script via ReportLab/PIL** |

### Key Provenance Finding
**Zero samples (0/230) were downloaded as raw external images from public dataset servers.** All 230 files were generated programmatically on-machine via [acquire_benchmark_data.py](file:///c:/Users/smara/Desktop/New%20folder/research/loop11_benchmark/datasets/acquire_benchmark_data.py). 

While the document geometries, field keys, and layout paradigms were modeled faithfully after the schemas of the respective public datasets, cataloging them as "external datasets" without an explicit synthetic provenance disclosure was misleading. Every sample has now been audited, cryptographically fingerprinted, and categorized under `VERIFIED_SYNTHETIC_MODEL` in [loop12_dataset_provenance.json](file:///c:/Users/smara/Desktop/New%20folder/research/loop12_audit/loop12_dataset_provenance.json).

---

## 2. SUITE-BY-SUITE PROVENANCE & AUTHENTICITY

### 2.1 FUNSD Suite (50 Samples)
- **Claimed Reference:** *Guillaume Jaume et al., "FUNSD: A Dataset for Form Understanding in Noisy Scanned Documents" (ICDAR-OST 2019)*.
- **Physical Media:** 50 PDF files in `research/loop11_benchmark/data/funsd/funsd_001.pdf` through `funsd_050.pdf`.
- **Generation Method:** Generated via ReportLab `SimpleDocTemplate` and `Table` elements. Synthetic forms incorporate 10 randomized institutional intake templates (Directorate of Higher Education, Odisha State Scholarship, etc.).
- **Licensing Context:** Real FUNSD is non-commercial research (CC BY-NC-SA 4.0). Because these samples are locally synthesized without copying original scanned images, there is no third-party copyright encumbrance.
- **Data Split:** 20 DEV, 15 VAL, 15 CHALLENGE.

### 2.2 SROIE Suite (60 Samples)
- **Claimed Reference:** *ICDAR 2019 Competition on Scanned Receipts OCR and Information Extraction*.
- **Physical Media:** 60 PNG images in `research/loop11_benchmark/data/sroie/sroie_001.png` through `sroie_060.png`.
- **Generation Method:** Generated via PIL drawing canvas with monospace font rendering, simulating thermal receipt printer dot-matrix artifacts, cut lines, dates, and currency totals.
- **Licensing Context:** Real SROIE is licensed for research competition use only. The synthetic generation circumvents redistribution liabilities.
- **Data Split:** 25 DEV, 20 VAL, 15 CHALLENGE.

### 2.3 Indic OCR Suite (40 Samples)
- **Claimed Reference:** *IIIT Hyderabad Indic Document Layout Parsing (IndicDLP) & Indian Language Scanned Text*.
- **Physical Media:** 40 PDF files in `research/loop11_benchmark/data/indic_ocr/indic_001.pdf` through `indic_040.pdf`.
- **Generation Method:** Generated via ReportLab canvas drawing government certificate headers with bilingual clauses (Hindi/English and Odia/English).
- **Critical Font Defect Uncovered:** ReportLab's standard Type 1 `Helvetica` font was used to render Devanagari and Odia strings. Because Helvetica lacks Indic glyph encodings, all Indic characters were converted to Latin capital `I`s (`II IIIIII IIII`). The benchmark images literally did not contain Indic characters.
- **Data Split:** 15 DEV, 15 VAL, 10 CHALLENGE.

### 2.4 DocLayNet Suite (30 Samples)
- **Claimed Reference:** *Pfitzmann et al., "DocLayNet: A Large Human-Annotated Dataset for Document-Layout Analysis" (KDD 2022 / IBM)*.
- **Physical Media:** 30 PDF files in `research/loop11_benchmark/data/doclaynet/doclaynet_001.pdf` through `doclaynet_030.pdf`.
- **Generation Method:** Generated via ReportLab complex multi-column frames, section headers, tables, and paragraphs.
- **Licensing Context:** Real DocLayNet is CDLA-Permissive-1.0. Synthetic samples comply with standard local research use.
- **Data Split:** 10 DEV, 10 VAL, 10 CHALLENGE.

### 2.5 Degradation / DIBCO Suite (50 Samples)
- **Claimed Reference:** *Document Image Binarization Contest (ICDAR / ICFHR DIBCO series)*.
- **Physical Media:** 50 PNG images in `research/loop11_benchmark/data/degradation/deg_001_skew.png` through `deg_050_shadow.png`.
- **Generation Method:** 10 clean base administrative certificates perturbed across 5 mathematical degradation regimes:
  1. *Skew:* Bilinear rotation from -20° to +25° (samples 1–10).
  2. *Gaussian Blur:* Radius $\sigma \in [1.0, 5.0]$ (samples 11–20).
  3. *Salt-and-Pepper Noise:* Density $p \in [0.01, 0.15]$ (samples 21–30).
  4. *Low Contrast:* Rescaling factor $\alpha \in [0.15, 0.65]$ (samples 31–40).
  5. *Vignette / Cast Shadow:* Non-linear spatial illumination gradient (samples 41–50).
- **Data Split:** 50 CHALLENGE.

---

## 3. PROVENANCE MANIFEST SUMMARY

All 230 samples have been logged with complete cryptographic provenance in [loop12_dataset_provenance.json](file:///c:/Users/smara/Desktop/New%20folder/research/loop12_audit/loop12_dataset_provenance.json).

```json
{
  "total_records": 230,
  "verified_synthetic_model_count": 230,
  "verified_external_official_count": 0,
  "duplicate_sample_ids": 0,
  "missing_files": 0,
  "hash_algorithm": "SHA-256",
  "provenance_status": "VERIFIED_SYNTHETIC_MODEL"
}
```

Every sample has been unambiguously attributed to its generator function, ground truth schema, and model baseline.
