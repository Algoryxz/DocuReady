# DOCUREADY — LOOP 42 LEARNINGS

1. **Check exact C-API symbol casing (`TessBaseAPIGetTsvText` vs `TessBaseAPIGetTSVText`):** `libtesseract-5.dll` exports `TessBaseAPIGetTsvText`, enabling full in-process TSV/bounding-box/confidence extraction with `0` subprocess spawns and 100% word/box parity.
2. **Preserve `pytesseract.image_to_data` monkeypatch guards (`_ORIG_PYTESSERACT_IMAGE_TO_DATA`):** Ensures unit tests that mock `pytesseract` continue to intercept OCR calls cleanly.
3. **Keep independent blind evaluations strictly separate from transformed copies:** Synthetic `BLIND42` documents surfaced a real probe-strip majority-Latin edge case that rotated copies of Loop 14/18 documents did not show.
