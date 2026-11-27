# LOOP 16: Technical Boundaries & Explicit Limitations

## 1. Overview

While the Loop 16 Adaptive Strategy Selector significantly improves OCR accuracy and cuts processing latency across diverse Indian document formats, rigorous engineering requires documenting its explicit boundaries, edge cases, and known limitations.

---

## 2. Script & Language Coverage Boundaries

1. **Restricted to English, Hindi, and Odia:**
   - The current rule-based script classifier and traineddata discovery pipeline are calibrated specifically for:
     * Latin (`eng` / English)
     * Devanagari (`hin` / Hindi)
     * Odia (`ori` / Odia)
   - Other major Indian languages recognized under the Eighth Schedule of the Constitution of India (e.g., Bengali, Tamil, Telugu, Marathi, Gujarati, Kannada, Malayalam, Punjabi, Assamese) are currently unsupported and will default to Latin or compound fallback.

2. **Minimum Glyph Count Threshold ($\ge 8$ glyphs):**
   - The thumbnail probe requires at least 8 recognizable Unicode characters in a script to declare its presence.
   - Isolated single-word Indic stamps, acronyms, or logos containing fewer than 8 glyphs may fail the threshold, leading the selector to choose `FAST_PATH_ENG` instead of a multilingual compound model.

---

## 3. Image Resolution & Font Size Limits

1. **700px Width Thumbnail Limit:**
   - The fast profiling pass operates on a 700px width grayscale thumbnail to maintain sub-30ms latency.
   - For document text formatted at tiny font sizes ($< 8\text{ pt}$ at 300 DPI), downsampling to 700px blurs fine vowel matras (such as Devanagari *chhoti-i* diacritics or Odia overhead loops). In such borderline cases, the probe may undercount Indic characters.

2. **Contrast & Faint Ink Threshold:**
   - The abstention gate triggers when foreground ink density is $< 0.005$ and Michelson contrast is $< 15$.
   - While effective for blank pages and severely faded photocopies, documents with faint carbon-copy entries or watermarked security paper may occasionally trigger premature abstention if lighting is uneven.

---

## 4. Geometric & Layout Segmentation Constraints

1. **Manhattan Layout Assumption:**
   - The column detector analyzes vertical projection profiles between $40\%$ and $60\%$ of page width to detect vertical quiet gutters.
   - Documents with non-Manhattan layouts (e.g., diagonal text, triangular text wraps, curved text around circular official seals, or multi-column grids with 3 or more asymmetric columns) cannot be cleanly segmented by the current two-column vertical gutter heuristic.

2. **Horizontal Table Rule Dependency:**
   - Table detection relies on detecting at least 3 continuous horizontal rules spanning $> 60\%$ of page width.
   - Borderless tables (whitespace-aligned tables with no printed grid lines) are not classified as tables by the rule detector and may be misclassified as multi-column layouts if a vertical gutter is present.

3. **Absence of Pre-OCR Affine Deskewing:**
   - The engine does not perform automatic deskewing or rotation before OCR.
   - Documents with physical scan tilt $> 2.5^\circ$ experience baseline fragmentation, increasing CER significantly (as observed in `DOC_DEG_01_MULTI_SCRIPT_SKEWED`).

---

## 5. Deployment & System Boundaries

1. **Local Offline Execution Only:**
   - The system operates 100% locally on Windows x64. It does not utilize cloud vision models, external APIs, or remote GPUs.
   - Processing throughput is bound by CPU single-core performance during Tesseract execution.

2. **Traineddata File Dependencies:**
   - The system requires `eng.traineddata`, `hin.traineddata`, and `ori.traineddata` in the local `tessdata` directory. If Indic traineddata files are missing, the engine gracefully degrades to `eng` with a logged diagnostic warning.
