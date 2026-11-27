# LOOP 47 — THRESHOLD & REGIONAL EVIDENCE AUDIT

- **`>= 6` Indic Codepoint Guard**: Prevented `0/14` false-positive triggers on `NEG47_INDIC_LIKE_DECORATIVE_MARKS`, signatures, seals, and noise, while preserving `100%` recall on standard Devanagari/Odia upper headers (`SYN_*_HDR_LAT_*`).
- **`0.003` Upper-Band Ink-Density Guard**: Skipped upper-band OCR on `NEG46_BLANK_UPPER_DENSE_LATIN` in `5.22 ms` vs `295.81 ms` on inked English headers.
- **`0.05..0.22` & `500 px` Probe Dimension**: Sufficient for `SYN47_SHALLOW_DEV_HDR` (`0.06..0.16`) and standard Odia headers (`0.05..0.21`), while `SYN47_SHALLOW_ORI_HDR` (`10%` height compressed Odia) exposed Odia's stricter vertical glyph-height floor compared to Devanagari.
