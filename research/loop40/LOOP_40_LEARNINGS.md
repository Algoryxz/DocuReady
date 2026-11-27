# Loop 40 Engineering Learnings

**Date:** 2026-11-27  
**Branch:** `loop-40-performance-multilingual-and-windows-qualification`

---

1. **Subprocess Spawn + DLL Reload Dominates Short OCR Probes:**
   - Spawning `tesseract.exe` via `pytesseract` for a 350 px script probe spent ~`3.5–7.5 s` loading `libtesseract-5.dll` (`101.47 MB`) and 3 LSTM models, while actual recognition took `~135–160 ms` in-process via `TessBaseAPI`.
2. **Preserve Test-Hook Compatibility When Optimizing Native Paths:**
   - `tests/test_loop39_probe_hardening.py` monkeypatches `pytesseract.image_to_string`. Checking `pytesseract.image_to_string is _ORIG_PYTESSERACT_IMAGE_TO_STRING` before invoking `_PROBE_ENGINE` preserves both 25x–47x production speedups and unit-test fault injection.
3. **Combined LSTM Language Models Are Non-Monotonic:**
   - In Tesseract 5.4.0, dropping `hin` from `eng+hin+ori` (`eng+ori`) degraded mixed English–Odia accuracy (`DOC_MIX_02` CER `9.36%` vs `6.35%`). Always validate language-subset ablations empirically rather than assuming fewer models always help.
4. **Separate Ground-Truth Excerpt Alignment from OCR Quality:**
   - Excerpt-only ground truth (`DOC_EXT_01_MOSPI_NADA_GUIDE`, 145 chars vs full-page OCR) inflates macro CER above `100%` for all engines. Micro CER/WER and length-matched ground truth give a cleaner signal.
5. **Account for Process-Spawn Variance in A/B Non-Inferiority Budgets:**
   - A `±1.5 s` margin on a `16.4 s` cold-process OCR batch with `5 s` stdev requires `n >= 90` pairs or warm-daemon benchmarking.
