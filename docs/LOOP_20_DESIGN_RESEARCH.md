# LOOP 20: Design Research & Desktop UI Freeze Audit

## 1. Governance & Scope Inspection

Per the Loop 20 Engineering Directive and the HackNation 2026 freeze mandate:
- **Loop 10 Competition Release**: FROZEN and PROTECTED at commit `bdc403a`.
- **Target Executables**: `apps/desktop/out/DocuReady-win32-x64/` (`DocuReady.exe`, `app.asar`, `docuready_sidecar.exe`) are bit-exact and immutable.
- **Frontend / Electron Codebase**: `apps/desktop/` is frozen; changes are restricted to research experiments in Python sidecar modules (`src/docuready/ingest/` and `src/docuready/outcome/`) unless a visual defect necessitates a UI adjustment.

---

## 2. Awesome Design MD Catalog Review

We evaluated the principles in [voltagent/awesome-design-md](https://github.com/voltagent/awesome-design-md), specifically:
- **Clarity of Epistemic Uncertainty**: Interfaces conveying document analysis must never display ambiguous or unverified data with the same visual confidence as high-certainty data.
- **Explainable Abstention UX**: When an automated decision engine abstains, the reviewer interface must display the exact reason (e.g. "Low OCR confidence (41%)", "Multiple plausible candidate cells detected", "Column boundary ambiguous") rather than a generic error code.
- **Unbroken Evidence Localization**: Reviewers must be able to visually trace an extracted field to its exact bounding box coordinates in the original PDF canvas.

---

## 3. UI Freeze Justification & Parity Assessment

During Loop 9 and Loop 10, the Electron desktop client was engineered with:
1. **Interactive Evidence Viewer** (`EvidenceViewer.tsx`): Renders normalized bounding boxes directly over the original rendered PDF canvas.
2. **Reviewer Triage Taxonomy** (`AuditFindings.tsx`): Displays discrete badges for `REVIEW / MANUAL_REVIEW`, `VERIFIED_TEXT`, `AMBIGUOUS`, and `MISSING`.
3. **Traceability Sidebar**: Links findings to page index, field label, raw OCR text, and calibrated confidence score.

Because the desktop frontend already contains full native support for displaying `is_ambiguous`, `uncertainty_reason`, `EvidenceState`, and bounding boxes, **NO changes to the desktop UI are required in Loop 20**.

All Loop 20 enhancements in table-aware cell association and evidence-based abstention integrate seamlessly into the existing Electron UI via the established sidecar IPC contract.
