# Loop 22 — Evidence Association Analysis

**Focus:** Traceability, Spatial Integrity, and Candidate Ambiguity Resolution  
**Module:** `src/docuready/ingest/table_association.py`

---

## 1. Explicit Evidence-to-Field Trust Architecture

In DocuReady, verification decisions are strictly tied to spatial and contextual provenance. A matching substring elsewhere on a page is never accepted as verification of a specific critical field.

Every extraction produces a `FieldEvidence` record containing:
- `field_name`: Symbolic identifier of the claim.
- `value`: Normalized candidate string.
- `raw_text`: Exact OCR text inside the cell.
- `bbox`: Absolute pixel bounding box `(x1, y1, x2, y2)`.
- `row_idx`, `col_idx`: 2D table grid indices.
- `col_header`: Reconstructed column header (including fused multi-tier paths).
- `confidence`: Word/cell level OCR confidence score.
- `is_ambiguous`: Boolean flag denoting spatial or syntactic uncertainty.
- `verification_decision`: Explicit discrete policy outcome (`VERIFY` or `ABSTAIN`).
- `abstention_reason`: Traceable explanation when verification is withheld.
- `provenance`: Dictionary tracking document ID, query mode, token count, and rejected candidates.

---

## 2. Association Quality vs OCR Character Quality

A crucial finding of Loop 22 is that **OCR accuracy does not equal verification reliability**:
- In `BLIND_09`, Tesseract recognized `'54000'` with 95.0% confidence and zero character errors. However, the value was in the *Freight* column, whereas the requested field was *Weight* (`18.5`). Associating `'54000'` with *Weight* was a complete failure of evidence association despite perfect OCR.
- In `CHALL_01`, Tesseract read `'70000'` with 96.0% confidence. But `'70000'` was *Net Release*, not *Penalty Levy*.
- In `CHALL_05`, Tesseract read `'15000 1500'` perfectly, but the cell merged two adjacent columns across an 8px borderless gutter.

Reporting OCR Character Error Rate (CER) alone obscures these critical association failures. DocuReady evaluates **Spatial Exact Match (SEM)** and **Critical Field Precision (CFP)** independently of raw character recognition.

---

## 3. Disambiguation Mechanisms

1. **Header-to-Field Semantic Cross-Check:**
   Before verifying a cell extracted via `col_idx`, the system cross-references `grid.col_headers[col_idx]` with `field_name` and `expected_type`. If the header explicitly contradicts the field (e.g. `Freight` for `weight`, or `Net Release` for `penalty`), `is_ambiguous = True` is set and verification is withheld.
2. **Multi-Token Numeric Guard:**
   When an amount, code, or quantity field captures a cell with multiple whitespace-separated tokens (e.g. `'15000 1500'`), the system detects gutter bleed and marks `is_ambiguous = True`.
3. **Repeated Label Collision:**
   When multiple rows match the same row pattern (e.g. repeated transaction ID in different ledger sections), `is_multi_row` is flagged, withholding verification unless distinct contextual headers disambiguate the rows.
