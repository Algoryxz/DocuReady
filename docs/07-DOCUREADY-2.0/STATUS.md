# DocuReady 2.0 — Status Tracker

**Last Updated:** 28 November 2026
**Previous Baseline SHA:** `9e2b4cf84c8cc0b562dad5de317d44ce23da0783` (PR #99)
**Updated `origin/main` SHA:** `f85e46a05c3bdb4895773fc82793c82e24cf5908` (PR #101)
**Historical Gate Status:** See [../STATUS.md](../STATUS.md) for Loop 1–47 / Gate G0–G5 records.

---

## Active Workstreams

| Workstream | Owner | Branch (Proposed if not yet created) | PR / Historical Ref | State | Blockers / Notes |
|---|---|---|---|---|---|
| **Docs & Baseline** | Team | `docs/docuready-2.0-kickoff-baseline` | [PR #99](https://github.com/Algoryxz/DocuReady/pull/99) (`merged`, `9e2b4cf`) | `merged` | Merged to `main` (`9e2b4cf`) as shared DocuReady 2.0 baseline. |
| **CI Memory Stability** | Antigravity | `fix/ci-memory-stability-docuready-2` | [PR #100](https://github.com/Algoryxz/DocuReady/pull/100) (`merged`, `c3d48ab`, head `bf045e2`) | `merged` | Stabilized Loop 03/04 memory tests and PIL lifecycle cleanup. Passed `CI Tests` ([46151091128](https://github.com/Algoryxz/DocuReady/actions/runs/46151091128), Python 3.11–3.14) and `Windows desktop release qualification` ([46151091118](https://github.com/Algoryxz/DocuReady/actions/runs/46151091118)). Follow-up Loop 03 test-validity hardening on `fix/loop03-memory-test-validity`. |
| **CI/CD → Frontend & QA** | Deepti | `fix/ci-cd-deepti` *(proposed)* | [PR #94](https://github.com/Algoryxz/DocuReady/pull/94) (`merged`, `b66b82b`) | `active` | Phase 1: CI/CD & Windows release pipeline (PR #94 merged). Phase 2: pair with Frontend owner on integration & QA. |
| **Testing & Quality** | Akriti | `feat/t4-2-indic-ocr-evaluation-corpus` | [PR #101](https://github.com/Algoryxz/DocuReady/pull/101) (`merged`, `f85e46a`) | `active` | PR #95 Indic dedup & PR #101 T4.2 Indic OCR evaluation corpus merged; Akriti's full 24-document paired OCR accuracy benchmark remains pending. |
| **Backend & Doc Intelligence** | Susmita | `feat/backend-susmita` *(proposed)* | — | `ready` | Own `src/docuready/**`, `sidecar/`, `packs/**`, API contracts, extraction/normalization/validation & regression compatibility. |
| **Frontend & Electron** | Project frontend owner | `feat/frontend-electron` *(proposed)* | — | `ready` | Own `apps/desktop/**`, Evidence Review Workspace, doc nav & finding-panel workflows, backend integration, Windows installer & `site/` download section. |

---

## Merged Upstream PRs (`9717ae5..f85e46a`)

- **PR #94 (`b66b82b`, `fix/ci-verification-stabilisation`):** **Merged.** Stabilized cross-platform OCR, POSIX `adaptive_ocr.py` tessdata resolution, probe diagnostics, and `.github/workflows/windows-release-qualification.yml`.
- **PR #95 (`1eca2a5`, `fix/T4.2-indic-candidate-dedup`):** **Merged.** Normalized Indic digits in OCR candidate deduplication (`src/docuready/ingest/extractor.py`, `tests/test_extractor.py`).
- **PR #96 (`0e14a6e`, `fix/ocr-tessdata-and-benchmark-integrity`):** **Merged.** Resolved system tessdata, verified loaded languages/symbols, and enforced dataset provenance hashes (`adaptive_ocr.py`, `tesseract_discovery.py`, `generate_dataset_provenance.py`).
- **PR #97 (`70b7ea5`, `fix/final-ocr-benchmark-review`):** **Merged.** Completed extra tessdata discovery, enforced audit manifest checks, and added unavailable probe spy tests (`tesseract_discovery.py`, `tests/test_tesseract_discovery.py`).
- **PR #98 (`aa29d07`, `fix/ocr-cache-identity-and-manifest-type`):** **Merged.** Verified cached `.traineddata` identity by size and SHA-256 (`_files_match` in `tesseract_discovery.py`) and rejected boolean `file_size_bytes` in benchmark provenance checks (`tests/test_loop12_benchmark_integrity.py`). Passed `CI Tests` ([46147105166](https://github.com/Algoryxz/DocuReady/actions/runs/46147105166)) and `Windows desktop release qualification` ([46147105057](https://github.com/Algoryxz/DocuReady/actions/runs/46147105057)).
- **PR #99 (`9e2b4cf`, `docs/docuready-2.0-kickoff-baseline`):** **Merged.** Established `docs/07-DOCUREADY-2.0/` baseline documentation. `CI Tests` ([46148680787](https://github.com/Algoryxz/DocuReady/actions/runs/46148680787)) on `9e2b4cf` failed on Python 3.11 & 3.12 due to Loop 03/04 RSS memory test methodology (`test_repeated_deskew_memory_stability` and `test_memory_stability_across_repeated_deskew_ingestion`).
- **PR #100 (`c3d48ab`, `fix/ci-memory-stability-docuready-2`, head `bf045e2`):** **Merged.** Fixed Loop 03/04 memory measurement methodology, closed temporary PIL image buffers in `deskew.py` and `extractor.py`, and reconciled `docs/07-DOCUREADY-2.0/`. Verified on PR head `bf045e2` by `CI Tests` ([46151091128](https://github.com/Algoryxz/DocuReady/actions/runs/46151091128), Python 3.11–3.14) and `Windows desktop release qualification` ([46151091118](https://github.com/Algoryxz/DocuReady/actions/runs/46151091118)).
- **PR #101 (`f85e46a`, `feat/t4-2-indic-ocr-evaluation-corpus`):** **Merged.** Added the T4.2 Indic OCR evaluation corpus (synthetic-only; does not constitute real-world OCR accuracy validation). Akriti's full 24-document paired OCR accuracy benchmark remains pending.

## Release & Licensing Gates

- **Windows Qualification Artifacts:** Existing GitHub Actions qualification artifacts are temporary CI outputs, not a permanent public release.
- **Distribution & Licensing Gate:** **OPEN** — AGPLv3/PyMuPDF/MuPDF (`pymupdf==2.1`) distribution clearance (`LICENSING_DECISION.md`) requires a qualified licensing review of third-party license obligations, corresponding-source, and notice requirements before public distribution. No legal clearance is claimed.