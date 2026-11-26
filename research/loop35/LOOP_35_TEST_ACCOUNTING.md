# DOCUREADY — LOOP 35 TEST ACCOUNTING

Unique test accounting (no double-counting):
- **Python Test Suite (`tests/`):** 874 existing tests + 9 new Loop 35 e2e tests = **883 unique Python tests**
  - **Passed:** 881
  - **Failed:** 2 (`tests/test_loop17_adaptive_efficiency.py::test_fast_profiling_performance` [1129.65 ms vs <850.0 ms] and `tests/test_loop18_accuracy_and_critical_fields.py::test_new_documents_profiling_and_execution` [1582.11 ms vs <1400.0 ms on `DOC_EXT_07_TECHNICAL_EDUCATION_DIPLOMA`]) — both are wall-clock OCR profiling latency threshold misses on this Windows host, not accuracy or safety failures.
  - **Skipped / Expected Failures:** 0 / 0
- **Loop 35 New E2E Suite (`tests/test_loop35_e2e_workflow.py`):** **9 / 9 passed** (included in the 883 Python total above, not double-counted).
- **Electron Desktop Suite (`apps/desktop/tests/`):** **25 unique TypeScript tests** (25 passed, 0 failed, 0 skipped).
- **Combined Unique Total:** **908 unique automated tests** (**906 passed, 2 wall-clock latency failures**).
