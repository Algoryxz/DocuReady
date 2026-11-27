# LOOP 44 — CORPUS MANIFEST

## 1. Core Benchmark & Validation Corpus

| ID | File Path | Language Bucket | Type | Notes |
|---|---|---|---|---|
| `DOC_CTRL_01` | `research/loop18/corpus/DOC_CTRL_01_ENGLISH_CERTIFICATE.png` | English (`eng`) | Real/Corpus | Loop 17 baseline (`< 850 ms` profile threshold) |
| `DOC_EXT_06` | `research/loop18/corpus/DOC_EXT_06_ODIA_REVENUE_NOTICE.png` | Odia + English (`ori+eng`) | Real/Corpus | Loop 18 baseline (`< 1400 ms` profile threshold) |
| `DOC_HIN_01` | `research/loop14/corpus/DOC_HIN_01_ADMIN_CIRCULAR.png` | Hindi (`hin`) | Real/Corpus | Monolingual Devanagari circular |
| `DOC_MIX_01` | `research/loop14/corpus/DOC_MIX_01_HIN_ENG_SCHOLARSHIP.png` | Mixed Hindi+Eng | Real/Corpus | Mixed-script scholarship form |
| `DOC_MIX_02` | `research/loop14/corpus/DOC_MIX_02_ORI_ENG_SCHOLARSHIP.png` | Mixed Odia+Eng | Real/Corpus | Mixed-script scholarship form |

## 2. Loop 44 Raster Diagnostic Fixtures

| ID | File Path | Language Bucket | Layout | Purpose |
|---|---|---|---|---|
| `BLIND44_IND_HDR_LAT_ID_RASTER` | `research/loop44/BLIND44_IND_HDR_LAT_ID_RASTER.png` | Odia + English | Odia header (`0.05..0.21`), Latin ID (`0.28..0.42`), blank lower (`0.50..1.00`) | Reproduces `BLIND43_IND_HDR_LAT_ID` via real raster OCR |
| `BLIND44_LAT_HDR_HIN_BODY_RASTER` | `research/loop44/BLIND44_LAT_HDR_HIN_BODY_RASTER.png` | English + Hindi | Latin header (`0.28..0.42`), Hindi body (`0.53..0.83`) | Strategy C regression guard (raster) |
| `BLIND44_ENG_UPPER_SEAL_RASTER` | `research/loop44/BLIND44_ENG_UPPER_SEAL_RASTER.png` | English (`eng`) | Geometric seal + English text (`0.07..0.17`), English body (`0.28..0.42`), blank lower | Strategy D false-positive guard (raster) |

## 3. Known Synthetic Rendering Limitation

As established in Loop 43, synthetic Indic fixtures rendered purely with Pillow `ImageDraw.text()` without `libraqm` HarfBuzz shaping produce unshaped glyphs that Tesseract cannot decode as Devanagari/Odia Unicode. Loop 44 raster fixtures therefore composite genuine shaped Indic crops from `DOC_EXT_06` and `DOC_HIN_01` alongside Pillow-rendered Latin text, and unit tests cover both `native_text` and composited raster paths.
