# LOOP 46 — ACCURACY & ROUTING REPORT

## 1. Routing Recall & Error Rates (Separated by Cohort)

- **Synthetic Positive Cohort**: **8 / 8 (100% Indic/Mixed Recall, 0% False-Negative Routing)**. Both `SYN_DEV_HDR_LAT_BODY` and `SYN_ORI_HDR_LAT_BODY` recovered to `GLOBAL_MULTILINGUAL` (`eng+hin` / `eng+hin+ori`).
- **Expanded Negative-Control Cohort**: **9 / 9 (0% False Multilingual Routing)** across synthetic (`7/7`) and real/corpus (`2/2`) negative controls.
- **Real/Corpus Cohort**: `5 / 5` CAL + `8 / 8` L18 BLIND routed accurately; `5 / 5` DocLayNet routed via `probe_uncertain=True` conservative fallback (`GLOBAL_MULTILINGUAL`).

## 2. Per-Language Baseline Context

Per Loop 43/44/45 baseline measurements (unchanged recognition models):
- English (`BLIND43_ENG_TAX`): `0.00%` CER / `0.00%` WER.
- Hindi (`BLIND43_HIN_AFFIDAVIT`): `10.62%` CER / `36.84%` WER.
- Odia (`BLIND43_ORI_CASTE`): `8.08%` CER / `38.46%` WER.
- Mixed Latin-header + Hindi-body (`BLIND43_LAT_HDR_HIN_BODY`): `12.83%` CER / `25.00%` WER.
- Recovering `SYN_DEV_HDR_LAT_BODY` and `SYN_ORI_HDR_LAT_BODY` from `FAST_PATH_ENG` to `GLOBAL_MULTILINGUAL` eliminates the `~44.55%` CER script-omission failure mode.
