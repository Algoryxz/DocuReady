# DOCUREADY — LOOP 43 REGIONAL OCR ARCHITECTURE

- **Document-Wide Adaptive (`FAST_PATH_ENG`, `MONOLINGUAL_*`, `GLOBAL_MULTILINGUAL`):** Single full-resolution `recognize_tsv()` pass (`TessBaseAPIGetTsvText`, `psm=3`) using `selected_lang`.
- **Two-Column Regional (`REGION_AWARE_ROUTING`):** Vertical gutter split at `split_x`, separate `left_crop` (`hin`/`ori`) and `right_crop` (`eng`) passes, with `left` coordinates translated by `+split_x`.
- **Multi-Region Fallback (`ocr_page_by_regions`):** Header/body/footer/table projection segmentation in `src/docuready/ingest/region_ocr.py` when no clean central gutter exists.
- **Safeguards:** Thumbnail probe text is **never** reused as full-resolution evidence; `RECOVERY_FALLBACK` (`eng+hin+ori`) triggers if `valid_words < 3` or `mean_conf < 25.0`.
