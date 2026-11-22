# LOOP 18: Failure Taxonomy & Root Cause Analysis

## 1. Executive Summary

As part of the adversarial audit of DocuReady's OCR extraction capabilities, we classified all observed errors across the 25-document expanded corpus and adversarial stress suite into our standardized six-category failure taxonomy.

This analysis establishes the fundamental physical and algorithmic boundaries of the Tesseract OCR engine when operating strictly offline without deep-learning cloud models.

---

## 2. Six-Pillar Failure Taxonomy & Occurrence Profile

```
                           DocuReady OCR Failure Modes
                                       │
        ┌──────────────┬───────────────┼──────────────┬──────────────┬─────────────┐
        ▼              ▼               ▼              ▼              ▼             ▼
   Segmentation  Character/Glyph   Reading-Order    Script       Omission      Artifact
     & Gutter      Confusion        Inversion     Misrouting    (Low Contrast)    Bleed
```

### Pillar 1: Segmentation & Gutter Misalignment
- **Description**: Text columns merged horizontally or single lines improperly split.
- **Root Cause**: Bounding box projection fails when column gutters are narrow (< 15 px) or when table cell borders are broken or dashed.
- **Mitigation in DocuReady**: Spatial layout clustering (`PageOCRData`) and two-column gutter projection analysis.

### Pillar 2: Character & Glyphic Confusion
- **Description**: Substitution errors between visually similar characters.
  - Alphanumeric: `0` $\leftrightarrow$ `O`, `8` $\leftrightarrow$ `B`, `1` $\leftrightarrow$ `I` / `l`, `5` $\leftrightarrow$ `S`.
  - Indic Scripts: Matra detachment (e.g. `ा`, `े`) and conjunct virama omission (`्`).
- **Root Cause**: Tesseract 5 LSTM language model applies dictionary priors that bias ambiguous glyphs toward common English dictionary words rather than arbitrary alphanumeric codes.
- **Mitigation in DocuReady**: Clean normalized critical field matching with punctuation-insensitive and digit-only validation passes.

### Pillar 3: Layout & Reading-Order Inversion
- **Description**: Multi-column text read left-to-right across columns rather than top-to-bottom within each column.
- **Root Cause**: Global OCR processes horizontal scanlines sequentially, interleaving lines from column A and column B.
- **Mitigation in DocuReady**: Column-aware spatial reconstruction and targeted two-column split routing.

### Pillar 4: Script & Language Misrouting
- **Description**: A multilingual document processed with a single-language model (e.g. `eng` only), rendering Devanagari or Odia text as garbled Latin noise (e.g. `_~|#`).
- **Root Cause**: The script probe strip (sampled from central 30% narrative body) might miss minority script tokens located exclusively in the header or footer banner.
- **Mitigation in DocuReady**: Fallback to `MULTILINGUAL_GLOBAL` whenever script distribution shows non-zero counts or when confidence drops below 60%.

### Pillar 5: Omission & Low-Contrast Drop
- **Description**: Entire words or lines missing from OCR output.
- **Root Cause**: Otsu binarization in Tesseract sets a global threshold that wipes out faint text in low-contrast scans (`CHALLENGE_04`).
- **Mitigation in DocuReady**: Abstention gate detects low character density and mean confidence < 38.0, cleanly rejecting the document rather than hallucinating partial tokens.

### Pillar 6: Artifact Bleed & Rubber Stamp Interference
- **Description**: Official rubber stamps, watermarks, or signatures overlaying critical text fields.
- **Root Cause**: Stamp ink merges with stroke pixels of underlying digits, breaking character contour recognition (`STRESS_02`).
- **Mitigation in DocuReady**: Multi-channel color filtering (filtering blue/purple ink channels before binarization) or flagging overlapping bounding boxes for human audit.
