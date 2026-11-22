# DOCUREADY — LOOP 13
## Sub-Stage Performance & Memory Profiling Report

**Harness:** `research/loop13/benchmark/perf_profiler_loop13.py`  
**Results Data:** `research/loop13/results/loop13_profiling_results.json`  
**Test Hardware:** Intel Core i7-11800H @ 2.30 GHz (Windows x64)  
**Sample Size:** 500 iterations per layout typology  
**Page Density:** 40 lines / page (~320 words / page)  

---

### 1. Executive Summary

To guarantee that DocuReady satisfies HackNation real-time demonstration constraints and production throughput requirements ($< 1.0\text{ s}$ per page), a rigorous sub-stage profiling harness was executed.

The spatial layout reconstruction engine introduces **4.93 ms** of CPU latency for full two-column spatial de-interleaving and **2.19 ms** for single-column bypass evaluation. This represents just **0.59%** of the overall $\sim 834\text{ ms}$ single-page OCR ingestion budget, with a peak memory overhead of under **50 KB**.

---

### 2. Microbenchmark Performance Metrics

| Layout Typology | Sub-Stage Operations | Iterations | Mean Latency per Page | Pipeline Budget Fraction (834 ms baseline) |
| :--- | :--- | :---: | :---: | :---: |
| **Two-Column Document** | Gutter detection, line splitting, bracket segmentation, dual-column sorting | 500 | **4.927 ms** | **0.591%** |
| **Single-Column Document** | Scanline gap check, multi-gap test, early-exit bypass | 500 | **2.191 ms** | **0.263%** |
| **Table Grid / Form** | Multi-gap histogram, label-value ratio evaluation, early exit | 500 | **2.415 ms** | **0.290%** |

---

### 3. Memory Allocation & Heap Profile

Memory impact was tracked using Python's `tracemalloc` instrumentation across 500 continuous page processing cycles:

- **Baseline Pre-Run Memory:** 28.4 MB (Python runtime + loaded models)
- **Peak Memory During Reconstruction:** 49.87 KB allocated
- **Net Leakage / Retained Memory:** **0.00 KB** (all intermediate coordinate lists and word candidate dictionaries are cleanly reclaimed after line construction)

```
[tracemalloc peak snapshot]
1. List comprehension in _cluster_words_raw: 24.2 KB
2. Bounding box dictionary construction: 16.5 KB
3. Split candidate set & line indices: 9.17 KB
Total Peak: 49.87 KB
```

---

### 4. Throughput & Scalability Analysis

- **Single-Threaded OCR Throughput:**
  - Before Loop 13: $\sim 1.199\text{ pages/sec}$ (834 ms per page)
  - With Loop 13 Spatial Reconstruction: $\sim 1.192\text{ pages/sec}$ (839 ms per page)
  - Net Throughput Impact: **$-0.58\%$** (imperceptible in desktop application use)

- **Scalability with Word Count ($N$):**
  - Scanline clustering: $\mathcal{O}(N \log N)$ (sorting words by $y_0, x_0$)
  - Gutter evaluation: $\mathcal{O}(L \cdot K)$ where $L$ is number of lines ($\approx 40$) and $K$ is candidates per line ($\le 4$). $\mathcal{O}(L) \ll \mathcal{O}(N)$.
  - Column sorting: $\mathcal{O}(N_1 \log N_1 + N_2 \log N_2) \le \mathcal{O}(N \log N)$.
  - Conclusion: Asymptotic time complexity remains $\mathcal{O}(N \log N)$, strictly bounded and immune to combinatorial explosion.
