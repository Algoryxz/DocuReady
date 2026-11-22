# Loop 21 Recommended Next Experiments & Loop 22 Directions

## 1. Context & Trajectory

Loop 21 resolved hierarchical 2-tier headers and low-resolution decimal point loss, improving critical field precision to **80.82%** with **1.92–2.15 ms** table processing overhead.

The next engineering loop (Loop 22) should address the remaining challenges identified in our failure analysis.

---

## 2. Prioritized Experiment Backlog

### Experiment 1: Key-Value Graph Association for Borderless Forms & Bills
- **Target Failure**: `BLIND_03_UTILITY_ELECTRICITY_BILL` (interleaved 2-column key-value pairs).
- **Hypothesis**: Form documents without explicit table grid borders are better represented as a directional spatial bipartite graph (connecting labels to horizontally or vertically aligned values) rather than a rigid NxM grid.
- **Proposed Architecture**:
  * Build a Delaunay triangulation or spatial k-NN adjacency graph between text tokens.
  * Connect label tokens to candidate value tokens using geometric ray-casting (rightward search for horizontal forms, downward search for vertical forms).
  * Filter edges using syntactic type compatibility (e.g. `Amount Due` $\to$ matches only currency tokens).
- **Latency Budget**: $< 2.0\text{ ms}$.

---

### Experiment 2: Morphological Single-Character Glyph Verification
- **Target Failure**: `BLIND_08_UNIVERSITY_SEMESTER_TRANSCRIPT` (`O` misrecognized as `fe}`).
- **Hypothesis**: For isolated single-character grade cells (A, B, C, D, E, F, O, S), when Tesseract produces non-alphabetic noise strings (`fe}`, `()`), targeted morphological shape descriptors (circularity, aspect ratio, Euler number) can disambiguate the true letter.
- **Proposed Architecture**:
  * If a cell in a "Grade" column contains non-standard characters, compute contour moments on the binary crop.
  * Circularity $4\pi \cdot \text{Area} / \text{Perimeter}^2 \approx 1.0$ indicates letter `O`.
  * Aspect ratio $\approx 0.5$ and single vertical stroke indicates letter `I`.
- **Latency Budget**: $< 0.1\text{ ms}$ per candidate cell.

---

### Experiment 3: Vertical Separator Edge Detection for Dense Multi-Column Ledgers
- **Target Failure**: `CHALL_01`, `CHALL_02` (bounding box bleed across 10+ columns).
- **Hypothesis**: In dense ledgers with narrow gutters, combining 1D text projection with vertical Sobel/morphological edge detection will prevent bounding box bleed across cell walls.
- **Proposed Architecture**:
  * Apply vertical morphological opening (`kernel = (1, 15)`) on the table image.
  * Intersect detected vertical lines with text gutters to snap column boundaries directly to physical gridlines.
- **Latency Budget**: $< 1.5\text{ ms}$.
