# DocuReady — Package Architecture Gap Inventory (Task T0.3 / Gate G0)

**Date:** 14 November 2026  
**Auditor / Owner:** Akriti Lohani (Platform, Privacy & Delivery Lead)  
**Target Architecture Reference:** `docs/ARCHITECTURE_V2.md` §10  
**Current Baseline Git Commit:** `272fd5f530938b27d67c5db60e595100e2144d8e`  
**Status:** Audit & Gap Inventory (Strictly Non-Modifying)

---

## 1. Executive Summary

Task T0.3 verifies the current packaging and distribution contracts of DocuReady following the initial package migration in PR #1 (`feature/g1-package-migration`). This document audits the actual package layout under `src/docuready/`, dependency placements in `pyproject.toml`, and optional extras declarations, explicitly comparing them against the target V2 architecture specified in `docs/ARCHITECTURE_V2.md` §10.

All identified differences are categorized into **Verified Present-State Gaps** (actual structural or dependency deviations) versus **Recommended Future Actions** with their corresponding backlog task assignments. In accordance with T0.3 scope boundaries, no architecture reorganization, dependency splitting, or downstream refactorings are executed within this PR.

---

## 2. Existing Package Structure Audit

The DocuReady source tree currently resides under `src/docuready/` (established in PR #1).

### 2.1 Current File & Module Inventory

```
src/docuready/
├── __init__.py                  # Exposes __version__ = "0.1.0"
├── generator.py                 # Synthetic document PDF generator (ReportLab)
├── pipeline.py                  # AuditPipeline orchestration entry point
├── domain/
│   ├── __init__.py
│   └── models.py                # Pydantic models, Enums, Evidence, Finding, AuditResult
├── evidence/
│   ├── __init__.py
│   └── calibrator.py            # ConfidenceCalibrator and field syntax validators
├── ingest/
│   ├── __init__.py
│   └── extractor.py             # Monolithic PDF (PyMuPDF) and OCR (pytesseract) extractor
├── interfaces/
│   ├── __init__.py
│   ├── cli.py                   # argparse CLI console script entry point (main)
│   └── ui/
│       ├── __init__.py
│       └── app.py               # Streamlit web application interface
├── normalize/
│   ├── __init__.py
│   └── normalizer.py            # Demographic normalizers (name, date, money, certs)
├── outcome/
│   ├── __init__.py
│   └── safety_layer.py          # Track B PASS verification and non-rejection checks
├── report/
│   ├── __init__.py
│   └── exporter.py              # Markdown and JSON report generator with PII redaction
└── rules/
    ├── __init__.py
    └── validator.py             # Hardcoded statutory rule validation functions (34 rules)
```

---

## 3. Current Dependencies & Optional Extras Analysis

### 3.1 Core Dependencies (`pyproject.toml`)

Currently declared under `[project.dependencies]`:

| Dependency | Current Version Pin / Specifier | Role in Codebase | Target Architecture Status |
|---|---|---|---|
| `pydantic` | `>=2.0.0` | Core domain models, validation, serialization | **Core** (Retain) |
| `pymupdf` | `==2.1` | Native PDF vector text extraction & rasterization | **Misplaced** (Belongs in optional extra `[pymupdf]`; see ADR-001) |
| `pillow` | `>=10.0.0` | Image handling for OCR decompression & rotation | **Core / OCR Dependent** |
| `numpy` | `>=1.24.0` | Array and image manipulation operations | **Core / OCR Dependent** |
| `pytesseract` | `>=0.3.10` | Python wrapper around external Tesseract OCR executable (engine/languages required only during OCR invocation, not vector extraction) | **Misplaced** (Unconditional core dependency; belongs in optional extra `[ocr]`) |

### 3.2 Optional Extras (`[project.optional-dependencies]`)

Currently declared under `[project.optional-dependencies]`:

| Extra Group | Declared Dependencies | Current Alignment with V2 Target |
|---|---|---|
| `ui` | `["streamlit>=1.30.0"]` | **Aligned** (Enables Streamlit web UI without bloating headless CLI) |
| `generator` | `["reportlab>=4.0.0"]` | **Present** (Enables synthetic test data generator in `src/docuready/generator.py`) |
| `dev` | `["pytest>=7.4.0", "pytest-cov>=4.1.0", "build>=1.0.0", "setuptools>=61.0.0", "wheel"]` | **Aligned** (Covers test runners, build backends, and coverage tooling) |
| `all` | `["streamlit>=1.30.0", "reportlab>=4.0.0", "pytest>=7.4.0", "pytest-cov>=4.1.0", "build>=1.0.0", "setuptools>=61.0.0", "wheel"]` | **Composite extra** (Convenience aggregate) |

---

## 4. Architectural Comparison: Present State vs. Target V2 Layout

| Component / Subsystem | Present Repository State (`main`) | Target V2 Architecture (`ARCHITECTURE_V2.md` §10) | Verified Gap Status |
|---|---|---|---|
| **Root Package Placement** | `src/docuready/` | `src/docuready/` | **MATCH** (Delivered in PR #1) |
| **Console Entry Point** | `docuready = "docuready.interfaces.cli:main"` | `docuready` console script | **MATCH** (Delivered in PR #1) |
| **Domain Modeling** | Monolithic `src/docuready/domain/models.py` | Granular `domain/{enums.py, models.py, facts.py, errors.py}` | **GAP**: Domain models, facts, enums, and exceptions not yet decomposed |
| **PDF Ingestion & Backends** | Hardcoded PyMuPDF 2.1 in `ingest/extractor.py` | Pluggable `ingest/pdf_backend/{base,pdfium,pymupdf}.py` behind `PdfBackend` interface | **GAP**: Backend abstraction absent; PyMuPDF is a direct core dependency (ADR-001) |
| **OCR Decoupling** | Direct pytesseract call in `ingest/extractor.py` | Decoupled `ingest/ocr.py` under optional `[ocr]` extra | **GAP**: OCR tightly coupled to core extractor; `[ocr]` extra absent |
| **Extract Subpackage** | None (extraction logic embedded in `ingest/extractor.py`) | Dedicated `extract/{classify.py, fields/, provenance.py}` | **GAP**: Dedicated `extract/` namespace missing |
| **Evidence & Calibration** | Single `evidence/calibrator.py` | Granular `evidence/{features.py, calibrator.py, states.py}` | **GAP**: Feature extractors and tri-state evidence models not separated |
| **Normalization** | Single `normalize/normalizer.py` | Granular `normalize/{names.py, dates.py, money.py, ids.py, digits.py}` | **GAP**: Specialized normalizers combined in one module |
| **Rules Engine** | Hardcoded 34 rules in `rules/validator.py` | Closed primitive engine `rules/{engine.py, primitives.py, loader.py, schema.py, lint.py}` | **GAP**: YAML rule packs and closed evaluation primitives not yet implemented |
| **Outcome Resolution** | Prototype `outcome/safety_layer.py` (current pipeline reports `overall_status: READY_TO_SUBMIT` with score 100 on clean packets) | Symmetric `outcome/resolver.py` with unified public status vocabulary (ADR-003) | **GAP**: V2 symmetric outcome resolver and status vocabulary not finalized; current pipeline emits `overall_status: READY_TO_SUBMIT` (preserved as existing behavior for future T2.1 review without in-flight vocabulary changes) |
| **Report Generation** | Single `report/exporter.py` | Granular `report/{builder.py, render_json.py, render_md.py, redact.py}` | **GAP**: Redaction and rendering pipelines not split into distinct modules |
| **Synthetic Generators** | `src/docuready/generator.py` inside core source tree | `eval/generators/` outside production package | **GAP**: Synthetic test data generation resides inside production runtime package |
| **Rule Packs Directory** | None (`packs/` missing) | `packs/{generic.demo/, odisha.subhadra/}` | **GAP**: External declarative rule packs not yet established |
| **Evaluation Tree** | None (`eval/` missing) | `eval/{generators/, data/, harness.py, baseline.json, EVAL_CARD.md}` | **GAP**: Evaluation split harness and evaluation cards absent |
| **Telemetry Configuration** | None (`.streamlit/config.toml` missing) | Committed `.streamlit/config.toml` with `browser.gatherUsageStats = false` | **GAP**: Telemetry suppression configuration uncommitted |
| **Licensing Documentation** | Apache-2.0 `LICENSE` present; `NOTICE` missing | `LICENSE` + `NOTICE` (third-party AGPL/provisional licensing disclosure) | **GAP**: Formal `NOTICE` file documenting provisional PyMuPDF caveat absent |

---

## 5. Dependency & Extra Placement Gap Inventory

### Gap DEP-01: Core Ingestion Couples AGPL-3.0 PyMuPDF
- **Description:** `pymupdf==2.1` is listed in `[project.dependencies]`, making the entire core distribution depend on an AGPL-licensed library by default.
- **Target Contract (ADR-001):** Core should depend on a permissive backend (e.g., `pypdfium2` / `pdfminer.six`), with PyMuPDF available only via optional extra `[pymupdf]`.
- **Governing Task:** Task **T1.3** (PDF backend / licence decision, Gate G1).
- **T0.3 Boundary:** Must **not** be modified in T0.3.

### Gap DEP-02: Core Package Couples Tesseract OCR Wrapper
- **Description:** `pytesseract>=0.3.10` is currently declared as an unconditional dependency under core `[project.dependencies]`. `pytesseract` is a Python wrapper around the external Tesseract OCR executable; installing the Python wrapper does not itself install the external Tesseract engine executable or trained language data. Furthermore, the external engine is only required when OCR functionality is explicitly invoked for scanned or unreadable raster pages, and is not required for native vector-only PDF extraction.
- **Target Contract:** OCR capability and its wrapper should be decoupled into an optional acceleration extra: `docuready[ocr]`.
- **Governing Task:** Task **T1.3** (PDF backend / licence decision, Gate G1).
- **T0.3 Boundary:** Must **not** be modified in T0.3.

### Gap DEP-03: Production Package Bundles Test Generator
- **Description:** `src/docuready/generator.py` and extra `[generator]` (ReportLab) are bundled inside `src/docuready/`.
- **Target Contract:** Synthetic packet generation belongs under `eval/generators/` and should not be part of the end-user wheel distribution.
- **Governing Task:** Task **T4.3** (Generator v2, Gate G5).
- **T0.3 Boundary:** Must **not** be relocated in T0.3.

---

## 6. Recommended Future Actions & Ownership Matrix

| Gap ID | Recommended Future Action | Target Gate | Owning Backlog Task | Assigned Lead |
|---|---|---|---|---|
| **GAP-01** | Commit `.streamlit/config.toml` to disable usage statistics and verify no-network contract | G1 | **T1.2** | Akriti |
| **GAP-02** | Introduce `PdfBackend` interface, evaluate permissive engines (`pypdfium2`), create `[pymupdf]` extra, and add `NOTICE` file | G1 | **T1.3** (ADR-001) | Akriti |
| **GAP-03** | Separate OCR dependencies into `[ocr]` extra; isolate OCR fallback invocation behind clear interface | G1 | **T1.3** | Akriti |
| **GAP-04** | Formalize PII redaction pipeline in `report/redact.py` with strict regex masking and safe logging | G1 | **T1.4** | Akriti |
| **GAP-05** | Decompose `domain/models.py` into `enums.py`, `models.py`, `facts.py`, and `errors.py` | G1/G2 | **T2.1** | Susmita |
| **GAP-06** | Replace hardcoded `outcome/safety_layer.py` with symmetric `outcome/resolver.py` implementing single public vocabulary | G2 | **T2.1** (ADR-003) | Susmita |
| **GAP-07** | Replace `rules/validator.py` with closed-primitive YAML pack engine `rules/{engine,primitives,loader,schema,lint}.py` | G3 | **T3.1 & T3.2** (ADR-002) | Susmita |
| **GAP-08** | Create `packs/` directory containing `generic.demo/` and `odisha.subhadra/` demo snapshots | G3/G4 | **T3.2 & T3.3** | Susmita |
| **GAP-09** | Move `src/docuready/generator.py` to `eval/generators/` and establish `eval/` benchmark tree | G5 | **T4.1 & T4.3** | Susmita |

---

## 7. Conclusion & Gate G0 Compliance Statement

The existing package structure under `src/docuready/` satisfies all prerequisite contracts for Gate G0:
1. Console script `docuready` is functional and correctly registered.
2. Clean editable installation with currently declared extras (`ui`, `generator`, `dev`) is supported and verified.
3. Distribution sdist and wheel builds succeed without error.
4. Installed wheel functions correctly in an isolated environment outside the repository.
5. Golden baseline snapshot (`tests/golden/legacy_v0/GOLDEN_BASELINE.json`) remains 100% byte-identical (SHA-256 `E8FB1A6B842A47089937777133DE79E1E7F704BEE591D5B4471A1A90BC8C5FA9`).
6. All structural and dependency differences relative to V2 are comprehensively cataloged above, ensuring zero premature or unauthorized refactorings occur prior to Gate G1.
