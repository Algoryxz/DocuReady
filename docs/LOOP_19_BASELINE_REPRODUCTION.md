# LOOP 19: Loop 18 Baseline Reproduction & Empirical Audit

## 1. Executive Summary

Prior to introducing any architectural or algorithmic modifications in Loop 19, we audited and reproduced the quantitative performance baseline established in Loop 18 (`9360fd2`).

All metrics from the 25-document expanded corpus benchmark (`research/loop18/strategy_results.json`), the adversarial stress suite (`research/loop18/results/stress_benchmark_results.json`), and the same-corpus comparative verification (`research/loop18/results/same_corpus_comparison.json`) were reproduced and validated.

---

## 2. Reproduced 25-Document Strategy Benchmark

| Strategy | Micro Corpus CER | Macro Per-Doc CER | Micro Corpus WER | Macro Per-Doc WER | Reading Inversion Rate | Mean Latency (ms) | Mean Invocations | Critical Field Match Rate | Mean Field CER |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Global Multilingual (`eng+hin+ori`)** | 23.78% | 434.94%* | 36.95% | 112.72% | 6.64% | 1,763.4 ms | 1.00 | 67/67 (100.0%) | 0.00% |
| **Page-Level Routing** | 44.16% | 453.55%* | 54.64% | 128.66% | 9.26% | 2,247.4 ms | 1.92 | 63/67 (94.0%) | 3.22% |
| **Region-Aware OCR** | 28.60% | 438.68%* | 42.52% | 117.48% | 7.02% | 4,916.7 ms | 1.16 | 67/67 (100.0%) | 0.00% |
| **Adaptive OCR (DocuReady)** | **24.44%** | **44.22%** | **38.03%** | **62.30%** | **7.05%** | **2,475.5 ms** | **1.12** | **67/67 (100.0%)** | **0.00%** |

*\*Note: Baseline strategies inflated macro CER on `CHALLENGE_01` (1639.6% on that document) due to raster OCR capturing background metadata tokens. Adaptive OCR correctly routed to native text extraction.*

---

## 3. Reproduced Adversarial Stress Performance

| Adversarial Fixture | Distortion Characteristic | Target Fields | Exact Match Rate | Mean Field CER | Mean Latency | Primary Failure Mode |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| `STRESS_01_SIMILAR_DIGIT_CONFUSION` | Font-level glyph similarity (0/O, 8/B, 1/I, 5/S) | 4 | **75.0% (3/4)** | 1.7% | 1,203.3 ms | Mixed case token `1Il5S` suffered confusion between `1` and `l`. |
| `STRESS_02_FAINT_RUBBER_STAMP_OVERLAY` | Translucent blue circular seal over text | 4 | **100.0% (4/4)** | 0.0% | 1,269.2 ms | Resilient: Otsu binarization separated faint ink from dark toner. |
| `STRESS_03_MULTICOLUMN_EMBEDDED_AMOUNTS` | Dense dual-column balance sheet with numbers | 4 | **50.0% (2/4)** | 24.2% | 1,571.0 ms | **Spatial Defect**: Column A numbers merged horizontally with Column B tokens. |
| `STRESS_04_SKEW_LOW_CONTRAST` | 2.8° rotation + 40% contrast reduction | 3 | **66.7% (2/3)** | 2.2% | 978.4 ms | Minor character drop in hospital code (`AIIMS-BBSR-8921`). |
| **Stress Suite Aggregate** | **All 4 Severe Adversarial Tests** | **15** | **73.3% (11/15)** | **7.0%** | **1,255.5 ms** | **Baseline Reproduced** |

---

## 4. Key Takeaways for Loop 19 Focus

The reproduction clearly isolated the exact vulnerability demanding architectural investigation in Loop 19:
- On single-column narrative documents, character recognition is highly accurate.
- On multi-column and tabular accounting records (`STRESS_03`), OCR words from adjacent cells bleed horizontally across columns, failing critical-field exact matching (50.0% failure on tabular amounts).
- Loop 19 must introduce table-aware spatial cell association to prevent horizontal cross-column bleeding.
