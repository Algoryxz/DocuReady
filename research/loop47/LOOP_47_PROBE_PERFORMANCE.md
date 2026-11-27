# LOOP 47 — UPPER-BAND PROBE PERFORMANCE & OVERHEAD DECOMPOSITION

Measured `n=10` paired stage timings (`research/loop47/LOOP_47_AUDIT_RAW.json`):

| Page Type | Crop/Resize (ms) | Central Probe (ms) | Lower Probe (ms) | Upper Probe (ms) | Full `profile_document()` (ms) | Full `execute_adaptive_ocr()` (ms) |
|---|---:|---:|---:|---:|---:|---:|
| `ENG_BLANK_UPPER` | 3.56 | 265.02 | 146.13 | **5.22** (skipped) | 453.97 | 1183.75 |
| `ENG_INKED_UPPER_L17` | 2.27 | 314.97 | 186.52 | **295.81** | 830.00 | 1416.29 |
| `ORI_HDR_LAT_BODY` | 4.81 | 160.66 | 86.70 | **612.67** | 1057.46 | 2720.37 |
| `ORI_HDR_LAT_ID` | 4.66 | 72.60 | **9.17** (blank) | **609.73** | 771.44 | 2036.68 |

**Finding**: On English pages with blank upper bands, the `0.003` ink gate avoids OCR (`5.22 ms`). On inked English pages (`DOC_CTRL_01`), the `500 px` upper-band `eng+hin+ori` probe adds `~295.81 ms`.
