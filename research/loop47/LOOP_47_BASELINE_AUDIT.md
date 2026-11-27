# LOOP 47 — BASELINE AUDIT

| Field | Value |
|---|---|
| **Working Branch** | `loop-47-independent-mixed-script-generalization` |
| **Base Commit** | `a9d9b7f2b44d540e905d22e3e0496da0d88bb702` (Loop 46) |
| **Loop 46 Ancestor Check** | `git merge-base --is-ancestor a9d9b7f HEAD` → `0` (PASS) |
| **Loop 10 Ancestor Check** | `git merge-base --is-ancestor bdc403a HEAD` → `0` (PASS) |
| **Protected Release** | `bdc403a` (Loop 10 — unmodified, unpromoted) |

Inspected Loop 46 source (`src/docuready/ingest/adaptive_ocr.py`), `tests/test_loop46_indic_header_latin_body.py`, `research/loop46/LOOP_46_QUALIFICATION_RAW.json`, and `research/loop46/LOOP_46_QUALIFICATION_MATRIX.md`. Strategy C is evaluated **unchanged** in Loop 47.
