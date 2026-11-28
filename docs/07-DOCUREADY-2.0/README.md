# DocuReady 2.0 — Documentation Baseline

**Repository:** `Algoryxz/DocuReady` (Previous baseline: `9717ae5`)
**Updated Base `origin/main` SHA:** `9e2b4cf84c8cc0b562dad5de317d44ce23da0783` (PR #99 merged)
**Status:** Loop 0 — Shared Team Execution Baseline (PRs #94–#99 merged)

---

## Navigation

| Document | Purpose |
| :--- | :--- |
| [PRODUCT_BRIEF.md](PRODUCT_BRIEF.md) | Vision, target users, product boundaries, 10-feature classification, and 24-hour vertical slice scope |
| [BASELINE_AUDIT.md](BASELINE_AUDIT.md) | Forensic inventory of implemented, partial, missing, and unverified capabilities, CI/CD, security, and doc contradictions |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Actual system architecture and data flow across Electron, Preload/IPC, React/PDF.js, and Python Sidecar |
| [API_AND_DATA_CONTRACTS.md](API_AND_DATA_CONTRACTS.md) | Shared interface contracts for Sidecar JSON-RPC, Electron IPC, Evidence/Findings, Coordinates, Replacement, Annotations, and Export |
| [TEAM_WORKSTREAMS.md](TEAM_WORKSTREAMS.md) | Four-person ownership, branch names, file boundaries, and dependency order |
| [24H_EXECUTION_PLAN.md](24H_EXECUTION_PLAN.md) | 24-hour execution timeline, milestones, and deliverables |
| [ACCEPTANCE_CRITERIA.md](ACCEPTANCE_CRITERIA.md) | Functional, security, reliability, test matrix, and final demonstration criteria |
| [DECISIONS.md](DECISIONS.md) | Accepted decisions, rejected ideas, and unresolved questions/blockers |
| [STATUS.md](STATUS.md) | Live task owner, branch, PR, state, blockers, and verification evidence |

---

## Target Experience (DocuReady 2.0 Vertical Slice)

> **Guided Application Workspace → Document Intelligence → Evidence Review → Correct → Re-audit → Redacted Report**

## Non-Negotiable Baseline Rules

1. **Offline-first & privacy-preserving:** Local document processing; zero cloud OCR or cloud storage; default PII redaction on exports and logs; conservative abstention (`REVIEW` / `UNCERTAIN`) over false `PASS` or false `FAIL`.
2. **Human review never mutates engine verdicts:** Session-level human annotations and review acknowledgements are advisory metadata only; they must never silently overwrite `PASS`/`FAIL`/`REVIEW` outcomes.
3. **Ephemeral session handling:** Do not persist sensitive citizen documents or create a local document history without an explicit retention, deletion, and security design.
4. **No new dependencies without necessity & licence review:** PyMuPDF (`AGPLv3`) legal clearance remains an open release blocker (`LICENSING_DECISION.md`).
5. **Respect merged PRs #94–#99 & frozen artifacts:** PRs #94–#99 are merged in `9e2b4cf`; preserve historical Loop 10 release artifacts and historical loop reports.
