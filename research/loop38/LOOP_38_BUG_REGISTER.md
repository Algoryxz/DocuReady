# DOCUREADY — LOOP 38 BUG REGISTER

- `BUG-036-001`: Unsigned Windows executables (`NotSigned`).
- `BUG-036-002`: Qualified safe to exclude 17 training EXEs (-63.41 MB) via Variant B end-to-end packet test.
- `BUG-036-003`: Loop 17/18 wall-clock profiling failures on Windows Tesseract 5.4.0.
- `BUG-038-001`: 2-pass raster probe overhead in `profile_document()` + `execute_adaptive_ocr()`.
- `BUG-038-002` (High, FIXED): `profile_document()` `timeout=2` caused non-deterministic Hindi/bilingual misrouting to `LATIN`; fixed to `timeout=8` (`adaptive_ocr.py:139`), restoring 26/26 pass on Loop 15-17.
