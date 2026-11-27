# LOOP 47 — REPRODUCIBLE COLD/WARM PERFORMANCE QUALIFICATION

Raw observations are preserved in `research/loop47/LOOP_47_AUDIT_RAW.json`. `profile_document()` and `execute_adaptive_ocr()` are reported separately.

## 1. Profile-Stage Performance (`profile_document()`)

| Mode | Cohort | `n` | Mean (ms) | Median (ms) | p95 (ms) | Stdev (ms) | Min (ms) | Max (ms) | Threshold | Status |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| Warm paired | L17 (`DOC_CTRL_01`) | 30 | **817.17** | 751.67 | 1224.20 | 182.46 | 628.37 | 1239.98 | `< 850 ms` (warm) | **PASS** |
| Warm paired | L18 (`DOC_EXT_06`) | 30 | **323.34** | 321.30 | 494.36 | 112.95 | 134.11 | 535.60 | `< 1400 ms` (warm) | **PASS** |
| Cold subprocess (L46 ref) | L17 (`DOC_CTRL_01`) | 5 | 996.48 | 965.44 | — | — | 919.28 | 1180.58 | `< 850 ms` | Above on cold DLL+3rd probe |
| Cold subprocess (L47*) | L17 (`DOC_CTRL_01`) | 5 | 461.31 | 440.53 | — | — | — | 555.08 | `< 850 ms` | Measured |
| Cold subprocess (L47*) | L18 (`DOC_EXT_06`) | 5 | 2458.09 | 3380.18 | — | — | 279.83 | 3954.94 | `< 1400 ms` | *Contended with parallel pytest |

## 2. Full End-to-End Performance (`execute_adaptive_ocr()`) — Separate Scope

| Mode | Cohort | `n` | Mean (ms) | Median (ms) | p95 (ms) | Stdev (ms) |
|---|---|---:|---:|---:|---:|---:|
| Warm paired | L17 (`DOC_CTRL_01`) | 30 | 1326.98 | 1215.95 | 1804.97 | 235.76 |
| Warm paired | L18 (`DOC_EXT_06`) | 30 | 3100.91 | 3177.89 | 5567.67 | 1161.57 |
| Cold subprocess (L47*) | L17 (`DOC_CTRL_01`) | 5 | 780.28 | 786.22 | — | — |
| Cold subprocess (L47*) | L18 (`DOC_EXT_06`) | 5 | 16373.09 | 16013.64 | — | — |
