# DOCUREADY — LOOP 42 CONCURRENCY & LIFECYCLE REPORT

- **Language-Switching Init/Delete (`eng -> hin -> ori -> eng+hin -> eng+ori -> eng+hin+ori`):** `6 / 6` returned `rc == 0` and deleted cleanly.
- **8-Thread E2E Concurrency Stress (`24` full `execute_adaptive_ocr` calls alternating `DOC_CTRL_01` & `DOC_EXT_06`):** **`0 / 24` mismatches**, `0` deadlocks, `0` crashes.
- **100-Call Sustained E2E Lifecycle (`execute_adaptive_ocr`):**
  - Step `0`: `284.05 MiB` RSS, `262` handles
  - Step `25`: `284.48 MiB` RSS, `262` handles
  - Step `50`: `282.45 MiB` RSS, `262` handles
  - Step `75`: `284.63 MiB` RSS, `262` handles
  - Step `100`: `284.72 MiB` RSS, `262` handles
  - **Net Delta:** `+0.67 MiB` RSS, **`0` handle leak** (`262 -> 262`).
