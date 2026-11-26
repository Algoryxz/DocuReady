# DOCUREADY — LOOP 35 COMPLETE APPLICATION WORKFLOW ARCHITECTURE

Inspected directly against source implementation:
1. **Startup & Recovery:** `apps/desktop/src/main.ts` & `WorkspaceManager.initialize()` (`apps/desktop/src/main/workspace.ts`) cleans stale temp dirs.
2. **Sidecar Lifecycle:** `SidecarManager` (`apps/desktop/src/main/sidecar.ts`) spawns `docuready_sidecar.exe` via stdio JSON-RPC, enforces health handshake and crash recovery.
3. **Import & Magic-Byte Validation:** `IpcHandlerRegistry` (`apps/desktop/src/main/ipc.ts`) -> `WorkspaceManager.registerDocument()` -> `validateFileSize()` (<=50MB) & `validateFileSignature()` (`%PDF-`, PNG, JPEG).
4. **Extraction & OCR:** `AuditPipeline.load_and_audit_packet()` (`src/docuready/pipeline.py`) -> `DocumentExtractor` (`src/docuready/ingest/extractor.py`) -> `script_router`, `region_ocr`, `adaptive_ocr`, `table_association`.
5. **Validation & Safety:** `DocuReadyValidator.validate_packet()` -> `validate_packet_slots()` -> `DecisionSafetyLayer` -> `resolve_outcome()` (V2 Section 6 truth table).
6. **Presentation:** `FindingPanel.tsx` (`apps/desktop/src/renderer/components/FindingPanel.tsx`) renders `PASS`, `WARN`, `REVIEW`, `MISSING`, `FAIL` with ARIA roles and evidence links.
7. **Export & Cleanup:** `export_audit_report_json()` & `generate_readiness_summary_markdown()` (`src/docuready/report/exporter.py`) with PII redaction enabled by default.
