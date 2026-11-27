# DocuReady Loop 03 — Skew Recovery, OCR Accuracy & Geometry Benchmark

## Executive Summary
- **Total Controlled Fixtures:** 43 across 4 modalities (Clean, Low-DPI, Shadow, Tables)
- **Ground Truth Angle Range:** [-45.0°, +45.0°]
- **Mean Angle Estimation Error:** 0.06° (Clean Scans: 0.056°)
- **Max Angle Estimation Error:** 0.1°
- **Mean Field Recovery Rate:** 26.7% (was 0-25% uncorrected at ≥5° skew)
- **Bounding Box Geometry Integrity:** 43/43 (100% within page bounds)
- **Mean Skew Estimation Time:** 163.3 ms
- **Mean Total Pipeline Time:** 2047.2 ms

## Modality Performance Breakdown
| Category | Fixtures | Mean Angle Error | Mean Recovery % | BBox Valid |
|---|---|---|---|---|
| `clean_scan` | 25 | 0.056° | 46.0% | 25/25 |
| `low_dpi` | 6 | 0.067° | 0.0% | 6/6 |
| `shadow` | 6 | 0.067° | 0.0% | 6/6 |
| `table` | 6 | 0.067° | 0.0% | 6/6 |

## Fixture-by-Fixture Verification Table
| Fixture | Category | GT Skew | Est Corr | Error | Matched Fields | BBox Valid | Time |
|---|---|---|---|---|---|---|---|
| `skew_clean_m45deg.pdf` | `clean_scan` | -45.0° | +45.0° | 0.00° | 0/4 (0.0%) | True | 1062.1 ms |
| `skew_clean_m35deg.pdf` | `clean_scan` | -35.0° | +34.9° | 0.10° | 0/4 (0.0%) | True | 948.5 ms |
| `skew_clean_m30deg.pdf` | `clean_scan` | -30.0° | +30.0° | 0.00° | 0/4 (0.0%) | True | 1006.4 ms |
| `skew_clean_m25deg.pdf` | `clean_scan` | -25.0° | +25.1° | 0.10° | 0/4 (0.0%) | True | 888.2 ms |
| `skew_clean_m20deg.pdf` | `clean_scan` | -20.0° | +20.1° | 0.10° | 0/4 (0.0%) | True | 1058.0 ms |
| `skew_clean_m15deg.pdf` | `clean_scan` | -15.0° | +15.0° | 0.00° | 4/4 (100.0%) | True | 2607.9 ms |
| `skew_clean_m12deg.pdf` | `clean_scan` | -12.0° | +12.0° | 0.00° | 0/4 (0.0%) | True | 769.1 ms |
| `skew_clean_m10deg.pdf` | `clean_scan` | -10.0° | +10.1° | 0.10° | 4/4 (100.0%) | True | 2559.9 ms |
| `skew_clean_m07deg.pdf` | `clean_scan` |  -7.0° |  +7.1° | 0.10° | 4/4 (100.0%) | True | 2491.9 ms |
| `skew_clean_m05deg.pdf` | `clean_scan` |  -5.0° |  +5.1° | 0.10° | 4/4 (100.0%) | True | 2408.9 ms |
| `skew_clean_m03deg.pdf` | `clean_scan` |  -3.0° |  +3.0° | 0.00° | 3/4 (75.0%) | True | 2460.8 ms |
| `skew_clean_m02deg.pdf` | `clean_scan` |  -2.0° |  +2.1° | 0.10° | 4/4 (100.0%) | True | 2263.3 ms |
| `skew_clean_p00deg.pdf` | `clean_scan` |  +0.0° |  +0.0° | 0.00° | 4/4 (100.0%) | True | 1445.5 ms |
| `skew_clean_p02deg.pdf` | `clean_scan` |  +2.0° |  -2.1° | 0.10° | 4/4 (100.0%) | True | 2522.9 ms |
| `skew_clean_p03deg.pdf` | `clean_scan` |  +3.0° |  -3.0° | 0.00° | 3/4 (75.0%) | True | 2657.1 ms |
| `skew_clean_p05deg.pdf` | `clean_scan` |  +5.0° |  -5.1° | 0.10° | 4/4 (100.0%) | True | 2605.3 ms |
| `skew_clean_p07deg.pdf` | `clean_scan` |  +7.0° |  -7.1° | 0.10° | 4/4 (100.0%) | True | 2941.0 ms |
| `skew_clean_p10deg.pdf` | `clean_scan` | +10.0° | -10.1° | 0.10° | 4/4 (100.0%) | True | 2934.9 ms |
| `skew_clean_p12deg.pdf` | `clean_scan` | +12.0° | -12.0° | 0.00° | 0/4 (0.0%) | True | 1033.0 ms |
| `skew_clean_p15deg.pdf` | `clean_scan` | +15.0° | -15.0° | 0.00° | 0/4 (0.0%) | True | 1109.6 ms |
| `skew_clean_p20deg.pdf` | `clean_scan` | +20.0° | -20.1° | 0.10° | 0/4 (0.0%) | True | 1110.2 ms |
| `skew_clean_p25deg.pdf` | `clean_scan` | +25.0° | -25.1° | 0.10° | 0/4 (0.0%) | True | 1473.8 ms |
| `skew_clean_p30deg.pdf` | `clean_scan` | +30.0° | -30.0° | 0.00° | 0/4 (0.0%) | True | 1071.3 ms |
| `skew_clean_p35deg.pdf` | `clean_scan` | +35.0° | -34.9° | 0.10° | 0/4 (0.0%) | True | 1117.1 ms |
| `skew_clean_p45deg.pdf` | `clean_scan` | +45.0° | -45.0° | 0.00° | 0/4 (0.0%) | True | 1550.0 ms |
| `skew_low_dpi_m15deg.pdf` | `low_dpi` | -15.0° | +15.0° | 0.00° | 0/1 (0.0%) | True | 1125.2 ms |
| `skew_low_dpi_m10deg.pdf` | `low_dpi` | -10.0° | +10.1° | 0.10° | 0/1 (0.0%) | True | 1033.3 ms |
| `skew_low_dpi_m05deg.pdf` | `low_dpi` |  -5.0° |  +5.1° | 0.10° | 0/1 (0.0%) | True | 3079.6 ms |
| `skew_low_dpi_p05deg.pdf` | `low_dpi` |  +5.0° |  -5.1° | 0.10° | 0/1 (0.0%) | True | 2959.9 ms |
| `skew_low_dpi_p10deg.pdf` | `low_dpi` | +10.0° | -10.1° | 0.10° | 0/1 (0.0%) | True | 2698.9 ms |
| `skew_low_dpi_p15deg.pdf` | `low_dpi` | +15.0° | -15.0° | 0.00° | 0/1 (0.0%) | True | 963.2 ms |
| `skew_shadow_m15deg.pdf` | `shadow` | -15.0° | +15.0° | 0.00° | 0/1 (0.0%) | True | 1401.4 ms |
| `skew_shadow_m10deg.pdf` | `shadow` | -10.0° |  +9.9° | 0.10° | 0/1 (0.0%) | True | 4940.6 ms |
| `skew_shadow_m05deg.pdf` | `shadow` |  -5.0° |  +5.1° | 0.10° | 0/1 (0.0%) | True | 5211.3 ms |
| `skew_shadow_p05deg.pdf` | `shadow` |  +5.0° |  -4.9° | 0.10° | 0/1 (0.0%) | True | 2514.3 ms |
| `skew_shadow_p10deg.pdf` | `shadow` | +10.0° | -10.1° | 0.10° | 0/1 (0.0%) | True | 1240.0 ms |
| `skew_shadow_p15deg.pdf` | `shadow` | +15.0° | -15.0° | 0.00° | 0/1 (0.0%) | True | 1326.0 ms |
| `skew_table_m15deg.pdf` | `table` | -15.0° | +15.0° | 0.00° | 0/0 (0.0%) | True | 1207.7 ms |
| `skew_table_m10deg.pdf` | `table` | -10.0° | +10.1° | 0.10° | 0/0 (0.0%) | True | 1151.2 ms |
| `skew_table_m05deg.pdf` | `table` |  -5.0° |  +5.1° | 0.10° | 0/0 (0.0%) | True | 4493.9 ms |
| `skew_table_p05deg.pdf` | `table` |  +5.0° |  -5.1° | 0.10° | 0/0 (0.0%) | True | 2360.3 ms |
| `skew_table_p10deg.pdf` | `table` | +10.0° | -10.1° | 0.10° | 0/0 (0.0%) | True | 4935.8 ms |
| `skew_table_p15deg.pdf` | `table` | +15.0° | -15.0° | 0.00° | 0/0 (0.0%) | True | 1290.9 ms |
