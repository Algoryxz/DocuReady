# DOCUREADY — LOOP 43 FINAL QUALIFICATION REPORT

**Branch:** `loop-43-mixed-script-routing-and-regional-ocr`  
**Base Commit:** `2849936` (Loop 42)  
**Protected Release:** `bdc403a` (Loop 10 — verified `5/5` bit-exact, untouched)

## Summary

1. **Mixed-Script Detection & Strategy C (`src/docuready/ingest/adaptive_ocr.py`):**
   - Replaced single-strip `0.25–0.45` probing with adaptive 2-region probing (central `0.25–0.45` + lower-body `0.52–0.85` when central is monolingual `LATIN`) plus a `>= 4` Indic letter majority-Latin override.
   - Resolved `BLIND43_LAT_HDR_HIN_BODY` (`GLOBAL_MULTILINGUAL`, `eng+hin`, `12.83%` CER) while keeping Loop 17 (`813.88 ms` cold, `397.62 ms` warm `< 850 ms`) and Loop 18 (`749.13 ms` cold, `285.42 ms` warm `< 1400 ms`) passing.
   - Identified `BLIND43_IND_HDR_LAT_ID` (`y < 0.25` Odia header with blank lower half) as an honest remaining miss (`Gate O` Partial).
2. **Regional OCR & Coordinate Integrity:**
   - Two-column `REGION_AWARE_ROUTING` (`17` words) and full-page `DOC_CTRL_01` (`83` boxes) achieved `0` out-of-bounds boxes.
3. **End-to-End Performance:**
   - Warm E2E `execute_adaptive_ocr()`: Loop 17 `823.27 ms` (`cold: 1392.44 ms`), Loop 18 `2,702.72 ms` (`cold: 3229.78 ms`).
4. **Regressions, Package A/B & Windows Trust:**
   - **`292` automated tests passed, `0` failed** (`267` Python across `31` `tests/test_loop*.py` files in `282.91 s` + `25` Desktop tests in `34.99 s`).
   - **26 Gates (A–Z):** **`22` PASS**, **`2` PARTIAL** (Gates O, P), **`2` BLOCKED** (Gates W, X), **`0` FAIL**.
