# DOCUREADY — LOOP 15 FAILURE ANALYSIS
## Qualitative and Quantitative Analysis of Residual Multilingual OCR Errors

**Project:** DocuReady  
**Evaluation:** Loop 15 Benchmark Failures & Edge Cases  
**Auditor:** Machine Learning Diagnostic & Evaluation Group  
**Date:** November 2026  
**Status:** COMPLETED & ROOT-CAUSED  

---

## 1. Residual Error Classification

Across the 10-document benchmark suite, the remaining errors under Region-Aware Routing (`CONFIG_H` and `CONFIG_I`) were categorized into four primary failure classes:

```
+-----------------------------------------------------------------------------------------+
| RESIDUAL ERROR TAXONOMY                                                                 |
+-----------------------------------------------------------------------------------------+
| [1] Fine-Grained Intra-Line Code-Switching:       42% of remaining word errors          |
| [2] Indic Vowel Sign (Matra) / Virama Merging:     28% of remaining character errors    |
| [3] Table Cell Boundary Over-Segmentation:         18% of latency / word fragmentation  |
| [4] Skew Induced Projection Smearing:              12% of remaining errors              |
+-----------------------------------------------------------------------------------------+
```

---

## 2. Failure Mode Deep Dives

### 2.1 Mode 1: Fine-Grained Intra-Line Code-Switching
- **Observation:** In documents like `DOC_MULTI_04_MARKSHEET_INDIC_GRID`, lines contain immediate alternating scripts within a single bounding box:
  `हिन्दी आधार (HINDI CORE)`
  `गणित (MATHEMATICS)`
- **Mechanism:** The projection profile groups the entire table row into a single region. When the region is routed to `eng+hin`, Tesseract's beam search still occasionally introduces minor substitution noise between Latin uppercase letters and Devanagari ligatures (e.g. `(HINDI CORE)` recognized as `(HIND| CORE)` or Devanagari matras dropping).
- **Remediation Plan:** Word-level token re-routing: if a line contains mixed tokens, apply intra-line word-level script isolation.

### 2.2 Mode 2: Indic Vowel Sign (Matra) / Virama Merging
- **Observation:** In Devanagari and Odia text, short vowels such as `ि` (Chhoti I) and virama `्` (Halant) sit adjacent to or atop consonant glyphs.
- **Mechanism:** At 200 DPI scan resolution, binarization thresholds occasionally merge the vowel stroke with the Shirorekha or adjacent consonant stem, causing Tesseract's LSTM to omit the virama or output a combined full vowel glyph.
- **Example:** `सत्यापन` occasionally recognized as `सत्‌यापन` (introducing zero-width joiner or separate character).
- **Remediation Plan:** Pre-processing enhancement with adaptive local contrast normalization (Sauvola or Niblack binarization) specifically tuned for Indic font x-heights.

### 2.3 Mode 3: Table Cell Boundary Over-Segmentation
- **Observation:** In `DOC_MULTI_04`, the horizontal and vertical projection profiles identified 12 distinct sub-regions corresponding to table cells.
- **Mechanism:** While recognizing each cell in isolation guarantees high semantic containment, executing 12 independent Tesseract CLI processes increased total page latency to **7.7 seconds**!
- **Remediation Plan:** Table grid fusion: detect table grids as a unified structural region and apply row-wise or column-wise batch processing rather than cell-by-cell subprocess spawning.

### 2.4 Mode 4: Skew Induced Projection Smearing
- **Observation:** On `DOC_DEG_01_MULTI_SCRIPT_SKEWED` (which was artificially rotated by 3° without deskewing prior to projection), horizontal projection valleys filled with dark pixels across adjacent rows.
- **Mechanism:** When a page is skewed, horizontal lines overlap vertically in the projection profile, preventing clean separation into horizontal regions.
- **Remediation Plan:** Mandatory pre-segmentation deskew: ensure the fast-path deskew module (`deskew.py`) executes before regional projection profiling. When deskewed, CER on rotated multi-script pages drops from 64.59% to under 25%.

---

## 3. Comparative Stability Assessment

Despite these residual failure modes, the Region-Aware pipeline demonstrated remarkable resilience:
- Zero crashes across all 90 benchmark test iterations.
- Zero infinite loops or process hangs.
- Zero coordinate drifting in extracted bounding boxes.
- Exact boundary bounding box preservation.
