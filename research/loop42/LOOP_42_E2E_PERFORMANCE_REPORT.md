# DOCUREADY — LOOP 42 END-TO-END PERFORMANCE REPORT

**Target:** Complete `execute_adaptive_ocr()` production path in `src/docuready/ingest/adaptive_ocr.py`.

## 1. Optimization Implemented

Extended `_InProcessScriptProbe` with a thread-safe per-`(lang, psm)` `TessBaseAPI` pool (`recognize_tsv()`) using `libtesseract-5.dll`'s `TessBaseAPIGetTsvText`, and wired `_run_image_to_data()` across all Stage 3 & Stage 4 full-resolution OCR call sites while preserving `pytesseract.image_to_data` monkeypatch compatibility.

## 2. Before vs. After End-to-End Benchmarks

| Workload | Loop 41 E2E Mean (Subprocess Stage 3) | Loop 42 Cold E2E Mean (`n=5`) | Loop 42 Warm E2E Mean (`n=10`) | Warm Median | Warm p90 / p95 | Warm Stdev | Speedup (Warm vs L41) |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Loop 17** (`DOC_CTRL_01`, `eng`) | `1,400.57 ms` | `1,279.16 ms` | **`821.33 ms`** | `800.19 ms` | `887.29 / 1057.20 ms` | `100.73 ms` | **-41.4%** |
| **Loop 18** (`DOC_EXT_06`, `eng+hin+ori`) | `3,786.29 ms` | `3,411.41 ms` | **`3,051.66 ms`** | `3,018.02 ms` | `3349.63 / 3786.43 ms` | `319.17 ms` | **-19.4%** |

Original `profile_document()` thresholds (`< 850.0 ms` L17, `< 1400.0 ms` L18) remain unchanged and passing (`142.09 ms` and `137.94 ms` in Loop 42 stage profiling).
