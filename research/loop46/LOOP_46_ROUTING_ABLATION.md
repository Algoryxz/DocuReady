# LOOP 46 — ROUTING ABLATION REPORT

Evaluated Strategy C (implemented in `src/docuready/ingest/adaptive_ocr.py`) across all cohorts (`research/loop46/LOOP_46_QUALIFICATION_RAW.json`):

## 1. Synthetic Positive Cohort (`8 / 8` PASS — `100%` Recall)

| Fixture | Expected | Observed Strategy | Language | Profile (ms) | Status |
|---|---|---|---|---:|---|
| `SYN_DEV_HDR_LAT_ID` | `INDIC_OR_MULTI` | `GLOBAL_MULTILINGUAL` | `eng+hin` | 1258.46 | **PASS** |
| `SYN_ORI_HDR_LAT_ID` | `INDIC_OR_MULTI` | `GLOBAL_MULTILINGUAL` | `eng+hin+ori` | 710.34 | **PASS** |
| `SYN_DEV_HDR_LAT_BODY` | `INDIC_OR_MULTI` | `GLOBAL_MULTILINGUAL` | `eng+hin` | 1252.22 | **PASS (FIXED)** |
| `SYN_ORI_HDR_LAT_BODY` | `INDIC_OR_MULTI` | `GLOBAL_MULTILINGUAL` | `eng+hin+ori` | 872.44 | **PASS (FIXED)** |
| `SYN_LAT_HDR_DEV_BODY` | `INDIC_OR_MULTI` | `GLOBAL_MULTILINGUAL` | `eng+hin` | 677.13 | **PASS** |
| `SYN_LAT_HDR_ORI_BODY` | `INDIC_OR_MULTI` | `GLOBAL_MULTILINGUAL` | `eng+hin+ori` | 1081.69 | **PASS** |
| `SYN_SHORT_UPPER_DEV` | `INDIC_OR_MULTI` | `GLOBAL_MULTILINGUAL` | `eng+hin+ori` | 46.98 | **PASS** |
| `SYN_SHORT_UPPER_ORI` | `INDIC_OR_MULTI` | `GLOBAL_MULTILINGUAL` | `eng+hin+ori` | 38.52 | **PASS** |

## 2. Real / Corpus Cohort (`18` Docs: `5 / 5` CAL + `8 / 8` L18 BLIND + `5 / 5` DocLayNet Conservative Fallback)

- `CAL` (`5/5`): `DOC_CTRL_01` → `FAST_PATH_ENG`; `DOC_EXT_06`, `DOC_MIX_01`, `DOC_MIX_02` → `GLOBAL_MULTILINGUAL`; `DOC_HIN_01` → `MONOLINGUAL_HIN`.
- `BLIND` Loop 18 (`8/8`): `CHALLENGE_02_ORI_ENG_2COL` → `REGION_AWARE_ROUTING`; `CHALLENGE_03_HIN_ENG_GRID`, `DOC_EXT_02..05` → `GLOBAL_MULTILINGUAL`; `CHALLENGE_06_FAINT_SEAL`, `STRESS_02_STAMP` → `FAST_PATH_ENG`.
- `BLIND` DocLayNet (`5/5`): `doclaynet_001..005` triggered `probe_uncertain=True` and routed conservatively to `GLOBAL_MULTILINGUAL` (`eng+hin+ori`).
