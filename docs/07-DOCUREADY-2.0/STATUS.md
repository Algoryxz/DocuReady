# DocuReady 2.0 — Status Tracker

**Last Updated:** 28 November 2026
**Previous Baseline SHA:** `9717ae56b3e672d0c6046ea4a918794db1cf1368`
**Updated `origin/main` SHA:** `70b7ea5f001a5a30404a13b7d347527c641a434b`
**Historical Gate Status:** See [../STATUS.md](../STATUS.md) for Loop 1–47 / Gate G0–G5 records.

---

## Active Workstreams

| Workstream | Owner | Branch (Proposed if not yet created) | PR / Historical Ref | State | Blockers / Notes |
|---|---|---|---|---|---|
| **Docs & Baseline** | Team | `docs/docuready-2.0-kickoff-baseline` | Pending PR | `in_review` | Rebased onto `70b7ea5`; must merge to `main` as shared starting point. |
| **CI/CD → Frontend & QA** | Deepti | `fix/ci-cd-deepti` *(proposed)* | [PR #94](https://github.com/Algoryxz/DocuReady/pull/94) (`merged`, `b66b82b`) | `active` | Phase 1: CI/CD & Windows release pipeline (PR #94 merged). Phase 2: pair with Frontend owner on integration & QA. |
| **Testing & Quality** | Akriti | `feat/pr95-akriti` *(proposed)* | [PR #95](https://github.com/Algoryxz/DocuReady/pull/95) (`merged`, `1eca2a5`) | `ready` | PR #95 Indic dedup merged; continue regression coverage, benchmark experiments, negative controls & before/after metrics. |
| **Backend & Doc Intelligence** | Susmita | `feat/backend-susmita` *(proposed)* | — | `ready` | Own `src/docuready/**`, `sidecar/`, `packs/**`, API contracts, extraction/normalization/validation & regression compatibility. |
| **Frontend & Electron** | Project frontend owner | `feat/frontend-electron` *(proposed)* | — | `ready` | Own `apps/desktop/**`, Evidence Review Workspace, doc nav & finding-panel workflows, backend integration, Windows installer & `site/` download section. |

---

## Merged Upstream PRs (`9717ae5..70b7ea5`)

- **PR #94 (`b66b82b`, `fix/ci-verification-stabilisation`):** **Merged.** Stabilized cross-platform OCR, POSIX `adaptive_ocr.py` tessdata resolution, probe diagnostics, and `.github/workflows/windows-release-qualification.yml`.
- **PR #95 (`1eca2a5`, `fix/T4.2-indic-candidate-dedup`):** **Merged.** Normalized Indic digits in OCR candidate deduplication (`src/docuready/ingest/extractor.py`, `tests/test_extractor.py`).
- **PR #96 (`0e14a6e`, `fix/ocr-tessdata-and-benchmark-integrity`):** **Merged.** Resolved system tessdata, verified loaded languages/symbols, and enforced dataset provenance hashes (`adaptive_ocr.py`, `tesseract_discovery.py`, `generate_dataset_provenance.py`).
- **PR #97 (`70b7ea5`, `fix/final-ocr-benchmark-review`):** **Merged.** Completed extra tessdata discovery, enforced audit manifest checks, and added unavailable probe spy tests (`tesseract_discovery.py`, `tests/test_tesseract_discovery.py`).

## Release & Licensing Gates

- **Windows Qualification Artifacts:** Existing GitHub Actions qualification artifacts are temporary CI outputs, not a permanent public release.
- **Distribution & Licensing Gate:** **OPEN** — AGPLv3/PyMuPDF/MuPDF (`pymupdf==2.1`) distribution clearance (`LICENSING_DECISION.md`) requires a qualified licensing review of third-party license obligations, corresponding-source, and notice requirements before public distribution. No legal clearance is claimed.