# DOCUREADY — LOOP 41 BENCHMARK FORENSICS REPORT

## 1. Reconciliation of Loop 39 vs. Loop 40 Reported Baselines

- **Loop 39 `research/loop39/performance_results.json`:** Measured `profile_document()` in isolation using `pytesseract` subprocess probing (`1610.15 ms` mean for Loop 17 across 30 reps; `1800.37 ms` mean for Loop 18 across 10 reps). Both exceeded the `< 850 ms` and `< 1400 ms` thresholds (`LOOP_39_LOOP17_LOOP18_REGRESSION.md`).
- **Loop 40 `LOOP_40_PERFORMANCE_ROOT_CAUSE.md`:** Quoted `3579.89 ms` (Loop 17) and `7570.39 ms` (Loop 18) from end-to-end pytest runs (`test_loop17_adaptive_efficiency.py` / `test_loop18_accuracy_and_critical_fields.py`), which included full pipeline / pytest fixture overhead rather than `profile_document()` alone.
- **Resolution:** Original Loop 17 (`< 850.0 ms`) and Loop 18 (`< 1400.0 ms`) gates measure `profile_document()` latency. Both definitions are preserved and reported separately below alongside full end-to-end `execute_adaptive_ocr()` timings.

## 2. Loop 41 Measured Performance (Cold Fresh-Process vs. Warm vs. E2E)

| Benchmark | `n` | Mean (ms) | Median (ms) | p90 (ms) | p95 (ms) | Stdev (ms) | Min (ms) | Max (ms) | Threshold | Status |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| **Cold Fresh-Process `profile_document` (L17)** | `5` | `286.31` | `287.00` | `305.38` | `305.38` | `12.18` | `274.60` | `305.38` | `< 850.0` | **PASS** |
| **Cold Fresh-Process `profile_document` (L18)** | `5` | `597.74` | `687.03` | `891.22` | `891.22` | `279.79` | `274.68` | `891.22` | `< 1400.0` | **PASS** |
| **Warm Steady-State `profile_document` (L17)** | `30` | `299.47` | `282.81` | `324.67` | `366.80` | `67.25` | `250.78` | `626.86` | `< 850.0` | **PASS** |
| **Warm Steady-State `profile_document` (L18)** | `10` | `307.44` | `305.60` | `321.24` | `351.59` | `20.39` | `279.79` | `351.59` | `< 1400.0` | **PASS** |
| **End-to-End `execute_adaptive_ocr` (L17)** | `5` | `1400.57` | `1408.05` | `1568.64` | `1568.64` | `159.24` | `1238.84` | `1568.64` | — | Info |
| **End-to-End `execute_adaptive_ocr` (L18)** | `5` | `3786.29` | `4201.69` | `4495.80` | `4495.80` | `1003.75` | `2040.98` | `4495.80` | — | Info |

Both cold fresh-process and warm steady-state `profile_document()` runs pass Loop 17 and Loop 18 thresholds without relaxing any assertion.
