# DOCUREADY — LOOP 41 CONCURRENCY REPORT

**Target:** `_InProcessScriptProbe` (`threading.Lock()` serialization around `TessBaseAPI`)

## 1. Test Results

| Test | Configuration | Result | Determinism / Mismatches |
|---|---|---|---|
| **Sequential Determinism** | 5 scripts (`eng`, `ori`, `hin`, `mix_hin`, `mix_ori`), 2 passes each | **PASS** | `5 / 5` exact match (`mismatches = 0`) |
| **8-Thread Concurrent Stress** | `ThreadPoolExecutor(max_workers=8)`, `40` calls across all 5 scripts | **PASS** (`21,693.3 ms`) | `0 / 40` mismatches, `0` deadlocks, `0` crashes |
| **Repeated Init/Close Cycles** | `20` independent `_InProcessScriptProbe()` init → recognize → close cycles | **PASS** | `20 / 20` succeeded |

## 2. Assessment

`self._lock = threading.Lock()` serializes all `TessBaseAPI` calls (`_ensure_init`, `recognize_gray`, `close`). Because `TessBaseAPIInit3` binds a fixed `eng+hin+ori` compound model and `PSM_SINGLE_BLOCK` once, no per-request language state mutation or cross-thread corruption occurs.
