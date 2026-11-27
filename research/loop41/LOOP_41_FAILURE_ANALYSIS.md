# DOCUREADY — LOOP 41 FAILURE ANALYSIS

1. **Tiny/Degenerate Image `ZeroDivisionError` (Caught & Fixed):**
   - **Location:** `src/docuready/ingest/adaptive_ocr.py:198` (`profile_document`).
   - **Root Cause:** Central strip crop `(int(0.15*w), int(0.25*h), int(0.85*w), int(0.45*h))` produced `(0, 0)` on `1x1` images before any dimension check, causing `350.0 / max(strip.size)` to raise `ZeroDivisionError`.
   - **Fix:** Added `or w < 10 or h < 10` to the unreadable early-return guard and covered it in `tests/test_loop41_inprocess_reliability.py`.
2. **Process Memory Measurement Bug in Initial Harness (Caught & Fixed):**
   - `GetCurrentProcess()` in `ctypes` requires `restype = ctypes.c_void_p`; default `c_int` caused `0.0` RSS/handles until fixed.
3. **Environment Blockers (Open):**
   - Unsigned Windows binaries (`CodeSigningCertCount = 0`) and no clean Windows VM (`BLOCKED`).
   - Package A/B `n = 10` CI `[-4584.03, +4516.29]` exceeds `+1500 ms` (`CONDITIONALLY QUALIFIED`).
