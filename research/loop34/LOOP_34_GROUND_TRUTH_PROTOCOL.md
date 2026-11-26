# DOCUREADY — LOOP 34 GROUND-TRUTH ANNOTATION & ADJUDICATION PROTOCOL

**Milestone:** Loop 34  
**Date:** 2026-11-26  

---

## 1. Dual-Pass Human Annotation Methodology

To eliminate ground-truth ambiguity and human error in the evaluation corpus, every critical field is subjected to a dual-pass annotation protocol:
1. **Pass 1 (Primary Annotation):** Independent human annotator identifies the target field, labels its visual bounding box $(x_1, y_1, x_2, y_2)$, transcribes the exact visual text verbatim, and tags its semantic data type (`text`, `amount`, `date`, `id`, `number`).
2. **Pass 2 (Verification Annotation):** A second senior annotator independently inspects the document image without viewing Pass 1 annotations, transcribing the field and verifying boundary margins.
3. **Pass 3 (Adjudication):** Where Pass 1 and Pass 2 disagree (character mismatch, bounding box discrepancy, or ambiguity), the lead domain auditor reviews the original high-resolution TIFF/PNG scan. If the visual glyph is inherently unreadable or ambiguous, the field is tagged `GROUND_TRUTH_AMBIGUOUS` and quarantined from accuracy denominators.

---

## 2. Typing & Normalization Contracts

- **Identifiers:** Exact raw character strings without quotes or trailing punctuation bleed (e.g. `BARB0BHUBAN`, `ABCDE1234F`).
- **Dates:** Stored as exact source representation (e.g. `05/09/2004`) alongside normalized ISO canonical format (`2004-09-05`).
- **Amounts:** Stored with currency symbols as appearing in scan (`INR 220000`, `Rs. 2,50,000/-`) alongside numeric float (`250000.0`).
- **Missing Fields:** Marked explicitly as `STATUS_ABSENT` to test false-positive extraction detection.
