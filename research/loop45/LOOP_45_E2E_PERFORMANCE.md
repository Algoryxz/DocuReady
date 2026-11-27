# LOOP 45 — REPRODUCIBLE PERFORMANCE QUALIFICATION

Raw observations (`n=30` interleaved warm, `n=5` cold subprocess) are preserved in `research/loop45/LOOP_45_BENCHMARK_BOUNDARIES.json`.

## 1. Profile-Stage Performance (`profile_document()`)

| Mode | Cohort | `n` | Mean (ms) | Median (ms) | p90 (ms) | p95 (ms) | Stdev (ms) | Min (ms) | Max (ms) | Threshold | Status |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|
| Warm paired | L17 (`DOC_CTRL_01`) | 30 | 467.52 | 467.03 | 506.03 | 523.16 | 30.88 | 418.49 | 561.73 | `< 850 ms` | **PASS** |
| Warm paired | L18 (`DOC_EXT_06`) | 30 | 317.89 | 336.63 | 378.47 | 384.42 | 55.69 | 127.07 | 396.10 | `< 1400 ms` | **PASS** |
| Cold subprocess | L17 (`DOC_CTRL_01`) | 5 | 540.12 | 473.67 | — | — | 237.45 | 346.06 | 954.30 | `< 850 ms` (mean) | **PASS** |
| Cold subprocess | L18 (`DOC_EXT_06`) | 5 | 762.01 | 724.51 | — | — | 73.13 | 698.49 | 877.45 | `< 1400 ms` | **PASS** |

## 2. Full End-to-End Performance (`execute_adaptive_ocr()`) — Reported Separately

| Mode | Cohort | `n` | Mean (ms) | Median (ms) | p90 (ms) | p95 (ms) | Stdev (ms) | Min (ms) | Max (ms) |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Warm paired | L17 (`DOC_CTRL_01`) | 30 | 963.20 | 948.57 | 1030.71 | 1034.47 | 55.66 | 895.98 | 1168.42 |
| Warm paired | L18 (`DOC_EXT_06`) | 30 | 2955.40 | 3181.71 | 3551.84 | 3559.10 | 538.49 | 1621.84 | 3585.81 |
| Cold subprocess | L17 (`DOC_CTRL_01`) | 5 | 1844.16 | 1809.18 | — | — | 253.68 | 1611.67 | 2256.20 |
| Cold subprocess | L18 (`DOC_EXT_06`) | 5 | 3853.46 | 3785.02 | — | — | 220.49 | 3676.41 | 4228.94 |
