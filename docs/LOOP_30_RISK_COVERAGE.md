# Loop 30 — Risk-Coverage Frontiers & Selective Verification Policy

## 1. Selective Verification Operating Trade-Off
DocuReady operates on a **Selective Verification** paradigm: rather than forcing a prediction on every candidate extraction, the system selectively abstains whenever risk indicators (low OCR clarity, entity ambiguity, template reuse, single-character identifier ambiguity, or cross-document conflict) exceed safety margins.

This architecture creates a controllable trade-off frontier between **Coverage** (percentage of claims verified) and **Precision** (correctness of verified claims).

---

## 2. Threshold Sensitivity Analysis

Across the 92 claims of the cross-document benchmark:

| Threshold ($T^*$) | Verified Claims | Exact Matches | False Verifications | Abstained Claims | Precision | Coverage | ECE (Verified) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **$T^* = 50.0$** | 56 | 51 | 5 | 36 | 91.07% | 60.87% | 14.22% |
| **$T^* = 60.0$** | 49 | 47 | 2 | 43 | 95.92% | 53.26% | 9.80% |
| **$T^* = 70.0$ (BASELINE)** | **42** | **42** | **0** | **50** | **100.00%** | **45.65%** | **5.93%** |
| **$T^* = 75.0$** | 38 | 38 | 0 | 54 | 100.00% | 41.30% | 5.21% |
| **$T^* = 80.0$** | 33 | 33 | 0 | 59 | 100.00% | 35.87% | 4.88% |
| **$T^* = 90.0$** | 22 | 22 | 0 | 70 | 100.00% | 23.91% | 3.12% |

### Strategic Operating Point: $T^* = 70.0$
- $T^* = 70.0$ is the optimal operating threshold on the Pareto frontier.
- Lowering to $T^* = 60.0$ gains $7.61\%$ coverage but permits 2 false verifications.
- Raising to $T^* = 80.0$ decreases coverage by $9.78\%$ without improving precision (which is already $100.0\%$).
- At $T^* = 70.0$, the system captures maximum verified evidence while ensuring zero observed false verifications.

---

## 3. False Verification Safety Boundaries
The safety profile of DocuReady is defended by five orthogonal layers:
1. **OCR Confidence Filter ($T^* = 70.0$):** Prunes noisy tokens.
2. **Entity Identity Resolution:** Requires consistent name, guardian, or tax/account identifier across documents.
3. **Document Independence Detector:** Suppresses duplicate files and template boilerplate masquerading as independent confirmation.
4. **Semantic Unit Normalizer:** Normalizes equivalent representations (e.g. 1 MT == 1000 KG) while detecting true unit/numerical mismatches.
5. **Cross-Document Contradiction Interceptor:** Overrides single-document confidence whenever two independent sources report conflicting values for the same entity field.
