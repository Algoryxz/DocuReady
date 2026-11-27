# DOCUREADY — LOOP 38 OCR ROUTING AUDIT

Audited `adaptive_ocr.py`, `script_router.py`, and `region_ocr.py`:
- Production `execute_adaptive_ocr()` routes single-column pages to `eng`, `hin`, `ori`, `eng+hin`, `eng+ori`, or `eng+hin+ori` (only when both Devanagari and Odia are present), and two-column bilingual gazettes to `REGION_AWARE_ROUTING`.
- **Critical Finding (`BUG-038-001`):** For raster pages without native PDF text, `profile_document()` invokes `tesseract(..., lang='eng+hin+ori')` FIRST, then `execute_adaptive_ocr()` spawns Tesseract a SECOND time.
