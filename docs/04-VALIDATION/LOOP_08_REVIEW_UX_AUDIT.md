# DOCUREADY — HUMAN REVIEW UX, EXPLAINABILITY & ACCESSIBILITY AUDIT

**Project:** DocuReady — HackNation 2026  
**Engineering Phase:** Loop 08 — Desktop Workflow Integrity & Review UX  
**Document:** `docs/04-VALIDATION/LOOP_08_REVIEW_UX_AUDIT.md`  
**Classification:** UX Engineering & Explainability Audit  

---

## 1. Executive Mission & Philosophy

Automated clerical pre-flight engines often fail user trust in one of two ways:
1. **False Confidence (Silent Over-Approval):** Passing unclear, ambiguous, or damaged documents automatically, leading to portal rejection, application cancellation, or loss of critical government scholarship funds.
2. **Opaque Rejection (Cryptic Errors):** Presenting vague error codes (e.g., `ERROR_403`, `VALIDATION_FAILED`) without identifying the document, page, reason, or remediation pathway.

DocuReady Loop 08 eliminates both extremes by introducing **Honest Conservative Abstention** and an **Explainability-First Human Review UX**.

---

## 2. Taxonomy of Review Reason Codes

When automated verification cannot safely certify a statutory check, DocuReady does not silently fail or hallucinate a pass. Instead, it generates a `REVIEW` finding backed by deterministic taxonomy:

| Status | Reason Code | Root Cause in Document | Actionable Human Guidance |
|---|---|---|---|
| `REVIEW` | `POOR_SCAN_QUALITY` / `LOW_CONFIDENCE` | OCR confidence or character edge gradient fell below calibrated threshold (skewed, blurry, low DPI scan). | Inspect the physical paper certificate. If text is legible to human eyes, proceed with caution or re-scan at 300+ DPI. |
| `REVIEW` | `AMBIGUOUS_EXTRACTION` / `MULTIPLE_DATES` | Document presents multiple candidate dates (e.g. Issue Date, Application Date, Notary Stamp Date). | Visually inspect the highlighted evidence bounding box. Verify whether the statutory validity refers to the issue date or renewal window. |
| `REVIEW` | `SOFT_NAME_VARIATION` | Name tokens match with minor token reordering, initials, or phonetic transliteration (e.g. "S. K. Patel" vs "Suresh Kumar Patel"). | Verify identity matching against primary photo ID or high-school certificate. Submit supporting affidavit if required by portal rules. |
| `REVIEW` | `DOC_EXPIRED_PENDING_RENEWAL` | Document has exceeded formal validity window but is within statutory grace or renewal processing window. | Verify if applicant holds a valid renewal acknowledgement slip from Tahsildar / Revenue Authority. |
| `MISSING` | `REQUIRED_DOCUMENT_ABSENT` | A mandatory statutory document (e.g. Income Certificate, Caste Certificate) was omitted from the packet. | Upload the required document to the workspace session to enable automated pre-flight checks. |
| `FAIL` | `HARD_STATUTORY_CONFLICT` | Explicit conflicting values (e.g., DOB `2004-05-12` vs `2003-08-20` or income exceeding threshold). | Rectify conflicting records at the issuing authority before portal submission. |

---

## 3. Evidence Navigation & Unlocated Evidence Handling

### 3.1 Primary Evidence Auto-Focus
In previous desktop builds, clicking a finding card in `FindingPanel` scrolled the card into view but left the center `EvidenceViewer` on whichever document was previously loaded.

In Loop 08, clicking any finding card or pressing `Enter`/`Space`:
1. Identifies the primary located evidence item for that rule (`ev.hasProvenance && ev.boundingBox`).
2. Automatically selects the corresponding document in `DocumentNav` (`activeDocumentId`).
3. Automatically sets the canvas page to `targetPage` (`pageNumber`).
4. Highlights the matching bounding box with active focus.

### 3.2 Unlocated Evidence Representation
When a finding relates to a missing document (`RULE-DOC-01`) or a non-extracted field:
- The system **never invents bounding box coordinates** (e.g. `[0, 0, 0, 0]` or arbitrary guesses).
- `hasProvenance` is explicitly marked `false` with `boundingBox: null`.
- The UI renders an honest `unlocated-evidence-notice` and `missing-doc-callout` clearly informing the user that the document was absent rather than displaying an empty or corrupted canvas.

---

## 4. Statutory Advisory & Non-Government Pre-Flight Notice

DocuReady is an applicant-side assistive pre-flight tool. To prevent any user confusion regarding legal authority:
1. **Permanent UI Disclaimer Strip:** Located immediately below the top header:
   > **Applicant Pre-Flight Verification:** Offline clerical assistance only. Does not constitute official government certification or guaranteed portal acceptance.
2. **Exported Report Notice:** Embedded in all exported JSON and Markdown reports:
   > **Statutory Notice & Disclaimer:** This report is an applicant-side clerical pre-flight check executed entirely on local hardware. DocuReady is an offline assistive tool and does NOT represent official government approval, statutory eligibility verification, or guaranteed admission/disbursement by any government authority or portal.

---

## 5. Accessibility & Usability (WCAG 2.1 AA Compliance)

| Requirement | Implementation in Loop 08 | Verification |
|---|---|---|
| **Keyboard Navigation** | All interactive elements (`FindingCard`, `DocumentCard`, `FilterPill`, `EvidenceBBox`, modal buttons) have explicit `tabIndex={0}`, `role="button"` or `role="tab"`, and `onKeyDown` listeners for `Enter` and `Space`. | Verified via DOM inspection and keyboard traversal. |
| **High-Visibility Focus** | Added universal `:focus-visible` styles with `2px solid var(--brand-accent)` and `outline-offset: 2px` across all controls. | Verified across light and dark theme regions. |
| **Non-Color Status Encoding** | Every status pill and badge pairs high-contrast background colors with explicit icons and text: `❌ FAIL`, `🚫 MISSING`, `⚠️ WARN`, `🔍 REVIEW`, `✅ PASS`. | Passes grayscale and color-blindness visual simulation. |
| **Modal Keyboard Traversal** | The System & Runtime Diagnostics modal listens for `Escape` key events and traps focus cleanly. | Tested in `main.tsx`. |
| **Text Contrast** | All text, badges, and metadata labels achieve greater than 4.5:1 contrast ratio against card and sidebar backgrounds (WCAG 2.1 AA compliant). | Validated against CSS palette variables. |
