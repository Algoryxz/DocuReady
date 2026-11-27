# LOOP 46 — EVIDENCE & OCR INTEGRITY REPORT

## 1. Native TSV / Subprocess Fallback Parity (All 6 Language Configs)

Verified `_PROBE_ENGINE.recognize_tsv()` against `pytesseract.image_to_data(..., output_type=Output.DICT)` on `DOC_CTRL_01_ENGLISH_CERTIFICATE.png` (`psm=6`), comparing `(text, left, top, width, height)` tuples (`research/loop46/LOOP_46_QUALIFICATION_RAW.json`):

| Language Config | Non-Empty Words | Exact Word + BBox Match |
|---|---:|---|
| `eng` | 59 | **True (59 / 59)** |
| `hin` | 59 | **True (59 / 59)** |
| `ori` | 70 | **True (70 / 70)** |
| `eng+hin` | 59 | **True (59 / 59)** |
| `eng+ori` | 59 | **True (59 / 59)** |
| `eng+hin+ori` | 59 | **True (59 / 59)** |

## 2. Coordinate Mapping, Rotation/Deskew, Two-Column & Table Association

- Two-column horizontal translation (`+sx`), table row/cell association (`test_loop19`), rotation/deskew, evidence provenance, confidence propagation, and abstention (`ABSTAIN_UNREADABLE`) are verified in the full `tests/test_loop*.py` and Electron desktop test suites (`LOOP_46_TEST_REPORT.md`).
