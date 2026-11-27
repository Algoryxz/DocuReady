# DOCUREADY — LOOP 36 SIDECAR STARTUP & RECOVERY REPORT

- **30-Repetition Health Benchmark (`performance_results.json`):**
  - Failures: 0 / 30
  - Cold first launch: `2666.12 ms`
  - Warm 29-rep mean: `1418.95 ms` (median `1279.46 ms`, p95 `2610.57 ms`, stdev `418.57 ms`)
- **Root Cause of Startup Time:** PyInstaller `_internal` DLL loading (122 DLLs + PyMuPDF/OpenCV/NumPy imports) plus first-run Windows Defender scan explains the ~2.67s–9.88s cold spike vs ~1.28s warm median.
- **Crash Recovery:** Electron SIGKILL crash recovery and audit cancellation recovery tests both passed (25/25).
