# LOOP 20: Technical Boundaries & Operational Limitations

## 1. Geometric & Structural Limitations

1. **Rotated & Skewed Documents (>3° Skew)**:
   - The 1D horizontal and vertical interval projection profiling assumes roughly axis-aligned documents ($<3^\circ$ skew).
   - *Operational Mitigation*: Skewed pages must route through the `deskew.py` preprocessing stage prior to table grid construction.

2. **Hierarchical Multi-Tier Sub-Headers**:
   - Complex nested headers with multiple levels of merged column spans (e.g. 3-tier financial accounting schedules) can cause row index shifts or collapse sub-columns into single intervals.
   - *Boundary*: Tables with up to 2 header rows are supported; tables with $\ge 3$ nested header tiers should route to human review.

3. **Curved / Distorted Warp Scans**:
   - Mobile camera photographs of thick books or bound ledgers with perspective distortion (cylindrical warping) break 1D projection profiling.

---

## 2. OCR Engine Boundaries

1. **Single-Character Glyphs**:
   - Isolated single-character marks (e.g. grade `'O'`, letter `'A'`, roman numeral `'I'`) are vulnerable to Tesseract OCR misclassification when font styling deviates from standard system sans-serif.

2. **Punctuation Sensitivity**:
   - Tiny decimal points (`.` vs `,`) in financial figures can occasionally be dropped if image resolution is below 200 DPI.

---

## 3. Scope & Competition Freeze Boundaries

1. **Zero External API / Cloud Dependencies**:
   - The engine operates strictly offline. Cloud vision APIs (AWS Textract, Google Cloud Document AI) are explicitly excluded by competition rules.

2. **Zero Heavy Neural Model Footprint**:
   - Deep learning table models (>100MB weights requiring GPU) are prohibited by Ponytail discipline and frozen package boundaries.
