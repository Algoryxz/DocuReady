# DocuReady 2.0 — Documentation Baseline

**Repository:** `Algoryxz/DocuReady`  
**Verified Base `origin/main` SHA:** `9717ae56b3e672d0c6046ea4a918794db1cf1368`  
**Branch:** `docs/docuready-2.0-kickoff-baseline`  
**Status:** Loop 0 — Shared Team Execution Baseline

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
5. **Respect PR #94 & frozen artifacts:** Deeptiman owns CI recovery PR #94 (`fix/ci-verification-stabilisation`); do not overwrite his branch or modify frozen Loop 10 release artifacts or historical loop reports.
