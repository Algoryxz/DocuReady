# LOOP 17: Benchmark Integrity, Scoring Methodology & Fairness Audit

## 1. Executive Summary

A core directive of Loop 17 is ensuring benchmark integrity. Research metrics must not be manufactured, biased, or overfit.
This report documents the mathematical definitions, scoring logic, boundary condition handling, and fairness safeguards implemented in `research/loop17/benchmark/run_strategy_benchmark.py`.

---

## 2. Metric Scoring Implementations

### 2.1. Character Error Rate (CER) & Word Error Rate (WER)
- **Mathematical Definition:**
  $$\text{CER} = \frac{\text{Levenshtein}(H_{\text{chars}}, R_{\text{chars}})}{\max(1, |R_{\text{chars}}|)}$$
  $$\text{WER} = \frac{\text{Levenshtein}(H_{\text{words}}, R_{\text{words}})}{\max(1, |R_{\text{words}}|)}$$
  where $H$ is the hypothesis string, $R$ is the reference ground truth string, and distance is computed via $O(N \times M)$ dynamic programming Levenshtein matrix.
- **Unicode Normalization:**
  All strings are pre-processed through `unicodedata.normalize("NFC", text)`. Zero-width non-joiners (`\u200c`), zero-width joiners (`\u200d`), and byte order marks (`\ufeff`) are stripped before distance calculation to prevent invisible tokenization penalties.

### 2.2. Empty Reference & Hypothesis Handling
- If reference is empty ($|R| = 0$):
  - If hypothesis is also empty ($|H| = 0$): $\text{CER} = 0.0, \text{WER} = 0.0$ (correctly recognized blank/abstained page).
  - If hypothesis is non-empty ($|H| > 0$): $\text{CER} = 1.0, \text{WER} = 1.0$ (penalizes hallucinations).
- If reference is non-empty and hypothesis is empty:
  - $\text{CER} = 1.0, \text{WER} = 1.0$.

### 2.3. Reading-Order Inversion Rate
- Maps ground-truth reference words to their true line indices ($0, 1, \dots, L-1$).
- Projects hypothesis lines onto the reference word index space to calculate mean line rank.
- Computes inversion pairs:
  $$\text{Inversion Rate} = \frac{\sum_{i < j} \mathbf{1}[\text{rank}_i > \text{rank}_j]}{\max(1, \text{Total Pairs})} \times 100\%$$
- A rate of $0.0\%$ indicates perfect monotonic top-to-bottom reading order.

---

## 3. Critical-Field Accuracy Verification

To prevent subjective scoring, critical-field matching uses strict criteria:
- Every field is declared in an independent contract file in `research/loop17/critical_fields/`.
- Numeric values (e.g. `180000`, `63750`) must match all digits exactly.
- Identification strings (e.g. `DL-REV-2026-9812`, `UU-2026-55194`) must match alphanumeric characters without missing digits or substitutions.
- Names permit case-insensitivity but must contain all expected surname and given-name components.

---

## 4. Leakage & Fairness Safeguards

1. **No Oracle Routing:** The adaptive selector executes before ground truth is accessed. The selector does not receive document IDs, filenames, or target languages.
2. **Timing Boundary Parity:** Every strategy's latency timer encapsulates:
   - Language selection / profiling
   - Subprocess invocation
   - Output parsing and bounding box construction
   - Memory tracing via `tracemalloc`
3. **No Exclusion of Challenging Cases:** Degraded, skewed, and unreadable scans are fully included in aggregate statistics.
