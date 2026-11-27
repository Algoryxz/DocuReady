# DOCUREADY — LOOP 14
## Multilingual Operational Boundaries, Known Limitations & Risk Disclosures

**Subsystem:** Multilingual Ingestion & Script Routing  
**Classification:** Technical Limitations Disclosure  

---

### 1. Document Script Boundaries

Loop 14 successfully established verified OCR accuracy for:
- Standard English documents (Latin script).
- Hindi administrative documents (Devanagari script).
- Odia state certificates (Odia script).
- Bilingual mixed-script forms (English/Hindi and English/Odia).

However, the Indian subcontinent encompasses 22 scheduled languages across 13 distinct writing systems. The table below delineates current system coverage:

| Script / Language | Support Level | Language Pack Status | Runtime Behavior / Fallback |
| :--- | :---: | :---: | :--- |
| **English (Latin)** | **PRODUCTION** | Bundled (`eng`) | Full extraction, layout reconstruction, rule evaluation. |
| **Hindi (Devanagari)** | **QUALIFIED** | Bundled (`hin`) | Automatic script routing, Devanagari Unicode preservation. |
| **Odia (Odia)** | **QUALIFIED** | Bundled (`ori`) | Automatic script routing, Odia Unicode preservation. |
| **Bengali / Assamese** | **UNSUPPORTED** | Not Bundled | Falls back to default English OCR; high error rate expected. |
| **Telugu / Kannada** | **UNSUPPORTED** | Not Bundled | Falls back to default English OCR. |
| **Tamil / Malayalam** | **UNSUPPORTED** | Not Bundled | Falls back to default English OCR. |
| **Urdu (Nastaliq)** | **UNSUPPORTED** | Not Bundled | Right-to-Left (RTL) layout unsupported in scanline engine. |

---

### 2. Known OCR Quality Limitations

1. **Complex Indic Ligature Ambiguity:**
   In older or low-resolution scans ($< 150\text{ DPI}$), Tesseract's LSTM line recognizer occasionally fails to segment stacked conjunct characters (e.g. `द्भ`, `ष्ट्र`, `ଙ୍କ୍ଷ`). This results in decomposed virama characters or character omissions.
2. **Indic vs Arabic Numeral Normalization:**
   Many Indian revenue documents express dates and monetary amounts in Devanagari numerals (`०, १, २, ३, ४, ५, ६, ७, ८, ९`) or Odia numerals (`୦, ୧, ୨, ୩, ୪, ୫, ୬, ୭, ୮, ୯`). While OCR correctly transcribes the glyph, downstream regex patterns designed strictly for ASCII digits (`[0-9]+`) require numeric normalization before arithmetic rule evaluation.
3. **Pure Image Odia Script Detection:**
   Tesseract's standard `osd.traineddata` model does not contain a dedicated Odia classifier. For pure raster images lacking native text or metadata clues, Odia documents may initially be classified as Latin unless an Odia keyword or circular dome heuristic is present.

---

### 3. Fail-Closed & Fallback Safeguards

1. **Conservative Abstention:** If script detection confidence is low or inconclusive, DocuReady falls back to `eng`. In no scenario does the system crash, exit abnormally, or emit corrupted binary data.
2. **Zero Hallucination:** DocuReady never invents field values, name tokens, or revenue numbers. If OCR quality is poor, the system abstains or reports `UNREADABLE`, prompting human review.
3. **Loop 10 Isolation:** All multilingual capabilities reside in the isolated Loop 14 research branch. The competition release in `apps/desktop/out/DocuReady-win32-x64/` remains strictly sealed.
