# DOCUREADY — LOOP 41 FALLBACK PARITY REPORT

**Comparison:** In-process `_PROBE_ENGINE.recognize_gray(thumb)` vs. subprocess `pytesseract.image_to_string(thumb, lang="eng+hin+ori", config="--psm 6", timeout=8)` on identical probe thumbnails across 5 script classes.

| Fixture | In-Process (ms) | Fallback (ms) | In Words / FB Words | Text CER Diff | In Script / FB Script | Parity |
|---|---:|---:|---:|---:|---|---|
| `eng` (`DOC_CTRL_01`) | `98.99` | `357.18` | `15 / 15` | `0.0000` | `LATIN / LATIN` | **EXACT** |
| `ori` (`DOC_EXT_06`) | `128.31` | `337.35` | `22 / 22` | `0.0000` | `MIXED_ODIA_LATIN / MIXED_ODIA_LATIN` | **EXACT** |
| `hin` (`DOC_HIN_01`) | `377.75` | `596.77` | `35 / 35` | `0.0000` | `DEVANAGARI / DEVANAGARI` | **EXACT** |
| `mix_hin` (`DOC_MIX_01`) | `117.39` | `312.19` | `21 / 21` | `0.0000` | `MIXED_DEVANAGARI_LATIN / MIXED_DEVANAGARI_LATIN` | **EXACT** |
| `mix_ori` (`DOC_MIX_02`) | `201.15` | `417.01` | `16 / 16` | `0.0000` | `MIXED_ODIA_LATIN / MIXED_ODIA_LATIN` | **EXACT** |

- Simulated DLL unavailability (`_unavailable = True`) returned `None` and triggered the `pytesseract` fallback cleanly.
- Fallback preserves identical text, word counts, script classification, and `probe_uncertain` semantics.
