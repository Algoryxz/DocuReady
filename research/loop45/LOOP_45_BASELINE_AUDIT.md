# LOOP 45 — BASELINE AUDIT

## 1. Repository & Branch State

| Field | Value |
|---|---|
| **Working Branch** | `loop-45-independent-upper-band-generalization` |
| **Base Commit** | `02baae0748600c7f5d4e22599426e1c02f65a717` (Loop 44) |
| **Loop 44 Ancestor Check** | `git merge-base --is-ancestor 02baae0 HEAD` → `0` (PASS) |
| **Loop 10 Ancestor Check** | `git merge-base --is-ancestor bdc403a HEAD` → `0` (PASS) |
| **Protected Release** | `bdc403a` (Loop 10 — unmodified, unpromoted) |

## 2. Loop 44 Changes Inspected

- `src/docuready/ingest/adaptive_ocr.py`: Strategy D conditional upper-band probe (`_probe_band(0.05, 0.22, max_dim=500.0)`) guarded by `>= 6` Devanagari/Odia codepoints when central (`0.25..0.45`) is `LATIN` and lower (`0.52..0.85`) is blank/inconclusive.
- `tests/test_loop44_upper_band.py`: 22 tests (20 `native_text`/unit + 2 composited raster tests).
- `research/loop44/`: 16 markdown reports + `LOOP_44_BENCHMARK_RAW.json` + `LOOP_44_ABLATION_AND_E2E.json`.
