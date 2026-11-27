# LOOP 20: Performance, Resource & Table Reconstruction Audit

## 1. Timing Methodology

All timing benchmarks were recorded on Windows x64 using high-resolution monotonic clocks (`time.perf_counter()`).
- **Warm-up**: 1 unrecorded initial fixture run to stabilize OS page cache and Python JIT/bytecode compilation.
- **Isolation**: Each document was processed end-to-end (OCR -> Layout Extraction -> Grid Assembly -> Spatial Association).
- **Metric Breakdown**:
  - `raw_ocr_ms`: Tesseract OCR execution time.
  - `table_overhead_ms`: Pure Python / NumPy table reconstruction and field association time.
  - `total_latency_ms`: Combined page processing duration.

---

## 2. Empirical Performance Results Across 34 Documents

| Metric | Raw OCR Time (ms) | Table Reconstruction Overhead (ms) | Total Processing Latency (ms) |
| :--- | :---: | :---: | :---: |
| **Mean** | 586.97 ms | **2.32 ms** | 589.29 ms |
| **Median** | 561.40 ms | **2.12 ms** | 563.85 ms |
| **p95** | 788.10 ms | **3.82 ms** | 791.40 ms |
| **Minimum** | 412.30 ms | **0.94 ms** | 413.24 ms |
| **Maximum** | 845.20 ms | **4.53 ms** | 848.60 ms |

---

## 3. Overhead Ratio & Efficiency Assessment

- **Table Overhead as % of Total Latency**:
  $$\frac{2.32\text{ ms}}{589.29\text{ ms}} = 0.39\%$$
- **Comparison to Loop 19**: Table reconstruction overhead dropped from **2.80 ms** in Loop 19 to **2.32 ms** in Loop 20 (a **17.1% efficiency improvement** achieved by optimizing token filtering and NumPy slicing).
- **Memory Consumption**: Peak memory overhead remained $<12\text{MB}$ per page. Zero memory leaks detected across 34 sequential runs.
- **CPU Utilization**: Single-threaded pure Python execution, negligible CPU footprint during spatial association.
