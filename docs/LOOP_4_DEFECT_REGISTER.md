# DocuReady Desktop — Loop 4 Defect Register
**Milestone:** Loop 4 Product Validation, Real-World Workflow Testing & Release Candidate Qualification  
**Date:** 16 November 2026

---

## 1. Defect Classification Criteria

- **Critical:** Fabricated evidence, incorrect provenance, sensitive-data leakage, or materially incorrect audit output. *Blocks RC qualification.*
- **High:** Broken core workflow, incorrect evidence navigation, or unreliable report export. *Blocks RC qualification.*
- **Medium:** Recoverable workflow failures, misleading diagnostics, or incomplete error guidance. *Requires remediation or documented mitigation.*
- **Low:** Cosmetic UI inconsistencies or non-blocking usability polish.

---

## 2. Defect Register and Resolution Ledger

| Defect ID | Severity | Category | Description | Root Cause | Status | Resolution / Verification |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **DEF-01** | **High** | Runtime Protocol | Windows child-process pipe encoding error (`UnicodeEncodeError`) during stdio frame emission. | Windows stdout defaults to legacy code page (cp1252), causing crashes when emitting currency symbols (`₹`) or Hindi characters. | **RESOLVED** | Configured `sys.stdout.reconfigure(encoding="utf-8")` and implemented direct UTF-8 binary buffer fallback in `_write_frame()`. Verified across 450+ Python tests and 21 desktop tests. |
| **DEF-02** | **Medium** | Diagnostics / Truthfulness | Ambiguous OCR runtime reporting in Desktop UI. | Diagnostics modal previously labeled local Tesseract discovery as "Active" without clarifying whether it was bundled or a host system prerequisite. | **RESOLVED** | Added `ocrSource: "system_prerequisite"` and `isBundled: false` tracking in discovery and sidecar protocol. UI now explicitly labels host Tesseract as `System Prerequisite, Discovered`. |
| **DEF-03** | **High** | Ingestion Boundaries | Lack of defensive limits on packet ingestion size. | Sidecar previously allowed arbitrary file counts and unbounded sizes, exposing desktop process to memory exhaustion on oversized packets. | **RESOLVED** | Enforced strict limits: 20 documents/packet, 50MB/file, 200MB/packet, 50 pages/doc. Zero-byte files rejected at boundary. Verified via `tests/test_adversarial_documents.py`. |
| **DEF-04** | **Critical** | Evidence Integrity | Potential bounding box fabrication on page-level statutory rules. | Rules evaluating general limits (e.g. statutory income ceiling) do not possess a single word coordinate in the document. | **RESOLVED** | Canonical engine explicitly emits `bounding_box: null`. Desktop normalizer and viewer render page-level finding badge without fabricating coordinates. Verified via `apps/desktop/tests/evidence.test.ts`. |
| **DEF-05** | **Medium** | Coordinate Transformation | Bounding box displacement on 90° and 270° rotated PDF pages. | PyMuPDF uses unrotated point coordinates relative to top-left, whereas PDF.js viewports apply rotation matrix. | **RESOLVED** | Implemented exact mathematical transformation accounting for page width, height, rotation angle, and scale factor in `apps/desktop/src/renderer/utils/coordinates.ts`. Verified in `tests/coordinates.test.ts`. |
| **DEF-06** | **High** | Data Lifecycle | Abandoned session files in OS temporary directories following sudden crash or power loss. | If application process is killed ungracefully, ephemeral workspace directories (`docuready-ws-*`) remained on disk. | **RESOLVED** | Implemented `recoverStaleWorkspaces()` startup sweep in `WorkspaceManager` that scans and unlinks abandoned session folders. Verified in `apps/desktop/tests/workspace.test.ts`. |
| **DEF-07** | **Blocking Gate** | Legal / Distribution | PyMuPDF AGPL-3.0 redistribution constraint. | PyMuPDF bundles compiled MuPDF C extensions licensed under AGPL-3.0. Closed-source binary distribution is prohibited without Artifex Commercial License. | **DOCUMENTED GATE** | Prepared complete technical audit in `docs/LICENSING_AND_DISTRIBUTION_AUDIT.md`. Binary is packaged and 100% ready; owner must formally sign off Option A (Commercial) or Option B (AGPL-3.0). |

---

## 3. Residual Defect Status

- **Critical Defects Remaining:** **0**
- **High Defects Remaining:** **0**
- **Medium Defects Remaining:** **0**
- **Blocking Legal/Commercial Gates:** **1** (`DEF-07`, PyMuPDF Commercial Licensing Decision)
