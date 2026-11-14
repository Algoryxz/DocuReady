# DocuReady Legacy V0 Golden Baseline Canonicalization Contract

**Contract Version:** `1.0.0`
**Reference Commit:** `9a0d00c8c9e02b2697d52589aa04ca211ffaf441`
**Artifact:** `GOLDEN_BASELINE.json`
**Raw SHA-256 Checksum:** `e8fb1a6b842a47089937777133de79e1e7f704bee591d5b4471a1a90bc8c5fa9`
**LF-Normalized SHA-256:** `1758de7778d32392d50a160e3b169d40439c4e48db0a2434409767e271cf6962`

---

## 1. Scope & Purpose

This golden snapshot preserves the exact authoritative behavior of the original DocuReady pre-submission audit engine (Loop 3 baseline) across all 8 standard synthetic demonstration packets:

1. `PKT_01_CLEAN` — Clean, fully compliant packet (Score: 100, Status: `READY_TO_SUBMIT`).
2. `PKT_02_NAME_CONFLICT` — Name variation across documents (Score: 75, Status: `ACTION_REQUIRED`).
3. `PKT_03_DOB_CONFLICT` — Date of Birth mismatch (Score: 75, Status: `ACTION_REQUIRED`).
4. `PKT_04_INCOME_CONFLICT` — Income ceiling breach (Score: 40, Status: `REJECT_PRECHECK`).
5. `PKT_05_MISSING_CERTIFICATE` — Missing mandatory caste certificate (Score: 65, Status: `REJECT_PRECHECK`).
6. `PKT_06_MULTIPLE_DEFECTS` — Multiple conflicting demographic and certificate issues (Score: 0, Status: `ACTION_REQUIRED`).
7. `PKT_07_UNREADABLE_DOC` — Corrupted / illegible scanned document (Score: 75, Status: `UNREADABLE_PACKET`).
8. `PKT_08_AMBIGUOUS_EVIDENCE` — Ambiguous evidence requiring citizen manual review (Score: 85, Status: `REVIEW_RECOMMENDED`).

This snapshot is a permanent regression barrier. Future architectural migrations (G1–G6) must demonstrate parity or formally explain and justify any intended outcome shifts.

---

## 2. Canonicalization Specification

The raw output of `AuditPipeline.load_and_audit_packet()` contains execution-environment non-determinism. To achieve reproducible bit-for-bit comparisons across machines and runs:

1. **Audit Timestamp (`timestamp`):** Replaced with literal token `"[NORMALIZED_AUDIT_TIMESTAMP]"`.
2. **Execution Latency (`execution_time_ms`):** Normalized to float `0.0`.
3. **Preserved Fields:**
   - `packet_id`, `scheme_name`, `readiness_score`, `overall_status`, `summary_counts`.
   - `findings`: Full array preserving finding order, `rule_id`, `rule_name`, `status`, `severity`, `penalty`, `field`, `documents_involved`, `message`, `evidence` spans/boxes, `remediation`, and `statutory_reference`.
   - `extracted_documents`: Complete dictionary keyed by document type enum string, including all extracted fields, bounding boxes, text snippets, and confidence levels.
4. **Serialization:** `json.dumps(..., indent=2, sort_keys=True)`.

---

## 3. Strict Invariance Rule

**This golden snapshot must NEVER be automatically regenerated or modified by test suites.** Any alteration of `GOLDEN_BASELINE.json` requires explicit architectural authorization.
