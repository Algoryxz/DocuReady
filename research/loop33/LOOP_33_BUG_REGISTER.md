# DOCUREADY — LOOP 33 DOMAIN RULE DEFECT & TECHNICAL DEBT REGISTER

**Milestone:** Loop 33 — Domain Rules & Decision Integrity  
**Component:** System-Wide Rules & Decision Engines  
**Evaluation Mode:** Independent Audit  
**Date:** 2026-11-25  

---

## 1. Executive Summary

During the comprehensive audit of DocuReady's 18 subsystems across all 8 rule families, four distinct domain rule observations, divergences, and technical debt items were systematically cataloged.

No critical regressions or false-verification vulnerabilities were discovered. The existing safety guardrails (Loop 27 identifier integrity, Loop 28 cross-document contradiction checks, and Loop 32 date/unit corrections) are operating as intended.

---

## 2. Defect Register

### RULE-033-001: Date Invariant Ambiguity Conservative Abstention on Identical Slash Strings
- **Subsystem:** `src/docuready/normalize/normalizer.py:compare_dates`
- **Severity:** Low (Behavioral Feature / Policy Intent)
- **Classification:** By-Design Conservative Policy
- **Description:** When comparing two identical ambiguous slash date strings (e.g. `'05/06/2024'` vs `'05/06/2024'`), `compare_dates` flags the format as ambiguous and returns `MatchGrade.AMBIGUOUS` with status `Status.REVIEW`. While raw character strings are identical, calendar semantics remain indeterminate without locale context (5 June 2024 vs 6 May 2024).
- **Remediation:** Retained as a deliberate conservative invariant. The engine must not convert typographic equality into calendar certainty across independent authorities.
- **Status:** Documented & Retained as Invariant.

---

### RULE-033-002: Hardcoded Procedural Citations vs Declarative Source Manifest
- **Subsystem:** `src/docuready/rules/validator.py:DocuReadyValidator`
- **Severity:** Low (Technical Debt)
- **Classification:** Architecture & Maintainability
- **Description:** The legacy procedural validator hardcodes citation strings (e.g., `"OSSP Guidelines 2024-25, Section 3.1 & NSP Common Framework"`) directly in Python finding constructors, rather than resolving them via the declarative source manifest (`packs/generic.demo/sources.yaml`).
- **Remediation:** Pure declarative scheme packs should be the primary vehicle for statutory citations.
- **Status:** Documented Technical Debt.

---

### RULE-033-003: Odisha Scheme Specific Rules Hardcoded as Global Defaults
- **Subsystem:** `src/docuready/rules/validator.py:SchemeConfig`
- **Severity:** Low (Configuration Coupling)
- **Classification:** Modular Architecture
- **Description:** `SchemeConfig` defaults `target_state` to `"ODISHA"` and `name` to `"Odisha Post-Matric Scholarship (SC/ST/OBC)"`, tightly binding the base configuration to one jurisdiction.
- **Remediation:** Declarative scheme pack loader injects jurisdiction parameters dynamically without hardcoded defaults.
- **Status:** Documented Architecture Observation.

---

### RULE-033-004: Income Tolerance Match Grade Divergence Between V1 and V2 Truth Tables
- **Subsystem:** `docuready.normalize.normalizer.compare_amounts` vs `outcome.resolver`
- **Severity:** Medium (Semantic Divergence)
- **Classification:** Engine Consistency
- **Description:** When declared income and certified income vary within a positive non-zero tolerance, the V1 procedural validator produced `PASS` with an informational note, whereas the V2 Section 6 truth table maps `MatchGrade.COMPATIBLE` to `Status.REVIEW`.
- **Remediation:** Standardized to the V2 truth table: variation within tolerance requires human officer review rather than automated unconditional clearance.
- **Status:** Standardized to V2 Conservative Truth Table.
