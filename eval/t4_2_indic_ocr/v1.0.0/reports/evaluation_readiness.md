# T4.2 Indic OCR Evaluation Readiness Report (v1.0.0)

- **Corpus:** `docuready-t4-2-indic-ocr` (`v1.0.0`)
- **Evaluation Role:** `held_out` (`training_eligible: false`)
- **Extraction Mode:** `LOCAL_OCR` (`native_text_layer: false`)
- **Sample Counts:** `12` Odia (`ori`, `ODIA`) + `12` Hindi (`hin`, `DEVANAGARI`) = `24` PNG documents (`96` field ground-truth records)

## Validation Status

| Check | Status | Summary | Report |
|---|---|---|---|
| Rendering & Rasterization | **PASS** | 24/24 PNGs (`1653x2339`, RGB, 200 DPI), zero native text layer, 100% font glyph coverage | [rendering_validation.json](rendering_validation.json) |
| Integrity & Determinism | **PASS** | 27/27 SHA-256 hashes verified, zero duplicate IDs/images, byte-identical regeneration | [integrity_validation.json](integrity_validation.json) |
| Ground-Truth Consistency | **PASS** | 96/96 records match `docuready.normalize.normalizer`, 80 Indic-digit raw records preserved | [ground_truth_validation.json](ground_truth_validation.json) |

## Paired OCR Comparison Matrix

| Language | Script | Baseline OCR | Indic OCR | Interface Verified |
|---|---|---|---|---|
| Odia (`ori`) | `ODIA` | `eng` | `eng+ori` | `DocumentExtractor().extract_document(path, expected_type=DocumentType.INCOME_CERT, ocr_langs=...)` |
| Hindi (`hin`) | `DEVANAGARI` | `eng` | `eng+hin` | `DocumentExtractor().extract_document(path, expected_type=DocumentType.INCOME_CERT, ocr_langs=...)` |

## Smoke Check Results (`Tesseract 5.5.4`)

On `T42_ORI_001.png` and `T42_HIN_001.png`, `DocumentExtractor.extract_document` exercised `LOCAL_OCR` with:
- `T42_ORI_001.png`: `eng` (`mean_ocr_confidence=0.713`) vs `eng+ori` (`mean_ocr_confidence=0.910`)
- `T42_HIN_001.png`: `eng` (`mean_ocr_confidence=0.688`) vs `eng+hin` (`mean_ocr_confidence=0.886`)

Full 24-document paired field-level OCR accuracy benchmarking remains for **Akriti** to execute and record separately.
