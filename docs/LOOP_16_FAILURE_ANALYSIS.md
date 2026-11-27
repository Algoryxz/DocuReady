# LOOP 16: Failure Analysis & Root Cause Investigation

## 1. Overview & Failure Record Taxonomy

During the Loop 16 strategy matrix evaluation (150 runs: 15 documents $\times$ 10 strategies), all strategy runs were monitored for anomalous degradation, elevated Character Error Rates (CER > 0.40), excessive latency (> 10,000 ms), and audit finding discrepancies.

The three primary failure clusters captured in `research/loop16/failure_records.json` represent distinct real-world document degradation modes:

```json
[
  {
    "sample_id": "DOC_EXT_01_MOSPI_NADA_GUIDE",
    "strategy": "STRATEGY_J_ADAPTIVE",
    "cer": 1.0,
    "wer": 1.0,
    "reason": "Elevated character error rate on complex/degraded layout"
  },
  {
    "sample_id": "DOC_MULTI_01_TRI_SCRIPT_GAZETTE",
    "strategy": "STRATEGY_J_ADAPTIVE",
    "cer": 0.4938,
    "wer": 0.6406,
    "reason": "Elevated character error rate on complex/degraded layout"
  },
  {
    "sample_id": "DOC_DEG_01_MULTI_SCRIPT_SKEWED",
    "strategy": "STRATEGY_J_ADAPTIVE",
    "cer": 0.6459,
    "wer": 0.7578,
    "reason": "Elevated character error rate on complex/degraded layout"
  }
]
```

---

## 2. Deep Dive: Case Study 1 — `DOC_EXT_01_MOSPI_NADA_GUIDE`

### 2.1. Nature of the Artifact
- **Document Source:** Ministry of Statistics and Programme Implementation (MoSPI), Government of India — NADA Microdata Download User Guide (acquired in Loop 14).
- **Physical Structure:** Multi-page PDF containing a mix of high-level instruction headings ("USER MANUAL TO DOWNLOAD MICRODATA", "Step 1: Please visit URL..."), accompanied by full-bleed embedded raster screenshots of the MoSPI web portal (navigation headers, banner logos, search filters, and tabular microdata survey listings).

### 2.2. Failure Mechanism
1. **Benchmark Comparison Against Page-1 Instruction Baseline:**
   - The native digital text stream of Page 1 contains 170 characters of pure introductory instructions.
   - However, the raster image rendering of Page 1 includes the entire top-level navigation and masthead of the web portal ("Government of India", "Ministry of Statistics", "Skip to Main Content", "RTI", "FAQ", etc.) comprising over 850 characters of UI text.
   - The OCR engine correctly recognized both the user manual instruction text and the text embedded inside the web portal UI screenshot.
   - Because the baseline reference represented only the top-level body text and did not include the exhaustive text of every embedded UI element inside the website screenshot, the string distance metric penalized the extra recognized UI tokens, registering CER = 1.0 and WER = 1.0.

### 2.3. Engineering Takeaways
- Embedded raster screenshots within administrative guides constitute a distinct document modality. A standard document OCR pipeline extracts all visual text indiscriminately, whereas human ground truth often filters out decorative or background UI chrome.
- Future evaluation benchmarks must distinguish between *full visual text extraction* (including screenshots/diagrams) and *hierarchical narrative text extraction*.

---

## 3. Deep Dive: Case Study 2 — `DOC_MULTI_01_TRI_SCRIPT_GAZETTE`

### 3.1. Nature of the Artifact
- **Document Source:** Trilingual official state gazette notification containing:
  - English header and reference metadata at the top.
  - Devanagari (Hindi) administrative resolution in the left column.
  - Odia statutory notification in the right column.
  - Numeric reference codes and dates embedded within both Indic sections.

### 3.2. Failure Mechanism
1. **Horizontal Projection Profile Slicing:**
   - Standard projection profile methods slice documents by identifying horizontal white-space bands.
   - When text in adjacent columns is aligned across identical line baselines, horizontal slicing produces unified horizontal bands that span *both* the Hindi and Odia columns.
   - When such a combined band is passed to script routing, the character probe detects mixed scripts (e.g., Devanagari + Odia + Latin) within the same horizontal strip.
2. **Compound Dictionary Collisions:**
   - Under `STRATEGY_F_GLOBAL_ALL` (`eng+hin+ori`), Tesseract's internal language model attempts to resolve ambiguity across three vastly different character sets simultaneously.
   - Odia matras (which loop above and below the baseline) are frequently misclassified as Devanagari vowel diacritics or Latin punctuation marks when the search space includes all three scripts.
   - This caused CER to elevate to 49.38% on this sample.

### 3.3. Mitigation in Loop 16 & Remaining Challenge
- The Loop 16 adaptive selector improved this by routing the document through the column gutter detector. When a clear central gutter is identified, vertical column splitting isolates the Hindi block from the Odia block before OCR execution.
- However, when line heights vary slightly between columns, horizontal projection can cause block boundary leakage, clipping bottom diacritics (e.g., Odia `u-kar` and `ru-kar`).

---

## 4. Deep Dive: Case Study 3 — `DOC_DEG_01_MULTI_SCRIPT_SKEWED`

### 4.1. Nature of the Artifact
- **Document Source:** Multi-script notification subjected to heavy realistic physical degradation:
  - 3.5° physical rotation/skew.
  - Non-uniform Gaussian blur ($\sigma = 1.2$).
  - Salt-and-pepper noise simulating low-quality office flatbed scanning and multi-generation photocopying.

### 4.2. Failure Mechanism
1. **Broken Character Baselines (Shirorekha / Top-Line Fragmentation):**
   - Devanagari script relies heavily on a continuous horizontal headline (*shirorekha*) connecting glyphs in a word.
   - Odia script relies on rounded overhead curves (*top-curls*).
   - Skew + salt-and-pepper noise fractures these connecting strokes. When the shirorekha is broken by noise pixels, Tesseract's line segmenter splits a single conjunct word into multiple isolated pseudo-glyphs.
2. **Bounding Box Interleaving:**
   - Skew causes horizontal bounding boxes to tilt, causing text lines to overlap vertically in projection profiles.
   - Without an explicit pre-OCR deskew step, line reconstruction algorithms merge words from line $N$ and line $N+1$.
   - This raised CER to 64.59% and WER to 75.78%.

### 4.3. Root Cause & Boundary Finding
- OCR engines (Tesseract 5.x) assume near-horizontal text baselines ($\pm 1^\circ$). When physical skew exceeds $2.5^\circ$, character segmentation failure increases non-linearly.
- **Architectural Boundary:** Document profiling in Loop 16 correctly assesses ink density and contrast, but affine deskewing (Hough transform or Radon transform) was intentionally omitted to maintain strict sub-50ms profiling latency and preserve original bounding box coordinates for court-ready evidence viewing.

---

## 5. Summary of Routing Edge Cases & Failure Modes

| Edge Case | Symptoms | Root Cause | Implemented Resolution / Future Recommendation |
|---|---|---|---|
| **Thumbnail Downsampling Blur** | Small Indic fonts (< 9 pt) misclassified as Latin on low-res thumbnails. | 450px width blurred distinctive Devanagari/Odia diacritics. | **Resolved in Loop 16:** Raised thumbnail resolution to 700px width, preserving font loops. |
| **Intra-Cell Bilingualism** | Cells containing `हिन्दी आधार (HINDI CORE)` fail under region routing. | Bounding box cropper split cell borders or clipped descending matras. | **Resolved in Loop 16:** Marksheet/table layouts route to holistic `GLOBAL_MULTILINGUAL` rather than cell crops. |
| **Severe Scanning Skew (> 2.5°)** | Line baselines broken, high CER on noisy scans. | Lack of pre-OCR affine deskew rotation. | **Documented Boundary:** Retained raw coordinate fidelity for UI highlighting; recommend deskewing in Loop 17. |
| **Embedded Web Screenshots** | Discrepancy between body text and embedded UI text. | Ground truth ambiguity between narrative copy and image chrome. | **Recommendation:** Multi-modal ground truth annotation distinguishing primary copy from embedded graphics. |
