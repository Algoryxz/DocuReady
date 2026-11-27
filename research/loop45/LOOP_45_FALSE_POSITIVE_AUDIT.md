# LOOP 45 — FALSE-POSITIVE & NEGATIVE-CONTROL AUDIT

## 1. Negative Controls (`6 / 6` PASS — `0%` False-Positive Multilingual Routing)

| Negative Control | Cohort | Artifacts Present | Observed Strategy | Profile (ms) | Status |
|---|---|---|---|---:|---|
| `NEG_ENG_CIRCULAR_SEAL` | Synthetic | Concentric circular seal + English text in `0.06..0.20` | `FAST_PATH_ENG` (`eng`) | 200.07 | **PASS** |
| `NEG_ENG_DECORATIVE_CREST` | Synthetic | Cross-hatched crest + box + English text in `0.06..0.20` | `FAST_PATH_ENG` (`eng`) | 181.73 | **PASS** |
| `NEG_ENG_UPPER_NOISE` | Synthetic | 1.5% salt-and-pepper noise in `0.05..0.25` | `FAST_PATH_ENG` (`eng`) | 90.05 | **PASS** |
| `NEG_ENG_DIAGONAL_MARKS` | Synthetic | 15 diagonal watermark strokes in `0.06..0.20` | `FAST_PATH_ENG` (`eng`) | 171.73 | **PASS** |
| `CHALLENGE_06_FAINT_SEAL` | Real/Corpus | Faint rubber seal over numeric ID | `FAST_PATH_ENG` (`eng`) | 606.58 | **PASS** |
| `STRESS_02_STAMP` | Real/Corpus | Faint rubber stamp overlay | `FAST_PATH_ENG` (`eng`) | 792.48 | **PASS** |

All negative controls remained on `FAST_PATH_ENG` (`0` false triggers of Strategy D).
