# DOCUREADY — LOOP 43 END-TO-END PERFORMANCE REPORT

Profile-stage (`profile_document`) and full end-to-end (`execute_adaptive_ocr`) measurements reported separately:

| Metric | `n` | Mean (ms) | Median (ms) | p90 / p95 (ms) | Stdev (ms) | Min / Max (ms) | Threshold | Status |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| **Cold `profile_document` (L17)** | `5` | `813.88` | `782.00` | `938.43 / 938.43` | `103.41` | `692.98 / 938.43` | `< 850.0` | **PASS** |
| **Cold `profile_document` (L18)** | `5` | `749.13` | `642.57` | `1111.28 / 1111.28` | `207.41` | `615.36 / 1111.28` | `< 1400.0` | **PASS** |
| **Warm `profile_document` (L17)** | `10` | `397.62` | `395.24` | `409.08 / 435.13` | `17.21` | `375.70 / 435.13` | `< 850.0` | **PASS** |
| **Warm `profile_document` (L18)** | `10` | `285.42` | `283.80` | `292.09 / 298.63` | `6.58` | `276.90 / 298.63` | `< 1400.0` | **PASS** |
| **Cold E2E `execute_adaptive_ocr` (L17)** | `5` | `1392.44` | `1428.57` | `1520.30 / 1520.30` | `102.05` | `1260.70 / 1520.30` | — | Info |
| **Cold E2E `execute_adaptive_ocr` (L18)** | `5` | `3229.78` | `3216.36` | `3338.35 / 3338.35` | `66.32` | `3158.39 / 3338.35` | — | Info |
| **Warm E2E `execute_adaptive_ocr` (L17)** | `10` | `823.27` | `807.07` | `865.83 / 957.54` | `53.14` | `785.28 / 957.54` | — | Info |
| **Warm E2E `execute_adaptive_ocr` (L18)** | `10` | `2702.72` | `2695.67` | `2782.97 / 2841.87` | `70.70` | `2614.71 / 2841.87` | — | Info |
