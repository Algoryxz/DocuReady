# DOCUREADY — LOOP 42 INVESTIGATION & QUALIFICATION PLAN

**Mission:** Profile and optimize end-to-end OCR workflow performance without sacrificing accuracy or evidence integrity, verify per-language native vs. fallback equivalence (`eng`, `hin`, `ori`, `eng+hin`, `eng+ori`, `eng+hin+ori`), expand independent multilingual blind evaluation, and re-verify Package A/B, Windows trust, and full regression suites.  
**Branch:** `loop-42-e2e-ocr-performance-and-production-qualification` (from `66d7c3f`)  
**Protected Release:** Loop 10 (`bdc403a`) — immutable.

---

## 1. Agent Ownership

| Role | Scope | Primary Deliverables |
|---|---|---|
| **Agent A — End-to-End Performance** | 16-stage pipeline profiling, OCR call counting, duplication audit, safe optimizations (e.g., in-process/cached `image_to_data` or intermediate reuse without thumbnail text reuse) | `LOOP_42_E2E_PERFORMANCE_REPORT.md`, `LOOP_42_PIPELINE_PROFILING_REPORT.md`, `LOOP_42_OCR_CALL_AUDIT.md` |
| **Agent B — Native OCR & Fallback** | Language-specific native vs subprocess parity across `eng`, `hin`, `ori`, `eng+hin`, `eng+ori`, `eng+hin+ori`; concurrency, language switching, RSS/handles, failure safety | `LOOP_42_NATIVE_FALLBACK_PARITY.md`, `LOOP_42_CONCURRENCY_LIFECYCLE_REPORT.md` |
| **Agent C — Multilingual Accuracy** | Loop 40 35-doc corpus + genuinely independent unseen blind corpus (`BLIND42`, distinct documents across all 5 language buckets), separate rotation vs independent-doc reporting | `LOOP_42_MULTILINGUAL_ACCURACY_REPORT.md` |
| **Agent D — Desktop & Windows Qualification** | Electron-to-sidecar IPC workflow, Package A/B, Authenticode & clean-VM blockers | `LOOP_42_PACKAGE_AB_REPORT.md`, `LOOP_42_WINDOWS_TRUST_REPORT.md` |
| **Integration Agent** | Shared-code integration, regression & security suites, Gates A–Z (`26` gates), failure analysis, learnings, final closeout | `LOOP_42_SECURITY_PRIVACY_REPORT.md`, `LOOP_42_TEST_REPORT.md`, `LOOP_42_QUALIFICATION_MATRIX.md`, `LOOP_42_FAILURE_ANALYSIS.md`, `LOOP_42_LEARNINGS.md`, `LOOP_42_FINAL_REPORT.md` |
