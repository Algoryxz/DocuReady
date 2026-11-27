# LOOP 45 — EVIDENCE INTEGRITY REPORT

## 1. Bounding-Box & Two-Column Coordinate Integrity (`0` Out-of-Bounds)

Executed `execute_adaptive_ocr()` on representative English, Odia, two-column bilingual, and upper-band composited documents (`research/loop45/LOOP_45_VALIDATION_RAW.json`):

| Document | Strategy | Recognized Boxes | Out-of-Bounds (`<0` or `>W,H`) | Status |
|---|---|---:|---:|---|
| `DOC_CTRL_01` | `FAST_PATH_ENG` | 59 | **0** | **PASS** |
| `DOC_EXT_06` | `GLOBAL_MULTILINGUAL` | 117 | **0** | **PASS** |
| `CHALLENGE_02_ORI_ENG_2COL` | `REGION_AWARE_ROUTING` | 64 | **0** | **PASS** |
| `SYN_ORI_HDR_LAT_ID` | `GLOBAL_MULTILINGUAL` | 46 | **0** | **PASS** |

## 2. Native/Fallback Parity, Rotation/Deskew, Table Association & Abstention

- Native TSV word+box parity across all 6 language configs (`eng`, `hin`, `ori`, `eng+hin`, `eng+ori`, `eng+hin+ori`) is covered by `tests/test_loop42_*.py` and verified `word_box_exact=True`.
- Rotation/deskew, two-column gutter split, table row/cell association (`test_loop19`), evidence provenance, confidence propagation, and abstention (`ABSTAIN_UNREADABLE`) are verified in the full `tests/test_loop*.py` and Electron desktop test suites (`LOOP_45_TEST_REPORT.md`).
