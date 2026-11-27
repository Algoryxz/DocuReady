# LOOP 17: Pre-Registered Experiment Plan

## 1. Research Objectives & Acceptance Targets

The primary objective of Loop 17 is to optimize the efficiency and execution latency of the Adaptive OCR Strategy Selector while maintaining or improving character accuracy, reading order fidelity, and critical-field reliability.

### Quantitative Acceptance Targets:
1. **Latency Reduction:** Reduce Loop 16 Adaptive mean latency by at least **20%** (target: $\le 2427.9\text{ ms}$, down from $3034.9\text{ ms}$).
2. **Character Accuracy Preservation:** Preserve mean CER within $\pm 1.0\%$ absolute of the Loop 16 baseline ($21.46\% \pm 1.0\% \implies \le 22.46\%$), targeting improvements where possible.
3. **Word Accuracy Preservation:** Maintain or improve mean WER ($\le 32.45\%$).
4. **Reading Order Inversion Constraint:** Maintain reading-order line inversions below $5.0\%$.
5. **Critical-Field Reliability:** Measure and report field exact match, date exact match, and identifier accuracy across structured documents.
6. **Invocation Efficiency:** Keep average OCR subprocess invocations $\le 1.25$ per page.
7. **Zero Label Leakage:** Ensure zero access to ground truth, filenames, or split metadata.

---

## 2. Experimental Hypotheses

### Hypothesis H1: Thumbnail Script Probe Optimization
- *Observation:* The 700px thumbnail Tesseract pass (`--psm 6`, `eng+hin+ori`) takes 200–250 ms per page.
- *Proposed Change:* Downsample the thumbnail probe image to 500px width and use `--psm 11` (sparse text finder) or an accelerated text strip. Alternatively, only probe Indic glyph presence if horizontal or character heuristics indicate non-Latin ink.
- *Expected Impact:* Reduces profiling latency by 80–120 ms per page without degrading script routing accuracy.

### Hypothesis H2: Column-Level Dual-Pass Rather than Multi-Region Crop Overkill
- *Observation:* `ocr_page_by_regions()` currently performs horizontal projection slicing *within* each column, creating 4 to 24 micro-crops and launching multiple Tesseract processes.
- *Proposed Change:* In two-column documents (`has_column_gutter == True`), perform a clean vertical split into two half-page images (Left Column and Right Column). Route each column as a single whole-block pass with its detected language.
- *Expected Impact:* Cuts two-column processing time from 4.4s–7.0s down to $\sim 2.2\text{s}–2.8\text{s}$, eliminating dozens of redundant process spawns while preserving reading order.

### Hypothesis H3: Self-Healing Fallback Threshold Calibration
- *Observation:* The fallback gate currently re-runs full `eng+hin+ori` OCR whenever valid words $< 3$ and mean confidence $< 25\%$, even on documents where low confidence was due to natural script characteristics.
- *Proposed Change:* Only trigger fallback when `ink_density > 0.02` (substantial ink) and extracted text is empty or pure noise characters.
- *Expected Impact:* Eliminates spurious second-pass OCR invocations, saving $\sim 2000\text{ ms}$ on challenging scans.

---

## 3. Evaluation Corpus Strategy

1. **Reproduction on 15-Document Corpus:**
   - First validate all optimizations against the identical 15-document corpus from Loop 16 (11 `PRIMARY_VALIDATION` + 4 `SEALED_CHALLENGE`).
2. **Corpus Expansion:**
   - Add new verified Indian administrative and identity documents (pension notices, income certificates, university marksheets, caste certificates) with verified ground truth and critical-field annotations.
3. **Split Isolation:**
   - Primary validation set used for heuristic tuning.
   - Sealed challenge set evaluated only at final qualification gate.

---

## 4. Execution Phases

```
PHASE 1: Baseline Reproduction & Profiler Breakdown (Completed)
PHASE 2: Corpus Expansion & Critical-Field Annotation
PHASE 3: Heuristic & Profiler Latency Optimization
PHASE 4: Column-Level Spatial OCR Optimization
PHASE 5: Full 10-Strategy Matrix Benchmark Execution
PHASE 6: Critical-Field Accuracy Evaluation
PHASE 7: Automated Test Suite & Regression Verification
PHASE 8: Final Qualification & Documentation Delivery
```
