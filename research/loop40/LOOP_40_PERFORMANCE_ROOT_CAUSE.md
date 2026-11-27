# Loop 40 Performance Regression Root-Cause & Resolution Report

**Date:** 2026-11-27  
**Branch:** `loop-40-performance-multilingual-and-windows-qualification`  
**Target File:** `src/docuready/ingest/adaptive_ocr.py`

---

## 1. Problem Statement

Loop 39 and Loop 40 baseline verification confirmed two severe `profile_document()` latency regressions against the Loop 17/18 acceptance gates:
- **Loop 17 (`DOC_CTRL_01_ENGLISH_CERTIFICATE`, 30 reps, threshold `< 850.0 ms`):** Loop 39 baseline mean `3579.89 ms` (4.2x over threshold).
- **Loop 18 (`DOC_EXT_06_ODIA_REVENUE_NOTICE`, 10 reps, threshold `< 1400.0 ms`):** Loop 39 baseline mean `7570.39 ms` (5.4x over threshold).

---

## 2. Root-Cause Stage Profiling

Stage-by-stage timing of `profile_document()` isolated the bottleneck:
1. **Image grayscale conversion, blank check, and two-column gutter projection:** `32.3 ms` (`DOC_CTRL_01`) / `53.6 ms` (`DOC_EXT_06`).
2. **`pytesseract.image_to_string(thumb, lang="eng+hin+ori", config="--psm 6")`:** `3070–4251 ms` (`DOC_CTRL_01`) / `7584 ms` (`DOC_EXT_06`).
   - Each call spawned a fresh `tesseract.exe` subprocess (`110–153 ms` bare process startup), dynamically loaded `libtesseract-5.dll` (`101.47 MB`), and deserialized three LSTM `.traineddata` models (`eng` 4.1 MB, `hin` 1.1 MB, `ori` 1.5 MB) from disk on every single `profile_document()` call.

---

## 3. Implemented Resolution

In `src/docuready/ingest/adaptive_ocr.py`:
1. **In-Process Cached `TessBaseAPI` Script Probe (`_InProcessScriptProbe`):**
   - Loads `libtesseract-5.dll` once via `ctypes.CDLL`, sets `OMP_THREAD_LIMIT=1`, initializes `TessBaseAPIInit3(..., "eng+hin+ori")` once with `PSM_SINGLE_BLOCK` (`6`), guards recognition with a `threading.Lock()`, frees UTF-8 buffers with `TessDeleteText`, and registers `atexit.register(_PROBE_ENGINE.close)` for `TessBaseAPIDelete`.
   - Preserves full fail-safe behavior and unit-test monkeypatch compatibility: if `pytesseract.image_to_string` is monkeypatched (as in `tests/test_loop39_probe_hardening.py`) or `libtesseract-5.dll` is unavailable, it seamlessly falls back to `pytesseract.image_to_string(...)`.
2. **Tighter Central Probe Strip & Thumbnail Scale:**
   - Cropped central narrative strip `(0.15*w, 0.25*h, 0.85*w, 0.45*h)` and scaled to max dimension `350.0 px` (validated in `ablate_probe.py` across `DOC_CTRL_01`, `DOC_EXT_06`, `DOC_HIN_01`, `DOC_ORI_01`, `DOC_MIX_01`, `DOC_MIX_02` with 6/6 exact script classification).

---

## 4. Before vs. After Benchmark Results (`performance_results.json`)

| Benchmark | Threshold | Loop 39 Baseline Mean | Loop 40 Cold (Fresh Process) | Loop 40 All-Reps Mean | Loop 40 Median | Loop 40 p90 / p95 | Loop 40 Steady-State Mean | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Loop 17** (`DOC_CTRL_01`, 30 reps) | `< 850.0 ms` | `3579.89 ms` | `271.96 ms` | **`142.00 ms`** | `137.28 ms` | `166.63 / 177.78 ms` | `134.51 ms` | **PASS** (25.2x speedup) |
| **Loop 18** (`DOC_EXT_06`, 10 reps) | `< 1400.0 ms` | `7570.39 ms` | `321.62 ms` | **`159.95 ms`** | `161.52 ms` | `190.78 / 208.56 ms` | `158.06 ms` | **PASS** (47.3x speedup) |

Both Loop 17 (`test_loop17_adaptive_efficiency.py`) and Loop 18 (`test_loop18_accuracy_and_critical_fields.py`) pytest suites now pass without relaxing any threshold or assertion.
