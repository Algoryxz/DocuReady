# DOCUREADY — LOOP 43 FAILURE ANALYSIS

1. **`BLIND43_IND_HDR_LAT_ID` Routing Miss (`Gate O` Partial):**
   - Odia header at `y < 0.25` was above the `0.25–0.45` central strip, and `0.52–0.85` was blank, so Strategy C did not inspect `0.08–0.25` and routed to `FAST_PATH_ENG` (`44.55%` CER). Fix for Loop 44: probe `0.08–0.25` when `0.52–0.85` is blank (`ink < 0.003`).
2. **Package A/B Statistical Margin (`Gate P` Partial):**
   - `n = 10` paired trials remain underpowered (`CI [-4584.03, +4516.29]` vs `+1500 ms`).
3. **Windows Code Signing & Clean VM (`Gates W, X` Blocked):**
   - Remain `BLOCKED` pending signing certificate and clean Windows VM.
