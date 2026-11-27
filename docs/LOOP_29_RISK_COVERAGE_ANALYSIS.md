# Loop 29 Risk-Versus-Coverage Analysis

## 1. Operating Point
- **Operating Threshold**: $T^* = 70.0$, $T_{\text{fuzzy}} = 75.0$
- **Observed False Verification Rate**: 0.00%
- **Claim Coverage**: 45.65% across Loop 28 corpus; 73.79% across Cohort M.

## 2. Tradeoff Curve
Under strict risk tolerance (0 permitted false verifications), coverage is deliberately bounded.
Relaxing contradiction or entity checks increases coverage to 83.70% (LOO-Contradiction) or 100% (Naive Baseline), but causes false verifications to surge from 0 to 35 and 50 respectively.
DocuReady strictly prioritizes evidence safety over headline coverage.
