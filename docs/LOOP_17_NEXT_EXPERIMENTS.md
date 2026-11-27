# LOOP 17: Future Research Roadmap & Loop 18 Proposals

## 1. Overview

Loop 17 successfully optimized adaptive OCR execution latency by 35.3% (reducing mean latency to 1962 ms) and established 100% critical-field accuracy on structured records.
Based on the residual failures and limitations identified, this roadmap outlines high-impact research experiments for Loop 18.

---

## 2. Priority 1: Sub-Millisecond Affine Deskewing with Inverse Coordinate Mapping

### Problem
Physical scan tilt of $> 2.5^\circ$ degrades projection profile column detection and breaks character headlines (*shirorekha*), as evidenced in `CHALLENGE_05_ROTATED_SKEW_GAZETTE`.

### Proposed Loop 18 Experiment
1. **Angle Estimation:** Compute dominant text orientation using minimum-bounding-box moments on connected components during the thumbnail pass (< 15 ms).
2. **In-Memory Deskew:** Rotate image array by $-\theta$ prior to OCR.
3. **Coordinate Inverse Mapping:** Transform all extracted word bounding boxes back to the original untampered image coordinate space via:
   $$\begin{bmatrix} x_{\text{orig}} \\ y_{\text{orig}} \end{bmatrix} = \mathbf{R}(\theta) \begin{bmatrix} x_{\text{deskewed}} \\ y_{\text{deskewed}} \end{bmatrix} + \mathbf{t}$$
   This preserves 100% legal evidentiary fidelity for desktop UI highlighting.

---

## 3. Priority 2: Recursive XY-Cut for Multi-Column Gazettes

### Problem
Certain official gazettes feature 3 columns, or full-width headers followed by 2 asymmetric columns, which defeat the simple central two-column quiet gutter heuristic.

### Proposed Loop 18 Experiment
- Implement recursive XY-cut (Ha, Haralick & Phillips) to decompose complex pages into a hierarchical spatial tree:
  `Root -> [Header (1-col), Body (3-col), Footer (1-col)]`.
- Route each spatial block independently to its optimal script model.

---

## 4. Priority 3: Expansion to Southern & Eastern Indic Scripts

### Scope
Incorporate Bengali (`ben`), Tamil (`tam`), and Telugu (`tel`):
- Expand thumbnail Unicode character ranges in `script_router.py`.
- Package and verify sidecar `traineddata` bundles.
- Acquire verified circulars from West Bengal, Tamil Nadu, and Andhra Pradesh government portals.

---

## 5. Priority 4: Desktop UI Critical-Field Verification Card

### Problem
Reviewers currently have to search through full extracted text to verify certificate IDs and dates.

### Proposed Loop 18 Experiment
- Implement a dedicated **Critical Fields Verification Pane** in the desktop Electron UI, displaying side-by-side:
  - Extracted Name, ID, DOB, and Amounts
  - Interactive source pixel crops from the original document
  - One-click confirmation / flag buttons for human-in-the-loop audit qualification.
