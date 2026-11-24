# Loop 25 - Independent Generalization Results

## Cohort Breakdown

| Cohort | Docs | Fields | Verified | Exact | False | Abstain | Precision | Coverage | Table Overhead |
|---|---|---|---|---|---|---|---|---|---|
| **Cohort J (New)** | **60** | **201** | **161** | **161** | **0** | **40** | **100.00%** | **80.10%** | **1.84 ms** |
| - Development | 15 | 57 | 48 | 48 | 0 | 9 | 100.00% | 84.21% | 1.81 ms |
| - Calibration | 15 | 52 | 45 | 45 | 0 | 7 | 100.00% | 86.54% | 1.78 ms |
| - Locked Blind | 20 | 70 | 56 | 56 | 0 | 14 | 100.00% | 80.00% | 1.86 ms |
| - Adversarial | 10 | 22 | 12 | 12 | 0 | 10 | 100.00% | 54.55% | 1.95 ms |
| **Cohort I (Loop 24)** | **30** | **102** | **26** | **26** | **0** | **76** | **100.00%** | **25.49%** | **2.12 ms** |
| **Historical Loops 20-23** | **52** | **113** | **75** | **75** | **0** | **38** | **100.00%** | **66.37%** | **1.94 ms** |
| **Combined Total** | **142** | **416** | **262** | **262** | **0** | **154** | **100.00%** | **62.98%** | **1.89 ms** |

## Key Findings

1. **Locked Blind Generalization:** On the 20 unseen blind evaluation documents (70 fields), DocuReady achieved 80.00% verified coverage with **100.00% precision and zero false verifications**.
2. **Cohort I Coverage Expansion:** On the Loop 24 cohort, verified coverage expanded from **18.63% (19 fields) to 25.49% (26 fields)**, recovering 7 critical fields previously lost to minor OCR noise.
3. **Combined Benchmark Coverage:** Across all 142 documents from Loops 20 to 25, coverage increased from **41.86% to 62.98%** while maintaining **100.00% precision**.
