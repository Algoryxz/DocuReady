# DOCUREADY — LOOP 43 REGIONAL SCRIPT DETECTION

## Strategy Ablation (A–D)

- **Strategy A (Single Central Strip `0.25–0.45`):** Fast (`33–313 ms`), but misses Indic bodies below `0.45` (`LAT_HDR_HIN_BODY` risk).
- **Strategy B (Fixed 3-Band Probe `0.12–0.35`, `0.35–0.60`, `0.60–0.88`):** `952–1,968 ms` — exceeds Loop 17 (`< 850 ms`) and Loop 18 (`< 1,400 ms`) latency budgets.
- **Strategy C (Selected — Adaptive 2-Region Probe + Indic Safeguard):**
  - Probes central strip (`0.25–0.45`, `350 px`).
  - Only if central strip is monolingual `LATIN`, probes lower body (`0.52–0.85`, skipping if blank `ink < 0.003`).
  - Safeguard: `>= 4` Devanagari or Odia letters anywhere overrides majority-Latin suppression (`is_mixed = True`).
  - **Result:** Loop 17 warm `397.62 ms` (`< 850 ms`), Loop 18 warm `285.42 ms` (`< 1,400 ms`, `0 ms` extra overhead), and `BLIND43_LAT_HDR_HIN_BODY` correctly routed to `GLOBAL_MULTILINGUAL` (`eng+hin`).
- **Strategy D (Uncertainty Fallback Only):** Preserved via `probe_uncertain -> GLOBAL_MULTILINGUAL (eng+hin+ori)`.
