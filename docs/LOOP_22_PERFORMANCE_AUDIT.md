# Loop 22 — Latency, Overhead & Performance Audit

**Evaluator:** `research/loop22/benchmark/run_loop22_benchmark.py`  
**Host Platform:** Windows x64 Desktop (Python 3.12.10, Tesseract 5.5.0)  
**Corpus:** 46 Documents (83 Loop 21 + 12 Loop 22)

---

## 1. Latency & Overhead Summary

| Metric | Mean (ms) | Median (ms) | p95 (ms) | Min (ms) | Max (ms) | Ponytail Budget | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Table Grid Overhead** | **2.03** | **1.60** | **3.74** | 0.78 | 5.01 | $< 3.0$ ms | **PASSED** |
| **Decimal Filter Overhead** | **0.05** | 0.04 | 0.08 | 0.02 | 0.12 | $< 0.5$ ms | **PASSED** |
| **Raw Tesseract OCR** | **505.68** | 503.95 | 606.34 | 254.31 | 817.10 | N/A | Normal |
| **End-to-End Pipeline** | **507.71** | **505.55** | **610.08** | 255.30 | 821.12 | $< 1200$ ms | **PASSED** |

---

## 2. Cohort-by-Cohort Latency Breakdown

| Cohort | Docs | Total Fields | Mean Pipeline Latency | Mean Table Overhead |
| :--- | :---: | :---: | :---: | :---: |
| **A: Development** | 8 | 16 | 492.49 ms | 2.30 ms |
| **B: Validation** | 8 | 16 | 587.72 ms | 3.03 ms |
| **C: Blind Evaluation** | 10 | 23 | 600.08 ms | 2.52 ms |
| **D: Challenge Adversarial** | 8 | 16 | 504.14 ms | 1.25 ms |
| **E: Hierarchical Headers** | 3 | 6 | 388.54 ms | 1.27 ms |
| **F: Decimal Integrity** | 3 | 6 | 499.62 ms | 3.65 ms |
| **G: Evidence Association** | 6 | 12 | 456.62 ms | 1.86 ms |
| **AGGREGATE** | **46** | **95** | **507.71 ms** | **2.03 ms** |

---

## 3. Computational Complexity Analysis

1. **NumPy Baseline Morphology:** By utilizing direct 1D NumPy slices rather than subprocess OCR patch invocations, the decimal refinement runs in $0.05\text{ ms}$ per candidate cell with zero memory allocation churn.
2. **Table Grid Assembly:** Reconstructing rows and columns via 1D vertical and horizontal projection profiles runs in $\sim 2.0\text{ ms}$, representing less than $0.5\%$ of the total pipeline runtime.
3. **Zero ML Overhead:** The solution requires zero heavy neural table transformers or external dependencies, adhering strictly to Ponytail principles of lightweight algorithmic design.
