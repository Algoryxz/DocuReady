# DocuReady Desktop — Electron Architecture & Delivery Plan

**Status:** Proposed implementation baseline  
**Branch:** `feat/electron-desktop-foundation`  
**Planning date:** 16 November 2026  
**Canonical engine:** Existing Python package in `src/docuready/`  
**Target:** Cross-platform offline-first desktop application (Windows, macOS, Linux)

## 1. Executive decision

Build DocuReady as a native-feeling Electron desktop application while retaining the existing Python audit engine as the sole source of truth for extraction, evidence calibration, normalization, rules, outcome resolution, and report generation.

Do not port the audit engine to TypeScript. Do not embed or wrap the existing Streamlit page as the desktop UI. The desktop renderer is a new React application; the Python package remains independently testable and callable through its CLI/API.

**Initial stack (subject to the proof-of-concept gate):**

- Electron Forge 8, TypeScript, Vite 8, React.
- Electron main process for OS integration, window lifecycle, file dialogs, and controlled IPC.
- A packaged Python sidecar process for audit operations.
- JSON Lines (one JSON request/response per line) over the child process stdin/stdout as the initial local bridge. No localhost HTTP server, open port, remote API, or cloud dependency.
- PDF.js for in-app PDF rendering and evidence overlays, with local bundled assets only.
- PyInstaller in onedir mode as the first Python packaging candidate; compare Nuitka only if PyInstaller cannot reliably package the native dependencies.
- Electron Forge makers for platform-specific installers and distributables.

Electron Forge 8 is selected rather than older Forge 7 examples: its current release line is ESM-only, requires Node.js 22.17+, and promotes the Vite plugin to stable. Pin exact tested versions in lockfiles; do not use floating production dependencies.

## 2. Current repository baseline (verified against GitHub on 16 Nov 2026)

- Repository: `Algoryxz/DocuReady`, public, default branch `main`.
- Latest observed main commit: `62425c94b20de6b435df4c16117786c3fc811595` (PR #70 merge, 15 Nov 2026 19:59 UTC).
- Immediately preceding merged feature: PR #69, scheme-aware document slot validation and anchor verification (T2.4).
- Latest merged remediation: PR #70, match grades, injected clock, and golden-test stability (T2.3).
- Existing engine: Python 3.11–3.14; Pydantic; PyMuPDF; Pillow; NumPy; pytesseract; Tesseract native executable for OCR.
- Existing interfaces: CLI and Streamlit. Existing core modules include domain models/enums, extractor, calibrator, normalizer, safety/outcome, validator, pipeline, generator, and privacy-aware report exporters.
- Existing validation assets: synthetic packet corpus, golden baseline, unit/integration/adversarial/contract tests, and four-version Python CI matrix.
- No `package.json` or Electron application was found at the repository root. No Electron implementation was found by repository code search.
- `docs/STATUS.md` was stale relative to actual main: it still named commit `3b10315` and T2.3 active/T2.4 pending. The actual latest commit search confirms both T2.3 and T2.4 merge commits are now on main. Refresh the status document before using it as a task authority.
- The README's current Streamlit interface is explicitly a local Python app; the Vercel site is informational only and is not an upload/audit backend.

The GitHub integration can inspect and update the remote repository, but cannot synchronize files into a developer's local working tree. Local checkout/update commands are provided in the handoff. No local machine changes are claimed by this document.

## 3. Product boundary and desktop user journeys

The desktop application is an applicant-side document preparation aid. It must never imply official eligibility, authentication, approval, or guaranteed portal acceptance.

### Primary journey

1. **Home / recent work** — create a new audit; show local-only processing notice; no document contents in recent-item metadata.
2. **Create packet** — choose a supported scheme/rule-pack snapshot and date context; show pack version/status and source-verification state.
3. **Add documents** — slot-based upload based on the scheme pack; support PDF first, then image inputs already supported by the engine. Validate extension, MIME/magic bytes, size, page count, and duplicate hashes before parsing.
4. **Review packet** — show required slots, missing slots, detected type, and wrong-slot warnings. Do not silently reclassify or discard.
5. **Run audit** — cancellable job with progress stages (intake, extraction, calibration, normalization, rules, report). Long-running work stays outside the renderer.
6. **Results dashboard** — packet-level readiness vocabulary from the Python domain enums; counts for confirmed findings, warnings, review, missing, and passes. Avoid presenting a score as a probability of approval.
7. **Evidence review** — split view with PDF page, extracted field, confidence/evidence state, source document, page number, and bounding-box highlight. Provide zoom, page navigation, and keyboard access.
8. **Finding details** — plain-language explanation, rule ID, match grade, source/citation verification status, affected evidence, limitations, and actionable remediation.
9. **Replace and rerun** — replace one slot and rerun the full packet in a new isolated job; preserve prior result only within the current session unless user explicitly saves a report.
10. **Export** — redacted JSON/Markdown first; PDF export only after layout and redaction tests. Make unredacted export a separate, explicit, audited opt-in if it is ever implemented.
11. **Privacy controls** — clear current session, delete saved packet/report files, inspect data directory, and view bundled engine/licence versions.

### Information architecture

- Home
- New Audit
- Packet Workspace
  - Documents
  - Evidence
  - Findings
  - Report
- Settings
  - Privacy & Storage
  - OCR Languages
  - About / Licences

No cloud account, login, analytics, remote model, or server is required for the MVP.

## 4. Proposed system architecture

```text
┌──────────────────────────── Electron Desktop ────────────────────────────┐
│                                                                          │
│  React + TypeScript Renderer                                             │
│  Home | Packet Workspace | PDF Evidence Viewer | Findings | Settings    │
│                │ typed, narrow window.docuready API                     │
│  ──────────────┼──────────────── contextBridge ────────────────────────  │
│  Preload       │ allow-listed methods; schema-validated payloads        │
│  ──────────────┼──────────────── IPC ──────────────────────────────────  │
│  Electron Main Process                                                   │
│  File dialogs | window lifecycle | job registry | temp workspace        │
│  Path validation | child process lifecycle | export/save dialogs         │
│                │                                                         │
│                │ stdio JSONL protocol (no TCP listener)                  │
│  ──────────────┼───────────────────────────────────────────────────────  │
│  Packaged Python Sidecar                                                 │
│  Intake → existing AuditPipeline → result DTO → redacted exports         │
│       │                                                                  │
│       ├── PyMuPDF / candidate PDFium backend                             │
│       └── Tesseract executable + selected traineddata                   │
│                                                                          │
│  User-selected files / private per-job temp directory / explicit exports│
└──────────────────────────────────────────────────────────────────────────┘
```

### Responsibility split

**Renderer**
- Pure presentation and navigation; no Node APIs, filesystem paths, shell commands, or direct child-process access.
- Receives typed, redacted DTOs; requests operations through the preload API.
- Never decides audit status or recomputes statutory rules.

**Preload**
- Exposes only named methods such as `selectDocuments`, `startAudit`, `cancelAudit`, `replaceDocument`, `exportReport`, `clearSession`, `getEngineHealth`.
- No generic `send(channel, ...)`, raw `ipcRenderer`, or unrestricted filesystem API.
- Runtime-validates arguments and response shapes.

**Electron main**
- Owns OS dialogs, file handles, canonical path resolution, job lifecycle, and sidecar startup/shutdown.
- Validates IPC sender and rejects navigation/new windows except explicit allow-listed external links.
- Copies accepted inputs to an app-owned per-job workspace with restrictive permissions where supported.
- Sends only generated job IDs and controlled workspace references to the sidecar; never trusts renderer-provided arbitrary paths.
- Removes temporary files on success, failure, cancellation, app shutdown, and startup recovery.

**Python sidecar**
- Exposes a small versioned protocol; calls the existing Python package, not duplicated business logic.
- Emits structured progress/errors without extracted values or raw OCR text.
- Writes reports only to a path explicitly supplied by the main process, after redaction defaults are applied.
- Supports graceful shutdown and cancellation between documents/pages. Hard termination is a last resort.
- Includes a health response containing protocol version, engine version, OCR binary/version, available language packs, and PDF backend.

### Initial protocol contract (v1)

Each line is one UTF-8 JSON object. Standard output is protocol-only; diagnostics go to standard error.

Request envelope:
```json
{"protocol":1,"id":"request-uuid","method":"health","params":{}}
```

Response envelope:
```json
{"protocol":1,"id":"request-uuid","ok":true,"result":{"engine":"docuready"}}
```

Progress event:
```json
{"protocol":1,"event":"progress","job_id":"job-uuid","stage":"extract","completed":2,"total":5}
```

Error envelope:
```json
{"protocol":1,"id":"request-uuid","ok":false,"error":{"code":"UNSUPPORTED_FILE","message":"The selected file type is not supported."}}
```

Protocol requirements:
- Maximum line size, request timeout, bounded queue, and bounded number of concurrent jobs.
- Strict method allow-list and Pydantic request/response models.
- No arbitrary Python expression, module, shell, or path invocation.
- Correlate every response by request ID; tolerate out-of-order progress events.
- Version negotiation and explicit incompatible-version failure.
- No raw PII in progress, diagnostics, or crash logs.

## 5. Security, privacy, and hostile-document controls

Electron increases local privilege; treat the renderer as untrusted web content even though it is bundled locally.

Mandatory Electron settings:
- `nodeIntegration: false`
- `contextIsolation: true`
- `sandbox: true`
- restrictive Content Security Policy; no remote scripts/fonts/assets
- custom local app protocol rather than arbitrary `file://` access where feasible
- validate every IPC sender and every payload
- deny unneeded permissions, navigation, popups, and webviews
- use Electron fuses to disable unused capabilities (including run-as-Node and CLI inspect/debug options in packaged builds, after validating developer workflow)
- keep Electron and Chromium patched; produce dependency and vulnerability reports

Document handling:
- Treat PDFs and images as hostile input.
- Validate file signatures, MIME, size, dimensions, page count, decompression/render limits, and duplicate hashes.
- Parse/render in a separate constrained process with timeout and memory ceilings where feasible.
- Never load embedded remote resources or execute document scripts/actions.
- Use a private per-job workspace; never use the repository root or current working directory as a data directory.
- Redact logs and default exports; avoid filenames containing PII in telemetry/logs.
- Clear temporary data in `finally` paths and recover stale workspaces on next startup.
- No analytics, crash upload, cloud sync, auto-update network check, or background HTTP calls in the offline MVP. Any future update mechanism requires a separate opt-in and threat-model review.

**Important existing gap:** current documentation contains both verified contract-test evidence and older target-only security statements. Do not copy privacy claims wholesale into desktop marketing. The Electron app requires its own zero-network, file-lifecycle, log-redaction, IPC, hostile-file, and packaged-build tests. The existing Python no-network contract does not by itself prove the whole desktop application makes no network calls.

## 6. Dependency and licence gates

No dependency or bundled binary is approved merely because its wrapper package has a permissive licence. Record direct, transitive, native, traineddata, and platform-specific licences in `NOTICE`.

| Component | Candidate | Current assessment / gate |
|---|---|---|
| Desktop runtime | Electron | MIT; pin maintained release and Chromium security updates |
| Build/distribution | Electron Forge 8 | MIT; Node 22.17+; Vite plugin stable in v8 release notes |
| UI | React + TypeScript | MIT; keep UI dependencies lean |
| PDF rendering | PDF.js / `pdfjs-dist` | Apache-2.0; bundle locally; verify version and worker assets |
| Python bundler | PyInstaller | GPL with bootloader exception and Apache-2.0 components; inspect full bundled licence terms and include notices |
| OCR engine | Tesseract 5 | Apache-2.0; package executable and language traineddata with required notices |
| Current PDF backend | PyMuPDF 2.1 | AGPL or commercial licence. Existing repo marks this as provisional; no desktop redistribution until project owner resolves and records the licensing path |
| Candidate PDF backend | pypdfium2 + PDFium | pypdfium2 Apache-2.0/BSD-3-Clause; PDFium BSD-style plus third-party dependency notices. Existing repository PDFium implementation is incomplete (`get_words()` raises `NotImplementedError`); must pass geometry and corpus parity tests before replacing PyMuPDF |
| Local persistence | SQLite (stdlib Python or better-sqlite3) | Prefer no database in MVP; if needed, store metadata only and document retention/encryption decisions |

### Hard release blocker: PDF backend licence

PyMuPDF documentation states that PyMuPDF/MuPDF are dual-licensed under AGPL and commercial terms. The repo pins PyMuPDF 2.1 and currently uses it as the production default. Before distributing binaries, choose one of:
1. Obtain and document the required commercial licence; or
2. Complete PDFium backend work, verify bounding-box geometry, extraction parity, adversarial handling, and all golden/corpus tests, then make the permissive path the packaged default; or
3. Explicitly accept AGPL obligations after a documented project-owner review.

Do not quietly ship the current default in a closed-source or proprietary desktop package.

## 7. Packaging and distribution plan

Build per operating system and architecture in CI; do not attempt to cross-compile native Python dependencies from one host.

- Windows x64 first: installer and portable smoke test; bundle Tesseract and language data.
- macOS arm64 + x64: signed/notarized release pipeline when Apple credentials are available.
- Linux x64: AppImage/deb or deb/rpm after choosing supported targets.
- Keep the Python sidecar in an unpacked resource directory (onedir) initially; avoid one-file extraction/startup complexity until measured.
- Bundle exact Tesseract binary and traineddata selected for supported languages. Do not assume system Tesseract exists on end-user machines.
- Verify PyMuPDF/PDFium, Pillow, NumPy, and all native libraries load from installed artifacts on clean machines.
- Generate SBOM and `NOTICE` per release; include third-party licences and attribution.
- Sign installers where feasible; publish SHA-256 checksums.
- Test install, launch, upgrade policy, uninstall, and user-data retention separately.

## 8. Proposed repository layout

Do not move or rename the existing `src/docuready` Python package.

```text
DocuReady/
├── apps/
│   └── desktop/
│       ├── package.json
│       ├── forge.config.ts
│       ├── vite.*.config.ts
│       ├── src/
│       │   ├── main/
│       │   ├── preload/
│       │   └── renderer/
│       └── tests/
├── sidecar/
│   ├── protocol/
│   ├── build/
│   └── tests/
├── src/docuready/                 # existing Python engine, unchanged as authority
├── tests/                         # existing engine tests and golden baselines
├── docs/
│   ├── ELECTRON_DESKTOP_PLAN.md
│   └── adr/
│       └── ADR-002-desktop-runtime-and-sidecar.md
└── NOTICE
```

## 9. Delivery sequence and acceptance gates

### D0 — Baseline refresh and architecture freeze
- Refresh `main`, status, open PRs, CI and branch state.
- Confirm latest T2.3/T2.4 code and run the existing Python suite on the current baseline.
- Preserve golden baseline checksum; do not rewrite fixtures.
- Inventory engine entry points, document formats, extraction result shape, cancellation limits, filesystem writes, and network call sites.
- Record desktop architecture and protocol ADR.

**Exit:** verified main SHA, green baseline test evidence, clean working tree, architecture ADR reviewed.

### D1 — Electron shell proof of concept
- Scaffold Electron Forge 8 + Vite 8 + React + TypeScript under `apps/desktop`.
- Implement secure BrowserWindow, preload bridge, strict CSP, local-only renderer, app menu, native open/save dialogs.
- Build a mock sidecar client and typed protocol tests.

**Exit:** packaged development shell starts on Windows/macOS/Linux CI; renderer cannot access Node; IPC sender/schema tests pass.

### D2 — Python sidecar integration
- Add a small Python module/entry point implementing protocol v1.
- Start/monitor child process from Electron main; implement health, version negotiation, progress, error mapping, cancellation and shutdown.
- Add a protocol adapter that calls existing `AuditPipeline` and serializes existing models.
- Test against synthetic packet corpus.

**Exit:** one end-to-end synthetic packet audit produces equivalent domain findings/readiness to Python CLI/API; no duplicate business rules; sidecar restart/failure paths tested.

### D3 — First usable desktop workflow
- Implement packet creation, slot-based document intake, audit progress, results, finding details, redacted report export, clear session.
- Add PDF.js viewer with page/bounding-box evidence overlay.
- Add document replacement and full rerun.

**Exit:** complete user journey works with synthetic fixtures; keyboard/accessibility and error states covered; evidence coordinates match source PDF.

### D4 — Hardening and privacy
- File validation and resource limits; isolated temporary workspace; startup cleanup; no-PII logging; redacted exports.
- Electron security audit and hostile document corpus.
- Full zero-network test across renderer, main, sidecar, and packaged app.
- Verify all data deletion and cancellation paths.

**Exit:** threat model tests pass; no undocumented network egress; no raw PII in logs; temp lifecycle verified on each OS.

### D5 — Reproducible packaging
- PyInstaller onedir builds for Windows, macOS, Linux.
- Bundle and smoke-test Tesseract + required language files.
- Resolve PDF backend licence blocker.
- Platform-specific signing/notarization and installer tests.
- SBOM, notices, checksums and release documentation.

**Exit:** installable clean-machine builds with working OCR/PDF parsing; licence review signed off; all engine and desktop tests green.

## 10. Test strategy

**Python engine (existing):**
- Keep all current unit, integration, adversarial, privacy, golden, and four-version CI tests.
- No golden changes for desktop-only work.
- Add protocol adapter tests and equivalence tests against existing CLI/API outputs.

**Electron:**
- Unit tests for typed IPC contracts, path validation, job state machine, error mapping, and data lifecycle.
- Main/preload security tests: renderer cannot use Node, untrusted sender rejected, navigation/popups denied.
- Playwright or Electron end-to-end tests for open → audit → evidence → replace → export → clear.
- Packaged smoke tests on clean OS runners.
- Network interception tests covering Electron main/renderer and Python child process.
- Hostile PDFs, malformed images, oversized files, corrupt files, cancellation and abrupt process termination.

**Golden/equivalence invariant:** For the same synthetic packet, scheme config, and `as_of`, desktop result DTO must preserve the Python engine's canonical status, finding IDs, match grades, reason codes, evidence provenance, and redacted export content. UI may format these values but cannot reinterpret them.

## 11. Immediate implementation queue

1. Refresh project status and add this plan to the desktop branch.
2. Write ADR-002 covering Electron main/renderer boundaries, stdio protocol, Python packaging, and local storage.
3. Scaffold Forge 8 + React/TypeScript + Vite 8 shell under `apps/desktop`.
4. Add the protocol v1 Python sidecar entry point and health handshake.
5. Prove a single synthetic packet audit end-to-end before implementing the visual dashboard.
6. Build the evidence viewer and workflow only after DTO/evidence coordinate contracts are stable.

## 12. Research references

- Electron security checklist: https://www.electronjs.org/docs/latest/tutorial/security
- Electron context isolation: https://www.electronjs.org/docs/latest/tutorial/context-isolation
- Electron IPC: https://www.electronjs.org/docs/latest/tutorial/ipc
- Electron process model: https://www.electronjs.org/docs/latest/tutorial/process-model
- Electron Forge 8 release notes (Node 22.17+, ESM-only, Vite plugin stable): https://github.com/electron/forge/releases
- Electron Forge getting started: https://www.electronforge.io/
- PyInstaller documentation: https://pyinstaller.org/en/latest/
- Tesseract documentation and Apache-2.0 licence: https://tesseract-ocr.github.io/tessdoc/
- pypdfium2 platform and licensing documentation: https://pypdfium2.readthedocs.io/en/stable/readme.html
- PyMuPDF licensing: https://pymupdf.readthedocs.io/en/latest/about.html
- PDF.js getting started: https://mozilla.github.io/pdf.js/getting_started/

---

**Decision record:** This is an engineering proposal, not a claim that the Electron application has been implemented, packaged, tested, or privacy-certified. All release blockers remain open until demonstrated by reproducible tests and project-owner acceptance.
