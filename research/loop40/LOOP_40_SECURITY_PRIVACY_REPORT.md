# Loop 40 Security & Privacy Report

**Date:** 2026-11-27  
**Branch:** `loop-40-performance-multilingual-and-windows-qualification`

---

## 1. Security & Privacy Controls Verified

1. **Offline-First Execution & Zero External Network Calls:**
   - The in-process `TessBaseAPI` probe added in `src/docuready/ingest/adaptive_ocr.py` loads `libtesseract-5.dll` and `tessdata` exclusively from the local Tesseract installation / bundled sidecar directory (`find_tesseract_binary_with_source()`, `get_unified_tessdata_dir()`). No network sockets, telemetry, or external API calls are introduced.
2. **Fail-Safe Probe Hardening (Loop 39 Preserved):**
   - `tests/test_loop39_probe_hardening.py` (3/3 PASS):
     - Probe exceptions/timeouts set `profile.probe_uncertain = True`, record `profile.probe_error`, set `primary_script = "UNKNOWN"`, and route to `GLOBAL_MULTILINGUAL` (`eng+hin+ori`) rather than `FAST_PATH_ENG`.
     - Sparse probe output (`< 5` chars) on an inked page sets `probe_uncertain = True` and routes to `GLOBAL_MULTILINGUAL`.
     - Blank/unreadable pages abstain via `ABSTAIN_UNREADABLE` with `ocr_model_invocations == 0`.
3. **PII Redaction, UI Privacy, IPC & Path Traversal Boundaries:**
   - `tests/test_redaction_safe_logging.py` — PASS
   - `tests/test_ui_privacy.py` — PASS
   - `tests/test_desktop_sidecar_protocol.py` — PASS
   - `tests/test_evidence_provenance_contract.py` — PASS
   - Electron `@docuready/desktop` (`npm test`, 25/25 PASS):
     - `WorkspaceManager.getDocumentContent` safely serves registered files and blocks directory traversal.
     - `getContentSecurityPolicy` enforces strict sandbox directives.
     - `validateFileSignature` validates PDF magic bytes and image formats.
     - `validateIpcSender` enforces IPC sender boundaries.
     - Diagnostic metadata enforces zero-PII and includes runtime health.
     - Session isolation and complete data purge verified.

---

## 2. Residual Risks

- **Windows Binary Authenticode Signing:** Unsigned (`NotSigned`) — tracked as `BLOCKED` in `LOOP_40_WINDOWS_TRUST_REPORT.md`.
- **In-Process `ctypes` Lifecycle:** `_InProcessScriptProbe` guards all `TessBaseAPI` calls with a `threading.Lock()`, initializes once, frees UTF-8 text buffers via `TessDeleteText` in `try/finally`, and registers `atexit.register(_PROBE_ENGINE.close)` to call `TessBaseAPIDelete`.
