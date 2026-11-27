# DOCUREADY — LOOP 11 STRUCTURED ERROR ANALYSIS & TAXONOMY
## Independent Dataset Benchmark, OCR Generalization & Performance Frontier

**Project:** DocuReady  
**Phase:** Phase 7 — Error Taxonomy & Forensic Diagnosis  
**Artifact Archive:** `research/loop11_benchmark/results/loop11_failure_cases.json`  
**Total Failures Analyzed:** 157 Independent Failures  
**Date:** 2026-11-22  

---

## 1. COMPREHENSIVE ERROR TAXONOMY

The 157 failure cases identified during the independent benchmark across the 230-sample corpus have been classified into five distinct error categories:

```
+-----------------------------------------------------------------------------------------+
|                          LOOP 11 ERROR TAXONOMY DISTRIBUTION (157)                      |
+--------------------+---------------------+--------------------+--------------------+----+
| RECEIPT_OCR_CONF   | HIGH_CER (Forms)    | DEGRADATION_CORRUP | SCRIPT_DELETION    | SKEW_LIMIT_EXCEEDED
| 60 Cases (38.2%)   | 50 Cases (31.8%)    | 27 Cases (17.2%)   | 10 Cases (6.4%)    | 10 Cases (6.4%)
| Dot-matrix spaces  | Reading order &     | Blur, noise, faint | Missing 'hin'/'ori'| Angles > 15 deg
| Character mergers  | label alignment     | token corruptions  | invocation args    | Radon bounds
+--------------------+---------------------+--------------------+--------------------+----+
```

---

## 2. DETAILED ROOT CAUSE DIAGNOSIS BY CATEGORY

### Category A: `RECEIPT_OCR_CONFUSION` (60 Samples / 38.2%)
- **Symptom:** Character substitution, missing spaces, or extraneous split spaces on low-resolution thermal receipt text.
- **Representative Examples:**
  - Ground Truth: `751007` $\rightarrow$ Hypothesis: `75 1007` (space insertion into postal PIN).
  - Ground Truth: `FEE STAMP` $\rightarrow$ Hypothesis: `FEESTAMP` (word merger due to narrow thermal kerning).
  - Ground Truth: `BARB0BHUBAN` $\rightarrow$ Hypothesis: `BARBOBHUBAN` (Digit 0 misclassified as Latin capital letter 'O').
- **Root Cause Hypothesis:**
  1. Fixed PSM mode (Page Segmentation Mode 3: Fully automatic) assumes standard document prose and misinterprets receipt column tabulations.
  2. Dot-matrix print heads create fragmented glyph strokes that fail Tesseract's connected-component binarization.
- **Classification:** **Benchmark Limitation & Edge-Case Vulnerability**.

---

### Category B: `HIGH_CER` (50 Samples / 31.8%)
- **Symptom:** High Character Error Rate (> 0.30) on structured multi-field application forms (FUNSD suite).
- **Representative Examples:**
  - Horizontal form fields where key label and value are separated by wide white space:
    `Candidate Registration ID:                 OD-2026-99214`
  - Linear text extraction collapses lines out of spatial sequence:
    `Candidate Registration ID: Full Legal Name: Date of Birth: OD-2026-99214 AARAV KUMAR PRADHAN 14/05/2004`
- **Root Cause Hypothesis:**
  `PageOCRData._build_lines` groups word tokens strictly by vertical proximity. When two columns exist, tokens from Column 1 and Column 2 are merged into a single wide line if their vertical baselines align within 4.0 points, disrupting reading order.
- **Classification:** **Structural Extraction Architecture Defect**.

---

### Category C: `DEGRADATION_OCR_CORRUPTION` (27 Samples / 17.2%)
- **Symptom:** Documents with severe speckle noise or contrast fading ($< 0.30$) generate garbled alphanumeric strings instead of triggering conservative abstention.
- **Representative Examples:**
  - Clean Text: `ANNUAL INCOME: INR 180000` under noise $\sigma = 45$ produced:
    `4NNU4L 1NC0M3: 1NR 18OO0O`
- **Root Cause Hypothesis:**
  DocuReady checks `_is_demonstrably_upright` and token confidence. However, if individual corrupted tokens have raw confidence $\ge 45\%$, they bypass the corrupt document rejection gate and pollute downstream normalizers.
- **Classification:** **Safety & False Clearance Risk (P0)**.

---

### Category D: `MULTILINGUAL_SCRIPT_DELETION` (10 Samples / 6.4%)
- **Symptom:** Complete deletion or ASCII corruption of Devanagari and Odia text.
- **Representative Examples:**
  - Ground Truth: `आय प्रमाण पत्र (INCOME CERTIFICATE)`
  - Hypothesis: `(INCOME CERTIFICATE)` (Devanagari deleted).
  - Ground Truth: `ଆୟ ପ୍ରମାଣ ପତ୍ର`
  - Hypothesis: `Si S@008 SMBH` (Odia rendered as ASCII garbage).
- **Root Cause Hypothesis:**
  In `extractor.py`, `pytesseract.image_to_data(img, output_type=...)` omits `lang="eng+hin+ori"`. Tesseract runs exclusively in English mode.
- **Classification:** **Model Configuration Gap (P1)**.

---

### Category E: `SKEW_RECOVERY_LIMIT_EXCEEDED` (10 Samples / 6.4%)
- **Symptom:** Extreme non-orthogonal skews ($|\theta| \ge 18^\circ$) fail deskew correction.
- **Representative Examples:**
  - Skew $\theta = +25.0^\circ$: Radon transform peak search damped by border clipping; estimated angle was $0.0^\circ$, leaving text at $25.0^\circ$ where Tesseract cannot read horizontal lines.
- **Root Cause Hypothesis:**
  `estimate_skew_angle` caps candidate angles and applies heavy dampening past $15^\circ$ to prevent false deskewing on upright tables (Loop 04 safety guard).
- **Classification:** **Documented Design Trade-Off**.

---

## 3. SEVERITY & IMPACT RANKING

| Category | Severity | Failure Count | Impact on Competition Release | Action Plan |
| :--- | :--- | :--- | :--- | :--- |
| **`DEGRADATION_OCR_CORRUPTION`** | **CRITICAL** | 27 | High (Risk of parsing corrupted digits) | Tighten confidence threshold for degraded scans (Backlog P0) |
| **`MULTILINGUAL_SCRIPT_DELETION`** | **MAJOR** | 10 | Medium (Bilingual docs only extract English) | Implement script-zoned multilingual OCR (Backlog P1) |
| **`HIGH_CER` (Reading Order)** | **MAJOR** | 50 | Low on standard PDFs, High on multi-column | Adopt 2D spatial column-aware line grouping (Backlog P1) |
| **`RECEIPT_OCR_CONFUSION`** | **MODERATE** | 60 | Negligible (Target fields 100% extracted) | Add character disambiguation dictionary (Backlog P2) |
| **`SKEW_RECOVERY_LIMIT_EXCEEDED`** | **MINOR** | 10 | Low (Real scans rarely exceed $15^\circ$) | Maintain conservative upright gate (Preserved) |
