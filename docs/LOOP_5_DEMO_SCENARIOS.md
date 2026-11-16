# DOCUREADY — HACKNATION 2026 COMPETITION DEMO SCENARIOS

**Milestone:** Loop 5 Phase 2 — Deterministic Demonstration Scenarios  
**Application Target:** DocuReady Desktop Application (Electron + React 19 + Python Sidecar)  
**Corpus Directory:** `tests/validation_corpus/`  
**Execution Mode:** 100% Offline, Deterministic Synthetic Data

---

## Scenario A: Standard Statutory Audit (Happy Path)

### Objective:
Demonstrate the core value proposition: importing a complete 6-document scholarship application packet, executing a statutory compliance audit in sub-100ms, displaying transparent rule passes, inspecting evidence provenance, and exporting a formal audit certificate.

### Step-by-Step Walkthrough:

1. **Step 1 — Launch & Clean Intake:**
   - Launch DocuReady via `apps/desktop/out/DocuReady-win32-x64/DocuReady.exe` (or `npm start` in development).
   - Observe initial clean state: "No documents imported. Drag and drop statutory application documents or select a folder to begin."
2. **Step 2 — Document Import:**
   - Click **"Select Documents"** (or point file selector to `tests/validation_corpus/`).
   - Select the 6 clean statutory documents:
     - `VAL_01_application_form.pdf`
     - `VAL_02_income_cert_clean.pdf`
     - `VAL_03_caste_cert_clean.pdf`
     - `VAL_04_residence_cert_clean.pdf`
     - `VAL_05_bank_passbook_clean.pdf`
     - `VAL_06_marksheet_clean.pdf`
   - Observe document cards appearing with verified file signatures (`PDF 1.4-1.7`, page counts, sizes).
3. **Step 3 — Audit Execution:**
   - Click **"Run Pre-submission Audit"**.
   - Observe progress indicator transitioning smoothly across stages:
     - Stage 1: Intake & Validation
     - Stage 2: Extraction & OCR Fallback Check
     - Stage 3: Statutory Rule Resolution
     - Stage 4: Redaction & Canonical Formatting
   - Real execution latency: **~60 ms** (appears instant).
4. **Step 4 — Findings Overview:**
   - Readiness Banner displays: **READY TO SUBMIT (100% Score)** in emerald green.
   - Summary counts: `8 Passed`, `0 Needs Checks`, `0 Action Required`.
   - Statutory rules verified: Name Consistency, Date of Birth alignment, Income Ceiling (< Rs. 2.5L), Income Certificate matching, Domicile verification (ODISHA), Bank Account DBT enablement, Marksheet qualification.
5. **Step 5 — Evidence & Source Page Navigation:**
   - Click on rule `RULE-INC-MATCH-PASS` ("Income declared in form matches revenue authority certificate").
   - PDF Evidence Viewer opens in split pane:
     - Left: Finding details, statutory citation (OSSP Guidelines 2024-25, Section 3.2), match grade `EXACT`.
     - Right: Rendered PDF with highlighted emerald bounding box around `1,20,000` on Page 1.
6. **Step 6 — Report Export:**
   - Click **"Export Audit Certificate"**.
   - JSON/PDF audit report generated. Verify zero PII in export metadata.

---

## Scenario B: Defective & Hostile Document Packet (Safety & Diagnostics)

### Objective:
Demonstrate DocuReady's defensive architecture when presented with corrupted files, unreadable passwords, mismatched applicant names, or income ceiling breaches. Prove that invalid evidence never becomes fabricated findings.

### Step-by-Step Walkthrough:

1. **Step 1 — Reset Session:**
   - Click **"Clear Session"** (ephemeral staging cleaned up in ~54ms).
2. **Step 2 — Import Defective & Hostile Files:**
   - Select:
     - `VAL_01_application_form.pdf` (Applicant: Aarav Sharma)
     - `VAL_07_income_cert_name_conflict.pdf` (Applicant: Vikramaditya Roy)
     - `VAL_08_income_cert_ceiling_exceeded.pdf` (Income: Rs. 4,50,000/-)
     - `VAL_09_corrupted_header.pdf` (Corrupted byte stream)
     - `VAL_11_encrypted_password.pdf` (AES-256 password protected)
     - `VAL_12_spoofed_text_as_pdf.pdf` (Plain text renamed as .pdf)
3. **Step 3 — Ingest Boundary Rejection:**
   - Observe immediate ingest feedback:
     - `VAL_12_spoofed_text_as_pdf.pdf`: Flagged with "Invalid magic bytes (not a valid PDF)".
     - `VAL_09_corrupted_header.pdf`: Flagged with "Corrupted document stream".
     - `VAL_11_encrypted_password.pdf`: Flagged with "Encrypted / Password Protected".
4. **Step 4 — Execute Audit on Contradictory Data:**
   - Execute audit with `VAL_01` and `VAL_07`.
   - Readiness Banner displays: **ACTION REQUIRED (Readiness Score: 0%)** in crimson.
   - Finding 1: `RULE-NAME-01` (`FATAL`, Penalty -40)
     - "Contradictory applicant name mismatch between Application Form ('Aarav Sharma') and Income Certificate ('Vikramaditya Roy')."
     - Statutory Reference: OSSP Guidelines 2024-25 Section 4.1.
     - Remediation: "Obtain an Income Certificate issued in the exact name of the applicant."
5. **Step 5 — Non-Fabrication Guarantee:**
   - Highlight that zero synthetic coordinates or false matches are generated for the corrupted or encrypted files. The system reports `UNREADABLE` / `CORRUPTED` without crashing.

---

## Scenario C: Evidence Traceability & Provenance Chain

### Objective:
Demonstrate the deep technical differentiation of DocuReady: every finding is tied to an immutable provenance chain from document pixel coordinates through OCR confidence calibration, match grade, and export.

### Step-by-Step Walkthrough:

1. **Step 1 — Load Traceability Sample:**
   - Load Scanned Domicile Certificate (`VAL_14_residence_cert_scanned.pdf`).
2. **Step 2 — Audit & OCR Provenance Inspection:**
   - Run audit.
   - Open Finding `RULE-DOM-PASS` ("Applicant domicile state matches required scheme jurisdiction").
3. **Step 3 — Inspect Provenance Chain:**
   - The UI reveals the full 4-tier Provenance Contract:
     - **Document Fingerprint:** SHA-256 hash of source PDF.
     - **Source Page:** Page 1 of 1.
     - **Bounding Box Geometry:** `[x0: 120.4, y0: 340.2, x1: 280.1, y1: 362.5]` points.
     - **Extraction Method:** `LOCAL_OCR` (Tesseract 5.4.0 with Leptonica 200 DPI binarization).
     - **Calibrated Confidence:** `0.944` (calibrated probability).
     - **Match Grade:** `EXACT` (case-insensitive normalized exact string match).
4. **Step 4 — Live Viewport Transformation:**
   - Rotate the PDF viewer by 90° and 180° using UI controls.
   - Observe that the highlighted bounding box smoothly transforms to track the exact rotated coordinate space without drifting or clipping.
5. **Step 5 — Cross-Reference Exported Audit Record:**
   - Open the exported JSON certificate side-by-side with the screen.
   - Point out that the exported record carries the exact same `evidence_id`, `rule_id`, and `reason_code` (`CONFIRMED_OK`), enabling downstream government portals to automate verification.

---
*HackNation 2026 Demonstration Scenarios Approved.*
