# DocuReady Loop 02 — Orientation Gate Assurance, Recovery Optimization & Benchmark Results

**Measurement Date:** 2026-11-22  
**Branch:** `loop-02-orientation-gate-assurance`  
**Execution Environment:** Windows 11 Enterprise (AMD64, 12 Cores, 15.73 GB RAM), Python 3.12.10, Tesseract 5.4.0.20240606, PyMuPDF 2.1, Pillow 12.3.0  

---

## 1. Executive Summary

In Loop 02, we conducted an exhaustive empirical evaluation of the OCR orientation fast-path gate, investigated recovery-path bottlenecks, eliminated an unmanaged C-level memory leak in PyMuPDF raster caching, and introduced Two-Tier OSD recovery.

### Key Breakthroughs:
1. **0.00% Rotated False-Upright Rate Across 70 Fixtures:** Every single rotated (90°, 180°, 270°), skewed (10°, 15°), and mixed-orientation page was rejected by the upright gate and safely routed to recovery or conservative abstention.
2. **29.7% Latency Reduction in Rotated Document Recovery:** Rotated documents dropped from **4,690.22 ms** to **3,296.25 ms** (saving **1,393.97 ms** on 90° scans) via Tier-A fast OSD scaling.
3. **68.55% Memory Footprint Reduction:** Resolved an unmanaged MuPDF `fz_store` raster cache retention issue. Peak process RSS dropped from **378.55 MB** down to **119.07 MB**, with memory growth across 10 repeated batch iterations plummeting from **113.68 MB to 0.98 MB**.
4. **Sub-5-Second 6-Document Packet Auditing:** Full realistic packet audit latency dropped to **4,522.16 ms** (a **60.75% total reduction** compared to the unoptimized baseline of 11,523.50 ms).
5. **100% Pass Rate on All Suites:** 66/66 Python tests, 21/21 Desktop Electron tests, golden baseline byte-for-byte parity, zero network egress, and competition demo walkthrough verified.

---

## 2. Definitive Loop 01 vs. Loop 02 Benchmark Comparison

All measurements recorded across 5 warm repeated iterations under identical local hardware conditions:

| Metric | Historical Baseline | Loop 01 | Loop 02 | Loop 01 $\rightarrow$ Loop 02 Change | Total vs Baseline |
|---|---:|---:|---:|---:|---:|
| **Upright Scanned Page Median** | 2,963.60 ms | 1,358.55 ms | **1,140.25 ms** | -218.30 ms (-16.07%) | **-61.52%** |
| **Rotated 90° Scan Median** | 3,118.15 ms | 4,690.22 ms | **3,296.25 ms** | **-1,393.97 ms (-29.72%)** | +5.71% |
| **Rotated 180° Scan Median** | 3,089.27 ms | 4,237.22 ms | **3,327.20 ms** | **-910.02 ms (-21.48%)** | +7.70% |
| **Rotated 270° Scan Median** | 3,169.71 ms | 4,929.68 ms | **3,364.10 ms** | **-1,565.58 ms (-31.76%)** | +6.13% |
| **Low-DPI Scan Median** | 3,062.46 ms | 1,487.79 ms | **1,113.06 ms** | -374.73 ms (-25.19%) | **-63.65%** |
| **Shadow Gradient Scan Median** | 2,650.34 ms | 1,301.33 ms | **1,035.38 ms** | -265.95 ms (-20.44%) | **-60.93%** |
| **Multi-page Native (4 pages)** | 30.51 ms | 26.50 ms | **26.76 ms** | +0.26 ms (+0.98%) | **-12.29%** |
| **6-Document Packet Audit Median** | 11,523.50 ms | 5,585.09 ms | **4,522.16 ms** | **-1,062.93 ms (-19.03%)** | **-60.75%** |
| **Peak Process Memory (RSS)** | 379.14 MB | 378.55 MB | **119.07 MB** | **-259.48 MB (-68.55%)** | **-68.59%** |
| **10-Iteration Memory Growth** | ~114 MB | ~114 MB | **0.98 MB** | **-112.70 MB (-98.86%)** | Fixed Leak |
| **Upright Fast-Path Rate** | 0.0% | 100.0% | **91.9%** | Conservative Abstention | Safe |
| **Rotated False-Upright Rate** | 0.0% | 0.0% | **0.00%** | Zero False Uprights | Critical Pass |
| **Field Extraction Accuracy** | 100.0% | 100.0% | **100.0%** | 100% Extraction | Preserved |
| **Orientation Recovery Rate** | 100.0% | 100.0% | **100.0%** | 100% Recovery | Preserved |

---

## 3. Gate Attack Corpus & Safety Evaluation

Evaluated across all 70 fixtures (60 Realistic Corpus + 10 Attack Fixtures):

| Category | Fixtures Tested | Fast-Path Accepted | Rejected / Routed to Recovery | False Uprights | Safety Status |
|---|---:|---:|---:|---:|---|
| **True Upright Scans & Natives** | 62 | 57 (91.9%) | 5 (Blank, Sparse, Degraded) | 0 | **PASSED** |
| **Orthogonal Rotations (90°, 180°, 270°)** | 4 | 0 (0.0%) | 4 (100.0%) | 0 | **PASSED (0% Flaw)** |
| **Small-Angle Skew (10°, 15°)** | 2 | 0 (0.0%) | 2 (100.0%) | 0 | **PASSED (0% Flaw)** |
| **Mixed Orientation Pages** | 1 | 0 (0.0%) | 1 (100.0%) | 0 | **PASSED (0% Flaw)** |
| **Adversarial Inverted Reversible Words** | 1 | 0 (0.0%) | 1 (100.0%) | 0 | **PASSED (0% Flaw)** |
| **Total Test Matrix** | **70** | **57** | **13** | **0 (0.00%)** | **100% SAFE** |

---

## 4. Benchmark Methodology Reconciliation

1. **Timing Boundaries:** Granular micro-benchmarks measure raw isolated C-library and CLI subprocess execution (`image_to_data`, `image_to_osd`). Document extraction benchmarks measure complete application logic (`extract_document`). Packet benchmarks measure the full ingestion, extraction, rule validation, and finding serialization pipeline.
2. **Cold-Start vs Warm Iterations:** 5 iterations are measured per workload using `time.perf_counter()`. First iteration cold-starts are captured and separated; reported medians reflect stable warm performance.
3. **Environment Standardization:** All benchmarks executed strictly offline under Windows 11 Enterprise (AMD64) using local Tesseract v5.4.0.20240606 without network calls or external APIs.
