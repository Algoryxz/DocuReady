# LOOP 18: Baseline Reproduction & Benchmark Integrity Audit

## 1. Executive Summary

As the first technical milestone of Loop 18, we reproduced and audited the baseline benchmark results reported by Loop 17 (`research/loop17/strategy_results.json` and `docs/LOOP_17_PERFORMANCE_REPORT.md`).

Our audit confirmed that the latency reduction and invocation efficiency gains reported in Loop 17 are genuine and reproducible. However, our deep line-by-line inspection of the benchmark evaluation script (`research/loop17/benchmark/run_strategy_benchmark.py`) uncovered two critical methodological nuances:
1. **The Reading-Order Inversion Metric Bug**: The reading-order inversion rate was reported as 0.0% across all strategies because words were collapsed into a single whitespace-joined string prior to evaluation, leaving `len(lines) == 1` and triggering an early exit guard.
2. **Macro Per-Document vs. Micro Corpus-Level CER**: Loop 17 reported the unweighted arithmetic mean of per-document CERs. Documents with extraneous token detections (e.g. `DOC_EXT_01` screenshot headers) produced individual CERs exceeding 100%, inflating the reported macro-average to ~52%.

---

## 2. Reproduction of Loop 17 Benchmark Results

We executed the baseline benchmark over the 20-document corpus defined in Loop 17. The reproduced figures match the committed results exactly:

| Strategy | Mean Invocations | Mean Latency (ms) | Macro CER (%) | Macro WER (%) | Reading Order Inversion (Reported) | Critical-Field Match Rate |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Global Multilingual (`eng+hin+ori`)** | 1.00 | 3,034.4 | 53.79% | 72.88% | 0.00%* | 36/42 (85.7%) |
| **Page-Level Routing** | 1.00 | 2,289.4 | 57.19% | 72.58% | 0.00%* | 35/42 (83.3%) |
| **Region-Aware OCR** | 1.85 | 3,838.7 | 54.06% | 71.04% | 0.00%* | 38/42 (90.5%) |
| **Adaptive OCR (Loop 17)** | **1.15** | **1,962.4** | **51.98%** | **70.11%** | 0.00%* | **42/42 (100.0%)** |

*\*Note: The 0.00% inversion rate was an artifact of the line flattening defect detailed below.*

### Key Reproduction Findings
1. **Latency Advantage Confirmed**: Adaptive OCR achieved a **35.3% reduction** in runtime compared to Global Multilingual (1,962.4 ms vs 3,034.4 ms) and a **48.9% reduction** compared to Region-Aware OCR (1,962.4 ms vs 3,838.7 ms).
2. **Invocation Efficiency**: Adaptive OCR invoked the OCR engine an average of 1.15 times per document, significantly avoiding the 1.85 invocations required by Region-Aware OCR.
3. **Critical Field Accuracy on Clean Corpus**: Across the 8 documents in the critical-field subset, Adaptive OCR achieved 42/42 exact field matches (100%).

---

## 3. Audit Findings: The Reading-Order Inversion Metric Defect

In `research/loop17/benchmark/run_strategy_benchmark.py`, lines 284–288:
```python
# Flattened hypothesis words
hyp_text = " ".join([w.get("text", "") for w in hyp_words if w.get("text")])
```
The script then evaluated reading-order inversions:
```python
def compute_reading_order_inversion(hyp_lines, ref_lines):
    if len(hyp_lines) < 2 or len(ref_lines) < 2:
        return 0.0
    ...
```
When `hyp_text.splitlines()` was called on a string joined solely with spaces, `hyp_lines` consisted of exactly 1 element. Consequently, `len(hyp_lines) < 2` was satisfied for every single document, causing `compute_reading_order_inversion` to return `0.0` universally.

### The Fix for Loop 18
DocuReady's ingest engine (`src/docuready/ingest/extractor.py`) contains a dedicated spatial clustering module:
```python
from docuready.ingest.spatial_layout import cluster_and_order_words
from docuready.ingest.extractor import PageOCRData
```
`PageOCRData(data, dpi=200).lines` groups words into actual spatial lines based on vertical bounding box overlap. Feeding these reconstructed lines into `compute_reading_order_inversion()` restores honest, measurable reading-order evaluation.

---

## 4. Audit Findings: Macro vs. Micro CER Discrepancy

Loop 17 calculated mean CER as:
$$\text{Macro CER} = \frac{1}{N} \sum_{i=1}^N \frac{\text{Levenshtein}(H_i, R_i)}{|R_i|}$$

For documents such as `DOC_EXT_01` (a screenshot of an administrative form), OCR recognized UI elements and browser chrome not present in the reference transcription, resulting in a per-document CER of 142.3%. Averaging this outlier heavily penalizes the aggregate.

In Loop 18, we report both:
1. **Macro CER / WER**: The unweighted per-document mean (for continuity with Loops 15–17).
2. **Micro Corpus-Level CER / WER**:
   $$\text{Corpus CER} = \frac{\sum_{i=1}^N \text{Levenshtein}(H_i, R_i)}{\sum_{i=1}^N |R_i|}$$
   This provides the true global character error rate across all processed text.
