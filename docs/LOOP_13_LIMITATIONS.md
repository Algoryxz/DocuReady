# DOCUREADY — LOOP 13
## Operational Boundaries, Unhandled Edge Cases & Engineering Roadmap

**Scope:** DocuReady Ingestion Subsystem  
**Component:** Spatial Reading Order & Multi-Column Reconstruction  
**Document Classification:** Engineering Limitations Disclosure  

---

### 1. Architectural Boundaries

Loop 13 successfully solves the primary cross-column line interleaving defect for standard 2-column administrative documents, gazette notifications, bracketed column layouts, and unequal column heights, while safeguarding single-column certificates, tabular key-value forms, and 3+ column table grids.

However, document layouts in the wild exhibit diverse geometric configurations. This document explicitly identifies current boundaries and edge cases that lie outside Loop 13's scope.

---

### 2. Document Layout Typologies & Current Capabilities

| Document Typology | Examples | Loop 13 Handling | Operational Behavior / Recommendation |
| :--- | :--- | :---: | :--- |
| **Single-Column Narrative** | Income certificates, caste certificates, official affidavits | **FULL SUPPORT** | 100% bypass parity; bit-exact golden baseline preservation. |
| **Two-Column Symmetrical** | Official government gazettes, scholarship guidelines | **FULL SUPPORT** | De-interleaved into Header $\to$ Col 1 $\to$ Col 2 $\to$ Footer. |
| **Bracketed Two-Column** | Circulars with spanning header titles and gazette footers | **FULL SUPPORT** | Spanning headers/footers isolated; body columns de-interleaved. |
| **Asymmetrical Two-Column** | Notice boards where Col 1 has 5 lines and Col 2 has 2 lines | **FULL SUPPORT** | Continuous column grouping; no premature footer termination. |
| **Key-Value Administrative Forms** | DHE scholarship intake forms, caste verification forms | **FULL SUPPORT** | Row-wise order preserved via form label / tabular heuristics. |
| **3+ Column Table Grids** | Marksheet tables, semester grade cards, fee schedules | **FULL SUPPORT** | Multi-gap histogram detection preserves row-by-row structure. |
| **3+ Column Narrative Flow** | 3-column newspaper broadsheets, multi-column magazines | **PARTIAL** | Currently safely falls back to default row-wise clustering. De-interleaving of 3+ continuous text columns is deferred to Loop 14. |
| **Irregular Text Wrapping** | Narrative text wrapping around circular logos or photos | **NOT SUPPORTED** | Non-rectangular column boundaries violate the vertical split model. Handled as standard scanlines. |
| **Serpentine / Boustrophedon Flow** | Comic books, non-standard marketing infographics | **OUT OF SCOPE** | Administrative scholarship audit does not encounter non-standard flow. |
| **Complex Nested Tables Inside Columns** | A multi-column article containing a mini-table inside Col 1 | **PARTIAL** | If table cells contain numeric tokens, the page may be protected as a table grid rather than split. |

---

### 3. Failure Mode Safety Analysis

When an ambiguous or unhandled layout is encountered:
1. **Conservative Abstention Principle:** DocuReady's spatial layout detector adheres to the conservative fallback principle. If gutter confidence is below threshold or ambiguous, it returns `SINGLE_COLUMN` / `KEY_VALUE_TABLE`.
2. **Impact of Fallback:** In the worst-case scenario on an unsupported layout, DocuReady reverts to its Loop 12 behavior (naive scanlines). It **never crashes**, never drops words, never invents text, and never generates invalid bounding boxes.
3. **Audit Engine Resilience:** Downstream audit decision rules are designed with fuzzy token matching, permissive token windows, and cross-document reconciliation, meaning that even if an unusual paragraph has scanline interleaving, critical isolated fields (e.g. `Applicant Name: ...`) are protected by the key-value safeguard.

---

### 4. Future Engineering Roadmap (Loop 14+)

1. **Connected Component Column Segmentation:**
   Replace the horizontal projection gap heuristic with recursive $X$-$Y$ cut or Voronoi tessellation to dynamically partition pages into arbitrary polygonal reading blocks.
2. **Table Cell Boundary Detection:**
   Incorporate explicit horizontal and vertical line segment detection (using morphological operations) to isolate table cells independently from narrative paragraphs.
3. **Deep Learning Document Layout Analysis (Optional Research Track):**
   Evaluate compact on-device vision models (such as LayoutLMv3-tiny or PP-Structure) for environments where an additional 15-20 MB model footprint and 50 ms latency are acceptable.
