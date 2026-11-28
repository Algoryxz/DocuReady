# DocuReady — Team Responsibilities and PRD/TRD Ownership

> [!NOTE]
> **DocuReady 2.0 Update (28 Nov 2026):** For the active DocuReady 2.0 & Windows Release Plan, team ownership is split across four contributors — **Akriti** (PR #95, Testing & Quality, `feat/pr95-akriti`), **Susmita** (Backend & Document Intelligence, `feat/backend-susmita`), **Project frontend owner** (Frontend & Electron, `feat/frontend-electron`), and **Deepti** (CI/CD via PR #94 `fix/ci-verification-stabilisation` / `fix/ci-cd-deepti`, then Frontend & QA collaboration). See the canonical ownership matrix in [docs/07-DOCUREADY-2.0/TEAM_WORKSTREAMS.md](07-DOCUREADY-2.0/TEAM_WORKSTREAMS.md).

**Version:** 1.0 · **Date:** 14 November 2026
**Repository:** `Algoryxz/DocuReady`
**Purpose:** Give Deeptiman, Akriti and Susmita a clear division of responsibilities so each person's ChatGPT/Antigravity workspace can understand the product, the assigned documents, the implementation boundaries and the review path.

> This is a proposed ownership split for the team to adopt. It assigns work by project area, not by an assumption about anyone's prior experience. The team can agree to adjust ownership before a task starts, but one task must always have one named primary owner.

---

## 1. Team structure at a glance

| Person | Primary role | Owns | Main project area |
|---|---|---|---|
| **Deeptiman** | Product owner and integration lead | PRD, product positioning, scope, public claims, end-to-end acceptance and release decisions | What DocuReady does, who it serves, what it must never claim, and whether a task meets the product contract |
| **Akriti** | Platform, privacy and delivery lead | Platform/infrastructure TRD, packaging, CI, OCR/PDF integration, runtime privacy, deployment and UI technical safeguards | How the application runs safely, reproducibly and privately |
| **Susmita** | Domain rules, evidence and evaluation lead | Validation/evidence TRD, scheme rules and source registry, matching semantics, rule-pack engine and evaluation | What the engine checks, how evidence is interpreted, where rules come from and how correctness is measured |

### Shared principles

- Each task has one primary owner who prepares the implementation and its tests.
- The other two contribute through review or a defined dependency; do not create two competing implementations of the same task.
- Deeptiman is the final product/gate acceptance owner. Technical review still needs evidence from the relevant owner and at least one non-author reviewer.
- Ownership does not grant permission to change another person's interface or contract unilaterally. Propose an RFC/ADR and agree the interface first.
- All team members follow `ARCHITECTURE_V2.md`, `BACKLOG.md`, the claims register, and the current `STATUS.md`.

## 2. PRD ownership — product requirements

PRD means *what the product should do and why*. Deeptiman is the primary owner of the PRD set. Akriti and Susmita contribute requirements from their technical/domain areas.

| Existing PRD/document | Primary owner | Contributors | Responsibility |
|---|---|---|---|
| `docs/01-PRODUCT/PROBLEM_STATEMENT.md` | Deeptiman | Susmita, Akriti | Define the applicant problem accurately; distinguish document inconsistency from eligibility decisions. |
| `docs/01-PRODUCT/PRODUCT_OVERVIEW.md` | Deeptiman | Akriti, Susmita | State the product purpose, user flow, boundaries and intended outcomes. |
| `docs/01-PRODUCT/PRODUCT_SCOPE.md` | Deeptiman | Akriti, Susmita | Define MVP scope, non-goals, exclusions and feature priority. |
| `docs/01-PRODUCT/TARGET_USERS.md` | Deeptiman | Susmita | Define applicants, student users and assisted-service operators without unsupported demographic claims. |
| `docs/01-PRODUCT/COMPETITIVE_POSITIONING.md` | Deeptiman | Susmita | Maintain the applicant-side preparation-aid position and evidence-backed differentiators. |
| `README.md` and `docs/CLAIMS_REGISTER.md` | Deeptiman | Akriti, Susmita | Ensure public claims are sourced, softened or removed; label synthetic results beside every table. |
| `docs/06-ROADMAP/PRODUCT_ROADMAP.md` | Deeptiman | Akriti, Susmita | Keep product milestones aligned to gates and actual technical feasibility. |

### PRD decisions Deeptiman must protect

1. DocuReady is an applicant-side preparation aid, not an eligibility decision, sanctioning authority or government portal.
2. It checks consistency across supplied documents and published document requirements, then explains defects and remediation.
3. It does not promise acceptance, eligibility, legal compliance or guaranteed rejection avoidance.
4. “No issues found” means only that the configured checks found no issue on the supplied evidence. It never means “approved” or “ready to submit”.
5. Claims such as applicant totals, rejection rates, accuracy, ECE, speed and privacy guarantees require entries in the claims register and credible evidence.

### PRD contributions expected from Akriti

- State measurable non-functional requirements: local runtime behaviour, network restrictions, memory/temp-file lifecycle, supported OS/Python versions, dependency constraints, accessibility and operational limitations.
- Translate privacy and security requirements into product acceptance criteria that can be tested.
- Flag product promises that the current platform cannot demonstrate.

### PRD contributions expected from Susmita

- Define document types/slots, required fields, user-visible defect categories, ambiguity cases and remediation expectations.
- Identify where scheme-specific requirements vary and must not be generalized.
- Review wording so the product describes document checks and does not imply eligibility or authenticity verification.

## 3. TRD ownership — technical requirements and design

TRD means *how the system is designed, implemented, integrated and verified*. The TRD is deliberately split by technical boundary.

| Existing TRD/document | Primary owner | Contributors | Responsibility |
|---|---|---|---|
| `docs/02-ARCHITECTURE/SYSTEM_ARCHITECTURE.md` | Akriti | Susmita, Deeptiman | Runtime components, module boundaries, deployment model and system-level data flow. |
| `docs/02-ARCHITECTURE/DATA_FLOW.md` | Akriti | Susmita | Intake-to-report lifecycle, temporary storage and trust boundaries. |
| `docs/02-ARCHITECTURE/EXTRACTION_PIPELINE.md` | Akriti | Susmita | PDF parsing, extraction orchestration, provenance and error handling. |
| `docs/02-ARCHITECTURE/OCR_ARCHITECTURE.md` | Akriti | Susmita | Tesseract integration, language packs, OCR fallback and engine manifest. |
| `docs/02-ARCHITECTURE/SECURITY_AND_PRIVACY.md` | Akriti | Deeptiman | No-network runtime, file limits, temp cleanup, telemetry, redaction and safe logging. |
| `docs/02-ARCHITECTURE/EVIDENCE_PROVENANCE.md` | Susmita | Akriti | Observation model, confidence states, provenance semantics and evidence traceability. |
| `docs/02-ARCHITECTURE/VALIDATION_ENGINE.md` | Susmita | Akriti, Deeptiman | Rules, matching, resolver contracts, reason codes, pack schema and deterministic outcomes. |
| `docs/06-ROADMAP/TECHNICAL_ROADMAP.md` | Akriti | Susmita | Technical milestones, dependency order and platform risks, aligned to gates. |
| `docs/ARCHITECTURE_V2.md` and ADR register | Deeptiman (decision owner) | Akriti, Susmita | Cross-cutting target contract and architectural decision acceptance. Technical sections are authored by the relevant owner. |
| `packs/**`, `sources.yaml`, `docs/CITATION_AUDIT.md` | Susmita | Deeptiman | Rule parameters, primary sources, review state, scheme applicability and pack lifecycle. |
| `eval/**`, `docs/REAL_SAMPLE_PROTOCOL.md` | Susmita | Akriti, Deeptiman | Split integrity, synthetic generator, false-pass evaluation, confidence intervals and sample governance. |
| `pyproject.toml`, CI workflows, Docker and SBOM files | Akriti | Susmita | Dependencies, licences in NOTICE, reproducible builds, test matrix and supply-chain controls. |

## 4. Backlog task ownership

The following assigns one primary owner to each V2 backlog item. It does not change task dependencies or acceptance criteria. For T0.1, the named owner coordinates the audit while the other two provide the specific evidence listed.

| Task | Primary owner | Supporting responsibility |
|---|---|---|
| T0.1 — Characterise current behaviour | **Deeptiman** | Akriti: CI/path canonicalization and code inventory. Susmita: rule IDs, citations and validation thresholds. Deeptiman accepts the audit. |
| T0.2 — CI that exercises OCR | **Akriti** | Susmita confirms language-specific OCR cases; Deeptiman accepts evidence and README claim changes. |
| T0.3 — Package contract verification (updated; migration already merged) | **Akriti** | Susmita checks rule/data import compatibility; Deeptiman confirms no behaviour drift. |
| T1.1 — Claims register and honest-claims pass | **Deeptiman** | Akriti verifies engineering claims; Susmita verifies rule/source and evaluation claims. |
| T1.2 — Telemetry off and no-network contract | **Akriti** | Susmita supplies full-pipeline and replacement test scenarios; Deeptiman accepts privacy language. |
| T1.3 — PDF backend interface/licence decision | **Akriti** | Susmita evaluates extraction/bbox and false-pass differences; Deeptiman reviews ADR and trade-off. |
| T1.4 — Redaction and safe logging | **Akriti** | Susmita identifies fields/values requiring safe treatment; Deeptiman accepts user-facing behaviour. |
| T1.5 — Citation audit and `sources.yaml` | **Susmita** | Deeptiman reviews citizen-facing wording; Akriti checks loader/metadata feasibility. |
| T2.1 — Status vocabulary and symmetric resolver | **Susmita** | Deeptiman owns product semantics/acceptance; Akriti integrates UI/CLI and status vocabulary. |
| T2.2 — Per-rule test matrix | **Susmita** | Akriti supports test infrastructure; Deeptiman reviews expected citizen meaning. |
| T2.3 — Match grades and injected clock | **Susmita** | Akriti supports pipeline/time injection; Deeptiman accepts compatibility and ambiguity language. |
| T2.4 — Slot validation | **Akriti** | Susmita defines slot anchors and expected ambiguous outcomes; Deeptiman reviews user flow. |
| T3.1 — Pack schema, loader and lint | **Susmita** | Akriti implements packaging/CI integration; Deeptiman approves lifecycle/governance. |
| T3.2 — Primitives and `generic.demo` port | **Susmita** | Akriti reviews engine interfaces/performance; Deeptiman accepts equivalence and scope. |
| T3.3 — `odisha.subhadra` demo snapshot | **Susmita** | Akriti: Evidence-matrix reviewer (reviews source traceability, verification states, pack schema compatibility, primitive contracts, and implementation implications); Deeptiman: Product Owner (reviews citizen-facing boundaries and gate sign-off). **Mandatory Governance Gate:** T3.3 implementation changes are blocked until Akriti has reviewed and explicitly agreed to the parameter-level source-verification matrix. |
| T3.4 — Report v2 | **Deeptiman** | Susmita validates findings/citations; Akriti implements renderer, redaction and schema integration. |
| T4.1 — Evaluation harness v2 | **Susmita** | Akriti provides CI reproducibility; Deeptiman signs off public metric wording. |
| T4.2 — Indic OCR and numerals | **Akriti** | Susmita defines cross-script ambiguity policy and evaluation; Deeptiman approves limitations. |
| T4.3 — Generator v2 | **Susmita** | Akriti supports reproducibility and CI; Deeptiman reviews data labelling. |
| T4.4 — Real-sample protocol | **Susmita** | Deeptiman approves consent and public-claims wording; Akriti reviews storage/access controls. |
| T5.1 — Container | **Akriti** | Susmita supplies demo pack fixtures; Deeptiman approves user-facing setup/limitations. |
| T5.2 — Supply chain | **Akriti** | Susmita checks runtime package needs; Deeptiman approves release-risk policy. |
| T5.3 — Release | **Deeptiman** | Akriti supplies build/SBOM evidence; Susmita supplies pack/evaluation evidence. |

### T3.3 Mandatory Evidence Gate & Governance Workflow

Per governance agreement between Susmita (Owner) and Akriti (Reviewer), T3.3 follows a strict five-stage evidence gate:

1. **Stage 1 — Source Verification:** Susmita prepares the complete parameter-level evidence matrix (`docs/04-VALIDATION/SUBHADRA_SOURCE_VERIFICATION_MATRIX.md`).
2. **Stage 2 — Review Submission:** Susmita shares the completed matrix with Akriti.
3. **Stage 3 — Evidence and Contract Review:** Akriti reviews official source URLs, document dates, retrieval dates, exact statutory clauses/printed pages, supporting wording, verification states, pack schema compatibility, primitive contracts, evidence-state behavior, severity and FAIL-capability implications, and proposed implementation boundaries.
4. **Stage 4 — Explicit Agreement:** **T3.3 implementation changes are blocked until Akriti has reviewed and explicitly agreed to the parameter-level source-verification matrix.** Silence, test results, preliminary comments, or an agent's GO recommendation do not constitute approval.
5. **Stage 5 — Implementation Authorization:** Only after explicit agreement may the team coordinate pack implementation, synthetic packet testing, evaluation updates, and report integration.

## 5. Track ownership and current handoff

| Work | Primary person | What the owner must deliver | What must not be assumed |
|---|---|---|---|
| Track A — PR #3, UI/privacy | **Akriti** | Actual upload/replacement lifecycle tests, committed Streamlit telemetry config, precise session cleanup, PII redaction tests, escaped rendering tests and V2-compliant labels. | The PR description is not proof that the config was committed or every privacy property is tested. |
| Track B — PR #2, decision safety | **Susmita** | Explicit evidence-state mapping, provenance tests, cross-doc rules, correct V2 status mapping, structured source-verification semantics and property/per-rule tests. | Evidence provenance is not source verification; a passing local test count is not remote CI acceptance. |
| Product contract and gate acceptance | **Deeptiman** | Product requirements, claims register, acceptance decisions, review of user-facing status language and release sign-off. | Product approval does not replace technical evidence or source verification. |

Track A and Track B remain separate implementation branches/PRs. They should not be combined into one large PR. Resolve the baseline CI issue first, then review and integrate each with its own handoff packet and green CI.

## 6. Working agreement for ChatGPT and Antigravity per teammate

Every person should paste the relevant part of this file into their own project/chat context and include the architecture, backlog, current status and their assigned task.

### Deeptiman's workspace

- Act as product owner and integration decision-maker.
- Maintain the PRD, claims register, public positioning and gate decisions.
- Ask for evidence: exact files, tests, output, branch/PR and commit SHA.
- Reject unsupported claims, unreviewed golden changes and unverified scheme rules.
- Do not ask Antigravity to edit or merge unrelated work while a bounded task is under review.

### Akriti's workspace

- Act within platform, privacy, packaging, OCR/PDF and delivery scope.
- Read the full task acceptance criteria and relevant TRD documents before implementation.
- Add tests for real production helpers, not tests that merely repeat the intended implementation in isolation.
- Record direct and transitive dependency licences and runtime versions.
- Raise an interface proposal before changing Susmita's rule semantics or Deeptiman's product contract.

### Susmita's workspace

- Act within domain rules, evidence semantics, scheme packs, matching and evaluation scope.
- Use primary sources for scheme requirements; never paraphrase law from memory.
- Mark sources `UNVERIFIED` where source evidence is unavailable; do not invent clauses, dates, caps or exemptions.
- Keep observation confidence, match grade and source verification separate.
- Raise an interface proposal before changing Akriti's ingestion/provenance contract or Deeptiman's public positioning.

### Shared implementation protocol

1. Read the assigned task and its dependencies in `BACKLOG.md`.
2. Confirm the current `main` and working-tree state before editing.
3. Implement one task on one branch and one PR.
4. Add/update tests with the behaviour change; never alter golden snapshots casually.
5. Return the handoff packet in the backlog format with evidence for each acceptance criterion.
6. Wait for explicit acceptance before starting the next task or merging.
7. Update `docs/STATUS.md` only with verified current facts.

## 7. Review and decision rules

- **Author:** implementation, tests, local reproduction, handoff packet.
- **Relevant second owner:** technical/domain review outside the author's own area.
- **Deeptiman:** product, safety-language and gate acceptance.
- **Merge:** only after required acceptance, all required CI checks green and no unresolved blocking review threads. Antigravity may create branches, commit, push and open PRs as instructed by the team; it must not merge on its own unless Deeptiman explicitly authorizes that task.
- **No direct edits to `main`, no force-push, no unreviewed golden regeneration, no real personal data.**

## 8. Definition of a complete task handoff

```text
Task: <ID>   Owner: <person>   Branch: <name>   PR: <URL>   Commit(s): <hashes>
Summary: <3–5 lines>
Files changed: <list>
Tests: <exact command> → <output tail and pass/fail/skip counts>
Acceptance criteria: <each criterion → PASS / FAIL / UNVERIFIED + evidence>
CI: <workflow/job links and final conclusions>
Deviations from spec: <none | list with reason>
Open questions / risks: <list>
Next task: <only the next dependency-approved task>
```
