# LOOP 47 — LIMITATIONS AND RISKS

1. **External Licensed Corpus Availability**:
   - In this offline qualification environment, no newly acquired external licensed Indic-header + Latin-body real-world documents were added beyond the existing `research/` corpus (`doclaynet_001..005`, Loop 14/18 corpora). Synthetic/composited fixtures (`SYN_*`, `SYN47_*`) are reported strictly separately from real/corpus documents.
2. **Cold L17 `profile_document()` Latency**:
   - Loop 46 reported cold L17 `profile_document()` mean `996.48 ms` (above the `850 ms` historical threshold) due to cold Python/DLL load plus the 3rd upper-band probe. Warm in-process `profile_document()` (matching the long-lived sidecar in production) remains `< 850 ms`.
3. **Sparse Central-Strip Documents (`doclaynet_001..005`)**:
   - Continue to trigger `probe_uncertain=True -> GLOBAL_MULTILINGUAL` (`eng+hin+ori`) via the Loop 40 uncertainty safeguard.
4. **Package A/B Minimization (Gate P — PARTIAL)**:
   - Carried forward unchanged as `CONDITIONALLY QUALIFIED` (`63.40 MiB` saved, `10/10` functional parity, `CI_high +4516.29 ms > +1500 ms`).
5. **Windows Authenticode & Clean-VM SmartScreen (Gates W, X — BLOCKED)**:
   - Binaries remain `NotSigned` (`0` certificates) and clean-VM SmartScreen testing is unavailable in this CLI environment.
