# DOCUREADY — LOOP 39 CHANGELOG

- `src/docuready/ingest/adaptive_ocr.py`: Added `probe_uncertain` and `probe_error` to `DocumentProfile`; probe exceptions/sparse text now route safely to `GLOBAL_MULTILINGUAL` (`eng+hin+ori`) instead of `LATIN`.
- `tests/test_loop39_probe_hardening.py`: Added 3 adversarial tests for probe timeout, sparse probe text, and blank-page abstention.
