# DOCUREADY — LOOP 41 FINAL QUALIFICATION REPORT

**Branch:** `loop-41-inprocess-ocr-reliability-and-release-qualification`  
**Base Commit:** `b487f03` (Loop 40)  
**Protected Release:** `bdc403a` (Loop 10 — verified `5/5` bit-exact, untouched)

## Summary of Findings

1. **In-Process OCR Reliability (`_InProcessScriptProbe`):**
   - `8`-thread concurrency (`40` calls): **`0` mismatches**, `0` deadlocks.
   - `20` init/close cycles: **`20/20` passed**.
   - `100`-call sustained lifecycle: RSS `160.04 -> 158.07 MiB`, OS handles `259 -> 259` (**zero memory/handle leak**).
   - Fallback parity across 5 scripts (`eng`, `ori`, `hin`, `eng+hin`, `eng+ori`): **`0.0000` CER difference** and exact word/script match vs `pytesseract`.
   - Fixed a `ZeroDivisionError` on `1x1` images in `src/docuready/ingest/adaptive_ocr.py:198` and added regression coverage in `tests/test_loop41_inprocess_reliability.py`.
2. **Benchmark Forensics & Performance:**
   - Reconciled Loop 39 (`1610.15` / `1800.37 ms` `profile_document()` subprocess) vs Loop 40 (`3579.89` / `7570.39 ms` E2E pytest).
   - Cold fresh-process `profile_document()` (`n=5`): L17 **`286.31 ms`** (`< 850 ms`), L18 **`597.74 ms`** (`< 1400 ms`) — **PASS**.
   - Warm steady-state `profile_document()`: L17 (`n=30`) **`299.47 ms`**, L18 (`n=10`) **`307.44 ms`** — **PASS**.
   - Full `execute_adaptive_ocr()` (`n=5`): L17 `1400.57 ms`, L18 `3786.29 ms`.
3. **Multilingual Accuracy & Package A/B:**
   - `BLIND41` (1.5° perturbed across 5 scripts) routed deterministically (`2.28%–13.88%` CER).
   - Variant B (`-63.40 MiB`, `10/10` functional parity) is **`CONDITIONALLY QUALIFIED`** (do not auto-promote; CI `[-4584.03, +4516.29 ms]` exceeds `+1500 ms` Gate P).
4. **Windows Release Trust:**
   - `DocuReady.exe`, `docuready_sidecar.exe`, and `DocuReady-0.1.0-Setup.exe` remain `NotSigned` (`0` certs in store), and clean-VM SmartScreen testing is **`BLOCKED`**.
5. **Regression Suites & Qualification Matrix:**
   - **`292` automated tests passed, `0` failed** (`267` Python across `31` `tests/test_loop*.py` files + `25` Desktop tests).
   - **26 Gates (A–Z):** **`23` PASS**, **`1` PARTIAL** (Gate P), **`2` BLOCKED** (Gates W, X), **`0` FAIL**.
