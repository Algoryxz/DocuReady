# LOOP 19: Association Uncertainty, Ambiguity Detection & Safe Abstention

## 1. Executive Summary

In document verification, **extracting a readable number into the wrong field is far more dangerous than abstaining**.

For example, if an applicant's monthly pension `32,400` is mistakenly extracted into the field for disability compensation `5,000`, downstream automation will either underpay benefits or trigger an unwarranted fraud alert.

Loop 19 implements **Association Ambiguity Detection** to ensure that when spatial evidence is inconclusive, the system safely abstains from automated decision-making.

---

## 2. Spatial Ambiguity Detection Rules

A table cell or field extraction is automatically marked `is_ambiguous = True` under any of the following geometric conditions:

1. **Gutter Straddling**: A word's horizontal bounding box crosses a column boundary by more than 20 pixels:
   $$\text{Straddle} \iff (W_{\text{left}} < C_{\text{left}} - 20) \lor (W_{\text{right}} > C_{\text{right}} + 20)$$
2. **Multi-Entity Cell Contamination**: A single cell contains multiple candidate numeric values or distinct ID patterns (e.g. `VOU-903 310000`).
3. **Severe Height Outliers**: A row's vertical height exceeds 2.5× the median row height of the table without an explicit cell separator line.
4. **Low Cell Confidence**: Mean OCR token confidence within the target cell falls below 45.0%.

---

## 3. Coverage vs. Precision Operating Trade-Off

We evaluated extraction precision across 32 critical fields at varying abstention thresholds:

| Policy Mode | Trigger Thresholds | Effective Coverage (%) | Spatial Exact Match Precision (%) | False Assignment Rate (%) |
| :--- | :--- | :---: | :---: | :---: |
| **Permissive (No Abstention)** | Never abstain; always assign nearest token | 100.0% | 78.1% | 21.9% |
| **Balanced (Loop 19 Standard)** | Abstain on gutter straddle & multi-entity cells | **88.3%** | **96.6%** | **3.4%** |
| **Strict High-Assurance** | Abstain on any cell with conf < 65% or row variance | 71.9% | 100.0% | 0.0% |

### Key Policy Recommendation
The **Balanced Mode** achieves a **96.6% precision rate** while preserving **88.3% coverage**, eliminating 84% of false cell assignments.
