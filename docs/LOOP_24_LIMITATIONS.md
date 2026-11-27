# LOOP 24 — KNOWN LIMITATIONS & FUTURE RESEARCH OPPORTUNITIES

## 1. Honest Appraisal of Limitations

While Loop 24 achieved its primary goals (**100.00% precision**, **0 false verifications**, and **2.08 ms overhead**), honest research requires documenting clear limitations:

### 1. Raw Coverage vs Absolute Precision Tradeoff
- On Cohort I, coverage is **18.63%** under the frozen $T^*=70.0$ threshold.
- While precision is 100%, 83 of 102 fields are abstained.
- **Root Cause**: 51 abstentions are driven by OCR token misrecognitions on hyphenated and alphanumeric row identifiers (e.g. `SKU-7734` read as `SKU-T734`). Because DocuReady demands strict token substring matching to avoid coordinate drift, these degraded identifiers cause the extraction to abstain safely rather than falsely guessing.

### 2. Upstream OCR Dependency
- The spatial grid assembly and field extraction engines rely on the upstream OCR tokens emitted by Tesseract.
- When Tesseract fails to detect an entire text line due to extreme low-contrast fading or severe skew $> 15^\circ$, the spatial association engine cannot recover the unindexed tokens.

### 3. Non-Standard Table Formats
- Curved text lines, circular graphs, and non-Euclidean key-value forms are outside the scope of Manhattan table grids.

---

## 2. Recommended Directions for Loop 25

1. **Fuzzy Levenshtein Identifier Matching with Confidence Penalties**:
   - For row identifiers with small character substitutions (e.g. `T734` vs `7734` with Levenshtein distance 1), explore gated fuzzy candidate matching conditioned on column header match and type compatibility.
2. **Multi-Scale Contrast Normalization**:
   - Pre-OCR local adaptive binarization (Sauvola / Niblack filtering) to recover faded dot-matrix print.
