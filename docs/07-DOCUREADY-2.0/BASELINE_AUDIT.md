# DocuReady 2.0 — Baseline Forensic Audit

**Audit Date:** 28 November 2026 (Previous baseline: `9717ae5`)
**Inspected `origin/main` SHA:** `70b7ea5f001a5a30404a13b7d347527c641a434b`
**Audit Method:** Parallel read-only inspection of `src/`, `sidecar/`, `packs/`, `eval/`, `apps/desktop/`, `site/`, `.github/workflows/`, `tests/`, and `docs/` + GitHub CLI (`gh`) inspection of PR #94 and Actions runs.

---

## 1. Repository Structure (Verified on `origin/main`)

| Path | Role |
|---|---|
| `src/docuready/` | Core Python audit package (`domain/`, `ingest/`, `evidence/`, `normalize/`, `outcome/`, `rules/`, `report/`, `interfaces/`, `pipeline.py`) |
| `sidecar/` | Standalone Python JSON-RPC stdio bridge (`docuready_sidecar.py`, `docuready_sidecar.spec`) |
| `apps/desktop/` | Electron 45.3.2 + React 19.2 + Vite 8.0 + PDF.js 6.5.438 Windows desktop app (`src/main.ts`, `src/preload.ts`, `src/main/`, `src/shared/`, `src/renderer/`, `tests/`) |
| `packs/` | Declarative YAML scheme packs (`generic.demo/` [`draft`], `odisha.subhadra/` [`demo_snapshot`]) |
| `eval/` | Synthetic-only evaluation harness (`harness.py`, `EVAL_CARD.md`, `reports/backend_comparison.md`) |
| `synthetic_data/` | Synthetic test packets (`pkt_01_clean` .. `pkt_08`, `ground_truth_manifest.json`) |
| `tests/` | 80 Python test files (`unit/`, `integration/`, `contract/`, `golden/legacy_v0/`, `test_loop*.py`) |
| `site/` | Static Vercel informational website (`index.html`, `vercel.json`) — **does not process documents** |
| `scripts/` | Release qualification (`verify_clean_windows_runtime.ps1`), privacy audit (`network_privacy_audit.py`), PDF backend eval |
| `docs/` | Governance, architecture, ADRs, historical `LOOP_*` logs (363 files), `04-VALIDATION/` (46 files), `history/` |
| `research/` | Historical loop research records (`loop16`–`loop47`, `repository-consolidation/`) |

---

## 2. Implemented / Partial / Missing / Unverified Matrix

| Capability | Status | Evidence (Exact Symbols & Paths) |
|---|---|---|
| **Python `AuditPipeline` & CLI** | Implemented | `src/docuready/pipeline.py` (`AuditPipeline.load_and_audit_packet`, `replace_document_and_reaudit`); `src/docuready/interfaces/cli.py` (`audit`, `benchmark`, `packs lint`) |
| **Vector & Local OCR Extraction** | Implemented | `src/docuready/ingest/extractor.py` (`DocumentExtractor.extract_document`, `_parse_fields_vector`, `_ocr_page`), `deskew.py`, `spatial_layout.py` |
| **9-Feature Confidence Calibrator** | Implemented | `src/docuready/evidence/calibrator.py` (`ConfidenceCalibrator`), `features.py`, `states.py` (`VERIFIED`, `PROVISIONAL`, `UNCERTAIN`) |
| **Normalizers (Indic digits, Verhoeff, Dates, INR, IFSC)** | Implemented | `src/docuready/normalize/normalizer.py` (`normalize_indic_digits`, `validate_verhoeff`, `parse_and_normalize_date`, `normalize_income`, `validate_ifsc_code`, `compare_names`) |
| **Hardcoded Scholarship Validator & Safety Layer** | Implemented | `src/docuready/rules/validator.py` (`DocuReadyValidator`), `src/docuready/outcome/safety_layer.py` (`DecisionSafetyLayer`), `resolver.py` |
| **Declarative Pack Engine (`PackExecutionEngine`)** | Partial (Disconnected from prod) | `src/docuready/rules/engine.py`, `loader.py`, `lint.py`, `primitives.py` — runs in `eval/harness.py` and tests, **not** wired into `AuditPipeline`, CLI, or sidecar |
| **Adaptive & Region-Aware OCR** | Partial (Disconnected) | `src/docuready/ingest/adaptive_ocr.py` (`execute_adaptive_ocr`), `region_ocr.py` (`ocr_page_by_regions`) — not called by `DocumentExtractor` |
| **Cross-doc Identity & Table Association** | Partial (Disconnected) | `src/docuready/evidence/cross_document.py`, `ingest/table_association.py` — not called by `DocumentExtractor` or `DocuReadyValidator` |
| **Desktop 3-Panel Evidence Viewer** | Implemented | `apps/desktop/src/renderer/components/{DocumentNav,EvidenceViewer,FindingPanel}.tsx`, `shared/{coordinates,evidence}.ts` |
| **Desktop Scheme Selector** | Stubbed / Disconnected | `apps/desktop/src/renderer/main.tsx:384-393` renders `scheme-select`, `workspace.ts` stores `schemeId`, but `ipc.ts:182-186` and `docuready_sidecar.py:195` ignore it |
| **Desktop Single-Doc Replacement & Re-audit** | Missing in Desktop (Exists in Python) | `AuditPipeline.replace_document_and_reaudit` exists in Python; Electron UI has no per-slot/per-doc replace action |
| **Desktop Guided Slot Checklist & Raw/Normalized View** | Missing | UI uses flat `+ Add Documents`; `ExtractedDocumentSummary` in `types.ts:157-162` is never rendered |
| **Session-Level Human Review Annotations** | Missing | Static `getReviewGuidance` only (`FindingPanel.tsx:33-51`); no annotation state or export |
| **Permissive PDF Backend (`PdfiumDocumentBackend`)** | Incomplete | `src/docuready/ingest/pdf_backend/pdfium_backend.py` raises `NotImplementedError` on `get_words()` |
| **Real-World OCR / Field Accuracy** | `UNVERIFIED` | `eval/EVAL_CARD.md` covers synthetic `test` split only (`n=48`: `0/24` false-pass, `0/24` false-fail, `12.5%` coverage, `87.5%` abstention); `T4.4` is protocol-only |
| **Loop 10 Frozen Release Artifacts on Disk** | `UNVERIFIED` (not in git tree) | `apps/desktop/out/` does not exist in clean `origin/main` checkout; hashes are recorded in `LOOP_32_RELEASE_HASH_RECONCILIATION.md` and `docs/04-VALIDATION/LOOP_10_FEATURE_FREEZE_RECORD.md` |

---

## 3. Known Limitations, Bugs & Discrepancies

1. **Scheme pack selection disconnected (`ipc.ts:182-186`, `docuready_sidecar.py:195`):** `schemeId` is never passed from IPC to the sidecar, and `AuditPipeline` does not execute `PackExecutionEngine`.
2. **Sidecar contract mismatches (`sidecar/docuready_sidecar.py` vs `sidecar/README.md`):**
   - `MAX_PAGE_COUNT_PER_DOC = 50` (`docuready_sidecar.py:19`) is defined but never enforced in `_handle()`.
   - `200MB per packet` limit in `sidecar/README.md:21` is enforced in `workspace.ts`, not in `docuready_sidecar.py`.
   - `health` returns `"tesseract_path": ocr_info.get("binary_path")` (`docuready_sidecar.py:146`), exposing the full host path contrary to `sidecar/README.md:45`.
   - Progress stages emit `1 → 2 → 3 → 5`, skipping stage `4`.
3. **Pack / Model gaps:** `packs/odisha.subhadra/pack.yaml:48` declares `doc_slots.ration_card`, which is absent from `DocumentType` (`domain/models.py`) and `resolve_doc_type()` (`rules/primitives.py`).
4. **Redaction & logging gaps:**
   - `exporter.py:110` outputs `f.remediation` unredacted in Markdown when `redact=True`.
   - `redact_audit_result_dict()` (`redact.py:185-190`) expects `documents` as a `dict` with `fields[name]["value"]`, which `docuready_sidecar._document_summaries()` does not emit.
   - `docuready_sidecar.py:298-302` prints raw `exc_msg` to `stderr`; `ipc.ts:88` logs `filePath` via `console.warn`.
   - `SafeLogFilter` is only wired in `rules/engine.py` and `report/redact.py`.
5. **Indic script gaps:** `normalize_name()` strips non-`[A-Z\s]` characters (wiping Devanagari/Odia names); `detect_image_script_osd()` maps `"Devanagari"` and `"Latin"` but not Odia; pure scanned Indic docs default to `"eng"` without `--ocr-pack` because `execute_adaptive_ocr()` is disconnected.
6. **UI / Evidence gaps:** Filename substring matching (`main.tsx:94,313,339,355`) links findings to documents; image bounding boxes use `img.naturalWidth`/`naturalHeight` (`EvidenceViewer.tsx:339-346`) whose parity with Python image-ingestion coordinates is `UNVERIFIED`; `DiagnosticReport.workspaceHealth` hardcodes `status: "healthy"` and `staleWorkspacesCleaned: 0` (`ipc.ts:329-330`).
7. **Duplicated code:** `extractor.py:996-997` duplicates `add_field_func("aadhaar_no", ...)`; Verhoeff logic is duplicated in `identifier_validation.py` and `normalizer.py`; `_get_ocr_availability()` in `docuready_sidecar.py:101` is dead code.

---

## 4. CI/CD State & Exact Run IDs

All workflows use **GitHub-hosted runners** (`ubuntu-24.04` and `windows-2022`). No self-hosted runners.

| Target | Workflow | Run ID | Status / Conclusion | Key Findings |
|---|---|---|---|---|
| `main` (`9717ae5`) | `CI Tests` | `46129673099` | `failure` | Baseline failures: `test_loop09_release_integrity.py` (missing `apps/desktop/out/DocuReady-win32-x64`), `test_loop10_demo_reliability.py` (missing `DocuReady.exe`), `test_loop12_benchmark_integrity.py` (missing `research/loop11_benchmark/data/funsd/funsd_001.pdf`), `test_loop14_multilingual_ocr.py`, `test_loop41_inprocess_reliability.py`, `test_loop44_upper_band.py`, `test_loop46_indic_header_latin_body.py`. |
| `main` (`9717ae5`) | `Windows desktop release qualification` | `46129673088` | `failure` | Failed on `main` baseline. |
| PR #94 (`fix/ci-verification-stabilisation`) | `CI Tests` & `Windows desktop release qualification` | `46140310777` / `b66b82b` | **merged** | Merged into `main` (`b66b82b`): stabilized cross-platform OCR, POSIX `adaptive_ocr.py` tessdata resolution, probe diagnostics, and Windows CI workflow. |
| PR #95 (`fix/T4.2-indic-candidate-dedup`) | OCR candidate dedup | `1eca2a5` | **merged** | Merged into `main` (`1eca2a5`): normalized Indic digits in OCR candidate deduplication (`extractor.py`, `tests/test_extractor.py`); broader T4.2/quality work continues. |
| PR #96 (`fix/ocr-tessdata-and-benchmark-integrity`) | OCR & benchmark integrity | `0e14a6e` | **merged** | Merged into `main` (`0e14a6e`): resolved system tessdata, verified loaded langs/symbols, and enforced dataset provenance hashes (`tesseract_discovery.py`, `generate_dataset_provenance.py`). |
| PR #97 (`fix/final-ocr-benchmark-review`) | OCR & benchmark review | `70b7ea5` | **merged** | Merged into `main` (`70b7ea5`): completed extra tessdata discovery, enforced audit manifest checks, and added unavailable probe spy tests. |

---

## 5. Security, Privacy & Release Freeze Safeguards

- **Electron hardening:** `contextIsolation: true`, `nodeIntegration: false`, `sandbox: true`, `webSecurity: true`, popup/navigation guards, CSP `connect-src 'self'`, `validateIpcSender` on all 10 IPC channels, and `PDF.js` `cMapUrl: undefined`.
- **Network isolation caveat:** `tests/contract/test_no_network.py` monkeypatches Python sockets; `scripts/network_privacy_audit.py` uses 50ms `psutil` polling (not kernel-level ETW/WFP). Do **not** claim `"100% Offline"` or `"zero-egress guarantee"`.
- **AGPLv3 blocker:** `pymupdf==2.1` is AGPLv3; `LICENSING_DECISION.md` §5 marks legal distribution clearance `OPEN`.
- **Frozen release safeguards:** Do not modify `tests/golden/legacy_v0/GOLDEN_BASELINE.json` (SHA-256 `E8FB1A6B842A47089937777133DE79E1E7F704BEE591D5B4471A1A90BC8C5FA9`), `docs/04-VALIDATION/LOOP_10_FEATURE_FREEZE_RECORD.md`, `docs/LOOP_*.md`, `docs/history/`, or `research/`.

---

## 6. Documentation Contradiction Register (Summary)

1. **Duplicate `ADR-002`:** `ADR-002-deployment-architecture.md` (Streamlit 3-tier) vs `ADR-002-desktop-runtime-and-sidecar.md` (Electron + Sidecar).
2. **Competing Architecture & Roadmap docs:** `docs/02-ARCHITECTURE/SYSTEM_ARCHITECTURE.md` (V1 `src/ui.py`, 7-state `EvidenceState`) vs `docs/ARCHITECTURE_V2.md`; `docs/06-ROADMAP/PRODUCT_ROADMAP.md` (Streamlit/WhatsApp/Flutter/DigiLocker) vs Desktop reality.
3. **Stale `README.md` badges & paths:** Static `Desktop Tests-25/25` and `Python Tests-916` badges, broken `(apps/desktop/out/make)` link, `apps/desktop/src/sidecar.ts` (actual: `src/main/sidecar.ts`), and omitted T4.1 `EVAL_CARD.md` coverage/abstention metrics.
4. **Website (`site/index.html`) drift:** Links to non-existent `#installation--setup` anchor and still describes the local app as "the Python/Streamlit application".
5. **UI offline overstatement:** `apps/desktop/src/renderer/main.tsx:486` displays `"100% Offline · Local Workspace"`, contradicting `PRIVACY_NETWORK_AUDIT.md` and `CLAIMS_REGISTER.md`.
