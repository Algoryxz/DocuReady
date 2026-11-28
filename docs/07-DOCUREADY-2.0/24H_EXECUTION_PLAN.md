# DocuReady 2.0 — 24-Hour Execution Plan

**Time Budget:** 24 Hours
**Updated Base origin/main SHA:** 70b7ea5f001a5a30404a13b7d347527c641a434b
**Target Vertical Slice:** Guided Application Workspace → Document Intelligence → Evidence Review → Correct → Re-audit → Redacted Report

---

## Timeline & Milestones

| Window | Milestone | Owners | Key Deliverables |
|---|---|---|---|
| **H0–H2** | **Baseline Sync & Contract Freeze** | All | Merge docs/docuready-2.0-kickoff-baseline (rebased onto 70b7ea5, with PRs #94–#97 merged). Freeze shared types in pps/desktop/src/shared/types.ts and sidecar/docuready_sidecar.py. |
| **H2–H10** | **Core Slice Implementation (Parallel)** | Susmita, Project frontend owner, Akriti, Deepti | **Susmita (eat/backend-susmita proposed):** Backend & document intelligence (src/docuready/**, sidecar/, packs/**), pack/slot wiring, extraction/normalization/validation, API contracts, documentId provenance, sidecar contract fixes.<br>**Project frontend owner (eat/frontend-electron proposed):** Electron & React integration (pps/desktop/**), Evidence Review Workspace, document nav & finding-panel workflows, schemeId forwarding, packet:replace-document IPC, guided slot checklist, raw-vs-normalized & cross-doc comparison, session annotations.<br>**Akriti (eat/pr95-akriti proposed; PR #95 merged):** Expand regression coverage, benchmark experiments, failure & negative-control investigation, before/after metrics.<br>**Deepti (ix/ci-cd-deepti proposed; PR #94 merged):** Phase 1 CI/CD stabilization and Windows release pipeline (DocuReady-Setup.exe, DocuReady-Portable.zip, SHA256SUMS.txt). |
| **H10–H16** | **Integration & Regression Testing** | Susmita, Project frontend owner, Akriti | Wire Electron ↔ Sidecar ↔ Renderer end-to-end; run Python regressions, Desktop Node tests, 	sc --noEmit, and new IPC/UI/replacement/redaction tests; Akriti coordinates quality evidence & before/after comparisons. |
| **H16–H20** | **Qualification & QA Review** | Deepti (Phase 2) + All | Deepti collaborates with the Project frontend owner on integration and QA; verify GitHub-hosted CI Tests (3.11–3.14), Windows packaging, clean-machine install/launch/uninstall, portable launch, English/Hindi/Odia OCR, sidecar health, and SHA-256 verification. |
| **H20–H24** | **Demo Rehearsal & Freeze** | All | Rehearse full 6-step Windows flow; confirm zero regressions on golden baseline (E8FB1A6B...) and privacy/redaction invariants; confirm AGPLv3/PyMuPDF licensing gate remains OPEN pending qualified legal review before any permanent public release. |