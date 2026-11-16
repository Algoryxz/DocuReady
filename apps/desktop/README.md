# DocuReady Desktop

Electron desktop shell for the existing Python DocuReady engine.

## Prerequisites

- Node.js 24 LTS (Electron Forge 8 requires Node.js 22.17 or newer).
- npm.
- Python 3.11–3.14 for sidecar development.
- The repository's supported Python dependencies and Tesseract OCR for real audit execution.

## Development

From this directory:

```bash
npm install
npm start
```

Type-check the desktop sources:

```bash
npm run lint:types
```

Package the current shell:

```bash
npm run package
```

The current renderer is an initial shell. It does not yet expose document selection or invoke the Python sidecar. Do not treat the app as an operational document-auditing tool.

## Security boundary

The renderer has no Node.js integration. It uses a minimal context-isolated preload bridge. Main-process IPC operations and the Python process manager will be added behind typed, allow-listed APIs. No remote UI assets or cloud service are required.

## Python sidecar development

From the repository root, configure a private workspace and run:

```bash
export DOCUREADY_WORKSPACE_ROOT=/absolute/path/to/private-workspace
python sidecar/docuready_sidecar.py
```

The sidecar accepts JSON Lines requests on stdin and writes protocol frames to stdout. Diagnostics go to stderr. The only currently implemented methods are `health` and `audit_packet`. The Electron main process has not yet been wired to this process.

For an audit request, the caller must stage a packet directory below `DOCUREADY_WORKSPACE_ROOT` and provide an explicit ISO `as_of` date. The sidecar returns a redacted public audit projection and document evidence metadata; it intentionally omits extracted field values from the document summary.

## Current limitations

- No IPC client or sidecar lifecycle manager yet.
- No native file selection, packet workspace, PDF viewer, or report-save dialog yet.
- No packaged Python runtime or bundled Tesseract binary yet.
- No platform-specific installer/signing configuration yet.
- PDF backend licensing must be resolved before binary redistribution.
- This workspace has not yet been built or tested on a developer workstation. Generate and commit a lockfile after local installation and validation.
