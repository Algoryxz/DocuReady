# Loop 21 Limitations & Operational Boundaries

## 1. Scope & System Boundaries

Loop 21 focused exclusively on two concrete architectural challenges in table evidence extraction:
1. **Hierarchical Multi-Tier Column Headers**
2. **Low-Resolution Decimal Point Retention**

While Loop 21 achieved complete resolution of the `VAL_05` and `BLIND_06` defects, the system operates under well-defined boundaries that must not be exceeded.

---

## 2. Document Layout Limitations

### 2.1 Arbitrary 3+ Tier Deep Nested Hierarchies
- **Current Support**: The system supports 2-tier hierarchical headers (Parent category + Leaf column headers) with horizontal span propagation.
- **Limitation**: Tables with 3 or more nested header tiers (e.g., `Financial Year` $\to$ `Quarter 1` $\to$ `Month 1` $\to$ `Sub-Metric`) are currently collapsed into 2 tiers. Deeper multi-level tree hierarchies are not yet modeled.

### 2.2 Row-Span (Merged Row Headers)
- **Current Support**: Column spans (`colspan`) in headers are supported and propagated.
- **Limitation**: Row spans (`rowspan`, where a single label in column 0 vertically spans multiple rows) are currently treated as separate rows where row 1 has an empty label. Downstream extraction relies on label inheritance, which can be ambiguous if multiple sub-tables share identical category names.

### 2.3 Highly Skewed or Rotated Tables ($> 5^\circ$)
- **Current Support**: Preprocessing deskew operates on full document pages up to $\pm 15^\circ$.
- **Limitation**: If a table inside an unskewed document is individually tilted (e.g. pasted or clipped into a collage at an angle), 1D horizontal and vertical projection histograms degrade.

---

## 3. OCR Engine & Numeric Limitations

### 3.1 Single-Character Font Glyphs
- The underlying Tesseract OCR engine occasionally misreads single sans-serif characters (such as grade `O` as `fe}` or `1` as `I`/`l`) at font sizes $\le 12\text{ px}$.
- DocuReady does not apply speculative dictionary substitutions to single characters to avoid introducing hallucinations.

### 3.2 Non-Dot Decimal Separators (European Commas)
- In European numeric formats, decimals use commas (`12,50` instead of `12.50`).
- Because Indian administrative and financial documents exclusively employ period decimal separators (`.` with `,` used for thousand grouping), the decimal point retention algorithm is strictly tuned for baseline dots. Applying it to European comma decimals would require explicit locale configuration.

---

## 4. Architectural Discipline

DocuReady deliberately enforces these boundaries rather than attempting to solve every arbitrary visual variation with uninterpretable, bloated neural models. Every extraction decision must remain traceable, deterministic, and verifiable.
