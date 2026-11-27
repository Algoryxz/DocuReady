# LOOP 44 — ROUTING ABLATION REPORT

## 1. Ablation Scope

Evaluated Strategy D (conditional upper-band `0.05..0.22` at `max_dim=500.0`, guarded by `>= 6` Devanagari/Odia codepoints) against Strategy C across the full Loop 14/18 raster corpus and the Loop 44 raster diagnostic fixtures (`research/loop44/LOOP_44_ABLATION_AND_E2E.json`).

## 2. Raster Routing Results

| Document | Primary Script | Strategy Selected | Language | Profile Latency (ms) | Outcome |
|---|---|---|---|---:|---|
| `DOC_CTRL_01` (English cert) | `LATIN` | `FAST_PATH_ENG` | `eng` | 896.45 | **PASS** |
| `DOC_EXT_06` (Odia notice) | `MIXED_ODIA_LATIN` | `GLOBAL_MULTILINGUAL` | `eng+hin+ori` | 396.63 | **PASS** |
| `DOC_HIN_01` (Hindi circular) | `DEVANAGARI` | `MONOLINGUAL_HIN` | `hin` | 1198.77 | **PASS** |
| `DOC_MIX_01` (Hindi+Eng) | `MIXED_DEVANAGARI_LATIN` | `GLOBAL_MULTILINGUAL` | `eng+hin+ori` | 368.37 | **PASS** |
| `DOC_MIX_02` (Ori+Eng) | `MIXED_ODIA_LATIN` | `GLOBAL_MULTILINGUAL` | `eng+hin+ori` | 698.17 | **PASS** |
| `BLIND44_IND_HDR_LAT_ID` (Raster) | `MIXED_ODIA_LATIN` | `GLOBAL_MULTILINGUAL` | `eng+hin+ori` | 864.07 | **FIXED (was FAST_PATH_ENG in L43)** |
| `BLIND44_LAT_HDR_HIN_BODY` (Raster) | `MIXED_DEVANAGARI_LATIN` | `GLOBAL_MULTILINGUAL` | `eng+hin` | 1728.57 | **PASS (no Strategy C regression)** |
| `BLIND44_ENG_UPPER_SEAL` (Raster) | `LATIN` | `FAST_PATH_ENG` | `eng` | 363.46 | **PASS (no false positive)** |

*Note: Single cold-cache ablation runs include first-time TessBaseAPI initialization for each `(lang, psm)` pair; see `LOOP_44_E2E_PERFORMANCE.md` for `n=30` warm and `n=5` cold subprocess distributions.*

## 3. Strategy Comparison Summary

- **Strategy A (Central strip only)**: Misses both Latin-header/Indic-body (`BLIND43_LAT_HDR_HIN_BODY`) and Indic-header/Latin-body (`BLIND43_IND_HDR_LAT_ID`).
- **Strategy B (Unconditional 3-band)**: Exceeds `< 850 ms` L17 budget (`952–1,968 ms`).
- **Strategy C (Central + conditional lower)**: Fixes `BLIND43_LAT_HDR_HIN_BODY`, misses `BLIND43_IND_HDR_LAT_ID`.
- **Strategy D (Loop 44 — Central + conditional lower + conditional upper at `max_dim=500`, `>= 6` Indic guard)**: Recovers **8 / 8** raster test cases with `0` false positives on English upper-seal pages and preserves `< 850 ms` / `< 1400 ms` warm `profile_document()` thresholds.
