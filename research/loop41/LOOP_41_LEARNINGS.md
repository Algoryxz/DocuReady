# DOCUREADY — LOOP 41 LEARNINGS

1. **Test degenerate boundary inputs (`1x1`, `0x0` crop) on every image preprocessing step:** Cropping `(0.15*w, 0.25*h, 0.85*w, 0.45*h)` before checking `w < 10 or h < 10` caused `ZeroDivisionError` in `profile_document()`. A 1-line guard fixed it cleanly.
2. **Always set `restype = ctypes.c_void_p` on Win32 `GetCurrentProcess()`:** Default `c_int` truncates the `-1` pseudo-handle and silently yields `0` in `GetProcessMemoryInfo` / `GetProcessHandleCount`.
3. **Separate cold fresh-process vs. warm steady-state vs. end-to-end benchmarks explicitly:** Reconciling Loop 39's `profile_document()` numbers against Loop 40's pytest E2E quotes eliminated apparent contradictions.
4. **Never auto-promote size optimizations that miss statistical non-inferiority gates:** Variant B (`-63.40 MiB`) is `CONDITIONALLY QUALIFIED` until `n >= 90` paired trials or a warm-throughput protocol closes Gate P.
