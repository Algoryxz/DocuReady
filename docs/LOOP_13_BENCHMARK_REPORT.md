# DOCUREADY — LOOP 13
## Benchmark Evaluation Report: Spatial Reading Order & Multi-Column Accuracy

**Project:** DocuReady  
**Evaluation Harness:** `research/loop13/benchmark/run_loop13_benchmark.py`  
**Results Data:** `research/loop13/results/loop13_benchmark_results.json`  
**Baseline Model:** Loop 12 Naive Scanline Clustering (`_cluster_words_raw`, $y_{\text{tol}}=8.0$)  
**Target Model:** Loop 13 Column-Aware Spatial Reconstruction (`cluster_and_order_words`)  

---

### 1. Benchmark Methodology

The Loop 13 benchmark suite measures document reading-order accuracy across six diverse document typologies covering both multi-column layouts and regression-critical single-column / tabular structures.

#### Evaluated Metrics
1. **Pairwise Inversion Error Rate (PIER):**
   The fraction of word pairs $(w_i, w_j)$ whose sequential order in the OCR output is inverted relative to their ground truth reading order:
   $$\text{PIER} = \frac{\sum_{i < j} \mathbf{1}[\text{pos}(w_i) > \text{pos}(w_j)]}{\binom{N}{2}}$$
2. **Word Error Rate (WER):**
   Normalized Levenshtein edit distance at word token granularity against the canonical ground truth transcription.
3. **Character Error Rate (CER):**
   Normalized Levenshtein edit distance at character granularity.
4. **Processing Latency Overhead:**
   Wall-clock CPU time added to the page ingestion pipeline in milliseconds.

---

### 2. Comparative Results Summary

| Document ID | Layout Category | Word Count | Baseline WER | Loop 13 WER | Baseline Inversion Rate | Loop 13 Inversion Rate | Latency Overhead |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `DOC_01_TWO_COL_NARRATIVE` | Two-Column Text | 18 | 66.67% | **0.00%** | 17.65% | **0.00%** | +4.33 ms |
| `DOC_02_HEADER_FOOTER_BRACKET` | Bracketed Multi-Column | 19 | 31.58% | **0.00%** | 5.26% | **0.00%** | +0.44 ms |
| `DOC_03_ASYMMETRIC_COLUMNS` | Asymmetric Columns | 15 | 66.67% | **0.00%** | 29.52% | **0.00%** | +0.52 ms |
| `DOC_04_KEY_VALUE_FORM` | Tabular Form | 13 | 0.00% | **0.00%** | 0.00% | **0.00%** | +0.40 ms |
| `DOC_05_MARKSHEET_TABLE_GRID` | 3-Column Data Grid | 12 | 0.00% | **0.00%** | 0.00% | **0.00%** | +0.24 ms |
| `DOC_06_SINGLE_COLUMN_CERTIFICATE` | Single-Column Narrative | 16 | 0.00% | **0.00%** | 0.00% | **0.00%** | +0.21 ms |
| **MACRO AVERAGE** | **All Categories** | — | **27.49%** | **0.00%** | **8.74%** | **0.00%** | **+1.02 ms** |

---

### 3. Detailed Document Case Analysis

#### Case 1: `DOC_01_TWO_COL_NARRATIVE` (Pure Two-Column Notification)
- **Baseline Behavior:** Words were merged scanline-by-scanline horizontally across the 120 pt gutter:
  *"The post-matric scholarship State verification offices scheme guidelines require shall inspect..."*
  Word Error Rate was 66.67%, with an inversion rate of 17.65%.
- **Loop 13 Behavior:** Gutter detected at $x = 295.0$. Column 1 sequenced first, followed by Column 2.
  WER dropped from **66.67% to 0.00%**, and inversion rate dropped from **17.65% to 0.00%**.

#### Case 2: `DOC_02_HEADER_FOOTER_BRACKET` (Spanning Header & Footer)
- **Baseline Behavior:** The top header ("GOVERNMENT OF INDIA") and footer ("Official Gazette Notification 2026") were preserved, but lines within the 2-column body were interleaved.
- **Loop 13 Behavior:** Zone segmentation correctly detected:
  - Header: $y < 100$ pt
  - Body: $x \le 295$ pt (Col 1) $\to x > 295$ pt (Col 2)
  - Footer: $y \ge 220$ pt
  WER dropped from **31.58% to 0.00%**.

#### Case 3: `DOC_03_ASYMMETRIC_COLUMNS` (Unequal Line Counts & Parallel Headings)
- **Challenge:** Left column had 4 lines; right column had 2 lines. Left column had "Primary Objective:" and right column had "Disbursement Window:", both ending with colons.
- **Loop 13 Behavior:** Parallel colon heading detection prevented false key-value classification. Left column lines 1–4 were sequenced, followed by right column lines 1–2.
  WER dropped from **66.67% to 0.00%**, and inversion rate dropped from **29.52% to 0.00%**.

#### Case 4, 5, 6: Regression Invariants (`DOC_04`, `DOC_05`, `DOC_06`)
- **Key-Value Form (`DOC_04`):** Preserved at 0.00% WER. "Applicant Name: ROHIT VERMA" remained intact on the same line.
- **Marksheet Grid (`DOC_05`):** 3-column table grid with numbers "100" and "92" preserved at 0.00% WER with row-wise integrity.
- **Single-Column Certificate (`DOC_06`):** Standard paragraph preserved at 0.00% WER with zero reordering.

---

### 4. Key Engineering Conclusion

The column-aware spatial reconstruction engine completely eliminates multi-column text interleaving across both symmetric and asymmetric column flows, achieving **0.00% WER** and **0.00% Inversion Rate** across all benchmark test documents while adding an average of just **1.02 ms** of overhead.
