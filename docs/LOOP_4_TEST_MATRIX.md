# DocuReady Desktop — Loop 4 Validation Test Matrix
**Milestone:** Loop 4 Product Validation, Real-World Workflow Testing & Release Candidate Qualification  
**Target:** Electron Desktop + Standalone Python Sidecar on Windows x64  
**Date:** 16 November 2026

---

## 1. Overview and Objectives

This test matrix formalizes the end-to-end qualification procedures for DocuReady Desktop. It tests the application as a cohesive desktop system (Electron main process, context-isolated preload bridge, React 19 renderer, sandboxed PDF.js viewer, and packaged Python onedir sidecar over JSONL stdio RPC).

---

## 2. Comprehensive Workflow Test Matrix

### Workflow A: Standard Application Packet (Happy Path)
| ID | Step | Input / Action | Expected Result | Automated Test / Procedure | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **WFA-01** | Application Initialization | Launch Electron Desktop app | Window opens with 3-panel workspace, Engine status reports "Healthy", zero sessions active. | `apps/desktop/tests/sidecar.test.ts` | **PASS** |
| **WFA-02** | Document Intake | Import 5 valid statutory documents (`VAL_01` to `VAL_05`) | Documents registered with unique `doc-*` IDs, file sizes, and valid MIME types. Raw host paths NOT leaked. | `apps/desktop/tests/workspace.test.ts` | **PASS** |
| **WFA-03** | Packet Creation | Create packet for scheme `odisha_post_matric` | Ephemeral directory created under `docuready-ws-*`, files staged safely, packet descriptor returned. | `apps/desktop/tests/workspace.test.ts` | **PASS** |
| **WFA-04** | Audit Execution | Start audit via `audit:start` | Stdio progress events streamed (`intake`, `extraction`, `validation`, `completed`), job completes with status `READY`. | `apps/desktop/tests/parity.test.ts` | **PASS** |
| **WFA-05** | Finding Inspection | Click finding card in right panel | Finding details expand (Rule ID, status, penalty, match grade, reason code, statutory citation, remediation). | `apps/desktop/tests/evidence.test.ts` | **PASS** |
| **WFA-06** | Evidence Navigation | Click "Inspect in Viewer ↗" on finding | Document switcher switches to source PDF, navigates to source page, scrolls bounding box into view. | `apps/desktop/tests/coordinates.test.ts` | **PASS** |
| **WFA-07** | Report Export | Invoke `exportReport({ format: "json" })` | Redacted canonical JSON report saved to user-selected path, containing 0 unredacted PII. | `apps/desktop/tests/parity.test.ts` | **PASS** |
| **WFA-08** | Session Destruction | Invoke `session:clear` | Ephemeral workspace directory recursively deleted, documents array cleared, active workspace count returns to 0. | `apps/desktop/tests/workspace.test.ts` | **PASS** |

---

### Workflow B: Mixed-Quality Packet (OCR and Multi-Format)
| ID | Step | Input / Action | Expected Result | Automated Test / Procedure | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **WFB-01** | Native Vector PDF | Import vector `application_form.pdf` | Extracted via `NATIVE_VECTOR` with exact character geometries and 0 OCR latency. | `tests/test_extractor.py` | **PASS** |
| **WFB-02** | Scanned Raster PDF | Import 200 DPI bitmap `VAL_04_residence_cert_scanned.pdf` | Detected as scanned; Tesseract OCR executed dynamically; confidence scores calibrated. | `tests/test_ocr_acceptance.py` | **PASS** |
| **WFB-03** | Missing OCR Fallback | Simulate Tesseract unavailable on scanned image | Fails closed with structured `OCR_UNAVAILABLE` or `UNREADABLE_DOC`; never fabricates missing text. | `tests/test_ocr_acceptance.py` | **PASS** |
| **WFB-04** | Negative Document | Import `VAL_13_irrelevant_resume.pdf` | Correctly identified as having zero scholarship slots; produces zero false-positive evidence. | `tests/test_dataset_ground_truth.py` | **PASS** |

---

### Workflow C: Evidence Geometry & Rotation Verification
| ID | Step | Input / Action | Expected Result | Automated Test / Procedure | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **WFC-01** | Upright Geometry (0°) | Upright document bounding box | Transform maps PyMuPDF top-left points directly to CSS pixels: `left = x0*s`, `top = y0*s`. | `apps/desktop/tests/coordinates.test.ts` | **PASS** |
| **WFC-02** | Rotated Geometry (90°) | 90° clockwise document (`VAL_06`) | Transform maps coordinates: `left = (pageH - y1)*s`, `top = x0*s`. Box aligns with visible text. | `apps/desktop/tests/coordinates.test.ts` | **PASS** |
| **WFC-03** | Rotated Geometry (180°) | 180° rotated document page | Transform maps coordinates: `left = (pageW - x1)*s`, `top = (pageH - y1)*s`. Box correctly oriented. | `apps/desktop/tests/coordinates.test.ts` | **PASS** |
| **WFC-04** | Rotated Geometry (270°) | 270° clockwise document page | Transform maps coordinates: `left = y0*s`, `top = (pageW - x1)*s`. Box accurately rendered. | `apps/desktop/tests/coordinates.test.ts` | **PASS** |
| **WFC-05** | Missing Coordinates | Finding with unlocated field (e.g. general income ceiling) | Evidence item has `bounding_box: null`. Rendered as "Page-level statutory finding" without box overlay. | `apps/desktop/tests/evidence.test.ts` | **PASS** |
| **WFC-06** | Coordinate Clamping | Negative or out-of-bounds coordinates | Coordinates clamped within `[0, 0, width, height]` without throwing DOM exceptions. | `apps/desktop/tests/coordinates.test.ts` | **PASS** |

---

### Workflow D: Adversarial Document Ingestion & Defensive Bounds
| ID | Step | Input / Action | Expected Result | Automated Test / Procedure | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **WFD-01** | 0-Byte Empty File | Import `VAL_10_empty_zero_byte.pdf` | Rejected at workspace boundary with structured `INVALID_PARAMS` error before sidecar processing. | `tests/test_adversarial_documents.py` | **PASS** |
| **WFD-02** | Corrupted PDF Header | Import `VAL_09_corrupted_header.pdf` | Document marked `CORRUPTED`; extracted fields empty; pipeline scores as missing doc without crash. | `tests/test_adversarial_documents.py` | **PASS** |
| **WFD-03** | Encrypted PDF | Import `VAL_11_encrypted_password.pdf` | Detected as password-protected; rejected with `NEEDS_PASSWORD` status; 0 credential leakage. | `tests/test_adversarial_documents.py` | **PASS** |
| **WFD-04** | Extension Spoofing | Plain text file renamed `.pdf` (`VAL_12`) | Magic byte validation (`%PDF`) rejects file during document registration. | `apps/desktop/tests/security.test.ts` | **PASS** |
| **WFD-05** | Document Limit (>20) | Attempt to stage packet with 21 documents | Rejected with `Packet document count exceeds maximum limit of 20`. | `tests/test_adversarial_documents.py` | **PASS** |
| **WFD-06** | File Size Limit (>50MB) | Attempt to stage 55MB document | Rejected with `Document exceeds maximum file size limit of 50MB`. | `apps/desktop/tests/security.test.ts` | **PASS** |
| **WFD-07** | Directory Traversal | Document filename containing `../../secret` | Rejected with `Directory traversal detected`. Workspace root containment strictly enforced. | `apps/desktop/tests/workspace.test.ts` | **PASS** |

---

### Workflow E: Process Failure, Cancellation & Recovery
| ID | Step | Input / Action | Expected Result | Automated Test / Procedure | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **WFE-01** | Process Sudden Crash | Kill sidecar child process with `SIGKILL` | SidecarManager detects termination; next IPC call automatically respawns child and executes cleanly. | `apps/desktop/tests/sidecar.test.ts` | **PASS** |
| **WFE-02** | Active Audit Cancel | Click "Cancel Audit" during extraction stage | `cancelAudit` hard-terminates long-running child, resets status to `cancelled`, respawns fresh worker. | `apps/desktop/src/main/sidecar.ts` | **PASS** |
| **WFE-03** | Stale Workspace Cleanup | Terminate app mid-audit; restart app | Startup sweep detects abandoned `docuready-ws-*` directories in tmp and removes them cleanly. | `apps/desktop/tests/workspace.test.ts` | **PASS** |
| **WFE-04** | Protocol Frame Overflow | Send payload > 1MB over stdio | Rejected with `REQUEST_TOO_LARGE` frame without buffer overflow or stream corruption. | `tests/test_desktop_sidecar_protocol.py` | **PASS** |
