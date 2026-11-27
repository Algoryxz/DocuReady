# DOCUREADY — LOOP 42 FAILURE ANALYSIS

1. **Mixed-Script Synthetic Blind Routing (`BLIND42_MIX_HIN_ENG`, `BLIND42_MIX_ORI_ENG`):**
   - Both documents placed a Latin header/roll number in the `0.25–0.45` probe band, causing Latin tokens to dominate the strip and routing to `FAST_PATH_ENG` (`9.01%` / `9.43%` CER). Kept unmodified without tuning on the blind set; documented as a future probe-band coverage item for Loop 43.
2. **Package A/B Statistical Margin (`Gate P`):**
   - `n = 10` paired trials remain underpowered (`CI [-4584.03, +4516.29]` vs `+1500 ms`).
3. **Windows Code Signing & Clean VM (`Gates W, X`):**
   - Remain `BLOCKED` pending signing certificate and clean Windows VM.
