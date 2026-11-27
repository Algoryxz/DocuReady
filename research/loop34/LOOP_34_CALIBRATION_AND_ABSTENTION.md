# DOCUREADY — LOOP 34 CALIBRATION & ABSTENTION REPORT

**Milestone:** Loop 34  
**Date:** 2026-11-26  
**Operating Threshold:** $T^* = 70.0$  

---

## 1. Confidence Calibration Metrics

Calibration evaluates the alignment between the confidence score emitted by the pipeline and true empirical accuracy:

| Calibration Scope | Sample Population | ECE (%) | MCE (%) | Brier Score |
| :--- | :--- | :---: | :---: | :---: |
| **Candidate-Level Calibration** | All raw OCR extraction candidates | 46.93% | 89.00% | 0.4603 |
| **Decision-Conditional Calibration**| Claims verified by Decision Safety Layer | **5.93%** | **5.93%** | **0.0037** |

---

## 2. Analysis of the Decision Calibration Invariant

- **Raw Candidates:** Raw OCR text contains low-confidence guesses and noise, producing an expected candidate ECE of 46.93%.
- **Decision Safety Layer Filtering:** By enforcing the $T^*=70.0$ confidence floor and multi-attribute corroboration, raw candidates below threshold are filtered out.
- **Decision Calibration:** The verified population achieves an ECE of 5.93% and a near-perfect Brier score of 0.0037, proving that when DocuReady says VERIFIED, confidence reliably indicates truth.
