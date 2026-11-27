# DOCUREADY — LOOP 43 MIXED-SCRIPT ROUTING ROOT CAUSE

1. **Single-Strip Blind Spot (`0.25–0.45`):** `profile_document()` previously sampled only `(0.15*w, 0.25*h, 0.85*w, 0.45*h)`. Documents with a tall Latin letterhead in `0.15–0.45` and Hindi/Odia body text in `0.52–0.85` were classified as monolingual `LATIN` (`FAST_PATH_ENG`).
2. **Majority-Latin Suppression (`detect_unicode_script()`):** Requiring `dev_ratio >= 0.15` / `odia_ratio >= 0.15` allowed high Latin token density to suppress genuine Indic characters when Indic ratio fell below 15%.
3. **Pillow Unshaped Rendering on `BLIND42_MIX_*`:** On synthetic `BLIND42_MIX_HIN_ENG` and `BLIND42_MIX_ORI_ENG` (rendered with `Nirmala.ttc` without `librqm` shaping), `eng+hin+ori` read `0–2` Devanagari/Odia characters across all 3 bands, explaining why those two synthetic fixtures routed to `FAST_PATH_ENG`.
