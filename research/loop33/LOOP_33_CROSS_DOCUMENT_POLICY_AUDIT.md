# DOCUREADY — LOOP 33 CROSS-DOCUMENT VERIFICATION POLICY AUDIT (FAMILY E)

**Milestone:** Loop 33 — Domain Rules & Decision Integrity  
**Component:** `src/docuready/evidence/cross_document.py`, `src/docuready/outcome/resolver.py`  
**Operating Thresholds:** $T^* = 70.0$, $T_{\text{fuzzy}} = 75.0$  
**Evaluation Date:** 2026-11-25  

---

## 1. Scope & Objectives

Rule Family E governs cross-document multi-evidence reasoning:
- **Applicant Entity Resolution:** Ensuring that documents in an application packet belong to the same person.
- **Contradiction Detection:** Identifying conflicting statements across independent certificates (e.g. differing DOB, conflicting father's name, mismatched caste category).
- **Corroboration Independence:** Guaranteeing that evidence from multiple documents is truly independent rather than repeated OCR artifacts from a shared page.
- **Missing-Evidence Detection & Conservative Abstention:** Abstaining when essential corroborating documents are absent or indeterminate.

---

## 2. Invariant Analysis & Cross-Document Semantics

### 2.1 Entity Resolution (`resolve_entity_match`)
- Evaluates candidate applicant records across documents using multi-attribute matching:
  - Name similarity (token sort ratio $\ge 0.85$ or exact compatible initials).
  - Date of birth identity (exact ISO date match).
  - Relative/Guardian name matching.
- If two documents show incompatible demographic attributes (e.g., DOB difference $> 0$ days without clerical error pattern), `resolve_entity_match()` rejects entity identity.

### 2.2 Corroboration Independence (`detect_document_independence`)
- Prevents false confidence inflation:
  - If two documents originate from the same scanned PDF page or share image hash fingerprints, they are marked as **Dependent**.
  - Repeated OCR misreads across dependent sources are not counted as independent multi-source verification.
  - Verification requires at least two **independent** document sources.

### 2.3 Contradiction vs Ambiguity
- When two independent documents assert mutually exclusive facts (e.g. Document A: "Category: SC", Document B: "Category: OBC"):
  - Engine emits `Status.FAIL` with reason `CONTRADICTION_DETECTED`.
- When evidence is partially unreadable or uncertain on one document:
  - Engine emits `Status.REVIEW` with reason `EVIDENCE_UNCERTAIN` or `EVIDENCE_AMBIGUOUS`.

**Audit Status:** APPROVED. Cross-document reasoning guarantees entity cohesion and prevents phantom corroboration.
