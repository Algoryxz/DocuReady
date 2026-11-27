# LOOP 16: Future Research Roadmap & Next Experiments

## 1. Overview

Loop 16 established an adaptive OCR strategy selector that resolves the conflict between global multilingual models and region-aware routing. Based on the empirical findings, error patterns, and limitations discovered during this loop, this document outlines high-priority research directions and experimental designs for Loop 17 and future engineering cycles.

---

## 2. Priority 1: Fast Affine Deskewing with Coordinate Preservation

### Motivation
In `DOC_DEG_01_MULTI_SCRIPT_SKEWED`, scan skew of 3.5° caused a spike in Character Error Rate (CER 64.59%) due to shirorekha fragmentation and cross-line bounding box interleaving.

### Proposed Architecture
1. **Low-Cost Angle Estimation:**
   - Compute the Hough line transform or min-area bounding rectangle on connected components during the thumbnail profiling pass (< 15 ms).
2. **In-Memory Image Rotation:**
   - Rotate the image buffer by $-\theta^\circ$ before OCR execution.
3. **Coordinate Inverse Transform (Back-Mapping):**
   - Transform all recognized character and word bounding box coordinates back to the original unrotated document space using the affine transformation matrix:
     $$\begin{bmatrix} x_{\text{orig}} \\ y_{\text{orig}} \end{bmatrix} = \mathbf{R}(\theta) \begin{bmatrix} x_{\text{rot}} \\ y_{\text{rot}} \end{bmatrix} + \mathbf{t}$$
   - This ensures that desktop UI highlighting, bounding box navigation, and legal evidence extraction remain 100% faithful to the original untampered document image.

---

## 3. Priority 2: Borderless Table Detection via Whitespace Projection

### Motivation
While documents with clear printed lines (`DOC_MULTI_04`, `CHALLENGE_03`) are easily detected via horizontal morphological kernels, borderless tables (financial records, marks lists formatted using whitespace tabs) lack explicit borders.

### Proposed Architecture
1. **Vertical Projection Density Peaks:**
   - Compute vertical projection across multiple horizontal slices.
   - Distinct, periodic vertical whitespace valleys indicate structured data columns.
2. **Whitespace Grid Routing:**
   - Route documents with detected multi-column whitespace grids to holistic compound models rather than spatial column splitters, preserving horizontal record coherence.

---

## 4. Priority 3: Expansion to Additional Eighth Schedule Indic Scripts

### Motivation
India has 22 officially recognized languages. Expanding beyond English, Hindi, and Odia is necessary for broader state-level governance document validation.

### Target Scripts for Phase 1 Expansion:
1. **Bengali / Bangla (`ben`):** Shares script characteristics with Assamese, widely used in Eastern India.
2. **Tamil (`tam`):** Southern Dravidian script with distinct non-shirorekha geometry.
3. **Telugu (`tel`):** Rounded Dravidian script with complex vowel diacritics.

### Experimental Design:
- Acquire open-source administrative circulars from state portals (e.g., WB Govt, TN Govt).
- Validate traineddata availability in sidecar distributions.
- Expand thumbnail Unicode range detection in `src/docuready/ingest/script_router.py`.

---

## 5. Priority 4: Recursive XY-Cut for Complex Multi-Column Layouts

### Motivation
The current column detector searches specifically for a central two-column quiet gutter. Official gazettes often incorporate 3 columns, or header banners spanning full width followed by 2 asymmetric columns.

### Proposed Architecture
- Implement recursive XY-cut (Ha, Haralick, and Phillips algorithm) on binarized projection profiles.
- Dynamically build a spatial layout tree:
  ```
  Root (Page)
   ├── Header Region (1-column, Latin + Hindi)
   ├── Main Body Region
   │    ├── Left Column (Odia)
   │    └── Right Column (English)
   └── Footer Region (1-column, Signatures & Seals)
  ```
- Route each leaf node independently through the adaptive language selector.
