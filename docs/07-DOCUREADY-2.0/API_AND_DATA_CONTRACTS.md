# DocuReady 2.0 — Shared API and Data Contracts

**Rule:** Shared files (`apps/desktop/src/shared/types.ts`, `sidecar/docuready_sidecar.py` protocol, `src/docuready/domain/models.py`) are cross-team contracts. No contributor may unilaterally alter these schemas without updating this document and notifying affected workstream owners.

---

## 1. Identifiers & Document Slots

- **Document ID (`documentId`):** `doc-<uuid>` assigned by `WorkspaceManager.registerDocument()`. Renderer must link findings and previews by `documentId` (or canonical slot + `documentId`), never solely by filename substring matching.
- **Packet ID (`packetId`):** `pkt-<8-hex>` assigned by `WorkspaceManager.createPacket()`.
- **Scheme / Pack ID (`schemeId`):** Canonical pack identifier (e.g., `generic.demo`, `odisha.subhadra`) or explicit legacy fallback (`odisha_post_matric`). Must be forwarded from UI → `packet:create` → `audit:start` → `sidecar` (`audit_packet`).
- **Document Slot (`DocumentSlotDTO`):**
  ```ts
  export type SlotStatus = "missing" | "staged" | "audited_ok" | "audited_issue" | "wrong_document" | "unreadable";

  export interface DocumentSlotDTO {
    slotId: string;           // e.g. "income_cert", "bank_passbook", "aadhaar"
    label: string;
    required: boolean;
    acceptedTypes: string[];  // ["pdf", "png", "jpg", "jpeg"]
    assignedDocumentId: string | null;
    status: SlotStatus;
    mismatchReason?: string | null;
  }
  ```

---

## 2. Document Processing & Audit Lifecycle

- **Document Lifecycle:** `selected` → `validated_signature` → `staged_in_packet` → `extracting` → `audited` | `replaced` | `removed` | `error`.
- **Audit Job Status (`AuditJobStatus`):** `"idle" | "staged" | "running" | "completed" | "failed" | "cancelled"`.
- **Audit Progress (`AuditProgress`):**
  ```ts
  export interface AuditProgress {
    packetId: string;
    stage: "intake" | "extraction" | "validation" | "redaction" | "completed";
    step: number;        // 1..5 monotonic (fix skipped step 4 in sidecar)
    totalSteps: number;  // 5
    percent: number;     // 0..100
    message: string;
  }
  ```
- **Failure & Cancellation:** `audit:cancel` must terminate/interrupt the active sidecar job, clean the cancelled packet workspace if requested, and return `{ packetId, status: "cancelled" }` cleanly. Sidecar errors must return sanitized error codes/messages with **zero** raw PII or host filesystem paths.

---

## 3. Evidence, Finding & Reason-Code Schema

- **Finding Status (`FindingStatus`):** `"PASS" | "FAIL" | "WARN" | "REVIEW" | "MISSING" | "NOT_APPLICABLE"` (canonical V2 vocabulary; never emit `UNKNOWN` or `READY_TO_SUBMIT`).
- **Readiness (`Readiness`):** `"NOT_READY" | "NEEDS_CHECKS" | "NO_ISSUES_FOUND"`.
- **Evidence State (`EvidenceState`):** `"VERIFIED"` ($P \ge 0.85$), `"PROVISIONAL"` ($0.60 \le P < 0.85$), `"UNCERTAIN"` ($P < 0.60$ or format invalid).
- **Match Grade (`MatchGrade`):** `"EXACT" | "COMPATIBLE" | "CONFLICT" | "AMBIGUOUS"`.
- **Evidence Item (`EvidenceProvenanceDTO`):**
  - `documentId?: string | null` (new 2.0 binding to eliminate filename ambiguity)
  - `slotId?: string | null`
  - `document_type: string`, `file_name: string`
  - `page_number: number | null` (1-indexed; `null` when document/page is missing or unlocated — never fabricate page `1`)
  - `bounding_box: [number, number, number, number] | null`
  - `raw_snippet: string` (redacted by default)
  - `extracted_field: string`, `extraction_method: "vector" | "ocr" | "none"`
  - `ocr_confidence: number | null`, `ocr_lang?: string | null`
- **Extracted Field Comparison (`ExtractedFieldComparisonDTO`):**
  - `fieldName: string`
  - `rawValue: string` (redacted for PII where applicable, or masked display)
  - `normalizedValue: string | null`
  - `evidenceState: EvidenceState`
  - `calibratedConfidence: number`
  - `uncertaintyReason: string | null`
  - `provenance: EvidenceProvenanceDTO | null`

---

## 4. Coordinate Convention (Source Page & Bounding Boxes)

- **Canonical Coordinate Space:** `[x0, y0, x1, y1]` in **top-left origin PDF points** (`72` DPI, `x0 < x1`, `y0 < y1`).
- **PDF Pages:** `EvidenceViewer` transforms PDF points to CSS viewport pixels via `transformBBoxToViewport(bbox, pageSize, scale, rotation)` (`apps/desktop/src/shared/coordinates.ts`), supporting `0°`, `90°`, `180°`, and `270°` rotations and clamping to page bounds.
- **Image Files (`.png`, `.jpg`, `.jpeg`):** Backend and renderer **must** agree on coordinate units (either normalize image coordinates to the image's natural pixel dimensions or report `pageSize` consistently). Workstream 1/2/3 must verify image bbox parity in `coordinates.test.ts` and `test_evidence_provenance_contract.py`.

---

## 5. Document Replacement & Re-Audit Contract

- **IPC Channel:** `"packet:replace-document"` (`{ packetId: string, slotId: string, replacementDocumentId: string }` or file-picker flow).
- **Semantics:** Replaces **only** the targeted slot's document in `WorkspaceManager` and invokes re-audit (`AuditPipeline.replace_document_and_reaudit` or updated `audit_packet`), preserving all other staged documents and their cached previews.
- **In-Memory State:** Previous findings for that packet are superseded by the new `RedactedAuditResult`; session annotations linked to unchanged documents may be preserved with a `"stale — re-verify after re-audit"` flag.

---

## 6. Human Review Annotation Semantics

```ts
export interface ReviewAnnotation {
  annotationId: string;
  packetId: string;
  ruleId: string;
  note: string;
  acknowledged: boolean;
  createdAt: string; // ISO-8601
}
```
- **Non-Negotiable Invariant:** Human review annotations are **session-only, in-memory** metadata. They **MUST NEVER** mutate or override the engine's `Finding.status` (`PASS`/`FAIL`/`REVIEW`) or `AuditResult.readiness`.
- **Persistence Boundary:** Annotations are cleared on `session:clear` and window close; they are not persisted to disk across sessions.

---

## 7. Redacted Export Contract

- **IPC Channel:** `"report:export"` (`{ packetId: string, format: "json" | "md" }`).
- **Contract:**
  - All Aadhaar, bank account, phone, currency, and `raw_snippet` / `remediation` PII must be redacted by default (`redact=True`).
  - Export must include `schemeId`, `packStatus` (e.g., `DEMO SNAPSHOT` disclaimer if applicable), `asOf` date, `readiness`, redacted findings, and (if present) a clearly separated `human_review_annotations` section labeled `"Advisory Session Notes — Does Not Alter Engine Verdict"`.
