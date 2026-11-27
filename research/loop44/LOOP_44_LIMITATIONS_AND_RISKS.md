# LOOP 44 — LIMITATIONS AND RISKS

1. **Pillow Indic Shaping Limitation**:
   - Pillow `ImageDraw.text()` without `libraqm` / HarfBuzz renders unshaped Devanagari/Odia glyphs that Tesseract cannot decode reliably. Synthetic Indic raster fixtures must use shaped text crops or `native_text` until `libraqm` is available in test environments.
2. **Cold Subprocess L17 `profile_document()` Variance**:
   - Warm in-process `profile_document()` on L17 (`DOC_CTRL_01`) comfortably passes `< 850 ms` (`mean 495.17 ms`, `p95 602.82 ms`). Cold subprocess `profile_document()` (`n=5`) averaged `935.71 ms` (`median 889.40 ms`, `min 867.51 ms`), reflecting Python interpreter startup + `libtesseract-5.dll` cold load overhead. In production, the long-lived Python sidecar keeps `_PROBE_ENGINE` warm.
3. **Package A/B Minimization (Gate P — PARTIAL)**:
   - Variant B saves `63.40 MiB` with `10 / 10` functional parity, but single-trial latency CI `[-4584, +4516 ms]` exceeds `+1500 ms`. Requires `n >= 90` paired trials to close.
4. **Windows Authenticode & Clean-VM SmartScreen (Gates W, X — BLOCKED)**:
   - Binaries remain unsigned (`NotSigned`, `0` certs) and clean-VM SmartScreen validation is unavailable in this CLI environment.
5. **Small Upper-Band Font Edge Case**:
   - Strategy D uses `max_dim = 500.0` for `0.05..0.22`, recovering `37` Odia characters where `350.0` recovered only `3`. Very small Indic watermarks (`< 6` recognized codepoints) are intentionally ignored by the false-positive guard.
