# PHASE 4 — CHANGE DEDUPLICATION & INTEGRATION PLAN

**Project:** `Algoryxz/DocuReady`  
**Date:** 2026-11-27

---

## 1. File-Level Integration Map (Production & Test Files Changed `origin/main..loop-47`)

Because `fix/final-desktop-release-stabilization` (`acd991e`) and `loop-01`..`loop-47` (`23a3e09`) form a **strictly linear 50-commit chain** on top of `origin/main` (`392ce9a`), every file's latest state on `loop-47` already incorporates all prior loop edits sequentially without cross-branch merge conflicts.

| Subsystem | Files Modified (`origin/main..loop-47`) | Contributing Loops | Authoritative State |
|---|---|---|---|
| **Electron Main & Sidecar** | `apps/desktop/src/main.ts`, `apps/desktop/src/main/sidecar.ts`, `apps/desktop/src/main/ipc.ts`, `apps/desktop/src/main/workspace.ts` | `fix/final-desktop-release-stabilization` (`4d89721`, `acd991e`), `loop-08` (`bea7856`), `loop-32` (`3806d76`) | `loop-47` (`23a3e09`) |
| **Electron Renderer & Shared** | `apps/desktop/src/renderer/components/DocumentNav.tsx`, `EvidenceViewer.tsx`, `FindingPanel.tsx`, `main.tsx`, `styles.css`, `apps/desktop/src/shared/evidence.ts` | `loop-06` (`d1f0f0e`), `loop-08` (`bea7856`), `loop-09` (`9c2fb6d`) | `loop-47` (`23a3e09`) |
| **Desktop Tests & Packaging** | `apps/desktop/tests/evidence.test.ts`, `sidecar.test.ts`, `workflow_lifecycle.test.ts`, `scripts/verify_clean_windows_runtime.ps1` | `fix/final-desktop-release-stabilization`, `loop-06`, `loop-08` | `loop-47` (`23a3e09`) |
| **OCR & Ingest Pipeline** | `src/docuready/ingest/extractor.py`, `deskew.py`, `spatial_layout.py`, `script_router.py`, `region_ocr.py`, `adaptive_ocr.py`, `tesseract_discovery.py`, `pymupdf_backend.py` | `loop-01`..`loop-05`, `loop-13`..`loop-17`, `loop-19`, `loop-32`, `loop-38`..`loop-44`, `loop-46` | `loop-47` (`23a3e09`) |
| **Table & Identifier Verification** | `src/docuready/ingest/table_association.py`, `src/docuready/ingest/identifier_validation.py` | `loop-19`..`loop-27` | `loop-47` (`23a3e09`) |
| **Normalization, Cross-Doc & Rules** | `src/docuready/normalize/normalizer.py`, `src/docuready/evidence/cross_document.py`, `src/docuready/rules/engine.py`, `src/docuready/rules/validator.py` | `loop-05`..`loop-07`, `loop-28`..`loop-29`, `loop-32` | `loop-47` (`23a3e09`) |
| **Benchmark & Corpus Scripts** | `scripts/benchmark_*.py`, `scripts/build_*_corpus.py`, `scripts/diagnose_deskew_failure_modes.py`, `scripts/evaluate_gate_safety.py`, `scripts/verify_audit_packets_under_skew.py` | `loop-01`..`loop-07` | `loop-47` (`23a3e09`) |
| **Python Regression Tests** | `tests/test_loop02_*` through `tests/test_loop46_*`, `tests/test_ocr_performance_and_adversarial.py` (34 test files) | `loop-01`..`loop-46` | `loop-47` (`23a3e09`) |

---

## 2. Deduplication & Conflict Assessment

- **Zero merge conflicts** exist along the `origin/main` -> `loop-47` chain.
- **No unique unmerged fixes** were found in the 16 non-ancestor `origin/*` branches or in the orphan `22377d5` (`loop-2`, `loop-3`) prototype branches that are missing from `loop-47` (verified in Phase 2).
- **Loop 10 Release Artifacts (`apps/desktop/out/`):** Gitignored on disk; must remain completely untouched by Git operations.

---

## 3. Execution & Integration Order (Phase 5–10)

1. **Create isolated integration branch** `integration/repository-wide-consolidation` from `origin/main` (`392ce9a`) using an isolated Git worktree (preserving the active working tree and all untracked files in `C:/Users/smara/Desktop/New folder`).
2. **Integrate in dependency order** onto `integration/repository-wide-consolidation`:
   - Group 1: `fix/final-desktop-release-stabilization` (`acd991e`) — Desktop sidecar spawn mutex, async shutdown, Squirrel hooks.
   - Group 2: `loop-01`..`loop-10` (`bdc403a`) — OSD/deskew, normalization, calibrated decision engine, desktop review UX, competition release freeze baseline.
   - Group 3: `loop-11`..`loop-29` (`e5fafd5`) — Spatial layout, multilingual script/region/adaptive OCR, table-aware evidence association, identifier validation, cross-document verification.
   - Group 4: `loop-30`..`loop-47` (`23a3e09`) — Repository defect fixes (`3806d76`, `12d6512`), probe reuse, upper-band mixed-script recovery, and validation suites.
   *(Because `origin/main..loop-47` is a clean linear chain, fast-forward/grouped merge in these 4 stages preserves full commit provenance without duplicating code.)*
3. **Full Technical Regression (Phase 6):** Execute complete Python `pytest` suite, Electron tests (`npm test`), TypeScript check (`npx tsc --noEmit` / typecheck), and targeted OCR/security/offline checks.
4. **Documentation & Release Integrity Audit (Phase 7–8):** Verify docs alignment and recompute SHA-256 hashes of all 5 Loop 10 release artifacts.
5. **Qualification & Main-Merge Approval (Phase 9–10):** Present full report and await explicit user approval before modifying `main`.
