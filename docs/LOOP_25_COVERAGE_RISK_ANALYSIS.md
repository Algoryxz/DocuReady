# Loop 25 - Coverage vs Risk Trade-Off Analysis

## Risk Profile

In automated document audit and verification, false verifications represent severe legal and financial risks (e.g. verifying an incorrect debt amount or toxic dosage). DocuReady's core design tenet is:

$$\text{Cost}(\text{False Verification}) \gg \text{Cost}(\text{Abstention})$$

## Empirical Frontier

| Threshold $T$ | Verified Claims | False Verifications | Precision | Coverage | Risk Assessment |
|---|---|---|---|---|---|
| $T=40.0$ | 88 | 1 | 98.86% | 88.00% | Unacceptable: 1 false verification |
| $T=50.0$ | 88 | 1 | 98.86% | 88.00% | Unacceptable: 1 false verification |
| $T=60.0$ | 88 | 1 | 98.86% | 88.00% | Unacceptable: 1 false verification |
| $T=65.0$ | 86 | 1 | 98.84% | 86.00% | Unacceptable: 1 false verification |
| **$T=70.0$ (Selected)** | **84** | **0** | **100.00%** | **84.00%** | **Optimal: Zero false verifications, maximum safe coverage** |
| $T=75.0$ | 80 | 0 | 100.00% | 80.00% | Safe, but unnecessarily loses 4 valid claims |
| $T=80.0$ | 76 | 0 | 100.00% | 76.00% | Over-conservative |
| $T=90.0$ | 36 | 0 | 100.00% | 36.00% | Severe under-coverage |
