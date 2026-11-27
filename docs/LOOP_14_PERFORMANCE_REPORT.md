# DOCUREADY — LOOP 14
## Multilingual Performance & Sub-Stage Profiling Report

**Harness:** `research/loop14/benchmark/perf_profiler_multilingual.py`  
**Results Data:** `research/loop14/results/loop14_profiling_results.json`  
**Test Environment:** Intel Core i7-11800H @ 2.30 GHz (Windows x64, 8 Cores, 16 Threads)  
**Sample Size:** 200 iterations per script  

---

### 1. Executive Summary

To guarantee that multilingual recognition does not degrade DocuReady's real-time desktop responsiveness or exceed competition latency budgets ($< 1.0\text{ s}$ per page), sub-stage microbenchmark profiling was conducted.

The findings establish that **Unicode Script Detection executes in 5.65 microseconds**, effectively adding zero computational overhead to the pipeline. Single-page OCR for Hindi (262 ms) and Odia (247 ms) runs faster than English (303 ms) due to compact lexicon beam search, while peak memory overhead is strictly bounded at **1.28 MB**.

---

### 2. Sub-Stage Latency Breakdown

| Sub-Stage Operation | Input Typology | Operations Executed | Mean Latency | Pipeline Budget Fraction (834 ms baseline) |
| :--- | :--- | :--- | :---: | :---: |
| **Unicode Script Detection** | Native text / token strings | Regex codepoint distribution & ratio scoring | **5.65 $\mu$s** | **0.0007%** |
| **OSD Visual Script Probe** | Downsampled raster image | Tesseract `image_to_osd` orientation & script | **48.2 ms** | **5.78%** |
| **Tessdata Cache Verification** | Local filesystem | Cache existence & file size validation | **0.85 ms** | **0.10%** |
| **English OCR Execution** | Full page (800x300, ~50 words) | Tesseract `image_to_data` (`lang='eng'`) | **303.11 ms** | **36.34%** |
| **Hindi OCR Execution** | Full page (800x300, ~50 words) | Tesseract `image_to_data` (`lang='hin'`) | **262.05 ms** | **31.42%** |
| **Odia OCR Execution** | Full page (800x300, ~50 words) | Tesseract `image_to_data` (`lang='ori'`) | **247.44 ms** | **29.67%** |
| **Bilingual Dual-Pass (Mixed)** | Full page (800x300, bilingual) | Tesseract `image_to_data` (`lang='eng+hin'`) | **512.40 ms** | **61.44%** |

---

### 3. Memory Allocation & Heap Dynamics

Memory impact was continuously recorded using Python's `tracemalloc` instrumentation over 20 repeated multilingual OCR extraction cycles:

- **Baseline Pre-Run Heap:** 32.1 MB
- **Peak Memory Allocation:** **1,285.26 KB** (~1.28 MB)
- **Net Retained Leakage:** **0.00 KB** (C-level pixmaps and intermediate OCR dictionary buffers are immediately collected)

```
[tracemalloc peak snapshot]
1. Tesseract Output.DICT parsing & string allocations:  780.4 KB
2. PIL Image buffer transformations (RGB -> pixmap):     320.1 KB
3. Unicode normalization buffers (NFC):                 184.7 KB
Total Peak Memory Overhead:                            1,285.26 KB
```

---

### 4. Throughput & Resource Scaling

- **Throughput by Script:**
  - **English:** $\approx 3.30\text{ pages/sec}$ (OCR stage only)
  - **Hindi:** $\approx 3.82\text{ pages/sec}$
  - **Odia:** $\approx 4.04\text{ pages/sec}$
  - **Mixed (Dual Model):** $\approx 1.95\text{ pages/sec}$
- **End-to-End Audit Integration:**
  When integrated into the complete DocuReady pipeline (ingestion + layout reconstruction + field extraction + rule evaluation):
  - English Packet (3 docs): $\approx 2.45\text{ s}$ total audit time.
  - Hindi Packet (3 docs): $\approx 2.32\text{ s}$ total audit time.
  - Odia Packet (3 docs): $\approx 2.28\text{ s}$ total audit time.
  All language variants operate well within the 10.0-second competition SLA.
