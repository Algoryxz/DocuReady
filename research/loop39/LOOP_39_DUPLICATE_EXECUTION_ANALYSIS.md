# DOCUREADY — LOOP 39 DUPLICATE EXECUTION ANALYSIS

On raster-only pages (`has_native_text=False`), `execute_adaptive_ocr()` performs 2 Tesseract invocations: (1) a 450px central-strip `eng+hin+ori` probe in `profile_document()`, and (2) the full-resolution OCR pass in `execute_adaptive_ocr()`.
