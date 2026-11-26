# DOCUREADY — LOOP 36 PORTABLE BUILD REPORT

- **Status:** **PASS** for packaged portable directory (`apps/desktop/out/DocuReady-win32-x64/`).
- Verified `docuready_sidecar.exe` executes health handshake, discovers bundled `tesseract.exe` and `eng`/`hin`/`ori` traineddata, handles spaces + Unicode paths under authorized `--workspace-root`, and rejects unauthorized paths (`WORKSPACE_VIOLATION`).
