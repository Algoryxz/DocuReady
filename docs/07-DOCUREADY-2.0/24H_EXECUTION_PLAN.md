# DocuReady 2.0 — 24-Hour Execution Plan

**Time Budget:** 24 Hours  
**Target Vertical Slice:** Guided Application Workspace → Document Intelligence → Evidence Review → Correct → Re-audit → Redacted Report

---

## Timeline & Milestones

| Window | Milestone | Owners | Key Deliverables |
|---|---|---|---|
| **H0–H2** | **Baseline & CI Green** | All + Deeptiman | Merge Loop 0 docs baseline (`docs/docuready-2.0-kickoff-baseline`) and PR #94 (`fix/ci-verification-stabilisation`). Sync shared types in `apps/desktop/src/shared/types.ts`. |
| **H2–H10** | **Core Slice Implementation (Parallel)** | User (WS1), Akriti (WS2), Susmita (WS3) | **WS1:** `schemeId` forwarding, `packet:replace-document` IPC, workspace hardening.<br>**WS2:** Pack/slot wiring, raw-vs-normalized field DTOs, `documentId` provenance, sidecar contract fixes.<br>**WS3:** Guided slot checklist UI, raw-vs-normalized & cross-doc comparison, uncertainty UX, per-slot replace button, session annotations. |
| **H10–H16** | **Integration & Regression Testing** | User, Akriti, Susmita | Wire Electron ↔ Sidecar ↔ Renderer end-to-end; run Python regressions, Desktop Node tests, `tsc --noEmit`, new IPC/UI/replacement/redaction tests. |
| **H16–H20** | **Qualification & QA Review** | Deeptiman (WS4) + All | GitHub-hosted `CI Tests` (3.11–3.14) and `Windows desktop release qualification` green; Deeptiman UX, accessibility, and integration QA pass. |
| **H20–H24** | **Demo Rehearsal & Freeze** | All | Verify clean Windows packaged app demo of the full 6-step flow; confirm zero regressions on golden baseline (`E8FB1A6B...`) and privacy/redaction invariants. |
