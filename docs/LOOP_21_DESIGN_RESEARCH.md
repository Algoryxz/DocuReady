# LOOP 21: Design Research & Desktop UI Freeze Audit

## 1. Governance & Scope Inspection

Per the Loop 21 Engineering Directive and the HackNation 2026 freeze mandate:
- **Loop 10 Competition Release**: FROZEN and PROTECTED at commit `bdc403a`.
- **Target Executables**: `apps/desktop/out/DocuReady-win32-x64/` (`DocuReady.exe`, `app.asar`, `docuready_sidecar.exe`) are bit-exact and immutable.
- **Frontend / Electron Codebase**: `apps/desktop/` is frozen; changes are restricted to research experiments in Python sidecar modules (`src/docuready/ingest/` and `src/docuready/outcome/`).

---

## 2. Awesome Design MD Catalog Review

We evaluated the principles in [voltagent/awesome-design-md](https://github.com/voltagent/awesome-design-md), specifically:
- **Hierarchical Field Breadcrumbs**: When presenting data from multi-tier tables, interfaces must display the full contextual path (e.g. `Quarter 1 Status → Q1 Actual: 38,500`) to prevent reviewer ambiguity.
- **High-Precision Numeric Legibility**: Decimal numbers and currency amounts must be formatted with consistent tabular numerals and clear visual separation from adjacent labels.
- **Traceable Coordinate Bounds**: Visual evidence overlays must map to the original document space, even when internal pre-scaling was applied during OCR.

---

## 3. UI Freeze Justification

Because the desktop frontend (`apps/desktop/`):
1. Already displays composite column header paths and hierarchical field labels via the established `FieldEvidence.col_header` contract.
2. Already supports normalized bounding box coordinate overlays on the un-scaled original PDF canvas.
3. Contains comprehensive triage badges for `REVIEW / MANUAL_REVIEW`, `VERIFIED_TEXT`, and `MISMATCH`.

**NO changes to the desktop UI are required in Loop 21**. All improvements in header fusion and decimal preservation operate transparently through the existing sidecar IPC API.
