# LOOP 47 — ROUTING GENERALIZATION REPORT

## 1. Real / Corpus Generalization (`22` Docs)
- **CAL (`5/5`)**: `DOC_CTRL_01` → `FAST_PATH_ENG`; `DOC_EXT_06`, `DOC_MIX_01`, `DOC_MIX_02` → `GLOBAL_MULTILINGUAL`; `DOC_HIN_01` → `MONOLINGUAL_HIN`.
- **BLIND Loop 18 (`12/12`)**: `CHALLENGE_02_ORI_ENG_2COL` → `REGION_AWARE_ROUTING`; `CHALLENGE_03`, `DOC_EXT_02..05`, `DOC_EXT_07..09`, `DOC_MULTI_01` → `GLOBAL_MULTILINGUAL`; `CHALLENGE_06`, `STRESS_02` → `FAST_PATH_ENG`.
- **BLIND DocLayNet (`5/5`)**: `doclaynet_001..005` routed conservatively via `probe_uncertain=True` → `GLOBAL_MULTILINGUAL`.

## 2. Synthetic Positive Cohort (`10 / 11` PASS)
- **Devanagari Upper-Band (`4/4` PASS)**: `SYN_DEV_HDR_LAT_ID`, `SYN_DEV_HDR_LAT_BODY`, `SYN_SHORT_UPPER_DEV`, `SYN47_SHALLOW_DEV_HDR` all routed `GLOBAL_MULTILINGUAL`.
- **Odia Upper-Band (`3/4` PASS)**: `SYN_ORI_HDR_LAT_ID`, `SYN_ORI_HDR_LAT_BODY`, `SYN_SHORT_UPPER_ORI` passed; `SYN47_SHALLOW_ORI_HDR` (`10%` height `0.06..0.16` compressed Odia header) fell below `>= 6` Odia codepoints and routed `FAST_PATH_ENG` (honest boundary limit).
- **Multi-Region & Lower-Band (`3/3` PASS)**: `SYN_LAT_HDR_DEV_BODY`, `SYN_LAT_HDR_ORI_BODY`, `SYN47_INDIC_HDR_LAT_BODY_INDIC_TBL` all passed.
