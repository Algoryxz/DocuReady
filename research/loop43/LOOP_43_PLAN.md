# DOCUREADY — LOOP 43 INVESTIGATION & QUALIFICATION PLAN

**Mission:** Diagnose and resolve mixed-script routing failures (`BLIND42_MIX_HIN_ENG`, `BLIND42_MIX_ORI_ENG`), ablate multi-region script detection strategies (A–D), verify regional OCR coordinate integrity, expand independent blind multilingual evaluation (`BLIND43`), and qualify end-to-end performance, native/fallback parity, and regressions.  
**Branch:** `loop-43-mixed-script-routing-and-regional-ocr` (from `2849936`)  
**Protected Release:** Loop 10 (`bdc403a`) — immutable.

---

## 1. Agent Ownership

| Role | Scope | Primary Deliverables |
|---|---|---|
| **Agent A — Mixed-Script Detection** | Reproduce `BLIND42_MIX_*` failures; inspect `detect_unicode_script()` & `profile_document()`; ablate Strategies A–D | `LOOP_43_ROUTING_ROOT_CAUSE.md`, `LOOP_43_REGIONAL_SCRIPT_DETECTION.md` |
| **Agent B — Regional OCR & Coordinates** | Compare document-wide vs regional OCR; verify crop-to-page coordinates, rotated/deskewed/multi-column/table-boundary integrity | `LOOP_43_REGIONAL_OCR_ARCHITECTURE.md`, `LOOP_43_COORDINATE_INTEGRITY_REPORT.md` |
| **Agent C — Accuracy & Dataset Evaluation** | Preserve Loop 40 (35) + `BLIND42` (5); create frozen `BLIND43` (`DEV`/`CALIBRATION`/`BLIND` independent docs incl. Latin-header/Indic-body & Indic-header/Latin-ID); CER, WER, field/table accuracy | `LOOP_43_MULTILINGUAL_ACCURACY_REPORT.md` |
| **Agent D — Performance & Desktop** | Cold/warm E2E & stage-by-stage timing, multi-region overhead, Electron-to-sidecar (`25/25`), Package A/B, Windows trust | `LOOP_43_END_TO_END_PERFORMANCE.md`, `LOOP_43_NATIVE_FALLBACK_PARITY.md`, `LOOP_43_PACKAGE_AB_REPORT.md`, `LOOP_43_WINDOWS_TRUST_REPORT.md` |
| **Integration Agent** | Shared-file integration (`adaptive_ocr.py`), full regressions, security/privacy, 26 Gates A–Z, failure analysis, learnings, final closeout | `LOOP_43_SECURITY_PRIVACY_REPORT.md`, `LOOP_43_TEST_REPORT.md`, `LOOP_43_QUALIFICATION_MATRIX.md`, `LOOP_43_FAILURE_ANALYSIS.md`, `LOOP_43_LEARNINGS.md`, `LOOP_43_FINAL_REPORT.md` |
