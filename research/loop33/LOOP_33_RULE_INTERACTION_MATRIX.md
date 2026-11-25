# DOCUREADY — LOOP 33 RULE INTERACTION MATRIX & EXECUTION LIFECYCLE (FAMILY H)

**Milestone:** Loop 33 — Domain Rules & Decision Integrity  
**Component:** System-wide Orchestration, `DecisionSafetyLayer`, `PackExecutionEngine`  
**Operating Thresholds:** $T^* = 70.0$, $T_{\text{fuzzy}} = 75.0$  
**Evaluation Date:** 2026-11-25  

---

## 1. Pipeline Execution Lifecycle

The DocuReady validation engine executes through 8 strictly sequential stages:

```
[Stage 1: Document Ingestion & Artifact Hashing]
       │
       ▼
[Stage 2: Document Slot Classification & Mismatch Quarantine]
       │
       ▼
[Stage 3: OCR & Native Extraction Pipeline]
       │
       ▼
[Stage 4: Normalization & Canonicalization (ISO Dates, Amounts, IDs)]
       │
       ▼
[Stage 5: Rule Execution (Procedural / Declarative Scheme Packs)]
       │
       ▼
[Stage 6: Cross-Document Entity Resolution & Contradiction Detection]
       │
       ▼
[Stage 7: Decision Safety Layer (10 Invariants Enforcement)]
       │
       ▼
[Stage 8: Final Outcome Resolution & Finding Report Generation]
```

---

## 2. Rule Interaction Matrix

The table below documents how rule families interact and which rule takes precedence during conflicting or overlapping evaluations:

| Interacting Rule Families | Interaction Scenario | Precedence / Resolution Policy | Invariant Applied |
| :--- | :--- | :--- | :---: |
| **Family D (Slot) $\times$ Family F (Completeness)** | Document uploaded to wrong slot (e.g. Caste in Income slot) | Slot mismatch quarantines document; Mandatory Income doc treated as MISSING | Invariant 6 |
| **Family D (Slot) $\times$ Family C (Income Ceiling)** | Invalid document in Income slot | Child field extraction returns None; Income ceiling check bypassed | Invariant 6 |
| **Family A (Identifier) $\times$ Family G (Abstention)** | Confusable glyphs in IFSC (`SBINO...`) | Strict regex fails; Confusable regex flags ambiguity $\to$ abstain REVIEW | Invariant 7 |
| **Family B (Date) $\times$ Family G (Abstention)** | Ambiguous slash date (`05/06/2024`) on expiration check | Safety layer evaluates both candidates; PASS only if both pass | Invariant 3 |
| **Family B (Date) $\times$ Family E (Cross-Doc DOB)** | DOB mismatch between Form and Marksheet | High School marksheet authoritative; If one uncertain $\to$ REVIEW | Invariant 2 |
| **Family C (Numeric) $\times$ Family E (Cross-Doc Equiv)** | Metric unit difference (`1 MT` vs `1000 KG`) | Mathematical equivalence acknowledged; Evidence policy requires conversion proof | Invariant 9 |
| **Family F (Scheme) $\times$ Family C (Academic Cutoff)** | SC/ST category applicant scoring 45% | Category relaxation applied (`PASS_ONLY` policy) $\to$ PASS | Invariant 8 |
| **Family F (Scheme) $\times$ Family D (Completeness)** | General category applicant missing Caste cert | Category exemption applied $\to$ `NOT_APPLICABLE`, zero penalty | Invariant 8 |

---

## 3. Deadlock & Order Independence Guarantee
1. **Purity:** All rule primitives are pure functions of `(document_packet, execution_context)`. No rule mutates packet state.
2. **Order Independence:** The final finding set is identical regardless of the order in which individual rules in Stage 5 are evaluated.
3. **Fail-Closed Convergence:** In any conflict between a permissive rule and a conservative safety invariant, the safety invariant dominates.

**Audit Status:** APPROVED. The rule interaction lifecycle is deterministic, deadlock-free, and fail-closed.
