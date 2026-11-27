# LOOP 46 — FALSE-POSITIVE & NEGATIVE-CONTROL AUDIT

## Expanded Negative-Control Cohort (`9 / 9` PASS — `0%` False Multilingual Routing)

| Document | Cohort | Artifact / Layout | Observed Strategy | Profile (ms) | Status |
|---|---|---|---|---:|---|
| `NEG_ENG_CIRCULAR_SEAL` | Synthetic | Concentric circular seal + English label | `FAST_PATH_ENG` | 236.36 | **PASS** |
| `NEG_ENG_DECORATIVE_CREST` | Synthetic | Cross-hatched crest + box + English label | `FAST_PATH_ENG` | 233.55 | **PASS** |
| `NEG_ENG_UPPER_NOISE` | Synthetic | 1.5% salt-and-pepper noise in upper band | `FAST_PATH_ENG` | 114.91 | **PASS** |
| `NEG_ENG_DIAGONAL_MARKS` | Synthetic | 15 diagonal watermark strokes | `FAST_PATH_ENG` | 185.71 | **PASS** |
| `NEG46_BLANK_UPPER_DENSE_LATIN` | Synthetic | Blank upper band + dense Latin body | `FAST_PATH_ENG` | 509.98 | **PASS** |
| `NEG46_AMBIGUOUS_TYPOGRAPHY` | Synthetic | Bracketed/slashed glyphs (`00/II/O1-l`) | `FAST_PATH_ENG` | 643.39 | **PASS** |
| `NEG46_OFFICIAL_STAMP_AND_WATERMARK` | Synthetic | Rectangular stamp + diagonal line | `FAST_PATH_ENG` | 794.33 | **PASS** |
| `CHALLENGE_06_FAINT_SEAL` | Real/Corpus | Faint seal over numeric ID | `FAST_PATH_ENG` | 853.84 | **PASS** |
| `STRESS_02_STAMP` | Real/Corpus | Faint rubber stamp overlay | `FAST_PATH_ENG` | 429.97 | **PASS** |

Zero English-only negative controls triggered Strategy C (`>= 6` Indic codepoint guard held `100%`).
