# DocuReady — Loop 03: Non-Orthogonal Skew Recovery, OCR Accuracy & Geometry Preservation

**Project:** DocuReady — HackNation 2026  
**Engineering Phase:** Sprint Optimization Loop 03  
**Base Commit:** `cdf6a5e` (Loop 02 Completion)  
**Branch:** `loop-03-skew-recovery-and-geometry`  
**Status:** COMPLETE & VERIFIED  

---

## 1. Executive Summary & Mission

Loop 01 introduced a fast-path speculative OCR mechanism and direct buffer decoding, reducing OCR latency by up to 63%. Loop 02 validated the safety of the upright gate, added a two-tier OSD recovery fallback, and eliminated native C-level pixmap retention leaks.

However, neither Tesseract OSD nor token-level aspect ratio checks handled **non-orthogonal skew** ($|\theta| \in [2^\circ, 45^\circ]$). When documents were scanned or photographed at non-orthogonal angles:
1. **At $\pm 2^\circ$ to $\pm 7^\circ$ Skew:** Individual words maintained width $\ge$ height, passing the token-level aspect ratio filter. However, vertical baseline drift across text lines ($\Delta y = W \cdot \tan\theta \gg 12\text{pt}$) completely shattered the 12pt spatial horizontal line clustering algorithm, fragmenting single text lines into disconnected fragments and causing up to 100% field extraction loss (e.g. `smp_21_rotated_5deg.pdf` extracted 0/6 fields).
2. **At $\ge 10^\circ$ Skew:** Tesseract's internal line segmentation collapsed, resulting in total token loss or degraded unreadable status.
3. **OSD Blindness:** Tesseract OSD only detects discrete orthogonal rotations ($0^\circ, 90^\circ, 180^\circ, 270^\circ$). It cannot estimate or correct non-orthogonal angles.

**Loop 03 Solution:**
- Engineered a lightweight, deterministic **Horizontal Projection Profile Variance Analysis** module (`docuready.ingest.deskew.estimate_skew_angle`) using pure NumPy and Pillow (no OpenCV or heavy native C dependencies).
- Formulated an exact **Inverse Affine Coordinate Transformation** (`docuready.ingest.deskew.transform_bbox_inverse`) that maps token and field bounding boxes from rotated deskew coordinates back to the original unrotated PDF page geometry.
- Enforced a strict **Upright No-Op Decision Invariant**: documents with $|\theta| < 1.0^\circ$ or peak-to-median variance confidence $< 5.0$ are never rotated or re-interpolated, preventing blur and zero-latency regression on aligned documents.
- Solved the **Tesseract Border Artifact Anomaly**: initialized Pillow's rotation canvas with paper-white fillcolor `(255, 255, 255)` rather than default black padding, eliminating border-induced layout analysis failures.

---

## 2. Architecture & Pipeline Design

```
+--------------------------------------------------------------------------------+
|                               Input Document Page                              |
+--------------------------------------------------------------------------------+
                                       |
                     Direct PyMuPDF Buffer Extraction (200 DPI)
                                       |
                                       v
+--------------------------------------------------------------------------------+
| Step 1: Speculative 0° Token OCR (pytesseract.image_to_data)                   |
+--------------------------------------------------------------------------------+
                                       |
                                       v
+--------------------------------------------------------------------------------+
| Step 2: Demonstrably Upright Gate (_is_demonstrably_upright)                   |
| - Substantive tokens (>=15 tokens, >=40 chars)                                 |
| - High mean confidence (>=70.0%) and high-confidence ratio (>=60%)             |
| - Token geometry invariant (>=70% tokens with width >= height)                 |
| - NEW: Baseline Slope Invariant (|median_token_slope| < 1.5°)                   |
+--------------------------------------------------------------------------------+
        |                                                        |
   PASSED (Upright)                                         FAILED (Skewed/Rotated)
        |                                                        |
        v                                                        v
+-------------------------------+       +------------------------------------------------+
| Return PageOCRData(rot=0)     |       | Step 3: Fast Blank Check (valid_tokens == 0)   |
| (0 ms deskew, 0 ms OSD)       |       +------------------------------------------------+
+-------------------------------+                                |
                                                          Tokens > 0
                                                                 |
                                                                 v
                                        +------------------------------------------------+
                                        | Step 4: Projection Profile Skew Estimation     |
                                        | - 600px height thumbnail binarization          |
                                        | - Coarse 1.5° sweep + Fine 0.2° sweep          |
                                        | - Peak-to-median variance ratio >= 5.0         |
                                        +------------------------------------------------+
                                                |                                |
                                          |angle| >= 1.0°                 |angle| < 1.0°
                                                |                                |
                                                v                                |
                                +--------------------------------+               |
                                | Deskew Image (White Padding)   |               |
                                | Re-run Token OCR               |               |
                                | Inverse Transform Bounding Box |               |
                                +--------------------------------+               |
                                        |                                        |
                                  Is Upright?                                    |
                                    |        |                                   |
                                  YES        NO (Still unreadable)               |
                                    |        |                                   |
                                    |        +-------------------+               |
                                    |                            |               |
                                    v                            v               v
                        +-----------------------+       +--------------------------------+
                        | Return PageOCRData    |       | Step 5: Two-Tier OSD Fallback  |
                        | (skew_angle=theta,    |       | - Tier A: 0.60x scaled OSD     |
                        |  orig_size=(W0, H0),  |       | - Tier B: 1.00x full-res OSD   |
                        |  rot_size=(W1, H1))   |       | For 90°, 180°, 270° orthogonal |
                        +-----------------------+       +--------------------------------+
```

---

## 3. Mathematical Coordinate Transformation Contract

When an image of dimensions $(W_0, H_0)$ is rotated counter-clockwise by correction angle $\theta_{\text{corr}}$ with `expand=True`, the resulting image has dimensions $(W_1, H_1)$.

### Center Coordinates
$$c_{x0} = \frac{W_0}{2.0}, \quad c_{y0} = \frac{H_0}{2.0}$$
$$c_{x1} = \frac{W_1}{2.0}, \quad c_{y1} = \frac{H_1}{2.0}$$

### Inverse Rotation Matrix
Because visual counter-clockwise rotation in downwards-$y$ image coordinates is represented by orthogonal matrix $R$, its inverse is $R^{-1} = R^T$:
$$\begin{pmatrix} x_0 - c_{x0} \\ y_0 - c_{y0} \end{pmatrix} = \begin{pmatrix} \cos\theta & -\sin\theta \\ \sin\theta & \cos\theta \end{pmatrix} \begin{pmatrix} x_1 - c_{x1} \\ y_1 - c_{y1} \end{pmatrix}$$

### Bounding Box Enclosure
For a bounding box $[x_0, y_0, x_1, y_1]$ detected in the deskewed image, all four vertices are mapped back to the unrotated coordinate space:
$$P_k = \{(x_0, y_0), (x_1, y_0), (x_0, y_1), (x_1, y_1)\}$$
$$(px_0, py_0) = \left( \max\left(0, \min_{k} x_0^{(k)}\right), \; \max\left(0, \min_{k} y_0^{(k)}\right) \right)$$
$$(px_1, py_1) = \left( \min\left(W_0, \max_{k} x_0^{(k)}\right), \; \min\left(H_0, \max_{k} y_0^{(k)}\right) \right)$$

Coordinates are converted into PDF point units via $\text{scale} = 72.0 / \text{dpi}$:
$$\text{bbox}_{\text{pdf}} = [px_0 \cdot \text{scale}, \; py_0 \cdot \text{scale}, \; px_1 \cdot \text{scale}, \; py_1 \cdot \text{scale}]$$

---

## 4. Empirical Benchmark Results

### 4.1 Controlled Skew Corpus (43 Fixtures)
Evaluated across `synthetic_data/skew_corpus/` spanning clean scans, low-DPI scans, shadow gradients, and tables across $[-45.0^\circ, +45.0^\circ]$:

| Modality / Category | Fixtures | Ground Truth Angle Range | Mean Angle Error | Mean Recovery % (Clean) | Geometry BBox Validity |
|---|---|---|---|---|---|
| **Clean Scans** | 25 | $[-45.0^\circ, +45.0^\circ]$ | **0.056°** | **94.4%** ($[-15^\circ, +15^\circ]$) | **100% Valid (25/25)** |
| **Low-DPI Scans** | 6 | $[-15.0^\circ, +15.0^\circ]$ | **0.067°** | Recovered | **100% Valid (6/6)** |
| **Shadow Gradients** | 6 | $[-15.0^\circ, +15.0^\circ]$ | **0.067°** | Recovered | **100% Valid (6/6)** |
| **Tables with Rules** | 6 | $[-15.0^\circ, +15.0^\circ]$ | **0.067°** | 100% Grid Preserved | **100% Valid (6/6)** |
| **Total / Aggregate** | **43** | $[-45.0^\circ, +45.0^\circ]$ | **0.060°** | **High Recovery** | **100% Valid (43/43)** |

### 4.2 Realistic Scanned Corpus (Loop 02 vs Loop 03 Comparison)

| Document | Skew Angle | Pre-Loop 03 Extracted | Loop 03 Extracted | Improvement |
|---|---|---|---|---|
| `smp_11_raster_scan.pdf` | $0^\circ$ (Upright) | 6/6 fields (100%) | **6/6 fields (100%)** | 0 ms overhead (No-Op) |
| `smp_19_rotated_2deg.pdf` | $+2^\circ$ | 3/6 fields (50%) | **6/6 fields (100%)** | +50% field recovery |
| `smp_20_rotated_-3deg.pdf` | $-3^\circ$ | 3/6 fields (50%) | **6/6 fields (100%)** | +50% field recovery |
| `smp_21_rotated_5deg.pdf` | $+5^\circ$ | **0/6 fields (0%)** | **6/6 fields (100%)** | **+100% TOTAL RECOVERY** |
| `smp_22_rotated_-4deg.pdf` | $-4^\circ$ | 4/6 fields (66%) | **5/6 fields (83%)** | +17% field recovery |
| `smp_23_rotated_90deg.pdf` | $90^\circ$ (Orthogonal) | 6/6 fields (100%) | **6/6 fields (100%)** | Two-Tier OSD intact |
| `smp_24_rotated_180deg.pdf` | $180^\circ$ (Orthogonal) | 6/6 fields (100%) | **6/6 fields (100%)** | Two-Tier OSD intact |
| `smp_61_rotated_270deg.pdf` | $270^\circ$ (Orthogonal) | 6/6 fields (100%) | **6/6 fields (100%)** | Two-Tier OSD intact |

---

## 5. Non-Negotiable Invariants & Safety Verification

1. **Upright Fast-Path Preservation:**
   Clean upright documents (0°) bypass skew correction and OSD completely. Speculative OCR returns in ~700 ms without additional image re-sampling or interpolation blur.
2. **Deterministic Confidence Floor:**
   If the peak-to-median ratio of difference variances is $< 5.0$ or estimated angle is $< 1.0^\circ$, no rotation is performed.
3. **Paper-White Canvas Protection:**
   Rotations utilize `fillcolor=(255, 255, 255)` rather than Pillow's default black canvas, preventing black-border anomalies from corrupting Tesseract's page layout analysis.
4. **Coordinate Integrity:**
   All field bounding boxes are guaranteed to lie within page boundaries ($[0, W_{\text{pt}}]$ and $[0, H_{\text{pt}}]$) and accurately highlight text in the desktop PDF viewer.
5. **Bit-Exact Golden Baseline:**
   Golden checksum `E8FB1A6B842A47089937777133DE79E1E7F704BEE591D5B4471A1A90BC8C5FA9` remains bit-exact and unchanged.
6. **Zero-Network Policy:**
   100% offline local processing without network sockets, external APIs, telemetry, or unvetted binary dependencies.

---

## 6. Full Regression Test Matrix

| Suite | Tests | Result | Notes |
|---|---|---|---|
| `tests/test_loop03_skew_recovery.py` | 6 | **6/6 PASSED** | Estimation accuracy, no-op gate, 5° & 10° recovery, bbox math, memory stability |
| `tests/test_loop02_orientation_assurance.py` | 7 | **7/7 PASSED** | Two-tier OSD, upright gate, memory retention |
| `tests/test_ocr_performance_and_adversarial.py` | 10 | **10/10 PASSED** | Performance benchmarks, adversarial noise, orientation stability |
| `tests/test_golden_baseline.py` | 13 | **13/13 PASSED** | Bit-exact baseline equivalence |
| `tests/test_pack_golden_baseline.py` | 9 | **9/9 PASSED** | Pack engine validation across 8 canonical packets |
| `tests/contract/test_claims.py` & `test_no_network.py` | 21 | **21/21 PASSED** | Zero network calls, offline security contract |
| `apps/desktop` (Node.js / Electron) | 21 | **21/21 PASSED** | IPC security, sidecar lifecycle, bounding box viewport transforms, workspace isolation |
| **Total Test Verification** | **87** | **87/87 PASSED (100%)** | |
