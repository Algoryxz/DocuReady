# DocuReady 2.0 — Product Brief

## 1. Vision & Positioning

**DocuReady** is an offline-first, deterministic pre-flight document readiness assistant for Indian scholarship and public-benefit applicants (and assisted-service/CSC operators). It checks multi-document application packets **before submission** for missing or mismatched documents, poor scan legibility, expired certificates, and cross-document clerical discrepancies, anchoring every finding to visual source-page coordinates.

### Product Boundaries (Non-Negotiable)
- DocuReady is an **applicant-side preparation aid**, not a government portal, sanctioning authority, or legal advisor.
- It **never** issues automatic fraud/authenticity verdicts, AI eligibility predictions, or official portal acceptance guarantees.
- `"NO_ISSUES_FOUND"` means only that the configured deterministic checks passed on the supplied evidence; it does not mean `"approved"` or `"ready to submit"`.

---

## 2. Target Users
1. **Primary:** Scholarship and welfare scheme applicants preparing multi-document PDF/image packets on a Windows desktop.
2. **Secondary:** Assisted-service / Common Service Centre (CSC) operators helping applicants pre-check packets locally without uploading citizen PII to third-party cloud tools.

---

## 3. Target Vertical Slice Experience

> **Guided Application Workspace → Document Intelligence → Evidence Review → Correct → Re-audit → Redacted Report**

---

## 4. Feature Candidate Classification (24-Hour Scope)

| # | Feature Candidate | Classification | Forensic Basis & 2.0 Action |
|---|---|---|---|
| 1 | **Guided packet intake & document-slot checklist** | **New implementation required** (UI + IPC); **Implemented in Python** (`doc_slots`, `slot_validator`) | `apps/desktop/src/renderer/main.tsx` currently has a flat `+ Add Documents` picker and a disconnected `scheme-select` dropdown (`odisha_post_matric` / `general_scholarship`). Wire real pack/slot metadata (`generic.demo`, `odisha.subhadra` with `DEMO SNAPSHOT` badge) and render a slot checklist. |
| 2 | **Missing / wrong document detection** | **Implemented but needs improvement** | `RULE-DOC-01` and `RULE-SLOT-01` (`slot_classifier.py`, `slot_validator.py`) work in `DocuReadyValidator`; UI needs slot-level mismatch indicators and explicit `documentId`/slot binding instead of filename substring matching. |
| 3 | **Document quality diagnostics** | **Implemented but needs improvement** | `RULE-DOC-02`, OCR confidence, and `EvidenceState` (`VERIFIED`/`PROVISIONAL`/`UNCERTAIN`) exist in `DocumentExtractor` + `ConfidenceCalibrator`; `adaptive_ocr.py` / `region_ocr.py` are disconnected. Surface per-document quality diagnostics clearly in the UI and wire safe quality/OCR improvements. |
| 4 | **Evidence review with source-page navigation & bounding boxes** | **Implemented but needs improvement** | 3-panel UI (`DocumentNav`, `EvidenceViewer`, `FindingPanel`) and `transformBBoxToViewport` (`0°/90°/180°/270°`) are wired for PDFs. Needs: auto-scroll to active bbox, unambiguous `documentId` linking, and verified image-coordinate alignment. |
| 5 | **Original OCR vs normalized value comparison** | **New implementation required** (UI + Sidecar DTO) | `ExtractedField` stores `raw_value` and `normalized_value`, and `RedactedAuditResult.documents` (`ExtractedDocumentSummary`) exists in `types.ts`, but the renderer never displays raw vs. normalized fields side by side. |
| 6 | **Confidence & uncertainty explanations** | **Implemented but needs improvement** | `ConfidenceCalibrator` produces `calibrated_confidence`, `evidence_state`, `is_uncertain`, and `uncertainty_reason`; `FindingPanel` shows static `getReviewGuidance`. Surface clear, plain-language uncertainty reasons and abstention explanations. |
| 7 | **Cross-document discrepancy comparison** | **Implemented but needs improvement** | `DocuReadyValidator` runs cross-doc name, DOB, income, IFSC, and account checks with `MatchGrade` (`EXACT`, `COMPATIBLE`, `CONFLICT`, `AMBIGUOUS`). `cross_document.py` is disconnected. Expose side-by-side cross-document field comparison in the Evidence Review Workspace. |
| 8 | **Document replacement & re-audit** | **New implementation required** (Desktop UI + IPC + Sidecar); **Implemented in Python** (`AuditPipeline.replace_document_and_reaudit`) | Python has `replace_document_and_reaudit` (`tests/test_replacement_rerun.py`), but Electron UI only has `Clear Session` or `Re-Run Audit` for the whole packet. Add per-slot/per-finding **Replace Document** and instant re-audit. |
| 9 | **Session-level human review annotations** | **New implementation required** | Currently no UI or schema for reviewer notes or review-item acknowledgement. Add ephemeral in-session annotations that **never** alter the engine's `PASS`/`FAIL`/`REVIEW` verdict. |
| 10 | **Redacted report export** | **Implemented but needs improvement** | `report:export` writes redacted JSON/Markdown (`redact.py`, `ipc.ts`). Fix `exporter.py:110` unredacted `f.remediation` gap, include pack metadata/disclaimer and session-only review notes (clearly separated from engine verdicts) in exports. |

---

## 5. Explicit Non-Goals (First 24 Hours)

- DigiLocker integration
- WhatsApp integration
- Mobile application (Flutter / Android)
- Live government portal integrations
- Automatic fraud / authenticity verdicts
- AI eligibility prediction
- Cloud OCR or cloud document storage
- Unverified new scheme rules
- Replacing PyMuPDF with PDFium (`PdfiumPageBackend.get_words()` remains unimplemented)
- Persistent citizen document history or local document database
