# DOCUREADY — WINDOWS CLEAN ENVIRONMENT VALIDATION REPORT

**Milestone:** Loop 6 — Release Integrity, Claims Audit & Independent Reproducibility  
**Date:** 2026-11-16  
**Auditor:** Antigravity Release Engineer / Independent QA Auditor  
**Repository:** `Algoryxz/DocuReady`  
**Test Harness:** `scripts/verify_clean_windows_runtime.ps1`  
**Raw Test Log:** `docs/clean_machine_validation.log`  

---

## 1. Executive Summary & Verification Matrix

Validation was conducted under an isolated, scrubbed Windows environment simulating a pristine consumer Windows 10/11 machine.

### Environment Isolation Constraints Enforced:
- **`PATH` Sanitization:** Purged of all developer tools, Node.js, Python, Git, and system Tesseract:
  ```powershell
  $env:PATH = "C:\Windows\system32;C:\Windows;C:\Windows\System32\Wbem;C:\Windows\System32\WindowsPowerShell\v1.0\"
  ```
- **Environment Variables Removed:** `DOCUREADY_*`, `TESSDATA_PREFIX`, `PYTHON*` completely unset.
- **Verification of Tool Unreachability:**
  - `Get-Command python` → `CommandNotFoundException` (**CONFIRMED UNREACHABLE**)
  - `Get-Command tesseract` → `CommandNotFoundException` (**CONFIRMED UNREACHABLE**)

### Overall Qualification Matrix:

| Verification Item | Target Distribution | Expected Behavior | Actual Observed Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| **1. Extraction & Layout** | Portable ZIP | Unpacks clean tree without nested paths | Extracted 1,877 files to temp sandbox | **PASSED** |
| **2. Binary Integrity** | Portable ZIP | `DocuReady.exe` & sidecar present | Executable & sidecar confirmed present | **PASSED** |
| **3. Health Handshake** | Packaged Sidecar | JSON-RPC protocol v1 response | `ok: true`, `status: "healthy"`, `protocol: 1` | **PASSED** |
| **4. Bundled OCR Discovery** | Packaged Sidecar | Discover bundled `tesseract.exe` 5.4.0 | `ocr_source: "bundled_resource"`, `is_bundled: true` | **PASSED** |
| **5. Clean Packet Audit** | `pkt_01_clean` | 100/100 score; zero violations | Score: 100, `NO_ISSUES_FOUND` | **PASSED** |
| **6. Degraded Scan OCR** | `pkt_07_unreadable_doc` | Raster PDF rendered & OCR executed | Tesseract executed via pipe; OCR fields populated | **PASSED** |
| **7. Discrepancy Detection** | `pkt_02_name_conflict` | Flag conflicting applicant name | `RULE-NAME-01 FAIL` flagged with coordinates | **PASSED** |
| **8. Bounding Box Provenance**| `pkt_02_name_conflict` | Physical page coordinates emitted | Form `[283.6, 123.7, 378.1, 137.5]` vs Marksheet | **PASSED** |
| **9. Process Lifecycle** | `DocuReady.exe` | Launches, renders, exits cleanly | PID 6664 launched & cleanly terminated | **PASSED** |
| **10. Zero-PII Redaction** | Export / Protocol | Redact names & sensitive data | Logs emit `'[REDACTED]'` strings | **PASSED** |
| **11. Sandbox Cleanup** | Temp directory | Leaves no persistent artifacts | Directory deleted cleanly; 0 residual files | **PASSED** |

---

## 2. Tested Distribution Artifacts

| Distribution | Tested File | Size | SHA-256 Checksum |
| :--- | :--- | :--- | :--- |
| **Windows Portable ZIP** | `apps/desktop/out/make/zip/win32/x64/DocuReady-win32-x64-0.1.0.zip` | 426.01 MB | `DEE339C290B23A953BF9A86ED94E0EDD1AAEE79C4E5714283C004350A80196C5` |
| **Windows Setup Installer** | `apps/desktop/out/make/squirrel.windows/x64/DocuReady-0.1.0-Setup.exe` | 415.65 MB | `E8326B71C919A203A3099126CB745C1FAC1D84D01BDBD1E442F1432D8578EC01` |

---

## 3. Detailed Execution Evidence

### 3.1. Sidecar Health Handshake (Without Host Python or Tesseract)
```json
{
  "protocol": 1,
  "id": "clean-h",
  "ok": true,
  "result": {
    "sidecar": "docuready-python",
    "protocol": 1,
    "engine_version": "0.1.0",
    "python": "3.12.10",
    "pdf_backend": "pymupdf",
    "ocr_available": true,
    "ocr_languages": ["eng"],
    "ocr_source": "bundled_resource",
    "is_bundled": true,
    "ocr_error": null,
    "tesseract_version": "5.4.0.20240606",
    "tesseract_path": "tesseract.exe"
  }
}
```
**Conclusion:** The sidecar correctly locates `tesseract.exe` within its bundled application resources and initializes the internal Python 3.12.10 runtime without external dependencies.

### 3.2. Clean Packet Audit (`pkt_01_clean`)
- **Readiness Score:** 100/100
- **Overall Status:** `NO_ISSUES_FOUND`
- **Rule Evaluations:** 8 passing checks (`RULE-NAME-PASS`, `RULE-DOB-PASS`, `RULE-INC-CEIL-PASS`, `RULE-INC-MATCH-PASS`, `RULE-EXP-PASS`, `RULE-BNK-IFSC-PASS`, `RULE-DOM-PASS`, `RULE-MRK-PASS`).
- **Provenance Anchor:** Application form applicant name bounding box: `[283.6, 123.7, 378.1, 137.5]`.

### 3.3. Degraded Document OCR Audit (`pkt_07_unreadable_doc`)
- **Execution Mode:** Scanned image PDF without native vector text layer.
- **OCR Invocation:** The bundled Tesseract engine executed on temporary PPM/PNG rasters.
- **Result:** Successfully parsed degraded fields, applied the 9-feature logistic calibrator, and downgraded uncertain OCR text to safe manual review rather than rejecting the applicant.

### 3.4. Name Discrepancy Detection (`pkt_02_name_conflict`)
- **Flagged Finding:**
  ```text
  RULE-NAME-01 FAIL Conflicting applicant names between APPLICATION_FORM ('[REDACTED]') and MARKSHEET ('[REDACTED]').
  ```
- **Provenance Bounding Boxes:**
  - `application_form.pdf` (Page 1): `[283.6, 123.7, 378.1, 137.5]`
  - `marksheet.pdf` (Page 1): `[128.1, 105.8, 217.0, 119.5]`

---

## 4. Reproducible Procedure for External Evaluators

Any engineer or evaluator can replicate this verification on an air-gapped Windows machine using the following PowerShell command:

```powershell
# In PowerShell:
$env:PATH = "C:\Windows\system32;C:\Windows;C:\Windows\System32\Wbem"
.\scripts\verify_clean_windows_runtime.ps1
```
The script will output exact timestamps, execution metrics, and pass/fail indicators directly to the console and to `docs/clean_machine_validation.log`.
