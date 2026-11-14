# DocuReady Statutory Validation Engine

## Ownership & Contribution Responsibilities

| Role | Assignee | Primary Scope & Focus |
|---|---|---|
| **Primary Owner** | **Susmita** (Domain Rules & Evaluation Lead) | Deterministic rules engine, bipartite entity matching, statutory citations, decision safety firewall |
| **Supporting Contributor** | **Akriti** (Platform, Privacy & Delivery Lead) | Pipeline integration, execution performance, injected time/clock abstraction |
| **Supporting Contributor** | **Deeptiman** (Product Owner & Integration Lead) | Citizen-facing finding explanations, remediation action clarity, status terminology |

### Detailed Responsibilities & Deliverables
- **Primary Owner (Susmita)**:
  - Architect and maintain the deterministic validation rule set, bipartite fuzzy string matching, date arithmetic, and income ceiling verifications.
  - Own the statutory citation matrix, official gazette references, and rule pack YAML schema (`packs/`).
  - Implement and maintain the `DecisionSafetyLayer` firewall: enforce symmetric resolution (prevent both unsupported PASS and unsupported FAIL) and downgrade uncertain evidence to human `REVIEW`.
- **Platform Contributor (Akriti)**:
  - Support high-performance rule execution, slot validation, and clock injection (`frozen_time`) for deterministic date testing.
- **Product Contributor (Deeptiman)**:
  - Review all citizen-facing finding explanations and remediation instructions for clarity and tone.

### Coordination & Review Gates
- Any addition, deletion, or threshold adjustment of validation rules requires Susmita's authoritative approval.
- Governed by [TEAM_RESPONSIBILITIES.md](../TEAM_RESPONSIBILITIES.md) and Gates G2/G3.

---

## Design Mission

The DocuReady Validation Engine executes deterministic, legally grounded, cross-document checks against extracted applicant packets.

Unlike generic linter tools or black-box LLM prompts:
1. Every rule corresponds directly to an enacted Indian statutory guideline or government scholarship / welfare scheme criterion.
2. Every finding provides complete provenance, citing the governing order, exact clause, conflicting field values, and actionable remediation steps.
3. Every finding is passed through the **Evidence Safety Layer**, preventing false rejections caused by OCR or extraction uncertainty.

---

## The 10 Core Statutory Validation Rules

| Rule ID | Rule Name | Governing Order / Statutory Authority | Exact Clause Citation | Scope / Condition |
| :--- | :--- | :--- | :--- | :--- |
| **RULE-NAME-01** | Cross-Document Name Inconsistency | MoSJE Scheme Guidelines / e-District Standard | Section 4.2: Name matching across ID and qualifying certificates | All applicant documents must match phonetically and token-wise. Salutations excluded. |
| **RULE-DOB-01** | Date of Birth Conflict | Secondary Education Board & DoPT Guidelines | Rule 8: Verification of Age via Matriculation Certificate | DOB in 10th marksheet is authoritative; application form must match. |
| **RULE-INC-01** | Income Exceeds Scheme Ceiling | Post-Matric Scholarship Scheme (MoSJE / MoMA) | Clause 3.1: Family annual income ceiling $\le \text{Rs. } 2,50,000$ | Income certificate annual income $\le 2.50 \text{ Lakhs}$. |
| **RULE-INC-02** | Declared vs. Certified Income Mismatch | State Scholarship Portal Compliance Guidelines | Guideline 5.1: Self-declaration must reconcile with Tehsildar certificate | Form income declaration must not conflict with issued certificate. |
| **RULE-VAL-01** | Certificate Expired | State Revenue Department Manual (Income) | Section 12: Validity of Income Certificate is 1 financial year | Issue date must be within 12 months of application date. |
| **RULE-CAS-01** | Category / Caste Mismatch | Central / State Caste Reservation List | Article 341/342 & Scheme Rule 4: Category claim substantiation | Declared category (SC/ST/OBC/GEN) must match certified category. |
| **RULE-RES-01** | Domicile / State Mismatch | State Domicile & Residence Rules | Rule 2: State domicile quota eligibility requirement | State/District in Residence Certificate must match declared domicile. |
| **RULE-DOC-01** | Missing Mandatory Document | Mandatory Application Checklist | Clause 2.1: Requisite documents for scholarship admission | Income, Caste (if reserved), Marksheet, and Passbook are mandatory. |
| **RULE-BNK-01** | Bank Passbook Name Discrepancy | PFMS / DBT Direct Benefit Transfer Manual | Section 6: Direct Benefit Transfer Bank Account Seeding | Account holder name on passbook must match applicant name. |
| **RULE-ACA-01** | Academic Eligibility / Cutoff | Scheme Minimum Educational Requirement | Guideline 6.2: Minimum aggregate marks (SC/ST Candidates Exempt) | General $\ge 50\%$; SC/ST candidates explicitly exempt per statutory order. |

---

## Two-Phase Evaluation Architecture

```mermaid
flowchart TD
    subgraph Phase 1: Pure Statutory Evaluation
        InputFields[Normalized Cross-Document Fields] --> EvalRules[Execute Rules RULE-NAME-01 to RULE-ACA-01]
        EvalRules --> RawFindings[Generate Raw Findings: VIOLATION | WARNING | PASS]
    end

    subgraph Phase 2: Evidence-Gated Safety Downgrade
        RawFindings --> SafetyFilter[Inspect EvidenceState of Supporting Fields]
        SafetyFilter --> CheckState{Supporting Fields Status}
        CheckState -->|All VERIFIED| KeepViolation[Retain VIOLATION / BLOCKING]
        CheckState -->|Contains PROVISIONAL| DowngradeWarn[Downgrade to WARNING + Notice]
        CheckState -->|Contains UNCERTAIN| DowngradeReview[Downgrade to MANUAL_REVIEW]
    end

    KeepViolation --> ConsolidatedReport[Audit Report & Remediation Plan]
    DowngradeWarn --> ConsolidatedReport
    DowngradeReview --> ConsolidatedReport
```

---

## Detailed Safety Downgrade Matrix

The central innovation of the DocuReady Validation Engine is its refusal to issue a blocking rejection to an applicant when the underlying evidentiary tokens have low OCR certainty:

```python
def apply_safety_downgrades(raw_finding: ValidationFinding, packet: DocumentPacket) -> ValidationFinding:
    supporting_fields = get_supporting_fields_for_rule(raw_finding.rule_id, packet)
    states = [f.evidence_state for f in supporting_fields]

    if EvidenceState.UNCERTAIN in states:
        return raw_finding.downgrade(
            new_severity=FindingSeverity.REVIEW,
            reason="Degraded document evidence. Cannot confirm violation without human inspection."
        )
    elif EvidenceState.PROVISIONAL in states and raw_finding.severity == FindingSeverity.VIOLATION:
        return raw_finding.downgrade(
            new_severity=FindingSeverity.WARNING,
            reason="Extracted evidence is provisional. Please verify document scan quality."
        )
    return raw_finding
```

---

## Actionable Remediation Guidance

Every finding emitted by the engine includes:
- **`finding_id`**: Unique instance key.
- **`rule_id`**: Canonical rule reference.
- **`severity`**: `VIOLATION` (fatal submission blocker), `WARNING` (potential flaw), `REVIEW` (OCR unreadable / needs check).
- **`statutory_reference`**: Clause and Gazette / Ministry order number.
- **`conflicting_documents`**: Specific document IDs and pages containing the conflict.
- **`remediation_action`**: Clear, plain-language instructions explaining how the applicant can resolve the issue (e.g., *"Obtain a revised Income Certificate from the Tehsildar office reflecting current fiscal year income"*).
