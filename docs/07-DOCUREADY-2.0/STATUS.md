# DocuReady 2.0 — Status Tracker

**Last Updated:** 28 November 2026  
**Verified `origin/main` SHA:** `9717ae56b3e672d0c6046ea4a918794db1cf1368`  
**Historical Gate Status:** See [../STATUS.md](../STATUS.md) for Loop 1–47 / Gate G0–G5 records.

---

## Active Workstreams

| Workstream | Owner | Branch | PR | State | Blockers / Notes |
|---|---|---|---|---|---|
| **Loop 0 — Docs & Baseline** | Team | `docs/docuready-2.0-kickoff-baseline` | Pending PR | `in_review` | Reconciled baseline & Windows release plan; must merge to `main` as shared starting point. |
| **CI/CD → Frontend & QA** | Deepti | `fix/ci-verification-stabilisation` (preserve) / `fix/ci-cd-deepti` | [#94](https://github.com/Algoryxz/DocuReady/pull/94) | `in_progress` | `CI Tests` run `46140310777` **PASSED** (Py 3.11–3.14); `Windows desktop release qualification` run `46140310782` `in_progress` at snapshot. Phase 2 pairs with Frontend owner. |
| **PR #95, Testing & Quality** | Akriti | `feat/pr95-akriti` (preserve PR #95 if open) | #95 | `ready` | Complete PR #95, expand tests, run post-integration regressions & benchmark comparisons. |
| **Backend & Doc Intelligence** | Susmita | `feat/backend-susmita` | — | `ready` | Own `src/docuready/**`, `sidecar/`, `packs/`, API contracts, extraction/OCR reliability. |
| **Frontend & Electron** | Project frontend owner | `feat/frontend-electron` | — | `ready` | Own `apps/desktop/**`, IPC/sidecar integration, Windows installer & `site/` download section. |

---

## Verified CI & Release Gate Snapshot (28 November 2026)

- **`main` (`9717ae5`):** `CI Tests` (`46129673099`) `failure`; `Windows desktop release qualification` (`46129673088`) `failure`.
- **PR #94 (`fix/ci-verification-stabilisation`):** `CI Tests` (`46140310777`) `success` across Python `3.11`, `3.12`, `3.13`, `3.14`; `CodeRabbit` `success`; `Vercel` `success`.
- **Distribution & Licensing Gate:** **OPEN** — AGPLv3 distribution clearance for bundled PyMuPDF/MuPDF (`LICENSING_DECISION.md`) must be resolved before publishing a permanent public installer.
