# LOOP 46 — LIMITATIONS AND RISKS

1. **Additional Profile-Stage Cost on English-Only Docs with Non-Blank Upper Bands**:
   - Strategy C probes `0.05..0.22` (`500 px`) on English documents that have ink (`>= 0.003`) in the upper band, adding `~250–300 ms` to `profile_document()` on L17 (`DOC_CTRL_01`) compared to Loop 45. Blank upper bands (`NEG46_BLANK_UPPER_DENSE_LATIN`) skip OCR in `< 1 ms`.
2. **Sparse Central-Strip Documents (`doclaynet_001..005`)**:
   - Unchanged from Loop 45: all 5 DocLayNet pages yield `< 5` characters in `0.25..0.45` and conservatively trigger `probe_uncertain=True -> GLOBAL_MULTILINGUAL`.
3. **Synthetic vs. Independent Real Corpus**:
   - Upper-header + Latin-body recovery was verified on composited raster fixtures (`SYN_DEV_HDR_LAT_BODY`, `SYN_ORI_HDR_LAT_BODY`) using shaped crops from `DOC_HIN_01` and `DOC_EXT_06`; independent real-world Indic-header + Latin-body documents with external ground truth remain a future corpus expansion item.
4. **Package A/B Minimization (Gate P — PARTIAL)**:
   - Carried forward unchanged as `CONDITIONALLY QUALIFIED` (`63.40 MiB` saved, `10/10` functional parity, `CI_high +4516.29 ms > +1500 ms`).
5. **Windows Authenticode & Clean-VM SmartScreen (Gates W, X — BLOCKED)**:
   - Binaries remain `NotSigned` (`0` certificates) and clean-VM SmartScreen testing is unavailable in this CLI environment.
