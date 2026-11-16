# DocuReady Desktop

Local-first Electron desktop application for the DocuReady document readiness engine.

## Overview

DocuReady Desktop integrates the canonical Python statutory audit engine as a background sidecar process over a secure stdio JSON Lines protocol, providing a 3-panel evidence inspection and explainability workspace:

- **Document Navigation Panel:** Manage and switch between packet documents with live status and issue counters.
- **Central Evidence Viewer:** Built on PDF.js with high-DPI canvas rendering, zoom controls, fit-to-width, page navigation, and exact bounding-box overlays.
- **Finding Inspection Panel:** Filter by status (PASS, WARN, FAIL, REVIEW), search by rule ID/field, sort by severity, inspect match grades, reason codes, statutory citations, and remediation guidance, with 1-click inspection linking directly to source document pages.

## Prerequisites

- Node.js 22.17+ or 24 LTS.
- npm 11+.
- Python 3.11–3.14 (with `docuready` installed, e.g. `pip install -e .`).
- Tesseract OCR (optional, for image/scanned document extraction).

## Development

From `apps/desktop`:

```bash
npm install
npm start
```

### Type-Checking & Verification

Run strict TypeScript type-checking:

```bash
npm run lint:types
```

Run the desktop test suite (IPC security, coordinate transformation, evidence normalizer, binary delivery, and end-to-end parity):

```bash
npm test
```

### Packaging

Package the application with Electron Forge 8:

```bash
npm run package
```

The output package will be generated under `apps/desktop/out/DocuReady-<platform>-<arch>/`.

## Security Architecture

- `nodeIntegration: false`
- `contextIsolation: true`
- `sandbox: true`
- Strict Content Security Policy (`default-src 'self'; script-src 'self'; object-src 'none'`)
- IPC sender origin validation on all invoke channels
- WebRequest restrictions: new windows and external navigations are denied
- Ingestion limits: 20 documents/packet, 50MB/file, 200MB/packet, 50 pages/file
- Ephemeral workspace isolation with automated multi-stage cleanup; privacy controls are not a guarantee of zero PII leakage

## Release Documentation

- [Release Readiness Specification](../../docs/RELEASE_READINESS.md)
- [Licensing & Distribution Audit](../../docs/LICENSING_AND_DISTRIBUTION_AUDIT.md)
- [Electron Desktop Architecture Plan](../../docs/ELECTRON_DESKTOP_PLAN.md)
- In-memory binary document delivery (`documents:get-binary` / `getDocumentBinary`) passes `Uint8Array` directly to the viewer without exposing filesystem paths
- File signature and size validation (50MB single file limit, 200MB packet limit)
- Isolated temporary workspaces with automatic cleanup on session clear or packet deletion
- Designed for local document processing. No claim of system-wide network isolation or zero outbound traffic is made; renderer CSP and process-level checks have narrower scopes.

## Coordinate Geometry Contract

PyMuPDF coordinates:
- Origin: Top-Left `(0, 0)` in PDF points (1/72 inch).
- Format: `[x0, y0, x1, y1]` where `x1 >= x0` and `y1 >= y0`.

PDF.js viewport coordinates:
- CSS pixels, scaled by zoom factor and transformed according to page rotation (0°, 90°, 180°, 270°).
- Supported by mathematical transformation in `apps/desktop/src/shared/coordinates.ts` (`transformBBoxToViewport`) with automatic boundary clamping and crop box offset handling.

