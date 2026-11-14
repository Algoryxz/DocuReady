# DocuReady — Product Overview

## Ownership & Contribution Responsibilities

| Role | Assignee | Primary Scope & Focus |
|---|---|---|
| **Primary Owner** | **Deeptiman** (Product Owner & Integration Lead) | Product purpose, value proposition, user workflow, boundary definition, citizen outcomes |
| **Supporting Contributor** | **Akriti** (Platform, Privacy & Delivery Lead) | Local-first runtime constraints, dual extraction pipeline workflow, performance feasibility |
| **Supporting Contributor** | **Susmita** (Domain Rules & Evaluation Lead) | Document slot definitions, deterministic rule audit flow, findings classification |

### Detailed Responsibilities & Deliverables
- **Primary Owner (Deeptiman)**:
  - Formulate and maintain the core product purpose, 6-stage workflow, and value proposition.
  - Enforce the fundamental product contract: DocuReady checks documents against published requirements; "No issues found" means only that configured checks passed on supplied evidence—it never implies "approved" or "ready to submit".
  - Ensure all public-facing workflow descriptions align with Gate G1 claims integrity.
- **Platform Contributor (Akriti)**:
  - Validate that extraction and remediation workflows (Steps 1, 2, and 5) map faithfully to system architecture capabilities (sub-second re-audit, local storage boundaries).
- **Domain Contributor (Susmita)**:
  - Ensure normalization, audit, and certificate generation stages (Steps 3, 4, and 6) accurately reflect rule-pack evaluation and finding schemas (`PASS`, `REVIEW`, `FAIL`, `UNKNOWN`).

### Coordination & Review Gates
- Changes to the core user journey or outcome definitions require sign-off from Deeptiman.
- Architectural alignment must be reviewed by Akriti; domain finding alignment by Susmita.
- Governed by [TEAM_RESPONSIBILITIES.md](../TEAM_RESPONSIBILITIES.md).

---

## 1. What is DocuReady?

**DocuReady** is an offline, client-side document pre-submission auditor designed to eliminate preventable administrative rejections for citizen welfare schemes, educational admissions, and public benefit programs.

**Tagline:**
> **Check your documents before you submit.**

DocuReady shifts document verification from the post-submission administrative bottleneck to the pre-submission applicant interface. Before an applicant submits their application packet on an official portal (such as the National Scholarship Portal or State e-Despatch), DocuReady inspects the documents locally, extracts cross-document facts, tests deterministic statutory eligibility criteria, highlights discrepancies with exact bounding-box evidence, and guides the applicant through immediate remediation.

---

## 2. Core Value Proposition

In citizen-facing government services, over **30% of scholarship and benefit applications are rejected or delayed** due to superficial, clerical errors:
- Minor name spelling discrepancies between Aadhaar, Marksheet, and Bank Passbook (e.g. initial expansion or middle name omissions).
- Date of Birth formatting anomalies (DD/MM vs MM/DD).
- Outdated or expired income certificates (exceeding state validity periods).
- Mismatched bank account or invalid IFSC numbers causing Direct Benefit Transfer (DBT) credit failures.
- Missing mandatory supporting documents or unreadable camera snapshots.

When an application is rejected after submission, the administrative appeal cycle takes weeks or months—often causing students to miss admission deadlines or lose annual funding.

DocuReady acts as a **"linter for documents"**:
1. **Local-First & Offline**: Runs entirely on the citizen's laptop, mobile device, or common service center (CSC) terminal without uploading sensitive personal documents to external cloud servers.
2. **Deterministic & Explainable**: Rules are based on verifiable statutory regulations, not probabilistic black-box LLM judgements. Every finding is linked to original document page numbers and visual bounding boxes.
3. **Actionable Remediation**: Instead of vague "document invalid" errors, DocuReady explains precisely which document has the discrepancy and allows instant replacement and re-audit in sub-second time.

---

## 3. Product Workflow

```
[1. Packet Upload] ────> [2. Extraction & OCR] ────> [3. Normalization]
                                                              │
[6. Export Report] <──── [5. Interactive Remediation] <──── [4. Deterministic Audit]
```

1. **Ingest Packet**: Applicant drops their multi-document application folder (PDFs or scans).
2. **Extract Evidence**: Dual-path engine extracts native vector text (4ms) or executes local Tesseract OCR on raster scans with auto-orientation and spatial Y-clustering.
3. **Normalize Entities**: Parses names, dates, currencies, IFSCs, and certificate reference numbers into canonical representations.
4. **Deterministic Audit**: Runs cross-document consistency checks and scheme-specific eligibility rules.
5. **Interactive Remediation**: Displays readiness score (0-100), findings categorized as `PASS`, `REVIEW`, `FAIL`, or `UNKNOWN`, and allows replacing defective documents with instant re-audit.
6. **Export Certificate**: Generates pre-submission readiness certificates in structured JSON and Markdown formats.
