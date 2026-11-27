# LOOP 45 — THRESHOLD & PROBE-RESOLUTION ABLATION

## 1. Character-Count Threshold Audit (Devanagari vs. Odia Independently)

Evaluated `detect_unicode_script()` across `1–20` Indic characters embedded in a 40-character English base:
- Both Devanagari and Odia reject `1` isolated character (`dev_letters < 2` / `odia_letters < 2` noise filter).
- At `2–5` characters, `detect_unicode_script()` records the count, while Strategy D's `>= 6` upper-band guard prevents sparse OCR noise from triggering multilingual routing.
- At `>= 6` characters, Strategy D reliably promotes the upper-band signal.

## 2. Upper-Band Probe Resolution Audit (`350 px` vs `500 px` vs `650 px`)

| Script | `max_dim` | Thumbnail Size | `dev` Chars | `ori` Chars | `>= 6` Guard | Latency (ms) |
|---|---:|---|---:|---:|---|---:|
| Devanagari (`0.05..0.22`) | 350 | `350×113` | 115 | 14 | **True** | 924.15 |
| Devanagari (`0.05..0.22`) | 500 | `500×161` | 150 | 8 | **True** | 960.38 |
| Devanagari (`0.05..0.22`) | 650 | `650×210` | 127 | 10 | **True** | 1187.09 |
| Odia (`0.05..0.22`) | 350 | `350×113` | 6 | 5 | True (via `dev` noise) | 441.53 |
| Odia (`0.05..0.22`) | **500** | **`500×161`** | **1** | **25** | **True** | **651.12** |
| Odia (`0.05..0.22`) | 650 | `650×210` | 0 | 26 | **True** | 592.86 |

### Conclusion
**Odia is substantially more sensitive to `350 px` downscaling than Devanagari**: at `350 px`, Odia dropped to `5` true Odia characters (below `6` on its own!), whereas Devanagari still yielded `115` characters. Raising `max_dim` to `500 px` for the conditional upper-band probe increases true Odia recall 5× (`5 → 25` chars) while keeping latency bounded (`651.12 ms`), justifying `max_dim=500.0` + `>= 6` Indic guard.
