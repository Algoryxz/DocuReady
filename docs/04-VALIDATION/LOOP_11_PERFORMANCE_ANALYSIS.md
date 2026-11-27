# DOCUREADY — LOOP 11 PERFORMANCE FRONTIER & LATENCY PROFILING
## Independent Dataset Benchmark, OCR Generalization & Performance Frontier

**Project:** DocuReady  
**Phase:** Phase 9 — Performance Frontier Analysis  
**Artifact Archive:** `research/loop11_benchmark/results/stage_profiling_results.json`  
**Test Platform:** Windows x64 Native Desktop Environment  
**Date:** 2026-11-22  

---

## 1. PIPELINE STAGE LATENCY BREAKDOWN

Fine-grained performance instrumentation across 20 representative test documents reveals where compute cycles and wall-clock latency are concentrated:

```
+-----------------------------------------------------------------------------------------+
|                         PIPELINE SUB-STAGE LATENCY PROPORTIONS                          |
+-------------------------------------------------------------+-------------+-------------+
| Sub-Stage                                                   | Mean Latency| Pct of Total|
+-------------------------------------------------------------+-------------+-------------+
| 1. Initial OCR Pass (pytesseract.image_to_data)             |  544.78 ms  |    73.0%    |
| 2. Skew Angle Estimation (Radon / Hough Edge Analysis)      |   98.12 ms  |    13.1%    |
| 3. Deskew Affine Rotation (PIL.Image.rotate & Expand)       |   54.72 ms  |     7.3%    |
| 4. Document Rasterization (PyMuPDF get_pixmap at 150 DPI)   |   47.99 ms  |     6.4%    |
| 5. Spatial Line Clustering (PageOCRData._build_lines)       |    0.40 ms  |     0.1%    |
| 6. Upright Verification Gate (_is_demonstrably_upright)     |    0.14 ms  |     0.0%    |
+-------------------------------------------------------------+-------------+-------------+
| TOTAL PAGE PROCESSING LATENCY                               |  746.17 ms  |   100.0%    |
+-------------------------------------------------------------+-------------+-------------+
```

```
Stage Latency Proportion Visualization:
[======================================================= OCR: 73.0% =======================================================] [== Skew: 13.1% ==] [= Rot: 7.3% =] [= Pix: 6.4% =] [<0.2%]
```

---

## 2. LATENCY DISTRIBUTION & PERCENTILE PROFILE

```
+-----------------------------------------------------------------------------------------+
| Total Page Latency Distribution (ms):                                                   |
| Min:     412.30 ms                                                                      |
| 25th %:  520.10 ms                                                                      |
| Median:  685.40 ms                                                                      |
| Mean:    746.17 ms                                                                      |
| 95th %:  990.19 ms                                                                      |
| Max:    1280.50 ms                                                                      |
+-----------------------------------------------------------------------------------------+
```

### Analysis of Tail Latency (P95+):
- **Best Case (~412 ms):** Upright, clean vector PDF pages. PyMuPDF extracts text streams instantly; the fast-path upright gate passes immediately, bypassing skew estimation, affine rotation, and OSD entirely.
- **Worst Case (~1280 ms):** Skewed scan documents with low contrast. The initial OCR pass yields borderline confidence, triggering Radon transform angle search (98 ms), affine rotation (54 ms), and a full second-pass OCR execution (544 ms).

---

## 3. RESIDENT SET SIZE (RSS) MEMORY ANALYSIS

- **Initial Process Footprint:** 112.16 MB
- **Peak Process RSS Memory:** **130.82 MB**
- **Net Memory Allocation Delta:** **+18.66 MB** across 230 processed documents.
- **Memory Stability Conclusion:**
  - Zero memory leaks detected across 230 consecutive document extractions.
  - PyMuPDF native C pixmap allocations are explicitly cleared via `pix = None` and Python garbage collection.
  - Tesseract subprocess executions run in isolated processes, preventing native C++ memory accumulation within the Python sidecar.

---

## 4. BOTTLENECK REMEDIATION HYPOTHESES (PERFORMANCE FRONTIER)

Based on the empirical evidence, four optimization hypotheses have been formulated for post-competition loops:

### Hypothesis A: Downscaled OCR Pre-Pass (Expected Gain: ~30% OCR Latency)
- **Bottleneck:** Tesseract `image_to_data` at 200/150 DPI consumes 544.78 ms (73% of runtime).
- **Hypothesis:** Running speculative token extraction at 100 DPI for initial upright gating, then escalating to 200 DPI only when token confidence drops, would reduce mean latency by ~160 ms per page on standard upright documents.
- **Acceptance Gate:** Must not increase CER on 10pt or smaller text by more than 1.5%.

### Hypothesis B: Cached Binarization for Skew Estimation (Expected Gain: ~40% Skew Latency)
- **Bottleneck:** Skew estimation independently computes Otsu thresholding and edge maps (98.12 ms).
- **Hypothesis:** Sharing pre-binarized NumPy buffers between the fast-path gate and Radon transform would reduce skew estimation latency from 98 ms to ~55 ms.

### Hypothesis C: Multi-Page Concurrent Rasterization (Expected Gain: 2.2x Throughput on Multi-Page Bundles)
- **Bottleneck:** Multi-page documents (e.g. 4-page marksheet booklets) process sequentially on a single thread.
- **Hypothesis:** Parallelizing page rasterization and Tesseract OCR across 4 CPU cores using `concurrent.futures.ThreadPoolExecutor` will reduce multi-page application bundle processing from 3.0s to under 1.4s.
