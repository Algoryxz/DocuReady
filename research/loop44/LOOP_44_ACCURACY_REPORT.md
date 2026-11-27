# LOOP 44 — ACCURACY & ROUTING REPORT

## 1. Per-Language & Per-Document Routing Summary

Per Loop 44 reporting integrity rules, results are reported separately per language bucket and document rather than hidden behind a single English-dominated aggregate.

### 1.1 Loop 44 Raster Diagnostic Cohort

| Document | Language Bucket | Expected Strategy | Observed Strategy (Strategy D) | Status |
|---|---|---|---|---|
| `BLIND44_IND_HDR_LAT_ID_RASTER` | Odia + English | `GLOBAL_MULTILINGUAL` | `GLOBAL_MULTILINGUAL` (`eng+hin+ori`) | **PASS (FIXED)** |
| `BLIND44_LAT_HDR_HIN_BODY_RASTER` | English + Hindi | `GLOBAL_MULTILINGUAL` | `GLOBAL_MULTILINGUAL` (`eng+hin`) | **PASS** |
| `BLIND44_ENG_UPPER_SEAL_RASTER` | English (with upper seal) | `FAST_PATH_ENG` | `FAST_PATH_ENG` (`eng`) | **PASS (0 FP)** |

### 1.2 Loop 14 / Loop 18 Corpus Routing

| Document | Language Bucket | Observed Strategy | Language | Status |
|---|---|---|---|---|
| `DOC_CTRL_01` | English (`eng`) | `FAST_PATH_ENG` | `eng` | **PASS** |
| `DOC_EXT_06` | Odia + English | `GLOBAL_MULTILINGUAL` | `eng+hin+ori` | **PASS** |
| `DOC_HIN_01` | Hindi (`hin`) | `MONOLINGUAL_HIN` | `hin` | **PASS** |
| `DOC_MIX_01` | Mixed Hindi+English | `GLOBAL_MULTILINGUAL` | `eng+hin+ori` | **PASS** |
| `DOC_MIX_02` | Mixed Odia+English | `GLOBAL_MULTILINGUAL` | `eng+hin+ori` | **PASS** |

## 2. BLIND43 Historical Baseline Context

In Loop 43, `BLIND43_IND_HDR_LAT_ID` failed routing (`FAST_PATH_ENG` → `44.55%` CER, `61.54%` WER) because Strategy C did not probe `y < 0.25` when the lower body was blank. With Strategy D (`_probe_band(0.05, 0.22, max_dim=500.0)` + `>= 6` Indic codepoint guard), both the unit fixture (`native_text`) and the rasterized `BLIND44_IND_HDR_LAT_ID_RASTER` fixture now route to `GLOBAL_MULTILINGUAL` (`eng+hin+ori`).
