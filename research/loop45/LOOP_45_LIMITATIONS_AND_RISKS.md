# LOOP 45 — LIMITATIONS AND RISKS

1. **Indic Header + Non-Blank Latin Body (`SYN_DEV_HDR_LAT_BODY`, `SYN_ORI_HDR_LAT_BODY`)**:
   - Strategy D only probes the upper band (`0.05..0.22`) when the lower body (`0.52..0.85`) is blank. When an Indic header co-occurs with a full non-blank Latin body, Strategy D does not trigger and routes to `FAST_PATH_ENG`. Addressing this without exceeding the `< 850 ms` L17 `profile_document()` budget remains an open engineering trade-off.
2. **Sparse Central-Strip Documents (`doclaynet_001..005`)**:
   - All 5 DocLayNet pages yielded `< 5` characters in the `0.25..0.45` central strip and conservatively triggered `probe_uncertain=True -> GLOBAL_MULTILINGUAL` (`eng+hin+ori`) via the Loop 40 safeguard. This avoids silent English-only drops at the cost of multilingual OCR latency on sparse-center layouts.
3. **Synthetic Indic Shaping**:
   - Pillow `ImageDraw.text()` without `libraqm` cannot shape complex Devanagari/Odia conjuncts; synthetic raster tests use composited shaped crops from `DOC_HIN_01` and `DOC_EXT_06`.
4. **Package A/B Minimization (Gate P — PARTIAL)**:
   - Carried forward unchanged as `CONDITIONALLY QUALIFIED` (`63.40 MiB` saved, `10/10` functional parity, `CI_high +4516.29 ms > +1500 ms`).
5. **Windows Authenticode & Clean-VM SmartScreen (Gates W, X — BLOCKED)**:
   - Binaries remain `NotSigned` (`0` certificates) and clean-VM SmartScreen testing is unavailable in this CLI environment.
