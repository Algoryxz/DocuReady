# DOCUREADY — LOOP 14
## Strategic Engineering Roadmap & Next Experiments (Loop 15+)

**Subsystem:** Multilingual Document Understanding & Fraud Intelligence  
**Focus:** Post-Loop 14 Exploration Tracks  

---

### 1. Track A: Specialized Indic Diacritic Post-Processing

- **Observed Problem:** Tesseract OCR occasionally isolates short-vowel matras (`ि`, `ি`, `ି`) as separate punctuation tokens (`|`, `f`, or isolated spaces).
- **Proposed Architecture (Loop 15):**
  - Implement a rule-based Indic Orthographic Repair module (`indic_ortho_repair.py`).
  - Automatically re-attach detached vowel matras to their preceding base consonant.
  - Re-compose decomposed virama ligatures into pre-composed Unicode forms using canonical NFC mapping.
- **Expected Outcome:** Projected further 10–15% WER reduction on Devanagari and Odia text without retraining the underlying LSTM model.

---

### 2. Track B: Mixed Arabic / Indic Numeral Normalization

- **Observed Problem:** Dates, amounts, and roll numbers in Indian government certificates frequently use Devanagari numerals (`०-९`) or Odia numerals (`୦-୯`).
- **Proposed Architecture:**
  - Introduce `normalize_indic_digits(text: str) -> str` in `src/docuready/ingest/normalizer.py`.
  - Transliterate all Indic numeral codepoints (`U+0966..U+096F` and `U+0B66..U+0B6F`) to standard ASCII Arabic digits (`0-9`) prior to regex extraction.
- **Expected Outcome:** Enables all existing numerical rule evaluators (`RULE-INC-01`, `RULE-AGE-01`) to parse vernacular income and age figures seamlessly.

---

### 3. Track C: Large-Scale Corpus Expansion (100+ Real Documents)

- **Strategy:** Build automated scrapers for official state gazette publication portals (e.g. `egazette.gov.in`, `odishagazette.nic.in`).
- **Target Collection:**
  - 50 bilingual English/Hindi central government gazettes.
  - 50 bilingual English/Odia state circulars.
  - 25 multi-column administrative broadsheets with authentic stamps and signatures.
- **Governance:** Apply strict provenance tagging (`VERIFIED_EXTERNAL`), manual dual-pass ground truth verification, and SHA-256 immutability.
