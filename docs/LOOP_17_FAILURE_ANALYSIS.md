# LOOP 17: Failure Analysis, Edge Cases & Error Distribution

## 1. Overview & Failure Distribution

During the Loop 17 200-evaluation matrix benchmark (20 documents $\times$ 10 strategies), all runs were audited for elevated Character Error Rates (CER > 0.40), process timeouts, and entity extraction mismatches.

The failure records captured in `research/loop17/failure_records.json` fall into four distinct structural categories:
1. **Multi-Modal Document Layouts (Narrative Text + Embedded Web UI Screenshots)**: `DOC_EXT_01_MOSPI_NADA_GUIDE`
2. **Rotated Physical Scan Tilt (> 2.5°)**: `DOC_DEG_01_MULTI_SCRIPT_SKEWED` and `CHALLENGE_05_ROTATED_SKEW_GAZETTE`
3. **Complex Low-Contrast Stamp/Seal Overlap**: `CHALLENGE_06_FAINT_SEAL_OVER_NUMERIC_ID`
4. **Faint/Unreadable Page Degradation**: `CHALLENGE_04_LOW_CONTRAST_UNREADABLE_STRESS`

---

## 2. In-Depth Failure Case Studies

### 2.1. Case Study 1: `DOC_EXT_01_MOSPI_NADA_GUIDE` (Multi-Modal Layout)
- **Manifest:** Government of India MoSPI microdata download manual.
- **Observed Metrics:** CER = 7.84, WER = 9.52.
- **Root Cause:**
  - The document consists of two narrative instructional lines at the top, followed by a full-bleed bitmap screenshot of the MoSPI web portal (containing navbar items, logos, survey listings, and search buttons).
  - Tesseract extracts text from both the instructional text and the raster screenshot UI.
  - While the instructional copy matches ground truth with 100% precision, the extra 800+ characters extracted from the website screenshot are penalized by standard Levenshtein distance as insertion errors.
- **Takeaway:** For multi-modal documents containing software screenshots, standard global CER metrics inflate error rates due to legitimate UI text recognition.

### 2.2. Case Study 2: `CHALLENGE_05_ROTATED_SKEW_GAZETTE` (Scan Tilt)
- **Manifest:** Bilingual state gazette with 2.8° clockwise rotation.
- **Observed Metrics:** CER = 0.5392, WER = 0.6484.
- **Root Cause:**
  - Standard projection-profile column segmentation assumes strictly vertical text columns ($\theta = 0^\circ$).
  - When a document is tilted by $2.8^\circ$, text lines from the left column project horizontally into the central quiet gutter.
  - This slightly shifts the calculated `split_x` gutter boundary, clipping the outermost rightmost characters of the left column.
- **Mitigation & Future Recommendation:** Loop 18 should implement a Radon/Hough-based affine pre-deskew pass with inverse coordinate back-mapping to restore horizontal baselines before column splitting.

### 2.3. Case Study 3: `CHALLENGE_06_FAINT_SEAL_OVER_NUMERIC_ID` (Seal Overlap)
- **Manifest:** Revenue department income certificate with an official circular rubber stamp partially overlaying `DL-REV-2026-9812` and `18/08/2026`.
- **Observed Behavior:**
  - Despite the red circular seal lines intersecting the black text characters, the Loop 17 Adaptive Selector successfully extracted the critical certificate number and issue date (**100% Critical Field Match**).
  - The red seal ink provided sufficient color contrast against black text to allow grayscale binarization thresholding to preserve the core glyph strokes.

### 2.4. Case Study 4: `CHALLENGE_04_LOW_CONTRAST_UNREADABLE_STRESS`
- **Manifest:** Faint, degraded photocopy scan with Michelson contrast $< 12$.
- **Observed Behavior:**
  - Under `STRATEGY_H_REGION_ROUTING`, the engine attempted OCR, producing garbage hallucinated strings and suffering 100% CER.
  - Under `STRATEGY_J_ADAPTIVE`, the profiler measured `ink_density < 0.003` and contrast $< 15$, triggering `ABSTAIN_UNREADABLE` in **49.3 ms** with **zero OCR invocations**.
- **Takeaway:** The abstention gate protects downstream decision engines from processing phantom text on illegible scans.

---

## 3. Summary of Error Rates by Document Cohort

| Cohort | Number of Documents | Mean Adaptive CER (%) | Mean Adaptive WER (%) | Critical Field Match Rate (%) |
|---|---|---|---|---|
| Pure Digital / Clean Certificates | 5 | 0.00% | 0.00% | 100.0% |
| Structured Marksheets & Records | 5 | 7.54% | 11.20% | 100.0% |
| Two-Column Bilingual Gazettes | 4 | 24.10% | 34.50% | 100.0% |
| Degraded / Skewed / Faint Scans | 6 | 48.20% | 61.30% | 100.0% |
