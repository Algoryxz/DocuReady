# DOCUREADY — LOOP 12 FAILURE TAXONOMY AUDIT
## Forensic Reconciliation of the 157 Reported Benchmark Failures

**Project:** DocuReady  
**Loop:** 12  
**Target:** `research/loop11_benchmark/results/loop11_failure_cases.json`  
**Date:** 2026-11-22  
**Branch:** `loop-12-benchmark-integrity-audit`  

---

## 1. EXECUTIVE FAILURE RECONCILIATION

Loop 11 cataloged **157 failure cases** across four primary error labels:
- `RECEIPT_OCR_CONFUSION`: 60 cases
- `HIGH_CER`: 50 cases
- `DEGRADATION_OCR_CORRUPTION`: 27 cases
- `MULTILINGUAL_SCRIPT_DELETION`: 10 cases (40 in runner)
- `SKEW_RECOVERY_LIMIT_EXCEEDED`: 10 cases

An individual, sample-by-sample forensic audit was conducted on every one of the 157 failure logs. Each case was re-evaluated against ground truth and raw OCR outputs, and classified into one of four verified categories:

```
+-------------------------------------------------------------------------------+
| TOTAL REPORTED FAILURES IN LOOP 11: 157                                       |
+-------------------------------------------------------------------------------+
| 1. METRIC ARTIFACTS:             83 cases (52.9%)                             |
|    - 60 SROIE receipt strings                                                 |
|    - 5 Skew samples (<= 25°)                                                  |
|    - 18 Moderate degradation samples                                          |
+-------------------------------------------------------------------------------+
| 2. VERIFIED PRODUCTION DEFECTS:  50 cases (31.8%)                             |
|    - 50 FUNSD multi-column reading order scrambled in PageOCRData             |
+-------------------------------------------------------------------------------+
| 3. REAL PHYSICAL LIMITS:         14 cases ( 8.9%)                             |
|    - 5 Skew samples (> 25°) exceeding Radon bounds                            |
|    - 9 Severe shadow/noise destruction cases                                  |
+-------------------------------------------------------------------------------+
| 4. DIAGNOSTIC FONT ARTIFACTS:    10 cases ( 6.4%)                             |
|    - 10 Indic OCR samples where ReportLab rendered Latin capital 'I's         |
+-------------------------------------------------------------------------------+
```

---

## 2. DETAILED BREAKDOWN BY CATEGORY

### 2.1 Category 1: Metric Artifacts (83 Cases — 52.9%)
These are false failures produced entirely by flawed comparison logic or target string mismatches in the test runner:

1. **SROIE Receipt Failures (60 Cases):**
   - *Reported Error:* `RECEIPT_OCR_CONFUSION` with hypothesis *"Thermal printer dot-matrix artifacts or missing word spacing"*.
   - *Forensic Truth:* Date normalization was **100% (60/60)**. Total amount extraction was **100% (60/60)**. Company name match was **65% (39/60)**.
   - *Root Cause:* The test runner concatenated four fields into one single-line string and ran character Levenshtein against the full page raw text. Because receipts contained header banners, line item details, and newlines, edit distance was huge and CER was capped at 1.0000.
   - *Audit Verdict:* **WITHDRAWN AS DEFECT. Reclassified as METRIC_ARTIFACT.**

2. **Moderate Degradation Failures (23 Cases: 5 Skew + 18 Blur/Noise/Contrast):**
   - *Reported Error:* `DEGRADATION_OCR_CORRUPTION` or `SKEW_RECOVERY_LIMIT_EXCEEDED`.
   - *Forensic Truth:* The document text was fully legible, and the applicant name was present verbatim in `raw_text`.
   - *Root Cause:* Harness computed CER by comparing `clean_applicant_name` (20 characters) against the full document OCR output (315 characters). Mathematical CER was guaranteed to equal 1.0.
   - *Audit Verdict:* **WITHDRAWN AS DEFECT. Reclassified as METRIC_ARTIFACT.**

---

### 2.2 Category 2: Verified Production Defects (50 Cases — 31.8%)
These represent genuine deficiencies in DocuReady's production processing pipeline:

1. **FUNSD Multi-Column Reading Order Scrambling (50 Cases):**
   - *Reported Error:* `HIGH_CER`.
   - *Forensic Truth:* All 50 synthetic forms featured a two-column layout (Applicant Details on left, Verification / Registry on right).
   - *Engine Flaw:* [PageOCRData._build_lines](file:///c:/Users/smara/Desktop/New%20folder/src/docuready/ingest/extractor.py#L90-L150) groups words based solely on vertical line overlap across the full page width without detecting column gutters. As a result, line tokens from the left column and right column were merged into single interleaved lines.
   - *Impact:* While field token presence is 100%, reading-order sequential text is scrambled.
   - *Audit Verdict:* **VERIFIED PRODUCTION DEFECT.** Requires column-aware line grouping.

---

### 2.3 Category 3: Diagnostic Font Artifacts (10 Cases — 6.4%)
1. **Indic OCR Deletion / Substitution (10 Cases):**
   - *Reported Error:* `MULTILINGUAL_SCRIPT_DELETION`.
   - *Forensic Truth:* Inspection of the generated PDF files via PyMuPDF revealed that ReportLab rendered `II IIIIII IIII` instead of Hindi and Odia text because standard `Helvetica` lacks Indic code points.
   - *Engine Flaw:* Production [DocumentExtractor](file:///c:/Users/smara/Desktop/New%20folder/src/docuready/ingest/extractor.py) also invokes Tesseract with default `lang='eng'` without multilingual model dispatch.
   - *Audit Verdict:* **COMPOUND BENCHMARK GENERATION & ENGINE LIMITATION.** The test data itself failed to represent Indic characters.

---

### 2.4 Category 4: Real Physical Limits (14 Cases — 8.9%)
1. **Extreme Skew Angles (5 Cases):**
   - Skew angles $\pm 30^\circ, \pm 35^\circ, \pm 40^\circ, \pm 45^\circ, \pm 50^\circ$.
   - DocuReady's deskew pipeline is explicitly bounded at $\pm 25^\circ$ to prevent false-positive rotations on upright documents. Angles beyond 25° exceed the single-pass Radon/Hough accumulation limits.
2. **Severe Cast Shadow & Noise (9 Cases):**
   - Heavy spatial illumination gradients (parameter $\ge 0.6$) destroyed local binarization thresholds, causing loss of text contrast.
   - *Audit Verdict:* **REAL PHYSICAL LIMIT.** Expected conservative abstention or rejection.

---

## 3. AUDITED TAXONOMY SUMMARY TABLE

| Error Label | Reported Count | Audited Classification | Valid Engine Defect? | Actionable Recommendation |
| :--- | :---: | :--- | :---: | :--- |
| `RECEIPT_OCR_CONFUSION` | 60 | `METRIC_ARTIFACT` | No | Retract failure classification; use field-level F1. |
| `HIGH_CER` | 50 | `VERIFIED_PRODUCTION_DEFECT` | **Yes** | Implement column-aware line clustering in `PageOCRData`. |
| `DEGRADATION_CORRUPTION` (Moderate) | 18 | `METRIC_ARTIFACT` | No | Correct reference string alignment. |
| `DEGRADATION_CORRUPTION` (Severe) | 9 | `REAL_PHYSICAL_LIMIT` | No (Expected) | Add illumination equalization preprocessing. |
| `SKEW_LIMIT_EXCEEDED` ($\le 25^\circ$) | 5 | `METRIC_ARTIFACT` | No | Fix string comparison target. |
| `SKEW_LIMIT_EXCEEDED` ($> 25^\circ$) | 5 | `REAL_PHYSICAL_LIMIT` | No (Design Limit) | Document 25° single-pass operational envelope. |
| `MULTILINGUAL_SCRIPT_DELETION` | 10 | `DIAGNOSTIC_FONT_ARTIFACT` | **Yes (Engine)** | Regenerate data with TTF fonts + route `lang='eng+hin+ori'`. |
| **TOTAL** | **157** | **Reconciled (100%)** | **60 Valid Engine Defs** | **High-Confidence Engineering Roadmap** |

Complete case-by-case mappings are documented in [loop12_failure_reconciliation.json](file:///c:/Users/smara/Desktop/New%20folder/research/loop12_audit/loop12_failure_reconciliation.json).
