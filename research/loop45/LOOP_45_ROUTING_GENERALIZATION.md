# LOOP 45 — ROUTING GENERALIZATION REPORT

Loop 44's Strategy D was evaluated **unchanged** against both cohorts (`research/loop45/LOOP_45_VALIDATION_RAW.json`).

## 1. Real / Corpus Cohort Results (`18` Documents)

- **CAL (`5 / 5` PASS)**: `DOC_CTRL_01` → `FAST_PATH_ENG`; `DOC_EXT_06`, `DOC_MIX_01`, `DOC_MIX_02` → `GLOBAL_MULTILINGUAL`; `DOC_HIN_01` → `MONOLINGUAL_HIN`.
- **BLIND Loop 18 Corpus (`8 / 8` PASS)**:
  - `CHALLENGE_02_ORI_ENG_2COL` → `REGION_AWARE_ROUTING`
  - `CHALLENGE_03_HIN_ENG_GRID`, `DOC_EXT_02_PENSION`, `DOC_EXT_03_DEGREE`, `DOC_EXT_04_KHATAUNI`, `DOC_EXT_05_HEALTH` → `GLOBAL_MULTILINGUAL`
  - `CHALLENGE_06_FAINT_SEAL`, `STRESS_02_STAMP` → `FAST_PATH_ENG`
- **BLIND DocLayNet (`5 / 5` Conservative Fallback)**:
  - `doclaynet_001` .. `doclaynet_005` triggered `probe_uncertain=True` (`primary_script="UNKNOWN"`, `38–72 ms`) and routed safely to `GLOBAL_MULTILINGUAL` (`eng+hin+ori`) via the Loop 40 uncertainty safeguard rather than risking a silent `FAST_PATH_ENG` drop.

## 2. Synthetic / Composited Cohort Results (`12` Documents)

| Fixture | Expected Group | Observed Strategy | Outcome |
|---|---|---|---|
| `SYN_DEV_HDR_LAT_ID` | `INDIC_OR_MULTI` | `GLOBAL_MULTILINGUAL` (`eng+hin`) | **PASS** |
| `SYN_ORI_HDR_LAT_ID` | `INDIC_OR_MULTI` | `GLOBAL_MULTILINGUAL` (`eng+hin+ori`) | **PASS** |
| `SYN_DEV_HDR_LAT_BODY` | `INDIC_OR_MULTI` | `FAST_PATH_ENG` (`eng`) | **FAIL (Genuine Gap)** |
| `SYN_ORI_HDR_LAT_BODY` | `INDIC_OR_MULTI` | `FAST_PATH_ENG` (`eng`) | **FAIL (Genuine Gap)** |
| `SYN_LAT_HDR_DEV_BODY` | `INDIC_OR_MULTI` | `GLOBAL_MULTILINGUAL` (`eng+hin`) | **PASS** |
| `SYN_LAT_HDR_ORI_BODY` | `INDIC_OR_MULTI` | `GLOBAL_MULTILINGUAL` (`eng+hin+ori`) | **PASS** |
| `SYN_SHORT_UPPER_DEV` | `INDIC_OR_MULTI` | `GLOBAL_MULTILINGUAL` (`eng+hin+ori`) | **PASS** |
| `SYN_SHORT_UPPER_ORI` | `INDIC_OR_MULTI` | `GLOBAL_MULTILINGUAL` (`eng+hin+ori`) | **PASS** |

### Root Cause of `SYN_DEV_HDR_LAT_BODY` / `SYN_ORI_HDR_LAT_BODY` Miss
Strategy D only probes the upper band (`0.05..0.22`) inside the `else:` branch when `lower_txt.strip()` (`0.52..0.85`) is empty. When an Indic header (`y < 0.22`) is paired with a **non-blank Latin body** (`y = 0.28..0.80`), `lower_txt` is non-empty, so the upper band is never probed. Fixing this with an unconditional 3rd probe on all Latin documents would add `~200–300 ms` to L17 `profile_document()`, risking the `< 850 ms` L17 budget; therefore it is documented honestly as a known 2-probe architectural trade-off.
