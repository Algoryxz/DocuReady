# LOOP 24 — RISK-COVERAGE ANALYSIS & SELECTIVE VERIFICATION

## 1. Selective Verification Theory

In high-stakes enterprise document processing (auditing, healthcare, legal compliance, tax settlement), the cost of a **false verification** vastly exceeds the cost of an **abstention**. An abstention can be routed to human review, whereas a false verification introduces silent corruption into financial ledgers or medical records.

Selective verification formalizes this tradeoff via **Risk-Coverage Curves**:
- **Verification Risk (False Verification Rate, FVR)**:
  $$\text{Risk} = \frac{\text{False Verifications}}{\text{Verified Claims}}$$
- **Coverage**:
  $$\text{Coverage} = \frac{\text{Verified Claims}}{\text{Total Evaluated Fields}}$$

---

## 2. Risk vs Coverage Tradeoff Table

From our empirical threshold sweep across the Development and Calibration cohorts:

| Threshold ($T$) | Coverage (%) | Precision (%) | False Verification Rate (%) | ECE | Brier Score | Risk Assessment |
| :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **40.0** | 27.27% | 93.33% | 6.67% | 0.125 | 0.067 | High risk: 1 false verification permitted |
| **45.0** | 27.27% | 93.33% | 6.67% | 0.125 | 0.067 | High risk: low-confidence OCR noise leaks |
| **50.0** | 27.27% | 93.33% | 6.67% | 0.125 | 0.067 | High risk |
| **55.0** | 27.27% | 93.33% | 6.67% | 0.125 | 0.067 | High risk |
| **60.0** | 27.27% | 93.33% | 6.67% | 0.125 | 0.067 | High risk |
| **65.0** | 27.27% | 93.33% | 6.67% | 0.125 | 0.067 | Marginal boundary |
| **70.0** | **21.82%** | **100.00%** | **0.00%** | **0.161** | **0.029** | **Optimal Operating Point: Zero False Verifications** |
| **75.0** | 21.82% | 100.00% | 0.00% | 0.161 | 0.029 | Zero false verifications |
| **80.0** | 18.18% | 100.00% | 0.00% | 0.147 | 0.024 | Overly conservative |
| **85.0** | 10.91% | 100.00% | 0.00% | 0.117 | 0.015 | Heavy coverage loss |
| **90.0** | 1.82% | 100.00% | 0.00% | 0.050 | 0.003 | Severe under-coverage |

---

## 3. Pareto Frontier Conclusion

The Pareto frontier clearly identifies $T^* = 70.0$ as the optimal operating point. At $T=70.0$, False Verification Rate drops to **0.00%**, achieving the required **100% precision guarantee** while retaining maximum possible coverage before precision is compromised.
