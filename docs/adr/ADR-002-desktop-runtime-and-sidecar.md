# ADR-002: Electron Desktop Runtime and Python Sidecar

- **Status:** Proposed; implementation authorization pending project-owner review
- **Date:** 16 November 2026
- **Branch:** `feat/electron-desktop-foundation`
- **Decision owners:** Product Owner / Integration Lead and Platform / Privacy Lead
- **Related plan:** [ELECTRON_DESKTOP_PLAN.md](../ELECTRON_DESKTOP_PLAN.md)

## Context

DocuReady's canonical audit engine is a Python package. The current interactive UI is Streamlit, which is not an appropriate foundation for a polished installable desktop workflow. Rewriting the engine in JavaScript would duplicate validated rules, evidence calibration, normalization, and report semantics, creating avoidable parity and safety risk.

The desktop application must remain local-first and must not introduce a cloud backend or network listener merely to connect its UI to the existing engine.

## Decision

1. Use Electron Forge 8 with React, TypeScript, and Vite 8 for the desktop shell.
2. Keep Python as the only implementation of audit decisions.
3. Run Python as a child sidecar process managed by Electron's main process.
4. Use a versioned JSON Lines protocol over child-process stdin/stdout for the first implementation. Do not use localhost HTTP, WebSockets, or a listening TCP port.
5. Keep the renderer sandboxed and isolated. Expose only narrow, typed operations through `contextBridge`.
6. Let Electron main own native dialogs, selected-file staging, canonical paths, sidecar lifecycle, job cancellation, and export destinations.
7. Keep the existing Streamlit and CLI interfaces until the desktop workflow has proven engine equivalence and is accepted.
8. Defer persistent packet history and database selection. The MVP is session-first with explicit export.

## Alternatives considered

### Port the Python engine to TypeScript

Rejected. It duplicates business rules and risks divergence in statuses, match grades, provenance, and safety handling.

### Keep Streamlit and wrap it in Electron

Rejected as the product architecture. It couples the desktop product to a browser-hosted UI server, complicates process management and lifecycle cleanup, and does not create a native desktop information architecture.

### Expose a localhost HTTP API from Python

Deferred/rejected for MVP. It introduces a listening socket, port selection, local-origin/CSRF concerns, and a larger attack surface. Reconsider only if a measured requirement demonstrates that stdio IPC is inadequate.

### Run system Python/Tesseract installed by the user

Rejected for consumer distribution. It creates fragile setup and version drift. Development may use host tools; packaged builds must bundle and verify a known runtime and OCR engine.

### Use an embedded database in MVP

Deferred. Current packet processing can remain stateless and session-first. Persistence increases retention, encryption, migration, deletion, and PII lifecycle obligations.

## Consequences

### Positive

- Existing Python engine and golden tests remain authoritative.
- No local network listener is required.
- Native dialogs and app lifecycle are handled in Electron main.
- UI and engine can be developed/tested independently.
- Protocol versioning permits future engine upgrades without renderer coupling.

### Costs and risks

- Python, native PDF libraries, OCR binaries, and traineddata must be packaged per OS/architecture.
- Sidecar startup, cancellation, crashes, and protocol framing require explicit engineering.
- JSON serialization must define stable DTOs and avoid leaking raw PII into logs.
- The current PyMuPDF default is AGPL/commercial dual-licensed. This is a binary redistribution blocker until resolved.
- Existing Python no-network tests do not prove desktop-wide zero egress; a new end-to-end packaged-app contract is required.

## Required implementation constraints

- Electron: `nodeIntegration: false`, `contextIsolation: true`, `sandbox: true`.
- Strict local-only Content Security Policy and no remote renderer assets.
- Validate IPC sender and payload schemas on every privileged operation.
- Do not expose raw `ipcRenderer`, generic IPC channels, filesystem access, or arbitrary paths to the renderer.
- Standard output is reserved for JSONL protocol messages; diagnostics go to standard error.
- Sidecar methods are allow-listed and versioned. No arbitrary module execution, shell execution, or expression evaluation.
- All input files are staged by Electron main into a private per-job directory after validation.
- Temporary files are cleaned on success, failure, cancellation, shutdown, and next-launch recovery.
- No telemetry, cloud sync, crash upload, or background update checks in the MVP.
- Do not change the engine's golden snapshots to accommodate the desktop adapter.

## Acceptance evidence required before release

- Synthetic packet parity between Python CLI/API and desktop adapter for readiness, findings, match grades, reason codes, provenance, and redacted exports.
- Protocol unit/integration tests, including malformed frames, oversized messages, version mismatch, process crash, timeout, cancellation, and restart.
- Electron security tests for sandbox, context isolation, IPC sender validation, navigation, popup denial, and CSP.
- Packaged app zero-network test spanning renderer, main process, and Python sidecar.
- File lifecycle and PII redaction tests on Windows, macOS, and Linux.
- Clean-machine packaged smoke tests with bundled OCR runtime and language data.
- Recorded PDF backend licensing decision and complete `NOTICE`/SBOM.

## Review

This ADR remains proposed until the Product Owner and Platform / Privacy Lead review the runtime, protocol, and licence implications. No release or privacy guarantee follows from this ADR alone.
