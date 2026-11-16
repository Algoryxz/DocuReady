# Python Sidecar

The sidecar is the local process boundary between the Electron main process and the existing DocuReady Python package. It does not implement independent audit logic; it calls `AuditPipeline`.

## Protocol v1

One JSON object per input line; one JSON object per response line. Progress events appear between request and response frames. Standard output is reserved strictly for protocol frames; all diagnostics go to standard error.

Supported methods:

- `health`: Returns engine version, python version, active PDF backend, and OCR availability.
- `audit_packet`: Staged packet directory, packet ID, and explicit ISO `as_of` date. Streams progress stages (`intake`, `extraction`, `validation`, `completed`) and returns redacted canonical findings with evidence provenance metadata.
- `shutdown`: Gracefully terminates the sidecar worker.

### Protocol Invariants & Security Boundaries

- The caller must configure `DOCUREADY_WORKSPACE_ROOT`. The supplied `packet_dir` must resolve strictly within that root; any directory traversal or path outside the managed workspace triggers a `WORKSPACE_VIOLATION` error frame.
- Protocol size limit: requests larger than 1MB are rejected with `REQUEST_TOO_LARGE`.
- Negative evidence handling: findings with missing documents or unlocated fields maintain empty evidence lists (`[]`) and never fabricate bounding box coordinates.
- Redaction policy: evidence snippet values are redacted to `"[REDACTED EVIDENCE SNIPPET]"` in public frames to ensure zero PII leaks while preserving exact coordinate geometries and page numbers.
- Processing limits: packets are restricted to a maximum of 20 documents, 50MB per individual file, 200MB per packet, and 50 pages per document. 0-byte files are rejected with structured errors.

## Standalone Sidecar Packaging (Loop 3)

The sidecar can be packaged into a standalone self-contained executable distribution via PyInstaller:

```bash
pyinstaller sidecar/docuready_sidecar.spec --noconfirm
```

This compiles the Python 3.12 runtime, PyMuPDF C extensions, and dependencies into `sidecar/dist/docuready_sidecar/`:
- Windows: `docuready_sidecar.exe`
- macOS / Linux: `docuready_sidecar`

Electron's `SidecarManager` automatically resolves the compiled binary from `resources/` or `sidecar/dist/` in production, with seamless fallback to `python sidecar/docuready_sidecar.py` in development environments.

## Dynamic OCR Runtime Discovery

OCR availability is dynamically detected via `src/docuready/ingest/tesseract_discovery.py`. It probes:
1. `DOCUREADY_TESSERACT_PATH` override
2. Bundled application resources (`process.resourcesPath/tesseract`)
3. System `PATH`
4. Standard operating system directories (`C:\Program Files\Tesseract-OCR\tesseract.exe`, `/usr/bin/tesseract`, etc.)

Sidecar `health` frames report sanitized binary metadata (basename only) and installed languages with zero host path exposure.

## Local Development & Testing

```bash
export DOCUREADY_WORKSPACE_ROOT=/absolute/path/to/private-workspace
python sidecar/docuready_sidecar.py
```

Run sidecar protocol unit and integration tests:

```bash
pytest tests/test_desktop_sidecar_protocol.py tests/test_evidence_provenance_contract.py tests/test_ocr_acceptance.py tests/test_adversarial_documents.py -v
```

