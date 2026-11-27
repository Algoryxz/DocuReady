# DocuReady Statutory Validation Engine (Architecture V2)

## Ownership & Contribution Responsibilities

| Role | Assignee | Primary Scope & Focus |
|---|---|---|
| **Primary Owner** | **Susmita** (Domain Rules & Evaluation Lead) | Deterministic rules engine, closed primitive registry, YAML pack schema, symmetric outcome resolution (`resolve_outcome`), statutory citations |
| **Supporting Contributor** | **Akriti** (Platform, Privacy & Delivery Lead) | Pipeline integration, execution performance, slot validation, injected time/clock abstraction |
| **Supporting Contributor** | **Deeptiman** (Product Owner & Integration Lead) | Citizen-facing finding explanations, remediation action clarity, status terminology |

### Detailed Responsibilities & Deliverables
- **Primary Owner (Susmita)**:
  - Architect and maintain the deterministic validation rule engine (`src/docuready/rules/engine.py`, `primitives.py`, `schema.py`, `loader.py`, `lint.py`) and YAML scheme packs (`packs/**`).
  - Maintain the canonical V2 outcome resolver (`src/docuready/outcome/resolver.py`) enforcing symmetric resolution (preventing both unsupported `PASS` and unsupported `FAIL` outcomes).
  - Own the statutory citation registries (`sources.yaml`) and per-rule/cross-pack regression suites.
- **Platform Contributor (Akriti)**:
  - Support high-performance rule execution, slot validation, and clock injection (`as_of`) for deterministic date testing.
- **Product Contributor (Deeptiman)**:
  - Review all citizen-facing finding explanations and remediation instructions for clarity and tone.

### Coordination & Review Gates
- Governed by [TEAM_RESPONSIBILITIES.md](../TEAM_RESPONSIBILITIES.md) and Gates G2/G3/G4.
- Legacy `DecisionSafetyLayer` (`src/docuready/outcome/safety_layer.py`) is retained solely as a compatibility shim; all V2 pack execution routes through `resolve_outcome()`.

---

## Design Mission

The DocuReady Validation Engine executes deterministic, data-driven, cross-document checks against extracted applicant packets using versioned YAML scheme packs over a closed primitive set.

1. **Rules are data; the engine is code.** Policy changes live in `packs/<pack_id>/pack.yaml` without arbitrary Python `eval`.
2. **Abstention is symmetric.** Uncertain or incomplete evidence can neither fail nor pass a rule.
3. **Every finding is traceable.** Findings link to observations, bounding boxes, page numbers, and `sources.yaml` entries.
4. **Deterministic and replayable.** All date-dependent rules consume an explicit injected `as_of: date` clock.

---

## Closed 9-Primitive Registry (`src/docuready/rules/primitives.py`)

| Primitive | Purpose | Fail-Closed / Uncertainty Behavior |
|---|---|---|
| `require_document` | Verifies mandatory document slot presence and minimum page count. | Absent/missing $\to$ `Raw.DOC_ABSENT`; `UNREADABLE`/`CORRUPTED` $\to$ `Raw.INDETERMINATE` / `UNCERTAIN`. |
| `field_present` | Verifies that required field(s) are extracted and non-empty across specified docs. | Absent/unreadable doc or missing/blank field $\to$ `Raw.INDETERMINATE` / `UNCERTAIN`. |
| `match_across` | Cross-document consistency (`grade=name \| date \| id \| text`). | Returns `MatchGrade` (`EXACT`, `COMPATIBLE`, `CONFLICT`, `AMBIGUOUS`) with weakest-evidence propagation. |
| `within_validity` | Validates document issue date against statutory validity window using `as_of`. | Unparseable/missing date $\to$ `Raw.INDETERMINATE` / `UNCERTAIN`. |
| `numeric_cap` | Evaluates numeric ceiling (`<= cap`). | Missing/unparseable value $\to$ `Raw.INDETERMINATE` / `UNCERTAIN`. |
| `numeric_consistency` | Evaluates numeric agreement across documents within tolerance. | Missing/unparseable value $\to$ `Raw.INDETERMINATE` / `UNCERTAIN`. |
| `age_on` | Evaluates `[min_age, max_age]` on `reference_date` (or injected `as_of`). | Missing/ambiguous DOB $\to$ `Raw.INDETERMINATE` / `UNCERTAIN`. |
| `enum_in` | Evaluates categorical field membership against allowed values. | Missing/empty value $\to$ `Raw.INDETERMINATE` / `UNCERTAIN`. |
| `legible` | Evaluates document-level OCR confidence against `min_confidence`. | Missing/unreadable doc $\to$ `Raw.INDETERMINATE` / `UNCERTAIN`. |

---

## Canonical V2 Outcome Resolution (`src/docuready/outcome/resolver.py`)

All rule evaluations emit a `Raw` outcome (`SATISFIED`, `VIOLATED`, `INDETERMINATE`, `DOC_ABSENT`, `EXEMPT`) paired with the weakest `EvidenceState` (`VERIFIED`, `PROVISIONAL`, `UNCERTAIN`) and optional `MatchGrade` (`EXACT`, `COMPATIBLE`, `CONFLICT`, `AMBIGUOUS`).

Transitional extractor states (`VERIFIED_TEXT`, `OCR_EXTRACTED`, `LOW_CONFIDENCE`, `AMBIGUOUS`, `NOT_FOUND`, `UNREADABLE`, `CONFLICTING`) are normalized fail-closed via `normalize_evidence_state()`.

| Raw | Weakest Evidence | Match Grade | Resolved `Status` | `ReasonCode` | Citizen Meaning |
|---|---|---|---|---|---|
| `DOC_ABSENT` | — | — | `MISSING` | `DOC_ABSENT` | Required document not supplied |
| `EXEMPT` | — | — | `NOT_APPLICABLE` | `EXEMPT:<REASON>` | Rule exempted for category |
| `INDETERMINATE` | any | — | `REVIEW` | `INSUFFICIENT_DATA` | Missing, unreadable, or ambiguous input |
| any | any | `AMBIGUOUS` | `REVIEW` | `EVIDENCE_UNCERTAIN` | Match is ambiguous; human check needed |
| `VIOLATED` | `VERIFIED` | `CONFLICT` / none | `FAIL` | `DEFECT_CONFIRMED` | Confirmed defect; fix before submitting |
| `VIOLATED` | `VERIFIED` | `COMPATIBLE` | `WARN` | `DEFECT_PROBABLE` | Compatible variation; check before relying |
| `VIOLATED` | `PROVISIONAL` | any (not `AMBIGUOUS`) | `WARN` | `DEFECT_PROBABLE` | Probable defect on provisional evidence |
| `VIOLATED` | `UNCERTAIN` | any | `REVIEW` | `EVIDENCE_UNCERTAIN` | Uncertain evidence; cannot confirm defect |
| `SATISFIED` | `VERIFIED` | `EXACT` / none | `PASS` | `CONFIRMED_OK` | No issue found on verified evidence |
| `SATISFIED` | `VERIFIED` | `COMPATIBLE` | `WARN` | `DEFECT_PROBABLE` | Compatible variation requires checking |
| `SATISFIED` | `PROVISIONAL` / `UNCERTAIN` | any | `REVIEW` | `CANNOT_CONFIRM` | Looks fine, but evidence too weak to pass |

### Additional Resolver Invariants
- **`MaxSeverity` Cap:** A rule's `max_severity` (`FAIL`, `WARN`, `REVIEW`) caps adverse statuses (`FAIL`/`WARN` downgraded to the cap with `ReasonCode.ADVISORY_RULE_CAP`), except structural `Raw.DOC_ABSENT` (`Status.MISSING`).
- **Packet Readiness (`Readiness`):**
  - `NOT_READY` if any finding is `Status.FAIL` or `Status.MISSING`.
  - `NEEDS_CHECKS` if any finding is `Status.WARN` or `Status.REVIEW`.
  - `NO_ISSUES_FOUND` otherwise.
- **CLI Exit Codes:** `0` (`NO_ISSUES_FOUND`), `1` (`NEEDS_CHECKS`), `2` (`NOT_READY`), `64` (usage/system error).
