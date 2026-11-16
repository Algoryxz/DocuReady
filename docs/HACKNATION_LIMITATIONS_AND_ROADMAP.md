# HACKNATION 2026 — CURRENT LIMITATIONS & STRATEGIC ROADMAP

**Project:** DocuReady  
**Document:** [`docs/HACKNATION_LIMITATIONS_AND_ROADMAP.md`](file:///c:/Users/smara/Desktop/New%20folder/docs/HACKNATION_LIMITATIONS_AND_ROADMAP.md)  
**Author:** Antigravity Engineering Agent

---

## 1. Honest, Evidence-Backed Account of Current Limitations

To maintain the highest engineering standards and integrity during competition evaluation, DocuReady’s known constraints and open gates are explicitly documented:

### 1.1 Single Statutory Scheme Target
- **Current State:** The active statutory rules (`src/docuready/rules/validator.py`) are calibrated against the reference specification: **Odisha State Post-Matric Scholarship (SC/ST/OBC) 2024-25**.
- **Limitation:** National schemes (e.g., Central NSP, PM-YASASVI) or alternate states with different mandatory certificate matrices require additional scheme configuration profiles.

### 1.2 PDF Backend Licensing Gate (PyMuPDF / AGPL-3.0)
- **Current State:** The production application uses PyMuPDF (fitz) as its primary PDF parsing backend, which is dual-licensed under AGPL-3.0 and commercial terms.
- **Limitation:** While open-source deployment under AGPL-3.0 is permissible, proprietary commercial distribution is gated until the project owner executes a commercial licensing agreement with Artifex (Option A) or completes the long-term migration to PDFium (Option C).

### 1.3 Table Regular Expression Coordinate Capture (DEF-05)
- **Current State:** In `application_form.pdf`, the annual income figure embedded in a multi-column table is parsed via robust regular expression extraction.
- **Limitation:** In this specific slot, word-token level bounding box coordinates are unavailable, and the engine safely sets `bounding_box: None`. While this correctly prevents coordinate hallucination, visual highlighting in the viewer falls back to full-page display for this single field.

### 1.4 Host System OCR Dependency
- **Current State:** While the Python engine and all data science libraries are fully bundled inside the standalone PyInstaller executable, the underlying Tesseract OCR engine (5.4.0) relies on local system installation on the host machine.
- **Limitation:** On a machine without Tesseract installed, scanned bitmap PDFs trigger a graceful notice: `"Not Installed (System Prerequisite)"`, whereas pure vector PDFs continue to audit at 100% functionality.

### 1.5 Operating System Packaging Verification
- **Current State:** Automated end-to-end builds, packaging, and sidecar verification have been validated specifically on **Windows 11 x64**.
- **Limitation:** macOS (Apple Silicon/Intel) and Linux (`.deb` / `.rpm` / AppImage) packaging pipelines are architecturally designed but remain unverified on native hardware.

---

## 2. Post-Hackathon Engineering Roadmap

```
+-----------------------------------------------------------------------------------+
| MILESTONE 1: Q1 2027 — Multi-Scheme Dynamic Rule Packs                            |
| - Pluggable JSON/YAML Scheme Definitions (NSP, PM-YASASVI, State Scholarships)    |
| - Dynamic form validator loader with rule schema versioning                       |
+-----------------------------------------------------------------------------------+
                                          |
+-----------------------------------------v-----------------------------------------+
| MILESTONE 2: Q2 2027 — Self-Contained OCR & PDFium Migration                      |
| - Custom PDFium character-bounding-box clustering to replace PyMuPDF (Option C)   |
| - Fully bundled, zero-install Tesseract / ONNX micro-OCR runtime                  |
+-----------------------------------------------------------------------------------+
                                          |
+-----------------------------------------v-----------------------------------------+
| MILESTONE 3: Q3 2027 — Cross-Platform Installer Certification                     |
| - Apple Silicon Universal 2 bundle with macOS Gatekeeper code signing             |
| - Linux AppImage / Snap packaging for rural kiosk distributions                   |
+-----------------------------------------------------------------------------------+
```

---
*Transparency Statement Certified for HackNation 2026 Evaluation.*
