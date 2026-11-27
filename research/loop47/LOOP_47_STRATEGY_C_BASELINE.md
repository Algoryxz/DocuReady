# LOOP 47 — STRATEGY C UNCHANGED BASELINE

Evaluated Loop 46 Strategy C **unchanged** (`src/docuready/ingest/adaptive_ocr.py`):
- **Real/Corpus (`22` docs)**: `5/5` CAL + `12/12` L18 BLIND routed accurately; `5/5` `doclaynet_001..005` triggered `probe_uncertain=True` and routed conservatively to `GLOBAL_MULTILINGUAL` (`eng+hin+ori`).
- **Synthetic Positive (`10/11` PASS)**: All 8 Loop 45/46 positive cases, `SYN47_SHALLOW_DEV_HDR`, and `SYN47_INDIC_HDR_LAT_BODY_INDIC_TBL` passed; `SYN47_SHALLOW_ORI_HDR` (`10%` height compressed Odia crop) missed (`FAST_PATH_ENG`).
- **Expanded Negative Controls (`14/14` PASS)**: `0%` false multilingual routing across all 12 synthetic + 2 real/corpus negative controls.
