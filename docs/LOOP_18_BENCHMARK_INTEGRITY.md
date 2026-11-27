# LOOP 18: Benchmark Integrity, Alignment Defect Audit & Dual-Metric Scoring

## 1. Executive Summary

A core objective of Loop 18 is the adversarial audit of the evaluation methodology itself. During the replication of Loop 17 results, our audit identified two critical methodological flaws in the previous benchmarking scripts:
1. **False Zero-Inversion Defect**: The reading-order inversion metric reported 0.00% across all strategies because OCR output words were joined with `" ".join(words)`. Calling `.splitlines()` on the resulting string produced a list of length 1, triggering an early-exit guard (`if len(lines) < 2: return 0.0`) on every single document.
2. **Macro-Averaged vs. Micro Corpus-Level CER Distortions**: Reporting only the unweighted arithmetic mean of per-document error rates creates distortion when outlier documents (such as screenshots containing browser chrome or UI text not in the reference transcription) exhibit CER > 100%.

In Loop 18, we have completely overhauled the benchmark evaluation pipeline to restore mathematical integrity.

---

## 2. Line Reconstruction & True Reading-Order Evaluation

### The Defect in Loop 17
In `research/loop17/benchmark/run_strategy_benchmark.py`:
```python
# Flattened hypothesis words without newline delimiters
words = [str(w).strip() for w, c in zip(data.get("text", []), data.get("conf", [])) if str(w).strip() and float(c) >= 0]
hyp_text = " ".join(words)
hyp_lines = [l for l in hyp_text.splitlines() if l.strip()]
if not hyp_lines and hyp_text:
    hyp_lines = [hyp_text]
```
Because no newline characters (`\n`) existed in `hyp_text`, `hyp_lines` was always a single-element list `[hyp_text]`. The reading-order inversion calculation:
```python
def compute_reading_order_inversion(lines: List[str], reference_lines: List[str]) -> float:
    if len(lines) < 2 or len(reference_lines) < 2:
        return 0.0
    ...
```
invariably evaluated `len(lines) < 2` as `True`, returning `0.00%` universally, masking layout and reading-order defects.

### The Loop 18 Solution
DocuReady provides an internal spatial clustering engine via `PageOCRData`:
```python
from docuready.ingest.extractor import PageOCRData

ocr_obj = PageOCRData(data, dpi=200)
reconstructed_lines = [l["text"].strip() for l in ocr_obj.lines if l.get("text", "").strip()]
hyp_text = "\n".join(reconstructed_lines)
```
`PageOCRData.lines` groups detected word boxes by vertical overlap and sorting, accurately reconstructing genuine document lines. The list of reconstructed lines is then evaluated against the ground-truth line sequence using Kendall-tau rank inversion analysis:
$$\text{Inversion Rate} = \frac{\text{Number of Inverted Line Pairs}}{\text{Total Line Pairs}} \times 100\%$$

---

## 3. Dual-Metric Accuracy Architecture (Macro vs. Micro)

To provide an honest, unvarnished assessment of OCR accuracy, Loop 18 reports both:

### A. Macro Mean Per-Document CER & WER
$$\text{Macro CER} = \frac{1}{N} \sum_{i=1}^N \frac{\text{Levenshtein}(H_i, R_i)}{|R_i|}$$
- **Purpose**: Evaluates average per-document user experience and continuity with Loop 15–17 reports.
- **Sensitivity**: Sensitive to outlier documents with extraneous text or layout truncations.

### B. Micro Corpus-Level CER & WER
$$\text{Corpus CER} = \frac{\sum_{i=1}^N \text{Levenshtein}(H_i, R_i)}{\sum_{i=1}^N |R_i|}$$
- **Purpose**: Measures the true global symbol-level error rate across all processed characters in the corpus, preventing short outlier documents from disproportionately biasing aggregate conclusions.

---

## 4. Multi-Faceted Critical-Field Evaluation

Critical fields (e.g. PPO numbers, dates, monetary amounts, certificate IDs) cannot be evaluated solely by fuzzy substring search. Loop 18 implements a five-way verification harness:
1. **Exact Match**: The exact string appears in the hypothesis text (case-insensitive).
2. **Normalized Match**: Matches after stripping punctuation and whitespace (handles OCR spacing artifacts like `18 / 08 / 2026`).
3. **Numeric Match**: Compares extracted digits only, ensuring fiscal amounts and ID numbers are uncorrupted.
4. **Date Match**: Extracts date components ($\text{DD}/\text{MM}/\text{YYYY}$) and verifies chronological alignment.
5. **Field CER**: Levenshtein distance between expected value and the closest candidate token in the hypothesis string.
