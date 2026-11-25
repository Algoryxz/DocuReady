# Loop 32 — Codebase Inventory & Architecture Map

## 1. Executive Summary
- **Python Source Modules:** 44 modules across `src/docuready/` (14,918 lines of code).
- **Desktop Electron Modules:** 17 modules across `apps/desktop/src/` (5,520 lines of code).
- **Python Test Suites:** 76 test files in `tests/`.
- **Desktop Test Suites:** 10 test files in `apps/desktop/tests/`.
- **Machine-Readable Inventory:** [module_inventory.json](file:///c:/Users/smara/Desktop/New folder/research/loop32/module_inventory.json).

---

## 2. Python Architecture (`src/docuready/`)

| Subsystem / Module | Responsibility | Key Inputs | Key Outputs | Dependencies | Tests | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `evidence.cross_document` | Cross-document corroboration, contradiction detection, entity resolution, and duplicate detection. | `FieldClaim`, `EntityIdentity`, `DocumentIdentity` | `CrossDocumentVerificationResult`, `VerificationOutcome` | Python stdlib (`re`, `hashlib`, `math`, `difflib`, `dataclasses`) | `tests/test_loop28_cross_document.py` | Healthy |
| `ocr.engine` | Document OCR, Tesseract routing, script-aware multilingual fallback. | Raw images, PDF bytes, DPI | Word bounding boxes, OCR tokens, character confidences | `pytesseract`, `PIL`, `pypdfium2` | `tests/test_ocr_integration.py`, `tests/test_loop14_multilingual_ocr.py` | Healthy |
| `ocr.orientation` | Two-tier orientation detection, upright fast-path, and rotation recovery. | Input document image | Corrected image, orientation angle ($0^\circ, 90^\circ, 180^\circ, 270^\circ$) | `cv2`, `numpy`, `PIL` | `tests/test_loop02_orientation_assurance.py` | Healthy |
| `ocr.deskew` | Skew angle estimation and affine deskew transformation. | Document image | Deskewed image, affine matrix | `cv2`, `numpy` | `tests/test_loop04_deskew_reliability.py` | Healthy |
| `table.reconstruction` | Borderless and bordered table grid detection, cell association, and header fusion. | OCR tokens, spatial bounding boxes | Reconstructed table, row-column cells | Python stdlib | `tests/test_loop19_table_association.py`, `tests/test_loop21_header_and_decimal.py` | Needs investigation |
| `normalizer` | Alphanumeric normalization, date parsing, currency, and numeric formatting. | Raw OCR strings | Clean normalized tokens | `re`, `datetime` | `tests/test_normalizer.py`, `tests/test_loop27_identifier_integrity.py` | Healthy |
| `decision` | Audit decision engine, statutory rule evaluation, and explainability. | Extraction outcomes, candidate claims | Final verification decision, findings ledger | Python stdlib | `tests/test_loop06_decision_engine.py`, `tests/test_decision_safety.py` | Healthy |
| `sidecar.protocol` | Sidecar IPC protocol, stdin/stdout JSON-RPC messaging. | Stdin JSON commands | Stdout JSON responses, stderr logs | Python stdlib | `tests/test_desktop_sidecar_protocol.py` | Healthy |

---

## 3. Electron Desktop Architecture (`apps/desktop/src/`)

| Component | Path | Responsibility | Inputs / Outputs | Error Handling | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Main Process Entry** | `main/index.ts` | Window lifecycle, single-instance lock, crash recovery. | App launch events -> BrowserWindow instance | Handles `render-process-gone`, `unresponsive` | Healthy |
| **Workspace Manager** | `main/workspace.ts` | Ephemeral session directory isolation, path traversal defense, file staging. | Local file paths -> staged session documents | Rejects `..`, invalid extensions, oversized files | Healthy |
| **Sidecar Manager** | `main/sidecar.ts` | Child process spawning, JSON-RPC communication, crash recovery. | Audit request -> JSON stdout responses | Restarts dead sidecar, enforces 60s timeout | Healthy |
| **Preload Bridge** | `preload/index.ts` | Context isolation, typed IPC renderer-to-main bridge. | UI invocations -> IPC messages | Context isolation enabled, zero Node.js leakage | Healthy |
| **Renderer UI** | `renderer/App.tsx` | Human review UX, PDF evidence viewing, status filtering. | React state, findings list | Error boundary, fallback status pills | Healthy |

---

## 4. Dependencies & Packaging Architecture
- **Packaging:** Electron Forge with `@electron-forge/maker-squirrel` and `@electron-forge/maker-zip`.
- **Runtime OCR:** Bundled Tesseract 5.3.3 binaries and traineddata (`eng`, `hin`, `ori`) in `sidecar/`.
- **Network Isolation:** Hardened Content Security Policy (`connect-src 'none'`), zero external cloud telemetry.
- **Dead Code & Circular Dependencies:** None detected in core execution paths.
