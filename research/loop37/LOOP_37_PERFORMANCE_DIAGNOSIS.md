# DOCUREADY — LOOP 37 PERFORMANCE DIAGNOSIS

Stage timing inside `profile_document()` on `DOC_CTRL_01_ENGLISH_CERTIFICATE`:
- `gray`: `2.1 ms`
- `crop/resize`: `1.5 ms`
- `pytesseract.image_to_string(..., lang='eng+hin+ori')`: `1738.2 ms` (vs `752.6 ms` for `eng` alone).

Root cause: Spawning Tesseract 5.4.0 subprocess and loading 3 LSTM models (`eng`+`hin`+`ori`) under Windows Defender Real-Time Protection dominates >99% of profiling time.
