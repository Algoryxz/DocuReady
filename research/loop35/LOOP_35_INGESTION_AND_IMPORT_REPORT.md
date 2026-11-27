# DOCUREADY — LOOP 35 INGESTION & IMPORT REPORT

Verified across `tests/test_loop35_e2e_workflow.py` and `apps/desktop/tests/`:
- **Empty & Corrupted PDFs:** Rejected or quarantined as `UNREADABLE`/`CORRUPTED`; never enter workflow as valid evidence.
- **Extension/Content Mismatches:** `validateFileSignature()` inspects magic bytes (`%PDF-`, PNG, JPEG), rejecting disguised text/binary files.
- **Size Limits:** `MAX_FILE_SIZE_BYTES = 50MB`, `MAX_PACKET_SIZE_BYTES = 200MB` enforced.
- **Path Traversal & Unicode:** `WorkspaceManager.getDocumentContent()` blocks traversal; Unicode paths (`आवेदन_पत्र_ओडिशा`) handled cleanly.
