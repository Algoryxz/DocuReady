# DOCUREADY — LOOP 41 PACKAGE A/B DECISION

**Decision:** **`CONDITIONALLY QUALIFIED`** (Do **NOT** auto-promote Variant B over Variant A).

## Evidence Summary (`research/loop40/ab_paired_trials.json`)

- **Size Reduction:** Variant B removes `17` unused Tesseract training/CLI executables, reducing sidecar size from `759,258,903` bytes (`1,837` files) to `692,773,837` bytes (`1,820` files) — saving **`66,485,066` bytes (`63.40 MiB`, `-8.76%`)** while keeping `tesseract.exe`, `libtesseract-5.dll`, and all `tessdata` intact.
- **Functional Parity:** `10 / 10` alternating paired runs (`20 / 20` total) succeeded with `ok == true` and `rc == 0`.
- **Statistical Non-Inferiority Margin (`delta <= +1500.0 ms`):** Mean paired difference (`B - A`) was **`-33.87 ms`**, but 95% CI was **`[-4584.03 ms, +4516.29 ms]`** (`+4516.29 > +1500.0 ms`) due to OS process-spawn / Defender jitter (`stdev 4.5–6.2 s` on ~`16.4 s` cold packet runs).
- **Qualification Path:** Retaining the original `+1500.0 ms` margin requires `n >= 90` paired trials or a separately approved warm-throughput protocol before promoting Variant B.
