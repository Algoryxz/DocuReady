# DOCUREADY — LOOP 15 BASELINE AUDIT
## Architectural Audit of Loop 14 Baseline & Multilingual OCR Deficiencies

**Project:** DocuReady  
**Evaluation Target:** Loop 14 Baseline (`ba3e306`)  
**Auditor:** DocuReady Forensic Verification Unit  
**Date:** November 2026  
**Status:** QUALIFIED FOR REGION-AWARE ARCHITECTURE  

---

## 1. Executive Summary

Loop 14 introduced script-aware language discovery and page-level language routing (`eng`, `hin`, `ori`, and combinations) to solve the catastrophic cross-script beam-search interference observed when Tesseract was invoked with `eng+hin+ori` simultaneously across whole pages.

The baseline audit confirms that while Loop 14 achieved dramatic improvements for single-script documents:
- Hindi single-script WER improved from **100.08%** to **44.80%**
- Odia single-script WER improved from **100.86%** to **39.86%**
- Single-column English certificates preserved **0.00%** regression and 100% bit-exact golden parity

**However, Loop 14 leaves a critical architectural flaw unsolved for mixed-script documents.**

---

## 2. Root Cause Analysis: The Page-Level Routing Defect

In Indian administrative reality, documents rarely consist of a single script in isolation. A standard government notification, university marksheet, or scholarship circular exhibits strong spatial heterogeneity:

```
+-----------------------------------------------------------------------+
|  MINISTRY OF TRIBAL AFFAIRS, GOVT OF INDIA (English Header)           |
+-----------------------------------------------------------------------+
|  छात्रवृत्ति सूचना एवं दिशा-निर्देश २०२६ (Hindi Section Title)          |
|  सभी पात्र अनुसूचित जनजाति विद्यार्थियों को सूचित किया जाता है...     |
+-----------------------------------------------------------------------+
|  ଅନୁସୂଚିତ ଜନଜାତି ଛାତ୍ରବୃତ୍ତି ସୂଚନା ୨୦୨୬ (Odia Translation Section)   |
|  ସମସ୍ତ ଯୋଗ୍ୟ ଛାତ୍ରଛାତ୍ରୀ ଆବେଦନ କରିବାକୁ ଅନୁରୋଧ...                       |
+-----------------------------------------------------------------------+
|  TABLE: Application Deadlines & Income Criteria (Bilingual / English) |
+-----------------------------------------------------------------------+
```

### The Inherent Dilemma of Page-Level Routing
1. **Dominant-Script Bias:** When a document has 60% Hindi body and 40% English headers/tables, page-level detection selects either `hin` or `eng+hin`.
2. **Beam-Search Interference:** If `eng+hin` or `eng+hin+ori` is selected for the whole page:
   - English numerals (`2026`) and Latin text in headers get mangled by the Hindi/Odia dictionary weights.
   - Devanagari matras (`ि`, `ी`, `ु`, `ू`, `्`) are misrecognized as Latin punctuation (`' : / -`).
   - Pure Odia text subjected to `eng+hin` collapses into unreadable gibberish.
3. **Single Script Selection Collapse:** If `hin` alone is selected for the whole page:
   - The English header `"MINISTRY OF TRIBAL AFFAIRS"` is completely destroyed (WER 100% on header lines).
   - If `eng` alone is selected, the Hindi and Odia paragraphs suffer 100% character destruction.

---

## 3. Quantitative Evidence from Loop 14 Results

From the Loop 14 benchmark evaluation on mixed and bilingual documents:
- **`DOC_MIX_01_HIN_ENG_SCHOLARSHIP`:**
  - `eng` only: WER = **100.00%** on Hindi body.
  - `hin` only: WER = **78.26%** (destroys English headers and dates).
  - `eng+hin` page-level: WER = **48.91%** (cross-script noise still causes substantial character substitution).
- **`DOC_MIX_02_ORI_ENG_SCHOLARSHIP`:**
  - `eng` only: WER = **100.00%** on Odia body.
  - `ori` only: WER = **68.75%** (destroys English headers and amounts).
  - `eng+ori` page-level: WER = **45.00%** (Latin numerals and abbreviations misclassified).

---

## 4. The Loop 15 Architectural Remedy: Region-Aware OCR Routing

To achieve near-zero cross-script interference without corrupting clean documents, DocuReady must segment the page into distinct spatial regions and route each region to its optimal language model:

1. **Spatial Region Decomposition:**
   - Detect layout boundaries (Header banners, Column blocks, Table grids, Footer bands).
   - Bounding boxes are determined geometrically using whitespace gutters, horizontal projection profiles, and structural layout cues.
2. **Script Identification per Region:**
   - Unicode codepoint analysis for text-bearing layers.
   - Morphological profiling (top Shirorekha headline in Devanagari vs curved top arches in Odia vs Latin baseline) and local script detection for raster blocks.
3. **Targeted Sub-Image OCR:**
   - Crop region from high-resolution page raster.
   - Execute Tesseract with pure target language model (`eng`, `hin`, or `ori`).
   - Avoid compound models (`eng+hin+ori`) except where fine-grained intra-line code-mixing occurs.
4. **Global Coordinate Transformation & Line Assembly:**
   - Translate region-local bounding box coordinates $[x_0, y_0, x_1, y_1]$ into page coordinates:
     $$x_{global} = x_{local} + X_{offset}$$
     $$y_{global} = y_{local} + Y_{offset}$$
   - Merge region tokens into the canonical reading-order reconstruction engine developed in Loop 13.

---

## 5. Architectural Guardrails & Invariants

- **Zero-Regression Guarantee:** Standard single-column English certificates must bypass regional partitioning overhead or produce bit-exact identical line grouping.
- **Coordinate Faithfulness:** No token coordinate bounding box may drift by more than 0.5 points from its true physical location.
- **Offline / Standalone Execution:** All routing and OCR must execute locally on Windows x64 without cloud API dependencies.
- **Deterministic Parity:** Repeated extraction of identical documents must produce bit-exact identical text and confidence outputs.
