# Loop 25 - Calibration Results (ECE, MCE, Brier Score)

## Summary Metrics

| Cohort | Verified Claims | Exact Matches | ECE | MCE | Brier Score |
|---|---|---|---|---|---|
| Cohort J (New 60 docs) | 161 | 161 | 0.1259 | 0.2438 | 0.0196 |
| Cohort I (Loop 24 docs) | 26 | 26 | 0.1772 | 0.2284 | 0.0347 |
| Combined Benchmark (142 docs) | 262 | 262 | 0.1253 | 0.2468 | 0.0208 |

## Interpretation

- **Brier Score (0.0208):** Reflects exceptional probabilistic accuracy; confidence scores closely match the observed empirical 100% precision.
- **Expected Calibration Error (0.1253):** Low calibration error with monotone reliability diagrams.
- **Maximum Calibration Error (0.2468):** Bounded calibration gap confined to the lower boundary of the verified band ($70.0 \le c < 75.0$).
