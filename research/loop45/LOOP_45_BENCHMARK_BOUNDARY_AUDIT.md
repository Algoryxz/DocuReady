# LOOP 45 — BENCHMARK BOUNDARY AUDIT

## 1. Investigation of Loop 44 Timing Discrepancy

Loop 44 reported:
- Loop 17 warm `profile_document()` (`n=30`): `495.17 ms`
- Loop 17 warm `execute_adaptive_ocr()` (`n=5`): `368.85 ms`

Since `execute_adaptive_ocr()` calls `profile_document()` internally on line 463 of `src/docuready/ingest/adaptive_ocr.py`, `execute_adaptive_ocr()` **cannot** be faster than `profile_document()` when measured under identical cache, thermal, and workload conditions.

## 2. Root Cause of the Loop 44 Anomaly

In Loop 44's `scratch_reproduce_and_benchmark.py`:
1. `profile_document()` ran `n=30` **sequentially before** `execute_adaptive_ocr()` (`n=5`), without `img.load()` pre-decoding and without warming up `execute_adaptive_ocr()`'s Stage 3 `eng` `TessBaseAPI` handle first.
2. Comparing a sequential `n=30` block against a small `n=5` block conflated OS/CPU frequency ramp and sample variance.

## 3. Interleaved Paired Stage-Timing Model (`n=30`, Loop 45)

Measured in `research/loop45/investigate_benchmark_boundary.py` after `img.load()` and 3 full `execute_adaptive_ocr()` warmups, alternating `profile_document()` and `execute_adaptive_ocr()` on every iteration (`n=30` paired observations, `research/loop45/LOOP_45_BENCHMARK_BOUNDARIES.json`):

| Stage / Boundary | L17 (`DOC_CTRL_01`, Eng) Mean (ms) | L18 (`DOC_EXT_06`, Ori+Eng) Mean (ms) |
|---|---:|---:|
| Standalone `profile_document()` | **467.52** | **317.89** |
| Internal `profile_document()` inside E2E | **465.18** | **321.66** |
| Stage 3/4 (`recognize_tsv` + quality gate delta) | **498.02** | **2633.74** |
| **Total `execute_adaptive_ocr()` E2E** | **963.20** | **2955.40** |

**Conclusion**: When measured with equivalent paired boundaries, internal `profile_document()` matches standalone `profile_document()` within `2.3–3.8 ms`, and `execute_adaptive_ocr()` is strictly additive (`profile + Stage 3/4 OCR`).
