# DOCUREADY — LOOP 44 FINAL REPORT
## Upper-Band Mixed-Script Recovery, Full E2E Performance Integrity & Release-Freeze Audit

**Branch:** `loop-44-upper-band-mixed-script-and-e2e-integrity`  
**Base Commit:** `e5ba978` (Loop 43)  
**Protected Release:** `bdc403a` (Loop 10 — unmodified, unpromoted)

---

## 1. Executive Summary

1. **Release Freeze Verified (`5 / 5` SHA-256 Exact Match)**:
   - All five Loop 10 artifacts match `docs/04-VALIDATION/LOOP_10_FEATURE_FREEZE_RECORD.md` byte-for-byte on disk.
   - The previously noted `app.asar` discrepancy was traced to a transcription typo (`...95368928a...`) in secondary notes; both disk and the freeze record read `d72882945989e468c76ce43840c16457aa94e59584dc6f953689a28a0014f27e`.
2. **Upper-Band Mixed-Script Recovery (Strategy D)**:
   - Implemented Strategy D in `src/docuready/ingest/adaptive_ocr.py`: when central (`0.25..0.45`) is monolingual `LATIN` and lower (`0.52..0.85`) is blank/inconclusive, probes upper band (`0.05..0.22`) at `max_dim=500.0` and reclassifies only when `>= 6` Devanagari/Odia codepoints are detected.
   - Resolved `BLIND43_IND_HDR_LAT_ID` on both unit (`native_text`) and composited raster (`BLIND44_IND_HDR_LAT_ID_RASTER`) fixtures → `GLOBAL_MULTILINGUAL` (`eng+hin+ori`), with `0` false positives on English upper-seal pages (`BLIND44_ENG_UPPER_SEAL_RASTER` → `FAST_PATH_ENG`).
3. **Profile-Stage vs. E2E Performance Integrity**:
   - Warm `profile_document()` (`n=30`): L17 `mean 495.17 ms` (`p95 602.82 ms`, `< 850 ms` PASS); L18 `mean 279.23 ms` (`p95 462.13 ms`, `< 1400 ms` PASS).
   - Cold `profile_document()` (`n=5` subprocess): L17 `mean 935.71 ms`; L18 `mean 798.22 ms`.
   - `execute_adaptive_ocr()` reported separately: Warm (`n=5`) L17 `368.85 ms`, L18 `1278.33 ms`; Cold (`n=5` subprocess) L17 `1792.19 ms`, L18 `4338.22 ms`.
4. **Evidence Integrity & Full Test Suite**:
   - Native TSV parity (`recognize_tsv()` vs `pytesseract.image_to_data`) verified `word_box_exact=True` across all 6 language configs (`eng`, `hin`, `ori`, `eng+hin`, `eng+ori`, `eng+hin+ori`).
   - **314 / 314 tests passing** (`289` Python + `25` Desktop), `0` failures.
5. **26-Gate Qualification Matrix (A–Z)**:
   - **23 PASS** (Gate O upgraded from PARTIAL to PASS), **1 PARTIAL** (Gate P: Package A/B), **2 BLOCKED** (Gates W, X: Windows Authenticode signing & clean-VM SmartScreen), **0 FAIL**.
