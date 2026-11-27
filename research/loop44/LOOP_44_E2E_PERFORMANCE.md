# LOOP 44 — E2E PERFORMANCE & PROFILE SEPARATION REPORT

## 1. Measurement Scope Separation

Per Loop 44 integrity rules, **profile-stage (`profile_document()`)** and **end-to-end (`execute_adaptive_ocr()`)** benchmarks are measured and reported separately. No E2E figure is substituted for a profile-stage threshold, and vice versa.

## 2. Profile-Stage Benchmarks (`profile_document()`)

| Metric | Cohort | `n` | Mean (ms) | Median (ms) | p90 (ms) | p95 (ms) | Stdev (ms) | Min (ms) | Max (ms) | Threshold | Status |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| Warm in-process | L17 (`DOC_CTRL_01`, Eng) | 30 | 495.17 | 477.92 | 569.60 | 602.82 | 74.29 | 409.36 | 752.00 | `< 850 ms` | **PASS** |
| Warm in-process | L18 (`DOC_EXT_06`, Ori) | 30 | 279.23 | 319.52 | 447.29 | 462.13 | 121.00 | 118.58 | 536.53 | `< 1400 ms` | **PASS** |
| Cold subprocess | L17 (`DOC_CTRL_01`, Eng) | 5 | 935.71 | 889.40 | — | — | — | 867.51 | 1131.59 | Informational | Measured |
| Cold subprocess | L18 (`DOC_EXT_06`, Ori) | 5 | 798.22 | 785.99 | — | — | — | 761.69 | 839.20 | Informational | Measured |

## 3. End-to-End Benchmarks (`execute_adaptive_ocr()`)

| Metric | Cohort | `n` | Mean (ms) | Median (ms) | Min (ms) | Max (ms) | Formal Threshold |
|---|---|---:|---:|---:|---:|---:|---|
| Warm in-process | L17 (`DOC_CTRL_01`, Eng) | 5 | 368.85 | 373.72 | 340.66 | 384.77 | None (transparency) |
| Warm in-process | L18 (`DOC_EXT_06`, Ori) | 5 | 1278.33 | 1227.35 | 1185.19 | 1512.80 | None (transparency) |
| Cold subprocess | L17 (`DOC_CTRL_01`, Eng) | 5 | 1792.19 | 1834.21 | 1650.41 | 1861.79 | None (transparency) |
| Cold subprocess | L18 (`DOC_EXT_06`, Ori) | 5 | 4338.22 | 4373.36 | 4214.58 | 4484.72 | None (transparency) |

## 4. Raw Data Artifacts

- `research/loop44/LOOP_44_BENCHMARK_RAW.json` (warm `n=30` profile + warm `n=5` E2E)
- `research/loop44/LOOP_44_ABLATION_AND_E2E.json` (raster ablation + cold `n=5` subprocess profile & E2E + TSV parity)
