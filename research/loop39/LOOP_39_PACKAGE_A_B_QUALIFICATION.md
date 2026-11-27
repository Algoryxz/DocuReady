# DOCUREADY — LOOP 39 PACKAGE A/B QUALIFICATION

Alternating paired trials (`A1, B1, A2, B2, A3, B3` in `ab_paired_trials.json`) across 5 multilingual images:
- **Variant A (Original, 759,258,903 B):** mean `27288.26 ms`, median `23595.81 ms`, 3/3 `ok=true`.
- **Variant B (Minimized, 692,773,837 B, -63.41 MB):** mean `27447.14 ms`, median `24649.1 ms`, 3/3 `ok=true`.
- **Difference:** `+0.58%` mean (within `~6500 ms` cold/warm stdev; Trial 3 had B faster than A: `22,746.77 ms` vs `23,473.09 ms`). Loop 38's 20.45% single-run gap was cold-start variance.
