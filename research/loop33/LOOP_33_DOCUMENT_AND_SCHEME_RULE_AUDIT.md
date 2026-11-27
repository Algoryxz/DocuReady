# DOCUREADY — LOOP 33 DOCUMENT & SCHEME PACK RULES AUDIT (FAMILY F)

**Milestone:** Loop 33 — Domain Rules & Decision Integrity  
**Component:** `packs/generic.demo/pack.yaml`, `src/docuready/rules/engine.py`, `src/docuready/rules/validator.py`  
**Operating Thresholds:** $T^* = 70.0$, $T_{\text{fuzzy}} = 75.0$  
**Evaluation Date:** 2026-11-25  

---

## 1. Scope & Objectives

Rule Family F governs document completeness, slot requirements, scheme eligibility, and category exemptions:
- **Mandatory Document Completeness (`RULE-DOC-01`):** Enforcing the presence of mandatory certificates (Income, Caste, Residence, Marksheet, Passbook, Application Form).
- **Legibility & Quality Requirements (`RULE-DOC-02`):** Ensuring minimum upload quality standards.
- **State Domicile Requirements (`RULE-DOM-01`):** Validating domicile against scheme target jurisdiction (e.g. ODISHA).
- **Category-Based Exemptions (`EXEMPT` / `NOT_APPLICABLE`):** Handling rules that do not apply to certain applicant categories (e.g., General category applicants exempt from Caste Certificate submission).

---

## 2. Invariant Analysis & Scheme Execution

### 2.1 Declarative Pack Engine Architecture
`PackExecutionEngine` in `src/docuready/rules/engine.py`:
- Pure Python execution of 9 closed primitives (zero `eval`/`exec`).
- Explicit clock boundary (`as_of`).
- Weakest-evidence propagation via `weakest_evidence()`.
- Category exemption tri-state: `EXEMPT`, `NOT_EXEMPT`, `UNCERTAIN`.

### 2.2 Category Exemption Handling (Safety Invariant 8)
- If an applicant belongs to the General category, rules requiring Caste Certificate (`caste_certificate`) evaluate to `ExemptionVerdict.EXEMPT`.
- Outcome resolver returns `Status.NOT_APPLICABLE` with `ReasonCode.EXEMPT:CATEGORY_EXEMPTION`.
- **Safety Invariant:** Exempt rules are never recorded as `Status.FAIL` or penalized.

### 2.3 Statutory vs Operational Rule Grounding
- **Statutory Rules:** `RULE-DOC-01` (Mandatory docs under Post-Matric Guidelines §7), `RULE-INC-01` (Ceiling under §3.1), `RULE-DOB-01` (CBSE Rule 69.2).
- **Operational Heuristics:** `RULE-DOC-02` (0.60 OCR confidence threshold), `RULE-FLD-01` (Application schema check), `RULE-DOM-01` (State domicile string check).

**Audit Status:** APPROVED. Family F correctly separates statutory mandates from operational guidelines and protects category exemptions.
