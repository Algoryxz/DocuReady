# DOCUREADY — LOOP 36 PERFORMANCE REPORT

- **Sidecar Cold/Warm Startup:** `2666.12 ms` cold / `1418.95 ms` warm mean (30 reps, 0 failures).
- **Carry-Forward Loop 17/18 Profiling Tests:** Reproduced exact misses (`test_fast_profiling_performance`: `1129.65 ms` vs `<850 ms`; `test_new_documents_profiling_and_execution`: `1582.11 ms` vs `<1400 ms`). Classified as environment-dependent Tesseract subprocess latency (`BUG-036-003`).
