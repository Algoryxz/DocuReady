# LOOP 46 — FAILURE REPRODUCTION

Reproduced both Loop 45 failures (`SYN_DEV_HDR_LAT_BODY` and `SYN_ORI_HDR_LAT_BODY`) under Loop 45 Strategy D (`research/loop46/LOOP_46_REPRO_AND_ABLATION.json`):

| Fixture | Central (`0.25..0.45`, `350×133`) | Lower (`0.52..0.85`, `350×220`) | Upper (`0.05..0.22`, `500×161`) | Loop 45 Decision |
|---|---|---|---|---|
| `SYN_DEV_HDR_LAT_BODY` | `ink=0.0992`, `180` Latin, `0` Indic (`LATIN`) | `ink=0.0302`, `90` Latin, `0` Indic (`LATIN`) | `ink=0.1129`, `150` Devanagari, `8` Odia, `17` Latin (`DEVANAGARI`) | `FAST_PATH_ENG` (`eng`) |
| `SYN_ORI_HDR_LAT_BODY` | `ink=0.0992`, `180` Latin, `0` Indic (`LATIN`) | `ink=0.0302`, `90` Latin, `0` Indic (`LATIN`) | `ink=0.0449`, `25` Odia, `1` Devanagari, `51` Latin (`MIXED_ODIA_LATIN`) | `FAST_PATH_ENG` (`eng`) |

**Confirmed Root Cause**: Because `lower_txt.strip()` was non-empty (`90` Latin chars), Strategy D's `else:` branch never executed, suppressing upper-band probing despite genuine Indic headers (`150` Devanagari / `25` Odia codepoints) in `0.05..0.22`.
