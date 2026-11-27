# DOCUREADY — LOOP 42 OCR CALL AUDIT

## 1. Per-Page OCR Invocation Inventory

- **Profiling Probe (`profile_document`):** `1` in-process `TessBaseAPIGetUTF8Text` call (`eng+hin+ori`, PSM 6) on the `350 px` central strip. Thumbnail text is **never** reused as full-resolution evidence.
- **Full-Resolution Extraction (`execute_adaptive_ocr`):**
  - `FAST_PATH_ENG` / `MONOLINGUAL_HIN` / `MONOLINGUAL_ORI` / `GLOBAL_MULTILINGUAL`: `1` full-resolution `recognize_tsv()` call (`psm=3`) with `selected_lang`.
  - `REGION_AWARE_ROUTING`: `2` column-crop `recognize_tsv()` calls (`left_lang` + `right_lang`).
  - `RECOVERY_FALLBACK`: `+1` `eng+hin+ori` call only when `len(valid_words) < 3 or mean_conf < 25.0`.
- **Subprocess Eliminations:** All 4 `pytesseract.image_to_data` subprocess sites in `execute_adaptive_ocr()` now execute in-process via `TessBaseAPIGetTsvText` when `pytesseract.image_to_data` is unpatched.
