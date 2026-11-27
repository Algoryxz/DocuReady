# LOOP 46 — PERFORMANCE REPORT (PAIRED `n=30` WARM + `n=5` COLD)

Raw observations are preserved in `research/loop46/LOOP_46_QUALIFICATION_RAW.json`. `profile_document()` and `execute_adaptive_ocr()` are reported separately.

## 1. Profile-Stage Performance (`profile_document()`)

| Mode | Cohort | `n` | Mean (ms) | Median (ms) | p95 (ms) | Stdev (ms) | Min (ms) | Max (ms) | Threshold | Status |
|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| Warm paired | L17 (`DOC_CTRL_01`) | 30 | **713.75** | 694.11 | 878.03 | 80.93 | 637.77 | 1043.62 | `< 850 ms` | **PASS** (mean/median) |
| Warm paired | L18 (`DOC_EXT_06`) | 30 | **299.53** | 293.32 | 350.51 | 28.94 | 274.09 | 421.93 | `< 1400 ms` | **PASS** |
| Cold subprocess | L17 (`DOC_CTRL_01`) | 5 | 996.48 | 965.44 | — | — | 919.28 | 1180.58 | `< 850 ms` | Above on cold DLL+3rd probe |
| Cold subprocess | L18 (`DOC_EXT_06`) | 5 | **648.48** | 625.83 | — | — | 608.20 | 722.79 | `< 1400 ms` | **PASS** |

## 2. Upper-Band Probe Overhead on English-Only Pages

- **Loop 45 L17 warm `profile_document()`**: `467.52 ms`
- **Loop 46 L17 warm `profile_document()`**: `713.75 ms` (**`+246.23 ms`** when upper band has ink `>= 0.003`; `< 1 ms` when upper band is blank).

## 3. Full End-to-End Performance (`execute_adaptive_ocr()`) — Separate Scope

| Mode | Cohort | `n` | Mean (ms) | Median (ms) | p95 (ms) | Stdev (ms) | Min (ms) | Max (ms) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Warm paired | L17 (`DOC_CTRL_01`) | 30 | 1244.15 | 1175.77 | 1473.97 | 281.87 | 1055.27 | 2639.72 |
| Warm paired | L18 (`DOC_EXT_06`) | 30 | 2855.47 | 2721.89 | 3504.32 | 292.07 | 2630.86 | 3620.17 |
| Cold subprocess | L17 (`DOC_CTRL_01`) | 5 | 1732.37 | 1726.00 | — | — | 1672.21 | 1835.32 |
| Cold subprocess | L18 (`DOC_EXT_06`) | 5 | 3787.13 | 3482.93 | — | — | 3376.28 | 4918.32 |
