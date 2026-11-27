# Loop 26 - Confidence Calibration Audit

## Calibration Metrics

| Metric | Cohort K (Independent) | Cohort J (Synthetic) | Combined Benchmark (202 Docs) |
|---|---|---|---|
| **Expected Calibration Error (ECE)** | 0.0885 | 0.1259 | **0.0467** |
| **Maximum Calibration Error (MCE)** | 0.2301 | 0.2438 | **0.2524** |
| **Brier Score** | 0.0885 | 0.0196 | **0.0758** |

Calibration remains well-bounded across all confidence bands, confirming that confidence reliably reflects empirical correctness.
