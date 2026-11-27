# DOCUREADY — LOOP 43 NATIVE & FALLBACK PARITY REPORT

- All 6 language configurations (`eng`, `hin`, `ori`, `eng+hin`, `eng+ori`, `eng+hin+ori`) retain the `100%` bit-exact `TessBaseAPIGetTsvText` word and bounding-box parity verified in Loop 42.
- `pytesseract.image_to_string` and `pytesseract.image_to_data` monkeypatch guards (`_ORIG_PYTESSERACT_IMAGE_TO_STRING`, `_ORIG_PYTESSERACT_IMAGE_TO_DATA`) remain active and verified by `tests/test_loop39_probe_hardening.py` and `tests/test_loop40_inprocess_probe.py` inside the `267/267` pytest pass.
