# Loop 22 — Architectural Boundaries & Limitations

**Status:** Honest Assessment of Edge Cases and Structural Ceilings  
**Module:** `src/docuready/ingest/table_association.py`

---

## 1. Document Complexity Ceilings

While Loop 22 substantially hardened evidence association and selective verification, the following known structural boundaries remain:

### A. Sub-8px Raster Character Heights
When text is rendered or scanned at resolutions where total character height is $\le 8\text{ px}$ (e.g. 6pt fonts at 150 DPI), isolated punctuation dots (periods, commas, colons) often occupy only 1 pixel and touch adjacent character bounding boxes. Morphology filters cannot reliably separate genuine dots from font serifs without sub-pixel super-resolution.

### B. Highly Skewed Non-Manhattan Grids
The table grid reconstruction assumes rectilinear rows and columns aligned with document axes ($\pm 1.5^\circ$ skew). For non-rectilinear, warped, or circular tables, 1D projection profiling degrades and requires polygon mesh extraction.

### C. Fully Borderless Tables with Overlapping Cell Text
When borderless tables contain multi-line wrapped text that overlaps horizontally across adjacent column boundaries without clear vertical whitespace gutters, projection profiling merges the columns. In Loop 22, the multi-token guard detects this and safely abstains, but extraction of the individual cell values remains unsupported.

---

## 2. Abstention Calibration Boundaries

The confidence threshold $T = 60.0$ was selected as the optimal empirical operating point based on the 46-document corpus. However:
- On documents with unusual or decorative typefaces, Tesseract's native confidence scores may drop across all characters, causing higher abstention rates.
- Conversely, on clean synthetic documents, high confidence may occasionally be reported on incorrect characters (such as digit '4' vs '8' substitutions).
