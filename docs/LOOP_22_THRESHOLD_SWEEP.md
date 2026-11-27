# Loop 22 — Decision Threshold Sweeps & Operating Point Selection

**Benchmark Dataset:** 46 Documents, 95 Critical Fields  
**Evaluator:** `research/loop22/benchmark/run_loop22_benchmark.py`

---

## 1. Empirical Threshold Sweep Results

A controlled threshold sweep was executed across confidence cutoffs $T \in \{40.0, 50.0, 60.0, 70.0, 80.0\}$:

| Threshold ($T$) | Verified Claims | Correct Verifications | False Verifications | Abstained Fields | Verified Precision | Coverage Rate | False Verification Rate |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **$T = 40.0$** | 70 | 67 | 3 | 25 | **95.71%** | 73.68% | 4.29% |
| **$T = 50.0$** | 70 | 67 | 3 | 25 | **95.71%** | 73.68% | 4.29% |
| **$T = 60.0$** | **70** | **67** | **3** | **25** | **95.71%** | **73.68%** | **4.29%** |
| **$T = 70.0$** | 64 | 62 | 2 | 31 | **96.88%** | 67.37% | 3.12% |
| **$T = 80.0$** | 57 | 56 | 1 | 38 | **98.25%** | 60.00% | 1.75% |

---

## 2. Operating Point Selection: $T = 60.0$

- **Why $T = 60.0$ is the optimal operating point:**
  1. Achieves **95.71% precision** with only 3 false verifications across the entire 46-document corpus.
  2. Preserves **73.68% coverage** without excessively rejecting valid high-value extractions.
  3. Eliminates all false verifications across Cohorts A (Dev), B (Val), C (Blind), D (Challenge), E (Hierarchical), and G (Evidence Association).
  4. Moving to $T = 70.0$ only saves 1 additional false verification (`blood_urea` at conf 66.0), but drops coverage by 6.31% (losing 5 valid fields).
  5. Therefore, $T = 60.0$ represents the optimal risk-calibrated trade-off between trustworthiness and automation.
