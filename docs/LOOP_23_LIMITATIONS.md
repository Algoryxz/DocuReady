# Loop 23 Limitations & Known Boundary Conditions

## 1. Physical Resolution & Discretization Limits

1. **Sub-6px Character Heights:**
   The morphology engine requires a minimum active character height of 6 pixels to detect baseline zones. Character glyphs rendered below 6px cannot be reliably segmented using pure pixel morphology and will trigger safe abstention.
2. **Touching Digits & Severe Kerning:**
   If the decimal dot touches adjacent numeral strokes on both sides (zero blank columns separating the dot from numbers), lateral isolation cannot verify that the ink is a dot rather than a serif or stroke artifact.
3. **Completely Fused Compound Columns ($< 6\text{ px}$ Gutter):**
   When two numeric columns are printed with fewer than 6 pixels of separation, Tesseract merges the digits into a single token without whitespace (e.g. `125001250`). In such cases, localized interior vertical projection cannot identify a valley without character-level segmentation models, causing the system to safely abstain.

---

## 2. Table Geometry Assumptions

1. **Orthogonal Grid Alignment:**
   The table association pipeline assumes tables are rectilinear with horizontally oriented rows and vertically oriented columns. Highly skewed tables ($> 5^\circ$) or non-orthogonal curved tables require pre-deskewing prior to table association.
2. **Header Hierarchy Depth:**
   The current multi-tier header fusion logic supports two-tier hierarchies (super-header + child header). Hierarchies of 3 or more tiers (e.g. Year $\rightarrow$ Quarter $\rightarrow$ Month $\rightarrow$ Metric) are flattened into a composite header.

---

## 3. Language & Script Boundaries

The micro-glyph disambiguation algorithms are calibrated for Latin/Arabic numerals (`0-9`). Devanagari or Odia numeric scripts (which have distinct structural stroke shapes) bypass Latin micro-glyph disambiguation and rely on multi-lingual script OCR routing established in Loops 14-19.
