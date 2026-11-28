# T4.2 Indic OCR Evaluation — Handoff to Akriti

- **Corpus Version:** `1.0.0`
- **Repository Path:** `eval/t4_2_indic_ocr/v1.0.0/`
- **Evaluation Role:** `held_out` (`training_eligible: false`, `extraction_mode: LOCAL_OCR`, `native_text_layer: false`)

## Corpus Inventory
- **Odia (`ori`, `ODIA`):** `12` PNGs (`eval/t4_2_indic_ocr/v1.0.0/documents/odia/T42_ORI_001.png` .. `T42_ORI_012.png`)
- **Hindi (`hin`, `DEVANAGARI`):** `12` PNGs (`eval/t4_2_indic_ocr/v1.0.0/documents/hindi/T42_HIN_001.png` .. `T42_HIN_012.png`)
- **Manifest:** [manifest.json](manifest.json)
- **SHA-256 Inventory:** [document_hashes.json](document_hashes.json)
- **Raw Ground Truth:** [ground_truth/raw.json](ground_truth/raw.json) (`96` field records)
- **Normalized Ground Truth:** [ground_truth/normalized.json](ground_truth/normalized.json) (`96` field records)

## Validation Status (Verified on Host)
- **Rendering & Rasterization:** `PASS` ([reports/rendering_validation.json](reports/rendering_validation.json)) — 24/24 PNGs (`1653x2339` RGB), zero native text layer, verified glyph coverage (`Nirmala.ttc`, `kalinga.ttf`, `mangal.ttf`).
- **Integrity & Determinism:** `PASS` ([reports/integrity_validation.json](reports/integrity_validation.json)) — 27/27 SHA-256 hashes match; byte-identical regeneration verified.
- **Ground-Truth Consistency:** `PASS` ([reports/ground_truth_validation.json](reports/ground_truth_validation.json)) — 96/96 records match `docuready.normalize.normalizer`.

## Paired OCR Configurations to Run
| Language | Files | Baseline Config | Indic Config |
|---|---|---|---|
| Odia (`ori`) | `documents/odia/*.png` (12) | `ocr_langs="eng"` | `ocr_langs="eng+ori"` |
| Hindi (`hin`) | `documents/hindi/*.png` (12) | `ocr_langs="eng"` | `ocr_langs="eng+hin"` |

## Verified Interface & First Command
`DocumentExtractor.extract_document()` natively accepts these PNGs and routes them to `LOCAL_OCR` (verified on `T42_ORI_001.png` and `T42_HIN_001.png` with Tesseract `5.5.4`).

First verification command you can run immediately:
```powershell
.\.venv\Scripts\python.exe eval\t4_2_indic_ocr\v1.0.0\generation\generator.py --verify-hashes
.\.venv\Scripts\python.exe -m pytest tests\test_t4_2_indic_ocr_corpus.py -q
```
Then iterate `manifest.json["documents"]` with `DocumentExtractor().extract_document(doc_path, expected_type=DocumentType.INCOME_CERT, ocr_langs=...)` to record paired `eng` vs `eng+ori` / `eng+hin` metrics.

## Remaining Notes / Blockers
- Requires Tesseract with `eng`, `ori`, and `hin` traineddata installed (e.g., user-local `%LOCALAPPDATA%\DocuReady-OCR\tesseract-env` on Windows or `tesseract-ocr-{eng,ori,hin}` in CI).
- Deterministic PNG regeneration requires Windows system fonts (`Nirmala.ttc`, `kalinga.ttf`, `mangal.ttf`); evaluation of the committed PNGs works on any OS.
