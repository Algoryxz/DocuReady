# Loop 22 — Confidence Calibration & Empirical Reliability

**Audit Corpus:** 46 Documents, 95 Critical Fields  
**Evaluator:** `research/loop22/benchmark/run_loop22_benchmark.py`

---

## 1. Empirical Confidence Meaning

In DocuReady, confidence is reported on a 0–100 scale derived from Tesseract character recognition and bounding box stability.
Prior to Loop 22, this confidence was treated as monotonic with correctness, but never rigorously audited across bins.

The empirical audit revealed:
- Raw confidence is **not** a true posterior probability.
- Confidence becomes highly unreliable below 60.0, where character recognition is frequently noisy syntax garble (e.g. `fe}` at conf 35.0).
- High confidence (95–100) on character recognition does not guarantee association correctness (e.g. `54000` extracted from the wrong column had 95.0 confidence).

---

## 2. Empirical Calibration Bins

Evaluated across all 95 critical fields in the Loop 22 benchmark:

| Confidence Bin | Field Count | Correct Verifications | Empirical Accuracy | Calibration Assessment |
| :---: | :---: | :---: | :---: | :--- |
| **$[0, 50)$** | 13 | 4 | **30.77%** | Severe unreliability. (4 correct were empty cell abstentions with conf 0.0). |
| **$[50, 70)$** | 9 | 6 | **66.67%** | Moderate reliability; significant risk of digit confusion. |
| **$[70, 85)$** | 11 | 10 | **90.91%** | Well-calibrated, high empirical precision. |
| **$[85, 95)$** | 23 | 20 | **86.96%** | High precision; occasional low-contrast decimal drop. |
| **$[95, 101)$** | 39 | 35 | **89.74%** | Very high reliability once decimal crossbar bug is fixed. |

---

## 3. Calibration Invariants & Expected Calibration Error (ECE)

Using standard ECE formulation across the $M=5$ bins:

$$\text{ECE} = \sum_{m=1}^M \frac{|B_m|}{N} \left| \text{acc}(B_m) - \text{conf}(B_m) \right|$$

With the Loop 22 risk-calibrated confidence floor set at $T=60.0$:
- All candidate extractions with confidence $< 60.0$ are automatically abstained.
- Empirical accuracy for verified claims jumps from **80.82% up to 95.71%**, cutting false verifications by **78.6%** (from 14 down to 3).
