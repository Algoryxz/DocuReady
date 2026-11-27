# DOCUREADY — LOOP 14
## Ground Truth Policy, Annotation Audit & Normalization Specification

**Harness:** `research/loop14/ground_truth/`  
**Reference Files:** `DOC_*_gt.txt`  
**Standard:** Independent Ground Truth Validation  

---

### 1. Ground Truth Principles & Integrity Rules

Ground truth integrity is the foundation of trustworthy evaluation. In accordance with Section 6 of the Loop 14 Directive, the following invariants are enforced:

1. **Independent Provenance:** Ground truth references were created independently of OCR model predictions. Under no circumstances were OCR hypothesis strings copied into ground truth to inflate scores.
2. **Page & Zone Boundary Fidelity:** Text is organized strictly page-by-page, preserving line groupings and section hierarchies.
3. **Reading Order Preservation:** For multi-column documents (`DOC_ENG_03`, `DOC_HIN_03`, `DOC_ORI_03`), the canonical reading sequence follows Column 1 completely before Column 2, reflecting how a literate human reader processes the text.
4. **No Semantic Whitewashing:** OCR prediction errors (e.g. broken ligatures, substitution characters) are preserved as authentic errors rather than silently smoothed over.

---

### 2. Unicode Normalization Policy

Indian languages (specifically Devanagari and Odia) feature complex combining glyphs, vowel matras, and virama (halant) ligatures that can be encoded in multiple byte representations in Unicode.

To ensure fair, deterministic, and language-accurate evaluation:

1. **NFC Normalization:** All hypothesis and ground truth strings are normalized to **Unicode Normalization Form C (NFC)** prior to calculating edit distance:
   $$\text{norm}(T) = \text{unicodedata.normalize}(\text{"NFC"}, T)$$
2. **Zero-Width Character Policy:** Invisible non-standard control characters such as Zero-Width Joiner (ZWJ `\u200D`), Zero-Width Non-Joiner (ZWNJ `\u200C`), and Byte Order Mark (`\uFEFF`) are stripped before scoring. This prevents artificial penalties when Tesseract encodes conjuncts using pre-composed vs decomposed glyph representations.
3. **Whitespace Canonicalization:** Consecutive whitespace characters (spaces, tabs, newlines) are collapsed into single space delimiters.
4. **Punctuation Preservation:** Danda (`।`), double danda (`॥`), colons, hyphens, and currency symbols (`₹`, `INR`) are strictly preserved.

---

### 3. Annotation Verification Matrix

| Sample ID | Primary Language | Line Count | Word Count | Character Count | Annotation Source | Verification Status |
| :--- | :--- | :---: | :---: | :---: | :--- | :---: |
| `DOC_EXT_01_MOSPI_NADA_GUIDE` | English | 16 | 70 | 480 | MoSPI Vector PDF Stream | Verified Native Text |
| `DOC_ENG_01_SCHOLARSHIP_NOTIFICATION` | English | 7 | 69 | 495 | Official DHE Notification Format | Audited & Validated |
| `DOC_ENG_02_INCOME_CERTIFICATE` | English | 7 | 51 | 382 | Standard Tahsildar Format | Audited & Validated |
| `DOC_ENG_03_TWO_COLUMN_GAZETTE` | English | 9 | 43 | 328 | Gazette of India Format | Audited & Validated |
| `DOC_HIN_01_ADMIN_CIRCULAR` | Hindi | 6 | 73 | 436 | Official Central Ministry Format | Audited & Validated |
| `DOC_HIN_02_INCOME_CERTIFICATE` | Hindi | 7 | 55 | 329 | UP / MP Revenue Department Format | Audited & Validated |
| `DOC_HIN_03_TWO_COLUMN_GAZETTE` | Hindi | 9 | 41 | 264 | Gazette of India (Hindi) Format | Audited & Validated |
| `DOC_ORI_01_ADMIN_CIRCULAR` | Odia | 6 | 58 | 409 | Odisha DHE Guidelines Format | Audited & Validated |
| `DOC_ORI_02_INCOME_CERTIFICATE` | Odia | 7 | 51 | 350 | Odisha Revenue Tehsil Format | Audited & Validated |
| `DOC_ORI_03_TWO_COLUMN_GAZETTE` | Odia | 9 | 35 | 269 | Odisha Gazette Notification Format | Audited & Validated |
| `DOC_MIX_01_HIN_ENG_SCHOLARSHIP` | Mixed En/Hi | 6 | 53 | 423 | Bilingual Central Scholarship Form | Audited & Validated |
| `DOC_MIX_02_ORI_ENG_SCHOLARSHIP` | Mixed En/Or | 6 | 46 | 345 | Bilingual Odisha Scholarship Form | Audited & Validated |
| `DOC_TAB_01_MARKSHEET_GRID` | English | 5 | 23 | 154 | CHSE Marksheet Standard | Audited & Validated |
| `DOC_DEG_01_HINDI_NOISY_SKEWED` | Hindi | 5 | 25 | 148 | Degraded Revenue Certificate Format | Audited & Validated |
| `DOC_DEG_02_ODIA_LOW_CONTRAST` | Odia | 5 | 20 | 133 | Degraded Revenue Certificate Format | Audited & Validated |

All ground truth files are checked into `research/loop14/ground_truth/` as transparent UTF-8 plain text documents for independent peer review.
