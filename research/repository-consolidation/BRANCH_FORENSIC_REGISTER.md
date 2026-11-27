# PHASE 2 — BRANCH FORENSIC REGISTER

**Project:** `Algoryxz/DocuReady`  
**Scope:** Forensic inspection of all 213 discovered Git refs (54 local branches, 77 remote non-PR refs, 82 `origin/pr/*` refs).

---

## 1. Local Branches — Detailed Forensic Entries (54 Branches)

### `feat/electron-desktop-foundation` (`d9323ea`)
- **Parents:** `0851dc8` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `d9323ea`
- **Ahead/Behind `origin/main`:** 78 behind / 0 ahead
- **Contained in:** `origin/main`=True, `loop-10`=True, `loop-47`=True
- **Latest Commit:** `d9323ea` (2026-11-16, DocuReady Auditor) — feat(loop4): product validation, real-world workflow testing & RC qualification
- **Containment:** Fully merged into `origin/main` (`392ce9a`).

### `feat/loop5-independent-validation-and-demo` (`22c75ef`)
- **Parents:** `587e10d` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `22c75ef`
- **Ahead/Behind `origin/main`:** 75 behind / 0 ahead
- **Contained in:** `origin/main`=True, `loop-10`=True, `loop-47`=True
- **Latest Commit:** `22c75ef` (2026-11-16, DocuReady Auditor) — feat(packaging): windows release hardening, bundled OCR runtime, packaging fixes & comprehensive README
- **Containment:** Fully merged into `origin/main` (`392ce9a`).

### `feat/loop6-release-integrity-and-reproducibility` (`360c3fb`)
- **Parents:** `8266d51` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `360c3fb`
- **Ahead/Behind `origin/main`:** 41 behind / 0 ahead
- **Contained in:** `origin/main`=True, `loop-10`=True, `loop-47`=True
- **Latest Commit:** `360c3fb` (2026-11-19, DocuReady Auditor) — fix(desktop): resolve Electron startup crash and verify clean Windows runtime
- **Containment:** Fully merged into `origin/main` (`392ce9a`).

### `fix/final-desktop-release-stabilization` (`acd991e`)
- **Parents:** `4d89721` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `392ce9a`
- **Ahead/Behind `origin/main`:** 0 behind / 2 ahead
- **Contained in:** `origin/main`=False, `loop-10`=True, `loop-47`=True
- **Latest Commit:** `acd991e` (2026-11-22, DocuReady Auditor) — fix(packaging): handle Squirrel Windows lifecycle hooks and tune qualification uninstaller polling
- **Commit Diff Stat:** `+57/-6` across 2 files (2 production/test/script files).
- **Production/Test Files Touched:** `apps/desktop/src/main.ts`, `scripts/verify_clean_windows_runtime.ps1`

### `loop-01-osd-performance-analysis` (`fd22194`)
- **Parents:** `acd991e` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `392ce9a`
- **Ahead/Behind `origin/main`:** 0 behind / 3 ahead
- **Contained in:** `origin/main`=False, `loop-10`=True, `loop-47`=True
- **Latest Commit:** `fd22194` (2026-11-22, DocuReady Auditor) — feat(ocr): eliminate redundant OSD via conservative upright fast-path and direct buffer decoding
- **Commit Diff Stat:** `+1328/-12` across 10 files (4 production/test/script files).
- **Production/Test Files Touched:** `scripts/benchmark_ocr_performance.py`, `src/docuready/ingest/extractor.py`, `src/docuready/ingest/pdf_backend/pymupdf_backend.py`, `tests/test_ocr_performance_and_adversarial.py`

### `loop-02-orientation-gate-assurance` (`cdf6a5e`)
- **Parents:** `fd22194` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `392ce9a`
- **Ahead/Behind `origin/main`:** 0 behind / 4 ahead
- **Contained in:** `origin/main`=False, `loop-10`=True, `loop-47`=True
- **Latest Commit:** `cdf6a5e` (2026-11-22, DocuReady Auditor) — fix(ocr): harden orientation gate, implement two-tier OSD recovery, and eliminate raster memory leak
- **Commit Diff Stat:** `+3502/-256` across 19 files (4 production/test/script files).
- **Production/Test Files Touched:** `scripts/build_attack_corpus.py`, `scripts/evaluate_gate_safety.py`, `src/docuready/ingest/extractor.py`, `tests/test_loop02_orientation_assurance.py`

### `loop-03-skew-recovery-and-geometry` (`1e1c876`)
- **Parents:** `cdf6a5e` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `392ce9a`
- **Ahead/Behind `origin/main`:** 0 behind / 5 ahead
- **Contained in:** `origin/main`=False, `loop-10`=True, `loop-47`=True
- **Latest Commit:** `1e1c876` (2026-11-22, DocuReady Auditor) — feat(ocr): add validated skew recovery and coordinate mapping
- **Commit Diff Stat:** `+3211/-20` across 52 files (5 production/test/script files).
- **Production/Test Files Touched:** `scripts/benchmark_skew_recovery.py`, `scripts/build_skew_corpus.py`, `src/docuready/ingest/deskew.py`, `src/docuready/ingest/extractor.py`, `tests/test_loop03_skew_recovery.py`

### `loop-04-deskew-reliability-and-audit-integrity` (`ee195c5`)
- **Parents:** `1e1c876` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `392ce9a`
- **Ahead/Behind `origin/main`:** 0 behind / 6 ahead
- **Contained in:** `origin/main`=False, `loop-10`=True, `loop-47`=True
- **Latest Commit:** `ee195c5` (2026-11-22, DocuReady Auditor) — feat(ocr): harden deskew reliability, ambiguity resolution, and audit integrity
- **Commit Diff Stat:** `+3281/-23` across 59 files (7 production/test/script files).
- **Production/Test Files Touched:** `scripts/benchmark_loop04_reliability.py`, `scripts/build_loop04_reliability_corpus.py`, `scripts/diagnose_deskew_failure_modes.py`, `scripts/verify_audit_packets_under_skew.py`, `src/docuready/ingest/deskew.py`, `src/docuready/ingest/extractor.py`, `tests/test_loop04_deskew_reliability.py`

### `loop-05-extraction-normalization-and-cross-document-reliability` (`17c33ea`)
- **Parents:** `ee195c5` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `392ce9a`
- **Ahead/Behind `origin/main`:** 0 behind / 7 ahead
- **Contained in:** `origin/main`=False, `loop-10`=True, `loop-47`=True
- **Latest Commit:** `17c33ea` (2026-11-22, DocuReady Auditor) — feat(extract): improve field normalization, candidate ambiguity, and cross-document intelligence (Loop 05)
- **Commit Diff Stat:** `+2071/-67` across 21 files (5 production/test/script files).
- **Production/Test Files Touched:** `scripts/benchmark_loop05_extraction.py`, `scripts/build_loop05_extraction_corpus.py`, `src/docuready/ingest/extractor.py`, `src/docuready/normalize/normalizer.py`, `tests/test_loop05_extraction_normalization.py`

### `loop-06-audit-decision-integrity-and-calibration` (`d1f0f0e`)
- **Parents:** `17c33ea` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `392ce9a`
- **Ahead/Behind `origin/main`:** 0 behind / 8 ahead
- **Contained in:** `origin/main`=False, `loop-10`=True, `loop-47`=True
- **Latest Commit:** `d1f0f0e` (2026-11-22, DocuReady Auditor) — feat(decision): calibrate audit decision engine, enforce 10 invariants, and harden explainability (Loop 06)
- **Commit Diff Stat:** `+9401/-14` across 100 files (8 production/test/script files).
- **Production/Test Files Touched:** `apps/desktop/src/renderer/components/FindingPanel.tsx`, `apps/desktop/src/shared/evidence.ts`, `apps/desktop/tests/evidence.test.ts`, `scripts/benchmark_loop06_decision_engine.py`, `scripts/build_loop06_decision_corpus.py`, `src/docuready/rules/engine.py`, `src/docuready/rules/validator.py`, `tests/test_loop06_decision_engine.py`

### `loop-07-adversarial-corpus-and-decision-generalization` (`250093f`)
- **Parents:** `d1f0f0e` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `392ce9a`
- **Ahead/Behind `origin/main`:** 0 behind / 9 ahead
- **Contained in:** `origin/main`=False, `loop-10`=True, `loop-47`=True
- **Latest Commit:** `250093f` (2026-11-22, DocuReady Auditor) — test(audit): expand adversarial corpus and validate decision generalization (Loop 07)
- **Commit Diff Stat:** `+69657/-18` across 789 files (4 production/test/script files).
- **Production/Test Files Touched:** `scripts/benchmark_loop07_adversarial.py`, `scripts/build_loop07_adversarial_corpus.py`, `src/docuready/rules/validator.py`, `tests/test_loop07_adversarial_generalization.py`

### `loop-08-desktop-workflow-integrity-and-review-ux` (`bea7856`)
- **Parents:** `250093f` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `392ce9a`
- **Ahead/Behind `origin/main`:** 0 behind / 10 ahead
- **Contained in:** `origin/main`=False, `loop-10`=True, `loop-47`=True
- **Latest Commit:** `bea7856` (2026-11-22, DocuReady Auditor) — feat(desktop): harden audit workflow, recovery, and human review UX (Loop 08)
- **Commit Diff Stat:** `+1447/-37` across 14 files (9 production/test/script files).
- **Production/Test Files Touched:** `apps/desktop/src/main/ipc.ts`, `apps/desktop/src/main/sidecar.ts`, `apps/desktop/src/renderer/components/DocumentNav.tsx`, `apps/desktop/src/renderer/components/EvidenceViewer.tsx`, `apps/desktop/src/renderer/components/FindingPanel.tsx`, `apps/desktop/src/renderer/main.tsx`, `apps/desktop/src/renderer/styles.css`, `apps/desktop/tests/workflow_lifecycle.test.ts`, `tests/test_loop08_desktop_workflow_integrity.py`

### `loop-09-windows-release-integrity-and-deployment` (`9c2fb6d`)
- **Parents:** `bea7856` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `392ce9a`
- **Ahead/Behind `origin/main`:** 0 behind / 11 ahead
- **Contained in:** `origin/main`=False, `loop-10`=True, `loop-47`=True
- **Latest Commit:** `9c2fb6d` (2026-11-22, DocuReady Auditor) — build(release): validate packaged Windows runtime and clean-machine deployment (Loop 09)
- **Commit Diff Stat:** `+888/-58` across 7 files (2 production/test/script files).
- **Production/Test Files Touched:** `apps/desktop/src/renderer/components/FindingPanel.tsx`, `tests/test_loop09_release_integrity.py`

### `loop-10-competition-demo-reliability-and-final-readiness` (`bdc403a`)
- **Parents:** `9c2fb6d` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `392ce9a`
- **Ahead/Behind `origin/main`:** 0 behind / 12 ahead
- **Contained in:** `origin/main`=False, `loop-10`=True, `loop-47`=True
- **Latest Commit:** `bdc403a` (2026-11-22, DocuReady Auditor) — test(demo): qualify competition workflow and freeze release scope (Loop 10)
- **Commit Diff Stat:** `+1257/-0` across 9 files (1 production/test/script files).
- **Production/Test Files Touched:** `tests/test_loop10_demo_reliability.py`

### `loop-11-independent-dataset-benchmark` (`e282e3b`)
- **Parents:** `bdc403a` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `392ce9a`
- **Ahead/Behind `origin/main`:** 0 behind / 13 ahead
- **Contained in:** `origin/main`=False, `loop-10`=False, `loop-47`=True
- **Latest Commit:** `e282e3b` (2026-11-22, DocuReady Auditor) — research(loop11): establish independent OCR dataset benchmark
- **Commit Diff Stat:** `+15078/-0` across 29 files (1 production/test/script files).
- **Production/Test Files Touched:** `tests/test_loop11_independent_benchmark.py`

### `loop-12-benchmark-integrity-audit` (`756062b`)
- **Parents:** `e282e3b` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `392ce9a`
- **Ahead/Behind `origin/main`:** 0 behind / 14 ahead
- **Contained in:** `origin/main`=False, `loop-10`=False, `loop-47`=True
- **Latest Commit:** `756062b` (2026-11-22, DocuReady Auditor) — research(loop12): audit benchmark provenance and scoring integrity
- **Commit Diff Stat:** `+8629/-0` across 20 files (1 production/test/script files).
- **Production/Test Files Touched:** `tests/test_loop12_benchmark_integrity.py`

### `loop-13-column-aware-reading-order` (`e601d11`)
- **Parents:** `756062b` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `392ce9a`
- **Ahead/Behind `origin/main`:** 0 behind / 15 ahead
- **Contained in:** `origin/main`=False, `loop-10`=False, `loop-47`=True
- **Latest Commit:** `e601d11` (2026-11-22, DocuReady Auditor) — feat(loop13): implement column-aware spatial reading order and india dataset discovery
- **Commit Diff Stat:** `+3208/-0` across 24 files (3 production/test/script files).
- **Production/Test Files Touched:** `src/docuready/ingest/extractor.py`, `src/docuready/ingest/spatial_layout.py`, `tests/test_loop13_column_aware_reading_order.py`

### `loop-14-india-document-corpus-and-multilingual-ocr` (`ba3e306`)
- **Parents:** `e601d11` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `392ce9a`
- **Ahead/Behind `origin/main`:** 0 behind / 16 ahead
- **Contained in:** `origin/main`=False, `loop-10`=False, `loop-47`=True
- **Latest Commit:** `ba3e306` (2026-11-22, DocuReady Auditor) — feat(loop14): implement script-aware multilingual ocr routing and india document corpus validation
- **Commit Diff Stat:** `+3521/-7` across 54 files (4 production/test/script files).
- **Production/Test Files Touched:** `src/docuready/ingest/extractor.py`, `src/docuready/ingest/script_router.py`, `src/docuready/ingest/tesseract_discovery.py`, `tests/test_loop14_multilingual_ocr.py`

### `loop-15-region-aware-multilingual-ocr` (`39cde88`)
- **Parents:** `ba3e306` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `392ce9a`
- **Ahead/Behind `origin/main`:** 0 behind / 17 ahead
- **Contained in:** `origin/main`=False, `loop-10`=False, `loop-47`=True
- **Latest Commit:** `39cde88` (2026-11-22, DocuReady Auditor) — feat(loop15): implement region-aware multilingual ocr and script-level routing
- **Commit Diff Stat:** `+4050/-0` across 44 files (2 production/test/script files).
- **Production/Test Files Touched:** `src/docuready/ingest/region_ocr.py`, `tests/test_loop15_region_aware_ocr.py`

### `loop-16-adaptive-ocr-strategy` (`de63549`)
- **Parents:** `39cde88` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `392ce9a`
- **Ahead/Behind `origin/main`:** 0 behind / 18 ahead
- **Contained in:** `origin/main`=False, `loop-10`=False, `loop-47`=True
- **Latest Commit:** `de63549` (2026-11-22, DocuReady Auditor) — feat(loop16): implement adaptive ocr strategy selector, accuracy optimization and latency reduction
- **Commit Diff Stat:** `+7193/-0` across 49 files (2 production/test/script files).
- **Production/Test Files Touched:** `src/docuready/ingest/adaptive_ocr.py`, `tests/test_loop16_adaptive_ocr.py`

### `loop-17-adaptive-ocr-efficiency-and-reliability` (`69addb5`)
- **Parents:** `de63549` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `392ce9a`
- **Ahead/Behind `origin/main`:** 0 behind / 19 ahead
- **Contained in:** `origin/main`=False, `loop-10`=False, `loop-47`=True
- **Latest Commit:** `69addb5` (2026-11-22, DocuReady Auditor) — feat(loop17): optimize adaptive OCR efficiency and critical-field reliability
- **Commit Diff Stat:** `+7356/-6` across 73 files (2 production/test/script files).
- **Production/Test Files Touched:** `src/docuready/ingest/adaptive_ocr.py`, `tests/test_loop17_adaptive_efficiency.py`

### `loop-18-independent-accuracy-and-critical-field-validation` (`9360fd2`)
- **Parents:** `69addb5` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `392ce9a`
- **Ahead/Behind `origin/main`:** 0 behind / 20 ahead
- **Contained in:** `origin/main`=False, `loop-10`=False, `loop-47`=True
- **Latest Commit:** `9360fd2` (2026-11-22, DocuReady Auditor) — feat(loop18): validate OCR accuracy and critical-field reliability
- **Commit Diff Stat:** `+6198/-0` across 100 files (1 production/test/script files).
- **Production/Test Files Touched:** `tests/test_loop18_accuracy_and_critical_fields.py`

### `loop-19-table-aware-evidence-and-field-association` (`2d7aab5`)
- **Parents:** `9360fd2` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `392ce9a`
- **Ahead/Behind `origin/main`:** 0 behind / 21 ahead
- **Contained in:** `origin/main`=False, `loop-10`=False, `loop-47`=True
- **Latest Commit:** `2d7aab5` (2026-11-22, DocuReady Auditor) — feat(loop19): improve table-aware evidence association reliability
- **Commit Diff Stat:** `+3065/-24` across 48 files (4 production/test/script files).
- **Production/Test Files Touched:** `src/docuready/ingest/adaptive_ocr.py`, `src/docuready/ingest/script_router.py`, `src/docuready/ingest/table_association.py`, `tests/test_loop19_table_association.py`

### `loop-2-robustness` (`caec706`)
- **Parents:** `22377d5` | **Root:** `22377d5`
- **Merge Base vs `main` (`22377d5`):** `22377d5` | **Merge Base vs `origin/main` (`392ce9a`):** None (unrelated root)
- **Ahead/Behind `origin/main`:** N/A
- **Contained in:** `origin/main`=False, `loop-10`=False, `loop-47`=False
- **Latest Commit:** `caec706` (2026-11-13, DocuReady Auditor) — feat(loop-2): implement real-world robustness, offline local OCR, uncertainty safety, and statutory rule integrity
- **Historical Prototype Lineage:** Belongs to the original HackNation MVP root (`22377d5`, 2026-11-13) under `docuready-mvp/`, `hacknation-arena*/`, prior to the `ba09593` package migration.

### `loop-20-blind-generalization-and-verification-reliability` (`1dcd69d`)
- **Parents:** `2d7aab5` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `392ce9a`
- **Ahead/Behind `origin/main`:** 0 behind / 22 ahead
- **Contained in:** `origin/main`=False, `loop-10`=False, `loop-47`=True
- **Latest Commit:** `1dcd69d` (2026-11-22, DocuReady Auditor) — feat(loop20): validate blind document generalization and verification reliability
- **Commit Diff Stat:** `+6253/-47` across 93 files (2 production/test/script files).
- **Production/Test Files Touched:** `src/docuready/ingest/table_association.py`, `tests/test_loop20_blind_generalization.py`

### `loop-21-header-fusion-and-decimal-integrity` (`4a6a46e`)
- **Parents:** `1dcd69d` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `392ce9a`
- **Ahead/Behind `origin/main`:** 0 behind / 23 ahead
- **Contained in:** `origin/main`=False, `loop-10`=False, `loop-47`=True
- **Latest Commit:** `4a6a46e` (2026-11-23, DocuReady Auditor) — feat(loop21): hierarchical header reconstruction and decimal integrity validation
- **Commit Diff Stat:** `+5365/-3` across 29 files (2 production/test/script files).
- **Production/Test Files Touched:** `src/docuready/ingest/table_association.py`, `tests/test_loop21_header_and_decimal.py`

### `loop-22-evidence-association-reliability` (`0b7629d`)
- **Parents:** `4a6a46e` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `392ce9a`
- **Ahead/Behind `origin/main`:** 0 behind / 24 ahead
- **Contained in:** `origin/main`=False, `loop-10`=False, `loop-47`=True
- **Latest Commit:** `0b7629d` (2026-11-24, DocuReady Auditor) — feat(loop22): improve evidence association reliability and selective verification
- **Commit Diff Stat:** `+5792/-13` across 31 files (2 production/test/script files).
- **Production/Test Files Touched:** `src/docuready/ingest/table_association.py`, `tests/test_loop22_evidence_association.py`

### `loop-23-microfont-numeric-and-narrow-gutter` (`f668ba2`)
- **Parents:** `0b7629d` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `392ce9a`
- **Ahead/Behind `origin/main`:** 0 behind / 25 ahead
- **Contained in:** `origin/main`=False, `loop-10`=False, `loop-47`=True
- **Latest Commit:** `f668ba2` (2026-11-24, DocuReady Auditor) — feat(loop23): improve microfont numeric integrity and narrow-gutter association
- **Commit Diff Stat:** `+11281/-95` across 60 files (2 production/test/script files).
- **Production/Test Files Touched:** `src/docuready/ingest/table_association.py`, `tests/test_loop23_microfont_and_narrow_gutter.py`

### `loop-24-independent-generalization-calibration` (`1623723`)
- **Parents:** `f668ba2` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `392ce9a`
- **Ahead/Behind `origin/main`:** 0 behind / 26 ahead
- **Contained in:** `origin/main`=False, `loop-10`=False, `loop-47`=True
- **Latest Commit:** `1623723` (2026-11-24, DocuReady Auditor) — feat(loop24): improve independent generalization and selective verification
- **Commit Diff Stat:** `+16476/-13` across 61 files (2 production/test/script files).
- **Production/Test Files Touched:** `src/docuready/ingest/table_association.py`, `tests/test_loop24_calibration_and_performance.py`

### `loop-25-row-label-recovery-and-coverage` (`5d9e84e`)
- **Parents:** `1623723` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `392ce9a`
- **Ahead/Behind `origin/main`:** 0 behind / 27 ahead
- **Contained in:** `origin/main`=False, `loop-10`=False, `loop-47`=True
- **Latest Commit:** `5d9e84e` (2026-11-24, DocuReady Auditor) — feat(loop25): evidence-guided row-label recovery, benchmark cohort J, and achieve 100% precision with 62.98% coverage
- **Commit Diff Stat:** `+32719/-5` across 108 files (2 production/test/script files).
- **Production/Test Files Touched:** `src/docuready/ingest/table_association.py`, `tests/test_loop25_row_label_recovery.py`

### `loop-26-independent-real-world-generalization` (`9509017`)
- **Parents:** `5d9e84e` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `392ce9a`
- **Ahead/Behind `origin/main`:** 0 behind / 28 ahead
- **Contained in:** `origin/main`=False, `loop-10`=False, `loop-47`=True
- **Latest Commit:** `9509017` (2026-11-24, DocuReady Auditor) — research(loop26): validate independent document generalization
- **Commit Diff Stat:** `+50741/-9` across 41 files (1 production/test/script files).
- **Production/Test Files Touched:** `src/docuready/ingest/table_association.py`

### `loop-27-identifier-integrity-and-verification-safety` (`511ba82`)
- **Parents:** `9509017` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `392ce9a`
- **Ahead/Behind `origin/main`:** 0 behind / 29 ahead
- **Contained in:** `origin/main`=False, `loop-10`=False, `loop-47`=True
- **Latest Commit:** `511ba82` (2026-11-24, DocuReady Auditor) — research(loop27): harden identifier integrity, character ambiguity guards and verification safety
- **Commit Diff Stat:** `+46817/-11` across 37 files (3 production/test/script files).
- **Production/Test Files Touched:** `src/docuready/ingest/identifier_validation.py`, `src/docuready/ingest/table_association.py`, `tests/test_loop27_identifier_integrity.py`

### `loop-28-cross-document-verification-reliability` (`ce0c9e7`)
- **Parents:** `511ba82` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `392ce9a`
- **Ahead/Behind `origin/main`:** 0 behind / 30 ahead
- **Contained in:** `origin/main`=False, `loop-10`=False, `loop-47`=True
- **Latest Commit:** `ce0c9e7` (2026-11-24, DocuReady Auditor) — research(loop28): strengthen cross-document verification reliability
- **Commit Diff Stat:** `+4936/-0` across 34 files (2 production/test/script files).
- **Production/Test Files Touched:** `src/docuready/evidence/cross_document.py`, `tests/test_loop28_cross_document.py`

### `loop-29-calibration-cohort-integrity-and-generalization` (`e5fafd5`)
- **Parents:** `ce0c9e7` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `392ce9a`
- **Ahead/Behind `origin/main`:** 0 behind / 31 ahead
- **Contained in:** `origin/main`=False, `loop-10`=False, `loop-47`=True
- **Latest Commit:** `e5fafd5` (2026-11-24, DocuReady Auditor) — research(loop29): reconcile calibration and cross-document reliability
- **Commit Diff Stat:** `+17112/-6` across 42 files (1 production/test/script files).
- **Production/Test Files Touched:** `src/docuready/evidence/cross_document.py`

### `loop-3-evidence-calibration` (`73b4051`)
- **Parents:** `c175f38` | **Root:** `22377d5`
- **Merge Base vs `main` (`22377d5`):** `22377d5` | **Merge Base vs `origin/main` (`392ce9a`):** None (unrelated root)
- **Ahead/Behind `origin/main`:** N/A
- **Contained in:** `origin/main`=False, `loop-10`=False, `loop-47`=False
- **Latest Commit:** `73b4051` (2026-11-13, DocuReady Auditor) — fix(loop-3-remediation): resolve odisha validity law, decouple scholarship rules, rename evidence quality score, and reconcile 100-sample benchmark
- **Historical Prototype Lineage:** Belongs to the original HackNation MVP root (`22377d5`, 2026-11-13) under `docuready-mvp/`, `hacknation-arena*/`, prior to the `ba09593` package migration.

### `loop-30-reproducibility-and-evaluation-integrity` (`626ad3c`)
- **Parents:** `e5fafd5` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `392ce9a`
- **Ahead/Behind `origin/main`:** 0 behind / 32 ahead
- **Contained in:** `origin/main`=False, `loop-10`=False, `loop-47`=True
- **Latest Commit:** `626ad3c` (2026-11-25, DocuReady Auditor) — research(loop30): reproduce and audit evaluation integrity
- **Commit Diff Stat:** `+11483/-0` across 31 files (0 production/test/script files).
- **Production/Test Files Touched:** None (research/audit/docs artifacts only).

### `loop-31-independent-qualification-audit` (`a05954a`)
- **Parents:** `626ad3c` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `392ce9a`
- **Ahead/Behind `origin/main`:** 0 behind / 33 ahead
- **Contained in:** `origin/main`=False, `loop-10`=False, `loop-47`=True
- **Latest Commit:** `a05954a` (2026-11-25, DocuReady Auditor) — research(loop31): independently reproduce evaluation qualification
- **Commit Diff Stat:** `+14680/-0` across 20 files (0 production/test/script files).
- **Production/Test Files Touched:** None (research/audit/docs artifacts only).

### `loop-32-repository-wide-bug-discovery` (`12d6512`)
- **Parents:** `3806d76` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `392ce9a`
- **Ahead/Behind `origin/main`:** 0 behind / 35 ahead
- **Contained in:** `origin/main`=False, `loop-10`=False, `loop-47`=True
- **Latest Commit:** `12d6512` (2026-11-25, DocuReady Auditor) — research(loop32): resolve audit discrepancies and finalize closeout corrections
- **Commit Diff Stat:** `+493/-175` across 11 files (2 production/test/script files).
- **Production/Test Files Touched:** `src/docuready/evidence/cross_document.py`, `tests/test_loop32_defect_reproduction.py`

### `loop-33-domain-rules-and-decision-policy-audit` (`decce84`)
- **Parents:** `12d6512` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `392ce9a`
- **Ahead/Behind `origin/main`:** 0 behind / 36 ahead
- **Contained in:** `origin/main`=False, `loop-10`=False, `loop-47`=True
- **Latest Commit:** `decce84` (2026-11-25, DocuReady Auditor) — research(loop33): audit domain rules and decision policy integrity
- **Commit Diff Stat:** `+4817/-0` across 27 files (1 production/test/script files).
- **Production/Test Files Touched:** `tests/test_loop33_rule_adversarial.py`

### `loop-34-independent-ocr-extraction-accuracy` (`fe7ce23`)
- **Parents:** `decce84` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `392ce9a`
- **Ahead/Behind `origin/main`:** 0 behind / 37 ahead
- **Contained in:** `origin/main`=False, `loop-10`=False, `loop-47`=True
- **Latest Commit:** `fe7ce23` (2026-11-26, DocuReady Auditor) — research(loop34): qualify independent OCR and extraction accuracy
- **Commit Diff Stat:** `+5170/-0` across 23 files (0 production/test/script files).
- **Production/Test Files Touched:** None (research/audit/docs artifacts only).

### `loop-35-end-to-end-workflow-reliability` (`3a7e55f`)
- **Parents:** `fe7ce23` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `392ce9a`
- **Ahead/Behind `origin/main`:** 0 behind / 38 ahead
- **Contained in:** `origin/main`=False, `loop-10`=False, `loop-47`=True
- **Latest Commit:** `3a7e55f` (2026-11-26, DocuReady Auditor) — research(loop35): qualify end-to-end workflow reliability
- **Commit Diff Stat:** `+989/-0` across 24 files (1 production/test/script files).
- **Production/Test Files Touched:** `tests/test_loop35_e2e_workflow.py`

### `loop-36-windows-release-installation-recovery-qualification` (`071e34a`)
- **Parents:** `3a7e55f` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `392ce9a`
- **Ahead/Behind `origin/main`:** 0 behind / 39 ahead
- **Contained in:** `origin/main`=False, `loop-10`=False, `loop-47`=True
- **Latest Commit:** `071e34a` (2026-11-26, DocuReady Auditor) — research(loop36): qualify Windows deployment and recovery
- **Commit Diff Stat:** `+928/-0` across 31 files (0 production/test/script files).
- **Production/Test Files Touched:** None (research/audit/docs artifacts only).

### `loop-37-windows-deployment-remediation` (`ea09c79`)
- **Parents:** `071e34a` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `392ce9a`
- **Ahead/Behind `origin/main`:** 0 behind / 40 ahead
- **Contained in:** `origin/main`=False, `loop-10`=False, `loop-47`=True
- **Latest Commit:** `ea09c79` (2026-11-26, DocuReady Auditor) — research(loop37): remediate Windows deployment blockers
- **Commit Diff Stat:** `+716/-0` across 33 files (0 production/test/script files).
- **Production/Test Files Touched:** None (research/audit/docs artifacts only).

### `loop-38-multilingual-ocr-routing-and-package-qualification` (`d66c8e5`)
- **Parents:** `ea09c79` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `392ce9a`
- **Ahead/Behind `origin/main`:** 0 behind / 41 ahead
- **Contained in:** `origin/main`=False, `loop-10`=False, `loop-47`=True
- **Latest Commit:** `d66c8e5` (2026-11-26, DocuReady Auditor) — research(loop38): optimize multilingual OCR routing and qualify package
- **Commit Diff Stat:** `+973/-1` across 34 files (1 production/test/script files).
- **Production/Test Files Touched:** `src/docuready/ingest/adaptive_ocr.py`

### `loop-39-ocr-probe-reuse-and-package-performance` (`77c1f57`)
- **Parents:** `d66c8e5` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `392ce9a`
- **Ahead/Behind `origin/main`:** 0 behind / 42 ahead
- **Contained in:** `origin/main`=False, `loop-10`=False, `loop-47`=True
- **Latest Commit:** `77c1f57` (2026-11-27, DocuReady Auditor) — research(loop39): qualify OCR probe reuse and package performance
- **Commit Diff Stat:** `+1085/-3` across 27 files (2 production/test/script files).
- **Production/Test Files Touched:** `src/docuready/ingest/adaptive_ocr.py`, `tests/test_loop39_probe_hardening.py`

### `loop-40-performance-multilingual-and-windows-qualification` (`b487f03`)
- **Parents:** `77c1f57` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `392ce9a`
- **Ahead/Behind `origin/main`:** 0 behind / 43 ahead
- **Contained in:** `origin/main`=False, `loop-10`=False, `loop-47`=True
- **Latest Commit:** `b487f03` (2026-11-27, DocuReady Auditor) — research(loop40): qualify OCR performance multilingual routing and Windows trust
- **Commit Diff Stat:** `+2816/-14` across 18 files (1 production/test/script files).
- **Production/Test Files Touched:** `src/docuready/ingest/adaptive_ocr.py`

### `loop-41-inprocess-ocr-reliability-and-release-qualification` (`66d7c3f`)
- **Parents:** `b487f03` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `392ce9a`
- **Ahead/Behind `origin/main`:** 0 behind / 44 ahead
- **Contained in:** `origin/main`=False, `loop-10`=False, `loop-47`=True
- **Latest Commit:** `66d7c3f` (2026-11-27, DocuReady Auditor) — research(loop41): qualify in-process OCR reliability and benchmark integrity
- **Commit Diff Stat:** `+344/-2` across 18 files (2 production/test/script files).
- **Production/Test Files Touched:** `src/docuready/ingest/adaptive_ocr.py`, `tests/test_loop41_inprocess_reliability.py`

### `loop-42-e2e-ocr-performance-and-production-qualification` (`2849936`)
- **Parents:** `66d7c3f` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `392ce9a`
- **Ahead/Behind `origin/main`:** 0 behind / 45 ahead
- **Contained in:** `origin/main`=False, `loop-10`=False, `loop-47`=True
- **Latest Commit:** `2849936` (2026-11-27, DocuReady Auditor) — research(loop42): qualify end-to-end OCR performance and production reliability
- **Commit Diff Stat:** `+317/-43` across 17 files (1 production/test/script files).
- **Production/Test Files Touched:** `src/docuready/ingest/adaptive_ocr.py`

### `loop-43-mixed-script-routing-and-regional-ocr` (`e5ba978`)
- **Parents:** `2849936` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `392ce9a`
- **Ahead/Behind `origin/main`:** 0 behind / 46 ahead
- **Contained in:** `origin/main`=False, `loop-10`=False, `loop-47`=True
- **Latest Commit:** `e5ba978` (2026-11-27, DocuReady Auditor) — research(loop43): improve mixed-script routing and qualify regional OCR
- **Commit Diff Stat:** `+230/-14` across 18 files (1 production/test/script files).
- **Production/Test Files Touched:** `src/docuready/ingest/adaptive_ocr.py`

### `loop-44-upper-band-mixed-script-and-e2e-integrity` (`02baae0`)
- **Parents:** `e5ba978` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `392ce9a`
- **Ahead/Behind `origin/main`:** 0 behind / 47 ahead
- **Contained in:** `origin/main`=False, `loop-10`=False, `loop-47`=True
- **Latest Commit:** `02baae0` (2026-11-27, DocuReady Auditor) — research(loop44): improve upper-band script recovery and qualify end-to-end performance
- **Commit Diff Stat:** `+1061/-3` across 20 files (2 production/test/script files).
- **Production/Test Files Touched:** `src/docuready/ingest/adaptive_ocr.py`, `tests/test_loop44_upper_band.py`

### `loop-45-independent-upper-band-generalization` (`c7ed04f`)
- **Parents:** `02baae0` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `392ce9a`
- **Ahead/Behind `origin/main`:** 0 behind / 48 ahead
- **Contained in:** `origin/main`=False, `loop-10`=False, `loop-47`=True
- **Latest Commit:** `c7ed04f` (2026-11-27, DocuReady Auditor) — research(loop45): validate regional routing generalization and benchmark integrity
- **Commit Diff Stat:** `+1632/-0` across 17 files (0 production/test/script files).
- **Production/Test Files Touched:** None (research/audit/docs artifacts only).

### `loop-46-indic-header-latin-body-recovery` (`a9d9b7f`)
- **Parents:** `c7ed04f` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `392ce9a`
- **Ahead/Behind `origin/main`:** 0 behind / 49 ahead
- **Contained in:** `origin/main`=False, `loop-10`=False, `loop-47`=True
- **Latest Commit:** `a9d9b7f` (2026-11-27, DocuReady Auditor) — research(loop46): recover Indic headers with Latin bodies safely
- **Commit Diff Stat:** `+1441/-7` across 20 files (2 production/test/script files).
- **Production/Test Files Touched:** `src/docuready/ingest/adaptive_ocr.py`, `tests/test_loop46_indic_header_latin_body.py`

### `loop-47-independent-mixed-script-generalization` (`23a3e09`)
- **Parents:** `a9d9b7f` | **Root:** `ba09593`
- **Merge Base vs `main` (`22377d5`):** None (unrelated root) | **Merge Base vs `origin/main` (`392ce9a`):** `392ce9a`
- **Ahead/Behind `origin/main`:** 0 behind / 50 ahead
- **Contained in:** `origin/main`=False, `loop-10`=False, `loop-47`=True
- **Latest Commit:** `23a3e09` (2026-11-27, DocuReady Auditor) — research(loop47): validate mixed-script generalization and probe efficiency
- **Commit Diff Stat:** `+1270/-0` across 17 files (0 production/test/script files).
- **Production/Test Files Touched:** None (research/audit/docs artifacts only).

### `main` (`22377d5`)
- **Parents:** None (root) | **Root:** `22377d5`
- **Merge Base vs `main` (`22377d5`):** `22377d5` | **Merge Base vs `origin/main` (`392ce9a`):** None (unrelated root)
- **Ahead/Behind `origin/main`:** N/A
- **Contained in:** `origin/main`=False, `loop-10`=False, `loop-47`=False
- **Latest Commit:** `22377d5` (2026-11-13, DocuReady Auditor) — baseline: DocuReady Loop 1 verified MVP state
- **Historical Prototype Lineage:** Belongs to the original HackNation MVP root (`22377d5`, 2026-11-13) under `docuready-mvp/`, `hacknation-arena*/`, prior to the `ba09593` package migration.

---

## 2. Remote-Tracking Non-PR Branches Not Ancestors of `origin/main` (16 Refs)

All 16 refs below are historical PR/feature/fix branches (dated 2026-11-14 to 2026-11-21) whose changes were either squash-merged, cherry-picked, or superseded by later PRs in `origin/main` (`392ce9a`).

| Remote Ref | HEAD | Merge Base | Behind/Ahead | Author | Date | Forensic Status |
|---|---|---|---|---|---|---|
| `origin/docs/post-g0.1-main-status-reconciliation` | `30513bd` | `c71a7e6` | 282 / 1 | Akriti Lohani | 2026-11-14 | Superseded by `origin/main` (PRs #15-#84) |
| `origin/docs/post-merge-g1-governance-reconciliation` | `1ce4d9f` | `e32825a` | 213 / 1 | Smarak Padhi | 2026-11-15 | Superseded by `origin/main` (PRs #15-#84) |
| `origin/docs/post-t0.3-documentation-reconciliation` | `2d6fb26` | `1fbc3b6` | 263 / 1 | Akriti Lohani | 2026-11-15 | Superseded by `origin/main` (PRs #15-#84) |
| `origin/docs/t3.2-formal-acceptance-reconciliation` | `f5d8cd7` | `607f0b9` | 3 / 1 | Akriti Lohani | 2026-11-21 | Superseded by `origin/main` (PRs #15-#84) |
| `origin/fix/T2.1-consolidated-decision-invariance` | `4733207` | `1a5fc70` | 165 / 1 | Deeptiman Parida | 2026-11-15 | Superseded by `origin/main` (PRs #15-#84) |
| `origin/fix/T2.1-contract-hardening` | `efe9ad8` | `354d4c3` | 163 / 1 | Deeptiman Parida | 2026-11-15 | Superseded by `origin/main` (PRs #15-#84) |
| `origin/fix/T2.1-mainline-outcome-repair` | `bac9f1b` | `e512e23` | 175 / 1 | Smarak Padhi | 2026-11-15 | Superseded by `origin/main` (PRs #15-#84) |
| `origin/fix/ci-reproducible-wheel-verification` | `9018f37` | `ac72e83` | 287 / 5 | Akriti Lohani | 2026-11-14 | Superseded by `origin/main` (PRs #15-#84) |
| `origin/fix/windows-exe-startup-and-ci` | `96b6b3f` | `3e207aa` | 62 / 2 | Smarak Padhi | 2026-11-16 | Superseded by PR #76 (`360c3fb`) & `fix/final-desktop-release-stabilization` (`4d89721`) |
| `origin/task/G0.1-runtime-support-modernization` | `1505811` | `2907fae` | 288 / 2 | Smarak Padhi | 2026-11-14 | Superseded by `origin/main` (PRs #15-#84) |
| `origin/task/T0.1-characterise-current-behaviour` | `4678cdf` | `a6a4990` | 299 / 1 | Smarak Padhi | 2026-11-14 | Superseded by `origin/main` (PRs #15-#84) |
| `origin/task/T0.3-package-contract-verification` | `200eb17` | `50ccf89` | 266 / 1 | Akriti Lohani | 2026-11-15 | Superseded by `origin/main` (PRs #15-#84) |
| `origin/task/T1.2-no-network-contract` | `79ac024` | `43767d4` | 257 / 1 | Smarak Padhi | 2026-11-15 | Superseded by `origin/main` (PRs #15-#84) |
| `origin/task/T2.1-status-vocabulary-resolver` | `2f02062` | `b5d53ab` | 169 / 2 | Susmita Rana | 2026-11-15 | Superseded by `origin/main` (PRs #15-#84) |
| `origin/task/T2.3-match-grades-injected-clock` | `78a8f72` | `16b80d5` | 128 / 2 | Agent 2 (T2.2) | 2026-11-15 | Superseded by `origin/main` (PRs #15-#84) |
| `origin/task/T2.4-slot-validation` | `1067f9b` | `00b99bd` | 124 / 1 | Akriti Lohani | 2026-11-16 | Superseded by `origin/main` (PRs #15-#84) |

---

## 3. Remote-Tracking Non-PR Branches Already Ancestors of `origin/main` (61 Refs)

All 61 refs are already reachable from `origin/main` (`392ce9a`) and require no separate integration.

| Remote Ref | HEAD | Author | Date |
|---|---|---|---|
| `origin` | `392ce9a` | Akriti Lohani | 2026-11-21 |
| `origin/branding/use-provided-logo` | `c0513c8` | Deeptiman Parida | 2026-11-15 |
| `origin/docs/g0-formal-acceptance` | `75eb2ac` | Smarak Padhi | 2026-11-15 |
| `origin/docs/g1-status-reconciliation-pr30` | `bc6c0b3` | Akriti Lohani | 2026-11-15 |
| `origin/docs/post-g0-acceptance-reconciliation` | `cb60eab` | Akriti Lohani | 2026-11-15 |
| `origin/docs/post-g2-merge-governance-accuracy` | `6f5ea68` | Deeptiman Parida | 2026-11-16 |
| `origin/docs/post-merge-g0-state-correction` | `b9acafa` | Smarak Padhi | 2026-11-14 |
| `origin/docs/post-merge-t0-reconciliation` | `7b32ff7` | Smarak Padhi | 2026-11-15 |
| `origin/docs/post-merge-t2.1-t2.2-governance-reconciliation` | `a31acbd` | Deeptiman Parida | 2026-11-15 |
| `origin/docs/post-pr53-governance-reconciliation` | `9b69d54` | Akriti Lohani | 2026-11-15 |
| `origin/docs/post-pr57-governance-reconciliation` | `d38cab8` | Akriti Lohani | 2026-11-15 |
| `origin/docs/post-pr6-status-reconciliation` | `e43d92f` | Smarak Padhi | 2026-11-14 |
| `origin/docs/post-pr61-governance-readme-sync` | `58e20b9` | Deeptiman Parida | 2026-11-15 |
| `origin/docs/post-pr62-governance-cleanup` | `f085770` | Deeptiman Parida | 2026-11-15 |
| `origin/docs/post-pr72-pr73-final-mainline-reconciliation` | `8dc1de2` | Deeptiman Parida | 2026-11-16 |
| `origin/docs/post-t1.2-status-reconciliation` | `5272668` | Akriti Lohani | 2026-11-15 |
| `origin/docs/post-t1.5-g1-reconciliation` | `d8d4fe0` | Smarak Padhi | 2026-11-15 |
| `origin/docs/readme-attribution-and-cleanup` | `14155f4` | Agent 2 (T2.2) | 2026-11-15 |
| `origin/docs/readme-branding-license-modernization` | `4619178` | Smarak Padhi | 2026-11-14 |
| `origin/docs/t0-1-acceptance-t0-2-review-status` | `0ecf3ef` | Akriti Lohani | 2026-11-14 |
| `origin/docs/t0.1-acceptance-status-reconciliation` | `e08a26e` | Akriti Lohani | 2026-11-14 |
| `origin/docs/t0.1-local-regression-evidence` | `6da1150` | Smarak Padhi | 2026-11-14 |
| `origin/docs/t2.2-acceptance-t2.3-kickoff` | `5534897` | Deeptiman Parida | 2026-11-15 |
| `origin/docs/t3.2-acceptance-evidence-wording-followup` | `320cd77` | Akriti Lohani | 2026-11-21 |
| `origin/docs/v2-architecture-team-ownership` | `51dee14` | Smarak Padhi | 2026-11-14 |
| `origin/feat/electron-desktop-foundation` | `e400e31` | Smarak Padhi | 2026-11-16 |
| `origin/feat/g1-qualification-mobile-deploy-resolution` | `b75ef85` | Akriti Lohani | 2026-11-15 |
| `origin/feat/loop5-independent-validation-and-demo` | `a9806ae` | Akriti Lohani | 2026-11-20 |
| `origin/feat/loop6-release-integrity-and-reproducibility` | `360c3fb` | DocuReady Auditor | 2026-11-19 |
| `origin/feature/g1-package-migration` | `31f2d4f` | Smarak Padhi | 2026-11-14 |
| `origin/feature/mobile-web-mvp` | `7efebb9` | Smarak Padhi | 2026-11-15 |
| `origin/feature/prototype-decision-safety` | `f78f0e6` | Smarak Padhi | 2026-11-14 |
| `origin/feature/prototype-ui-privacy` | `c7bcbdc` | Smarak Padhi | 2026-11-14 |
| `origin/fix/G0.1-post-merge-ci-hardening` | `d3684a3` | Smarak Padhi | 2026-11-14 |
| `origin/fix/T2.1-evidence-provenance` | `d8663d2` | Susmita Rana | 2026-11-15 |
| `origin/fix/T2.1-post-merge-stabilization` | `439bfd2` | Akriti Lohani | 2026-11-15 |
| `origin/fix/T2.3-acceptance-hardening-corrections` | `5e1684b` | Agent 2 (T2.2) | 2026-11-15 |
| `origin/fix/T2.3-final-acceptance-remediation` | `04f83d2` | Deeptiman Parida | 2026-11-16 |
| `origin/fix/T2.4-classification-hardening` | `96d00fa` | Akriti Lohani | 2026-11-16 |
| `origin/fix/T2.4-post-merge-hardening` | `0ed1c74` | Akriti Lohani | 2026-11-20 |
| `origin/fix/pyyaml-direct-dev-dependency` | `b75ef85` | Akriti Lohani | 2026-11-15 |
| `origin/fix/vercel-static-product-site` | `d419d2a` | Deeptiman Parida | 2026-11-15 |
| `origin/fix/windows-release-qualification-post-pr81` | `70eb10e` | Akriti Lohani | 2026-11-21 |
| `origin/main` | `392ce9a` | Akriti Lohani | 2026-11-21 |
| `origin/task/T0.2-ci-that-exercises-ocr` | `87ada00` | Akriti Lohani | 2026-11-14 |
| `origin/task/T0.2-ocr-success-proof` | `53d494b` | Smarak Padhi | 2026-11-15 |
| `origin/task/T1.1-claims-register` | `0e103fd` | Akriti Lohani | 2026-11-15 |
| `origin/task/T1.1-claims-register-corrective` | `ddec213` | Smarak Padhi | 2026-11-15 |
| `origin/task/T1.2-telemetry-off-no-network` | `5f2cc42` | Akriti Lohani | 2026-11-15 |
| `origin/task/T1.3-pdf-backend-licensing` | `0919c8c` | Smarak Padhi | 2026-11-15 |
| `origin/task/T1.3-pdf-backend-licensing-corrective` | `f237b77` | Smarak Padhi | 2026-11-15 |
| `origin/task/T1.4-redaction-safe-logging` | `fa966dd` | Smarak Padhi | 2026-11-15 |
| `origin/task/T1.4-redaction-safe-logging-corrective` | `d625e5e` | Smarak Padhi | 2026-11-15 |
| `origin/task/T1.5-citation-audit` | `8920519` | Smarak Padhi | 2026-11-15 |
| `origin/task/T1.5-citation-audit-corrective` | `602b663` | Smarak Padhi | 2026-11-15 |
| `origin/task/T2.2-per-rule-test-matrix` | `5c4a504` | Susmita Rana | 2026-11-15 |
| `origin/task/T2.2-validator-fixture-matrix` | `7a04ef3` | Agent 2 (T2.2) | 2026-11-15 |
| `origin/task/T3.1-pack-schema-loader-lint` | `d6f9fd1` | Deeptiman Parida | 2026-11-16 |
| `origin/task/T3.2-primitives-generic-demo-port` | `db20885` | Deeptiman Parida | 2026-11-17 |
| `origin/task/T3.2.1-post-merge-safety-equivalence` | `97f98d5` | Deeptiman Parida | 2026-11-17 |
| `origin/test/T2.2-validator-matrix-assertion-hardening` | `793739c` | Agent 2 (T2.2) | 2026-11-15 |

---

## 4. GitHub Pull Request Refs (`origin/pr/*`, 82 Refs)

All `origin/pr/1` through `origin/pr/83` refs are read-only GitHub PR mirror refs corresponding to the PRs already integrated into or superseded by `origin/main` (`392ce9a`).
