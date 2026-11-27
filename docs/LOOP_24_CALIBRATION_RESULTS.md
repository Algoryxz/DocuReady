# LOOP 24 — CALIBRATION RESULTS & STATISTICAL METRICS

## 1. Metric Formulations

To quantify whether DocuReady's confidence scores accurately reflect verification correctness, Loop 24 evaluated three standard probabilistic calibration metrics across verified claims:

1. **Expected Calibration Error (ECE)**:
   $$ECE = \sum_{m=1}^M \frac{|B_m|}{N} \left| \text{acc}(B_m) - \text{conf}(B_m) \right|$$
   where verified claims are partitioned into $M=5$ confidence bins $B_1, \dots, B_M$.
2. **Maximum Calibration Error (MCE)**:
   $$MCE = \max_{m=1,\dots,M} \left| \text{acc}(B_m) - \text{conf}(B_m) \right|$$
   measuring the worst-case divergence between confidence and empirical accuracy across any bin.
3. **Brier Score**:
   $$BS = \frac{1}{N} \sum_{i=1}^N \left( \frac{c_i}{100} - y_i \right)^2$$
   where $y_i = 1$ if the verified claim matches ground truth exactly (both value and spatial coordinate), and $0$ otherwise.

---

## 2. Empirical Calibration Results

| Corpus / Cohort | Verified Claims | Exact Matches | Empirical Accuracy | Mean Confidence | ECE | MCE | Brier Score |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Cohort I (30 Docs)** | 19 | 19 | **100.00%** | 82.74% | **0.1726** | **0.2500** | **0.0341** |
| **Combined Corpus (82 Docs)**| 90 | 90 | **100.00%** | 88.28% | **0.1172** | **0.1667** | **0.0212** |

---

## 3. Reliability Analysis

- **Zero Overconfidence**: Because empirical accuracy is 100.00% across all verified claims, the model does NOT exhibit dangerous overconfidence (where predicted confidence exceeds actual accuracy). Instead, it displays healthy slight underconfidence (mean confidence is 88.28% while accuracy is 100.00%), which provides a strong safety buffer against false claims.
- **Low Brier Score (0.0212)**: The Brier score is exceptionally low, indicating that the probability assignments are tightly concentrated near the true outcomes.
