# DocuReady T4.2 — Indic OCR Evaluation Corpus (`v1.0.0`)

## 1. Purpose & Scope
This corpus evaluates DocuReady's **T4.2 Indic OCR (`LOCAL_OCR`)** extraction and normalization pipeline on held-out synthetic Indian administrative documents rendered in **Odia (`ori`)** and **Hindi / Devanagari (`hin`)**.

- **Evaluation Role:** `held_out` (`training_eligible: false`) — not for calibration training.
- **Extraction Mode:** `LOCAL_OCR` (`native_text_layer: false`) — all 24 documents are pure raster RGB PNGs (`1653x2339`, 200 DPI).

## 2. Separation from T4.1 and T4.3
- **T4.1 (`eval/harness.py`, `eval/baseline.json`, `eval/EVAL_CARD.md`)** evaluates packet-level calibration and readiness decisions.
- **T4.3 (`eval/generators/generator_v2.py`)** generates synthetic PDFs across `dev`/`calib`/`test` splits for harness v2.
- **T4.2 (`eval/t4_2_indic_ocr/v1.0.0/`)** is an independently versioned, held-out **raster PNG** corpus specifically designed for paired `eng` vs `eng+ori` and `eng` vs `eng+hin` OCR evaluation. None of T4.1, T4.3, or the legacy golden baseline are modified by T4.2.

## 3. Languages, Scripts & Sample Counts
- **Odia (`ori`, `ODIA`):** `12` documents (`documents/odia/T42_ORI_001.png` .. `T42_ORI_012.png`)
- **Hindi (`hin`, `DEVANAGARI`):** `12` documents (`documents/hindi/T42_HIN_001.png` .. `T42_HIN_012.png`)
- **Fields per document (`96` total field records):** `dob`, `issue_date`, `annual_income`, `certificate_number`
- **Variations:** 4 layouts (`INCOME_CERTIFICATE_PORTRAIT`, `BILINGUAL_TWO_COLUMN_TABLE`, `COMPACT_BOXED_REGISTER`, `SUBHADRA_STYLE_WELFARE_SLIP`), 3 digit modes (all Indic digits, mixed Indic/ASCII digits, ASCII digits with Indic labels), varied date/currency separators, and mild scan degradation on 6 specimens.

## 4. Generation & Font Provenance
Documents are rendered deterministically (`GENERATOR_SEED = 20261128`) using PyMuPDF `2.1` HarfBuzz HTML/CSS shaping (`page.insert_htmlbox(..., archive=...)`) and rasterized at 200 DPI to RGB PNGs via Pillow (`compress_level=6`).

Font provenance (host system fonts, not redistributed in repo; recorded in [generation/font_provenance.json](generation/font_provenance.json)):
- **Nirmala UI (`Nirmala.ttc`)** — Odia, Devanagari, Latin
- **Kalinga (`kalinga.ttf`)** — Odia, Latin
- **Mangal (`mangal.ttf`)** — Devanagari, Latin

All synthetic applicant names, dates, incomes, and certificate numbers are fictional.

## 5. Regenerating & Verifying Hashes
Regenerate deterministically (Windows host with `Nirmala.ttc`, `kalinga.ttf`, `mangal.ttf`):
```powershell
.\.venv\Scripts\python.exe eval\t4_2_indic_ocr\v1.0.0\generation\generator.py
```
Verify all 27 SHA-256 hashes (24 PNGs + 3 metadata/ground-truth JSONs):
```powershell
.\.venv\Scripts\python.exe eval\t4_2_indic_ocr\v1.0.0\generation\generator.py --verify-hashes
```
Run full rendering, integrity, determinism, and ground-truth validation:
```powershell
.\.venv\Scripts\python.exe eval\t4_2_indic_ocr\v1.0.0\generation\validate_corpus.py
```

## 6. Ground Truth Schema
- **[ground_truth/raw.json](ground_truth/raw.json):** Exact rendered Unicode strings (preserving Odia `୦–୯` and Devanagari `०–९` digits).
- **[ground_truth/normalized.json](ground_truth/normalized.json):** Canonical normalized values computed using `docuready.normalize.normalizer` (`normalize_indic_digits`, `parse_and_normalize_date`, `normalize_income`, `normalize_cert_number`), plus provenance linking back to `document_sha256`.

## 7. Paired OCR Comparison Protocol
Run identical PNGs through `DocumentExtractor.extract_document(path, expected_type=DocumentType.INCOME_CERT, ocr_langs=...)`:
- **Odia (`documents/odia/*.png`):** `ocr_langs="eng"` vs `ocr_langs="eng+ori"`
- **Hindi (`documents/hindi/*.png`):** `ocr_langs="eng"` vs `ocr_langs="eng+hin"`

Store experimental outputs outside `ground_truth/` (e.g., under an experiment report file), record `tesseract --version` and `tesseract --list-langs`, and record any missing-language failures without falling back to `eng`.

## 8. Limitations & Validation Status
- **Synthetic-only:** Cleanly typeset digital documents (plus 6 mild blur/rotation specimens); does not replace real-world scanned field samples under `docs/REAL_SAMPLE_PROTOCOL.md`.
- **Sample size (`n=24`):** Chosen for fast deterministic paired CI/local evaluation across 4 layouts × 3 variants per script; not statistically powered for narrow confidence intervals.
- **Validated:** Rendering/rasterization, zero native text, glyph coverage, SHA-256 integrity, deterministic regeneration, normalizer contract parity, and 4-run `LOCAL_OCR` smoke test.
- **Not yet run:** Full 24-document paired field-level accuracy/WER/CER comparison (owned by Akriti).
