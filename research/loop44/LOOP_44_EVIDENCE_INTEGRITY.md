# LOOP 44 — EVIDENCE INTEGRITY REPORT

## 1. Native TSV Word & Bounding-Box Parity

Verified `_PROBE_ENGINE.recognize_tsv()` against `pytesseract.image_to_data(..., output_type=Output.DICT)` on `DOC_CTRL_01_ENGLISH_CERTIFICATE.png` across all 6 language configurations (`psm=6`), comparing non-empty `(text, left, top, width, height)` tuples:

| Language Config | Non-Empty Word Count | Exact Word + BBox Match |
|---|---:|---|
| `eng` | 59 | **True (59 / 59)** |
| `hin` | 59 | **True (59 / 59)** |
| `ori` | 70 | **True (70 / 70)** |
| `eng+hin` | 59 | **True (59 / 59)** |
| `eng+ori` | 59 | **True (59 / 59)** |
| `eng+hin+ori` | 59 | **True (59 / 59)** |

## 2. Coordinate Bounds & Table Association

- Two-column coordinate bounds and table-evidence association tests (`test_loop19`, `test_loop41`, `test_loop42`, `test_loop43`) are executed as part of the full `tests/test_loop*.py` regression suite (see `LOOP_44_TEST_REPORT.md`).
- Desktop bounding-box viewport transform and evidence provenance tests (`isValidBoundingBox`, `normalizeBoundingBox`, `transformBBoxToViewport`, `normalizeFindingsAndEvidence`) passed `25 / 25`.
