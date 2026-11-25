# DOCUREADY — LOOP 33 CONFIDENCE & ABSTENTION POLICY AUDIT (FAMILY G)

**Milestone:** Loop 33 — Domain Rules & Decision Integrity  
**Component:** `src/docuready/outcome/safety_layer.py`, `src/docuready/outcome/resolver.py`  
**Operating Thresholds:** $T^* = 70.0$, $T_{\text{fuzzy}} = 75.0$  
**Evaluation Date:** 2026-11-25  

---

## 1. Scope & Objectives

Rule Family G governs confidence score qualification, evidence calibration, and fail-safe abstention policies:
- **Operating Threshold $T^* = 70.0$:** Evidence with confidence $< 70.0$ cannot achieve `EvidenceState.VERIFIED`.
- **Fuzzy Threshold $T_{\text{fuzzy}} = 75.0$:** String and demographic matching require similarity $\ge 75.0$ to qualify as compatible match.
- **Fail-Safe Abstention:** Any rule with uncertain, uncorroborated, or ambiguous evidence must abstain (`Status.REVIEW`) rather than trigger an unsupported statutory rejection (`FAIL`) or clearance (`PASS`).
- **Weakest-Evidence Propagation:** In composite evidentiary chains, the outcome inherits the confidence of the weakest link.

---

## 2. Invariant Analysis & Confidence Semantics

### 2.1 The V2 Section 6 Truth Table
`resolve_outcome()` in `src/docuready/outcome/resolver.py`:
- `Raw.PASS` + `EvidenceState.VERIFIED` $\to$ `Status.PASS`
- `Raw.PASS` + `EvidenceState.AMBIGUOUS` $\to$ `Status.REVIEW` (`EVIDENCE_AMBIGUOUS`)
- `Raw.PASS` + `EvidenceState.UNCERTAIN` $\to$ `Status.REVIEW` (`EVIDENCE_UNCERTAIN`)
- `Raw.VIOLATED` + `EvidenceState.VERIFIED` $\to$ `Status.FAIL`
- `Raw.VIOLATED` + `EvidenceState.AMBIGUOUS` $\to$ `Status.REVIEW` (`EVIDENCE_AMBIGUOUS`) [unless decision-invariant]
- `Raw.VIOLATED` + `EvidenceState.UNCERTAIN` $\to$ `Status.REVIEW` (`EVIDENCE_UNCERTAIN`)
- `Raw.DOC_ABSENT` $\to$ `Status.MISSING` (`DOC_ABSENT`)
- `Raw.EXEMPT` $\to$ `Status.NOT_APPLICABLE` (`CATEGORY_EXEMPTION`)

### 2.2 Decision Safety Layer Guardrails
`DecisionSafetyLayer` strictly enforces:
- **No unsupported PASS on missing/unreadable evidence** (Invariant 1).
- **No unsupported FAIL on ambiguous evidence** (Invariant 2).
- **Single-source verification bar** (Invariant 4): statutory claims require corroboration.
- **Confidence floor enforcement** (Invariant 7): confidence $< T^*$ forces `REVIEW`.

**Audit Status:** APPROVED. Family G rules strictly maintain the fail-safe boundary and prevent false positive clearances.
