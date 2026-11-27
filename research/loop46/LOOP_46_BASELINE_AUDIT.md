# LOOP 46 — BASELINE AUDIT

| Field | Value |
|---|---|
| **Working Branch** | `loop-46-indic-header-latin-body-recovery` |
| **Base Commit** | `c7ed04f41e3da903493803bb7f0263f96121ed4b` (Loop 45) |
| **Loop 45 Ancestor Check** | `git merge-base --is-ancestor c7ed04f HEAD` → `0` (PASS) |
| **Loop 10 Ancestor Check** | `git merge-base --is-ancestor bdc403a HEAD` → `0` (PASS) |
| **Protected Release** | `bdc403a` (Loop 10 — unmodified, unpromoted) |

Inspected Loop 45 artifacts (`LOOP_45_VALIDATION_RAW.json`, `LOOP_45_BENCHMARK_BOUNDARIES.json`, `LOOP_45_QUALIFICATION_MATRIX.md`) and `src/docuready/ingest/adaptive_ocr.py` (lines 285–345).
