# DOCUREADY — LOOP 41 IN-PROCESS OCR AUDIT

**Target:** `src/docuready/ingest/adaptive_ocr.py` (`_InProcessScriptProbe`, lines 45–133)

## 1. Architecture & Lifecycle Audit

- **DLL Discovery & Loading:** Uses `find_tesseract_binary_with_source()`, locates sibling `libtesseract-5.dll` via `ctypes.CDLL`, and sets `OMP_THREAD_LIMIT=1` before initialization.
- **TessBaseAPI Lifecycle:** `TessBaseAPICreate()` -> `TessBaseAPIInit3(api, tessdata_dir, b"eng+hin+ori")` -> `TessBaseAPISetPageSegMode(api, 6)` (`PSM_SINGLE_BLOCK`). Buffers allocated by `TessBaseAPIGetUTF8Text` are freed in a `finally:` block via `TessDeleteText(ptr)`.
- **Cleanup:** `atexit.register(_PROBE_ENGINE.close)` calls `TessBaseAPIDelete(self._api)` under `self._lock` and resets `self._api = None` so subsequent calls cleanly re-initialize if needed.
- **Monkeypatch & Fallback Safety:** `profile_document()` checks `if pytesseract.image_to_string is _ORIG_PYTESSERACT_IMAGE_TO_STRING:` before calling `_PROBE_ENGINE.recognize_gray(thumb)`. If `None` is returned (e.g. missing DLL or init failure), it seamlessly falls back to `pytesseract.image_to_string(thumb, lang="eng+hin+ori", config="--psm 6", timeout=8)`.

## 2. Defect Found & Fixed in Loop 41

- **Degenerate Tiny-Image `ZeroDivisionError`:** `profile_document()` cropped `(0.15*w, 0.25*h, 0.85*w, 0.45*h)` before checking minimum dimensions, causing `strip.size == (0, 0)` and `ZeroDivisionError` on `1x1` images. Fixed with `if ink_density < 0.003 or w < 10 or h < 10:` in `src/docuready/ingest/adaptive_ocr.py`.
