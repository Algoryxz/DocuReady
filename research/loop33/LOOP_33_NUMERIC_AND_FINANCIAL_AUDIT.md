# DOCUREADY — LOOP 33 NUMERIC & FINANCIAL RULES AUDIT (FAMILY C)

**Milestone:** Loop 33 — Domain Rules & Decision Integrity  
**Component:** `src/docuready/normalize/normalizer.py`, `src/docuready/rules/validator.py`, `src/docuready/evidence/cross_document.py`  
**Operating Thresholds:** $T^* = 70.0$, $T_{\text{fuzzy}} = 75.0$  
**Evaluation Date:** 2026-11-25  

---

## 1. Scope & Objectives

Rule Family C governs quantitative, financial, and metric comparisons:
- **Income Ceiling Compliance (`RULE-INC-01`):** Statutory ceiling check (e.g. $\le 250,000$ INR under Post-Matric Scholarship guidelines).
- **Cross-Document Income Declaration Match (`RULE-INC-02`, `RULE-INC-03`):** Reconciliation between Application Form declared income and Income Certificate certified income.
- **Academic Cutoff & Relaxations (`RULE-MRK-01`):** Percentage score compliance and category relaxation policies (`PASS_ONLY`, `RELAXED_50`, `STRICT`).
- **Financial Format Normalization:** Parsing Lakhs/Crores, commas in Indian numbering system (`1,50,000`), decimals, and currency tokens (`₹`, `Rs.`).
- **Physical Unit Equivalence vs Evidence Policy:** Handling metric conversions (`1 MT == 1000 KG`) while maintaining evidence policy boundaries.

---

## 2. Invariant Analysis & Metric Handling

### 2.1 Currency & Number Parsing
`parse_amount_inr()` extracts numeric values from Indian textual amounts:
- Formats handled: `Rs. 2,50,000.00`, `2.5 Lakhs`, `250000`, `INR 1,20,000/-`.
- Indian number grouping (1,00,000 = 1 Lakh) is correctly normalized without truncation.
- Invalid or unparseable amount strings return `None` and fail closed to `UNKNOWN`/`REVIEW`.

### 2.2 Income Ceiling & Tolerance Policy
- `RULE-INC-01` strictly checks `certified_income <= income_ceiling`. Any amount exceeding the ceiling produces statutory `FAIL`.
- `RULE-INC-02` compares declared vs certified income. Default tolerance is 0.0 INR (zero tolerance). When declared income differs from certified income by more than `income_tolerance`, the rule emits a discrepancy finding.

### 2.3 Decoupling Physical Equivalence from Evidence Policy (BUG-032-003 Resolution)
A key architectural principle reinforced in Loop 32 closeout and audited here:
- **Physical Equivalence:** Physical metric conversions (e.g., `1 MT = 1000 KG`) are mathematically valid equations.
- **Evidence Policy Conflict:** In statutory compliance verification, declaring "1 Metric Ton" when a certificate requires "1000 Kilograms" requires documentary equivalence or approved conversion schedules.
- `evaluate_semantic_claim_equivalence()` recognizes mathematical identity, but marks evidence compliance policy conflicts when scheme rules mandate explicit unit congruence.

### 2.4 Academic Cutoffs & Category Relaxations
- `min_academic_percentage`: 50.0% standard.
- SC/ST cutoff policy:
  - `PASS_ONLY`: Any passing grade $\ge 33\%$ qualifies reserved category applicants under statutory guidelines (Ministry of Social Justice & Empowerment).
  - `RELAXED_50`: Requires 50% for reserved, 60% for general.
  - `STRICT`: Equal cutoff across all categories.

**Audit Status:** APPROVED. Family C enforces strict arithmetic bounds with category relaxations and clear unit decoupling.
