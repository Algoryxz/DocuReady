# DOCUREADY — LOOP 39 ROUTING ARCHITECTURE AUDIT

Audited `profile_document()` and `select_ocr_strategy()` in `src/docuready/ingest/adaptive_ocr.py`. Discovered that prior exception/sparse-text handling silently defaulted `primary_script = 'LATIN'`, risking `FAST_PATH_ENG` routing on failed Indic probes. Hardened via `probe_uncertain=True` -> safe `GLOBAL_MULTILINGUAL` (`eng+hin+ori`) fallback.
