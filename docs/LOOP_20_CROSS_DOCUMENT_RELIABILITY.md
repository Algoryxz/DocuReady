# LOOP 20: Cross-Document Evidence Verification Report

## 1. Governance & Cross-Document Architecture

Multi-document auditing requires establishing whether evidence from two distinct documents (e.g. an application form vs an official invoice, or a sanctioned budget vs a bank transaction) agrees, conflicts, or is unverified.

Loop 20 formalizes `verify_cross_document_evidence()` in `src/docuready/ingest/table_association.py`.

The function evaluates two discrete `FieldEvidence` objects and returns one of six mutually exclusive audit classifications:
1. `AGREEMENT`: Values match with traceable cell provenance in both documents.
2. `MISMATCH`: Values discrepancy detected between the two documents.
3. `MISSING`: Field absent or blank in one or both documents.
4. `UNREADABLE`: OCR confidence below legible threshold (<30%) in either document.
5. `AMBIGUOUS_ASSOCIATION`: Either piece of evidence suffers from ambiguous bounding boxes or multiple row candidates.
6. `INSUFFICIENT_EVIDENCE`: Supporting evidence missing or unanchored.

---

## 2. Experimental Verification on Audit Pairs

We tested the cross-document engine against controlled audit pairs:

### Case 1: Genuine Discrepancy Detection (`CHALL_07` vs `CHALL_08`)
- **Document A (`CHALL_07`)**: Central Warehousing Invoice `INV-2026-904` — Portland Slag Cement Sanction Amount: `₹75,400`.
- **Document B (`CHALL_08`)**: District Site Receipt Voucher — Portland Slag Cement Site Claim: `₹78,400`.
- **Engine Result**:
  ```json
  {
    "status": "MISMATCH",
    "is_verified": false,
    "reason": "Evidence discrepancy: Document 1 has '75400' while Document 2 has '78400'",
    "ev1_value": "75400",
    "ev2_value": "78400",
    "ev1_bbox": [731, 191, 774, 203],
    "ev2_bbox": [731, 191, 774, 203]
  }
  ```
- **Audit Outcome**: Discrepancy cleanly flagged. System refused to falsely verify clearance.

### Case 2: Multi-Document Concordance (`CHALL_07` vs `CHALL_08` Item 2)
- **Document A (`CHALL_07`)**: Structural Steel TMT Sanction Amount: `₹124,000`.
- **Document B (`CHALL_08`)**: Structural Steel TMT Site Claim: `₹124,000`.
- **Engine Result**:
  ```json
  {
    "status": "AGREEMENT",
    "is_verified": true,
    "reason": "Values match exactly with verifiable cell provenance in both documents",
    "ev1_value": "124000",
    "ev2_value": "124000"
  }
  ```
- **Audit Outcome**: Confirmed clearance with unbroken bidirectional provenance.

### Case 3: Ambiguous or Degraded Evidence
- When one document has `is_ambiguous = True`, the engine returns `AMBIGUOUS_ASSOCIATION` (`is_verified = False`), routing to human review.
- When one document has OCR confidence $<30\%$, the engine returns `UNREADABLE` (`is_verified = False`).
