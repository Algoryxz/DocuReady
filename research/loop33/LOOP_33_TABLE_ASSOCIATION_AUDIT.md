# DOCUREADY — LOOP 33 TABLE & FIELD ASSOCIATION AUDIT (FAMILY D)

**Milestone:** Loop 33 — Domain Rules & Decision Integrity  
**Component:** `src/docuready/ingest/table_extraction.py`, `src/docuready/rules/slot_validator.py`, `src/docuready/evidence/cross_document.py`  
**Operating Thresholds:** $T^* = 70.0$, $T_{\text{fuzzy}} = 75.0$  
**Evaluation Date:** 2026-11-25  

---

## 1. Scope & Objectives

Rule Family D governs structural document parsing, table cell-to-header association, and document slot validation:
- **Table Cell & Header Alignment:** Extracting tabular marks, subject lists, and financial transaction rows from marksheets and bank statements.
- **Column Gutter Traps:** Preventing multi-column OCR text bleed across adjacent table columns.
- **Field Completeness (`RULE-FLD-01`):** Verifying the presence and legibility of required fields on target document slots.
- **Document Slot Validation (`RULE-SLOT-01`):** Verifying that documents uploaded to slots match the expected document type semantically.

---

## 2. Invariant Analysis & Structural Semantics

### 2.1 Document Slot Mismatch Quarantine (Safety Invariant 6)
If an applicant uploads an electricity bill or caste certificate to the `INCOME_CERT` slot:
1. `validate_packet_slots()` detects slot misclassification.
2. Emits `RULE-SLOT-01` (CRITICAL finding).
3. The slot is added to `mismatched_slots`.
4. **Quarantine Guarantee:** All subsequent field extraction lookups for that slot (`get_f(dt, field)`) return `None`.
5. The system never evaluates income ceiling or validity on a mismatched document.

### 2.2 Table Gutter and Cell Association
- In Marksheet parsing, subject rows are bound to their respective maximum and obtained marks columns.
- `extract_table_data()` enforces bounding-box column boundary checks. Text from column $N+1$ cannot bleed into column $N$.
- Multiline cell values are aggregated within row y-coordinate thresholds.

### 2.3 Unreadable & Scan Quality Handling (`RULE-DOC-02`)
- If a document is flagged `UNREADABLE` or has OCR confidence $< 0.60$:
  - Emits `RULE-DOC-02` (CRITICAL / UNKNOWN).
  - Score penalty: 25 points.
  - Does not trigger statutory rejection (`FAIL`), but flags the scan for re-upload (`REVIEW`).

**Audit Status:** APPROVED. Slot quarantine and table gutter boundaries protect against out-of-context field extractions.
