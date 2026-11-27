# DOCUREADY — LOOP 42 PIPELINE PROFILING REPORT

Stage-by-stage breakdown (`n = 5` each) prior to Stage 3 in-process TSV optimization:

| Pipeline Stage | Loop 17 Mean (Median) | Loop 18 Mean (Median) | Invocations / Page |
|---|---:|---:|---:|
| 1. File load & RGB decode | `5.44 ms` (`3.23 ms`) | `6.82 ms` (`7.30 ms`) | `1` |
| 2. `profile_document()` (incl. in-process probe) | `142.09 ms` (`114.87 ms`) | `137.94 ms` (`132.65 ms`) | `1` |
| 3. `select_ocr_strategy()` | `0.01 ms` (`0.01 ms`) | `0.01 ms` (`0.01 ms`) | `1` |
| 4. Full-res `execute_adaptive_ocr()` OCR stage | `419.81 ms` (`438.87 ms`) | `1,452.70 ms` (`1,425.74 ms`) | `1` |
| 5. Result serialization (`json.dumps`) | `0.02 ms` (`0.02 ms`) | `0.02 ms` (`0.02 ms`) | `1` |

Full-resolution Stage 3 OCR (`pytesseract.image_to_data` subprocess) accounted for `74%` (L17) to `91%` (L18) of pipeline time, motivating the in-process `TessBaseAPIGetTsvText` integration.
