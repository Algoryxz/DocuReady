# DOCUREADY — LOOP 40 FINAL QUALIFICATION REPORT

**Date:** 2026-11-27  
**Branch:** `loop-40-performance-multilingual-and-windows-qualification`  
**Base Commit:** `77c1f57056fc5373d6b0f30ff24bb6108a5f25fd` (Loop 39)  
**Protected Competition Release:** `bdc403a601f88008c43c0630f5e8c71ce22c9977` (Loop 10 — verified bit-exact 5/5 SHA-256)

---

## Executive Summary

Loop 40 resolved both the Loop 17/18 `profile_document()` performance regressions and the Loop 39 mixed English–Odia OCR accuracy regression in `src/docuready/ingest/adaptive_ocr.py`, qualified the fixes across a 35-document multilingual corpus (`DEV`, `CALIBRATION`, `BLIND`), ran 215 automated tests (`190` Python + `25` Electron) with zero failures, executed `n = 10` alternating paired Package A vs. Variant B trials, and audited Windows Authenticode signing posture.

### Key Outcomes

1. **Performance Regression Eliminated (`LOOP_40_PERFORMANCE_ROOT_CAUSE.md`):**
   - Replaced per-call `tesseract.exe` subprocess spawning during script probing with a thread-safe in-process `TessBaseAPI` (`libtesseract-5.dll`) cache + tighter central probe strip (`350 px`, `0.25–0.45` height), preserving `pytesseract` monkeypatch compatibility and `probe_uncertain` fail-safes.
   - **Loop 17 (`DOC_CTRL_01_ENGLISH_CERTIFICATE`, 30 reps, threshold `< 850 ms`):** Mean **`142.00 ms`** (cold `271.96 ms`, steady-state `134.51 ms`) vs Loop 39 `3579.89 ms` (**25.2x faster**).
   - **Loop 18 (`DOC_EXT_06_ODIA_REVENUE_NOTICE`, 10 reps, threshold `< 1400 ms`):** Mean **`159.95 ms`** (cold `321.62 ms`, steady-state `158.06 ms`) vs Loop 39 `7570.39 ms` (**47.3x faster**).

2. **Multilingual Generalization & Eng+Ori Fix (`LOOP_40_MULTILINGUAL_ACCURACY_REPORT.md`):**
   - Updated `select_ocr_strategy()` so `GLOBAL_MULTILINGUAL` routes `has_ori` to `eng+hin+ori` instead of `eng+ori`.
   - `DOC_MIX_02_ORI_ENG_SCHOLARSHIP` improved from CER `9.36%` / WER `21.74%` to **CER `6.35%` / WER `17.39%`**.
   - Across the 35-document corpus (`DEV=10`, `CALIBRATION=19`, `BLIND=6`), Adaptive OCR beat Global `eng+hin+ori` overall (micro CER **`19.56%`** vs `20.81%`; micro WER **`32.43%`** vs `33.74%`) and on `BLIND` (`17.16%` vs `19.10%` CER).

3. **Package A vs. Variant B (`LOOP_40_PACKAGE_AB_QUALIFICATION.md`):**
   - Removing 17 unused Tesseract CLI/training EXEs saved **`66,485,066` bytes (`63.40 MiB`)** with `10/10` functional parity and `-33.87 ms` mean paired difference, though the 95% CI `[-4584.03, +4516.29 ms]` did not meet the `+1500 ms` statistical bound due to `n=10` process-spawn variance.

4. **Windows Release Trust (`LOOP_40_WINDOWS_TRUST_REPORT.md`):**
   - `DocuReady.exe`, `docuready_sidecar.exe`, and `DocuReady-0.1.0-Setup.exe` are `NotSigned`; code-signing and clean-VM SmartScreen gates are honestly marked **`BLOCKED`**.

5. **Qualification Matrix (`LOOP_40_QUALIFICATION_MATRIX.md`):**
   - **26 Gates (A–Z):** **23 PASS**, **1 FAIL** (Gate P), **2 BLOCKED** (Gates W, X).
