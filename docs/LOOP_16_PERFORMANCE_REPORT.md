# LOOP 16: Performance, Latency & Resource Utilization Report

## 1. Executive Summary

A critical objective of Loop 16 was to eliminate unnecessary OCR computation and subprocess latency without sacrificing accuracy. In Loop 15, Region-Aware OCR spawned up to 24 subprocesses per document, resulting in mean latencies of 4.4 to 4.5 seconds per page and peak latencies exceeding 14 seconds.

In Loop 16, the **Adaptive Strategy Selector** (`STRATEGY_J_ADAPTIVE`):
- Reduced OCR process invocations from **2.67 down to 1.13 per page** (a **57.7% reduction**).
- Achieved a median latency of **2728.17 ms** and mean latency of **3034.89 ms**, cutting P95 latency by **53.7%** (from 14,255 ms down to 6,605 ms).
- Added only **18 to 35 ms** of profiling overhead per page, which is completely offset by the elimination of redundant OCR subprocesses.
- Maintained an ultra-lean memory footprint with **peak RAM usage under 3.5 MB** per document execution.

---

## 2. Latency Metrics Across the Strategy Matrix

The table below summarizes latency across all 15 documents (150 benchmark runs) on standard x64 execution hardware:

| Strategy | Mean Latency (ms) | Median Latency (ms) | P95 Latency (ms) | Mean OCR Invocations | Invocations vs Baseline |
|---|---|---|---|---|---|
| `STRATEGY_A_ENG` | 1026.62 | 862.58 | 2526.35 | 1.00 | Baseline |
| `STRATEGY_B_HIN` | 1247.26 | 1107.87 | 3347.95 | 1.00 | Baseline |
| `STRATEGY_C_ORI` | 1386.90 | 1021.89 | 4200.63 | 1.00 | Baseline |
| `STRATEGY_D_ENG_HIN` | 1479.11 | 1185.51 | 3500.07 | 1.00 | Baseline |
| `STRATEGY_E_ENG_ORI` | 1519.98 | 1080.56 | 4208.59 | 1.00 | Baseline |
| `STRATEGY_F_GLOBAL_ALL` | 1960.48 | 1428.87 | 5928.59 | 1.00 | Baseline |
| `STRATEGY_G_PAGE_ROUTING` | 2301.66 | 2209.15 | 4008.71 | 1.87 | +87% |
| `STRATEGY_H_REGION_ROUTING` | 4401.96 | 3483.60 | 14255.81 | 2.67 | +167% |
| `STRATEGY_I_REGION_FALLBACK` | 4559.13 | 3763.00 | 13779.22 | 2.67 | +167% |
| **`STRATEGY_J_ADAPTIVE`** | **3034.89** | **2728.17** | **6605.18** | **1.13** | **+13%** |

---

## 3. Profiling Overhead Breakdown

The adaptive selector executes a three-stage heuristic profiler prior to OCR invocation:

```
+-------------------------------------------------------------+
| Stage 1: Native Digital Text Inspection (PyMuPDF)           |  ~1.2 ms
|  - Check for embedded text streams                          |
|  - If pure Latin text >= 200 chars -> FAST_PATH_ENG         |
+-------------------------------------------------------------+
                              | (Raster scan fallback)
                              v
+-------------------------------------------------------------+
| Stage 2: Geometric & Contrast Analysis (NumPy)              |  ~8.5 ms
|  - Compute foreground ink density (threshold < 0.005)       |
|  - Compute Michelson contrast (threshold < 15)              |
|  - Detect vertical column quiet gutters (x in [0.42, 0.58]) |
|  - Count horizontal rules (table/grid detection)            |
+-------------------------------------------------------------+
                              | (If readable scan)
                              v
+-------------------------------------------------------------+
| Stage 3: Low-Resolution Thumbnail Script Probe (Tesseract)  | ~18.5 ms
|  - 700px width thumbnail pass with psm=11 (sparse text)     |
|  - Count Latin, Devanagari, and Odia unicode points         |
+-------------------------------------------------------------+
                              |
                              v
                TOTAL PROFILING LATENCY: 24.2 to 34.8 ms
```

### Why Profiling Saves Time
Even though the 700px thumbnail probe consumes ~18 ms, it provides decisive intelligence:
- If a document is a marksheet (`DOC_MULTI_04`, `CHALLENGE_03`), it routes directly to `GLOBAL_MULTILINGUAL` (1 invocation, ~2.7 s) instead of Region-Aware OCR (6 to 24 invocations, ~6.4 to 14.2 s). **Net saving: 3.7 to 7.8 seconds per page.**
- If a document is an unreadable scan (`CHALLENGE_04`), it aborts immediately. **Net saving: 2.5 to 5.0 seconds of useless inference.**

---

## 4. Memory Footprint & Resource Utilization

Memory consumption was tracked across all 150 benchmark runs using Python's `tracemalloc` instrumentation:

| Metric | Region Routing (`STRATEGY_H`) | Adaptive Routing (`STRATEGY_J`) | Delta |
|---|---|---|---|
| **Mean Peak RAM (MB)** | 2.84 MB | 2.15 MB | -24.3% |
| **Max Peak RAM (MB)** | 4.88 MB | 3.42 MB | -29.9% |
| **Subprocess Handle Leaks** | 0 | 0 | Deterministic cleanup |
| **GDI / Handle Consumption** | Stable | Stable | Within Windows desktop limits |

### Resource Management Safeguards:
1. **Subprocess Isolation:** Every OCR invocation uses context-managed temp files and explicitly closed process pipes, preventing file handle exhaustion on Windows.
2. **Thumbnail Image Sizing:** Profiling operates on a downscaled 700px grayscale copy of the page (~0.35 MB uncompressed buffer), avoiding memory spikes associated with full 300 DPI multi-megapixel rasters.
3. **Deterministic Memory Cleanup:** `pix.tobytes()` and image arrays are explicitly deleted after profiling, ensuring predictable garbage collection between multi-page documents.

---

## 5. Desktop Application Responsiveness Impact

In the Electron desktop application, Python backend processing communicates asynchronously with the desktop UI via JSON-RPC / IPC.
- In Loop 15, multi-page region OCR caused long UI spinner pauses (up to 14.2s per page), creating perception of application hang.
- In Loop 16, Adaptive OCR brings average page turnaround down to ~3.0 seconds, with progressive progress updates dispatched after Stage 1 (profiling) and Stage 2 (OCR execution).
- The zero-invocation abstention gate on unreadable scans instantly returns an actionable diagnostic message to the user within **56 ms**, preventing frozen UI states.
