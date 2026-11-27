# DOCUREADY — LOOP 43 LEARNINGS

1. **Adaptive 2-region probing preserves latency budgets while catching Latin-header + Indic-body documents:** Only probing the lower body when the central strip looks monolingual `LATIN` adds `0 ms` overhead to Indic/mixed pages (`DOC_EXT_06` `285.42 ms` warm) while keeping `DOC_CTRL_01` (`397.62 ms` warm) well under `850 ms`.
2. **Short-page documents with top Indic headers (`y < 0.25`) and blank lower halves need an upper-band fallback when `0.52–0.85` is empty.**
3. **Pillow `ImageDraw.text` without `librqm` shaping degrades synthetic Devanagari/Odia rendering:** Always distinguish unshaped synthetic text from real scanned/shaped Indic documents when interpreting CER.
