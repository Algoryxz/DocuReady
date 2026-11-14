# DocuReady — Prototype Demonstration Runbook

**Document Version:** 1.0.0 (Track A Prototype Release)
**Target Repository:** `Algoryxz/DocuReady`
**System Target:** Local-first, deterministic document readiness linter for citizen welfare schemes.

---

## 1. Environment Setup & Prerequisites

DocuReady runs entirely client-side without external cloud dependencies or API keys.

### System Requirements
- **Python**: Version `3.10`, `3.11`, or `3.12` (supported in CI matrix).
- **Operating System**: Linux, macOS, or Windows.
- **Optional Local OCR Engine**: Tesseract OCR (`v5.0+`) for low-quality scan OCR fallback.
  - *Windows*: Default installation path is `C:\Program Files\Tesseract-OCR\tesseract.exe`.
  - *Ubuntu/Debian*: `sudo apt-get install -y tesseract-ocr`
  - *macOS*: `brew install tesseract`

### Virtual Environment Setup
```bash
# Clone and enter the canonical repository
git clone https://github.com/Algoryxz/DocuReady.git
cd DocuReady

# Create an isolated virtual environment
python -m venv .venv

# Activate the virtual environment
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# Linux / macOS:
source .venv/bin/activate
```

---

## 2. Installation Commands

Install the `docuready` package in editable mode with all optional extras (`ui`, `generator`, `dev`):

```bash
# Install package with all dependencies
pip install -e ".[all]"

# Verify package installation and CLI entry point
docuready --help
```

---

## 3. Local Launch Command

Launch the interactive applicant-facing Streamlit application:

```bash
# Launch Streamlit web interface
streamlit run src/docuready/interfaces/ui/app.py
```

*Note: Streamlit telemetry and usage metrics are automatically disabled via `.streamlit/config.toml`.*

The application will open in your default browser at `http://localhost:8501`.

---

## 4. The 8 Demonstration Packets & Inspection Scenarios

DocuReady includes 8 synthetic demonstration packets under `synthetic_data/`, representing typical real-world citizen application hurdles:

| Packet ID | Intended Demonstration Scenario | Expected Status | Expected Score | Key Defects Inspected |
| :--- | :--- | :---: | :---: | :--- |
| **`PKT_01_CLEAN`** | **Flawless Baseline Packet**: All 6 mandatory documents present, consistent applicant name, matching DOB, certified income ₹1,80,000 within statutory ceiling. | `READY_TO_SUBMIT` | **100 / 100** | 0 defects. Ideal baseline. |
| **`PKT_02_NAME_CONFLICT`** | **Demographic Discrepancy**: Minor name mismatch between Application Form (`Smruti Ranjan Nayak`) and Income Certificate (`Smruti Nayak`). | `ACTION_REQUIRED` | **75 / 100** | 1 critical defect (`RULE-NAME-01`). |
| **`PKT_03_DOB_CONFLICT`** | **Date of Birth Contradiction**: Application Form declares `14/05/2003`, but Marksheet certifies `14/06/2003`. | `ACTION_REQUIRED` | **75 / 100** | 1 critical defect (`RULE-DOB-01`). |
| **`PKT_04_INCOME_CONFLICT`** | **Statutory Ceiling Breach**: Certified annual income of ₹3,20,000 exceeds the Odisha Post-Matric scheme threshold of ₹2,50,000. | `REJECT_PRECHECK` | **40 / 100** | Fatal economic barrier (`RULE-INC-01`) + mismatch (`RULE-INC-02`). |
| **`PKT_05_MISSING_CERTIFICATE`** | **Packet Incompleteness**: Omission of mandatory Caste Certificate (`CASTE_CERT`). | `REJECT_PRECHECK` | **65 / 100** | Fatal missing document barrier (`RULE-DOC-01`). |
| **`PKT_06_MULTIPLE_DEFECTS`** | **Compound Failure**: Expired income certificate (issued 2020), name discrepancy, DOB conflict, and academic score failure. | `ACTION_REQUIRED` | **0 / 100** | 4 concurrent defects. Submissions blocked. |
| **`PKT_07_UNREADABLE_DOC`** | **Scan Degradation / OCR Failure**: Severe image blur and low DPI on income certificate. | `UNREADABLE_PACKET` | **75 / 100** | 1 critical scan defect (`RULE-DOC-02`). |
| **`PKT_08_AMBIGUOUS_EVIDENCE`** | **Format Ambiguity / Permissible Variation**: Ambiguous date notation (`05/06/2003` DD/MM vs MM/DD) and initials variation (`S. R. Nayak`). | `REVIEW_RECOMMENDED` | **85 / 100** | 2 advisory review items (`RULE-NAME-02`, `RULE-DOB-02`). |

---

## 5. End-to-End Walkthrough

### Step 1: Navigate to Screen 2 ("Upload Documents")
1. In the left navigation sidebar, select **"2. Upload Documents"**.
2. Under **"1. Load Demonstration Test Packet"**, choose `PKT_03_DOB_CONFLICT` from the dropdown.
3. Click **"📥 Load & Audit Selected Packet"**.
4. Observe the instant audit completion message (< 20 ms).

### Step 2: Inspect Dashboard & Extraction Evidence (Screens 1 & 3)
1. Navigate to **"1. Dashboard"**: Observe readiness score of `75 / 100` and determination `🟠 ACTION REQUIRED`.
2. Navigate to **"3. Document Extraction & Evidence"**:
   - Expand the **Marksheet** section.
   - Inspect the exact extracted `dob` field: raw value `14/06/2003`, normalized format `2003-06-14`, and bounding box coordinates.
   - Review the verbatim raw text snippet preview.

### Step 3: Inspect Cross-Document Validation Matrix (Screen 4)
1. Navigate to **"4. Cross-Document Validation"**.
2. Look at **"2. Date of Birth Cross-Comparison"**:
   - Notice the side-by-side callouts comparing `Application Form (14/05/2003)` against `Marksheet (14/06/2003)`.

### Step 4: Review Findings & Remediation Guidance (Screen 5)
1. Navigate to **"5. Audit Results"**.
2. Observe finding card **"1. Cross-Document Date of Birth Consistency (-25 pts)"**.
3. Read the actionable guidance:
   > 👉 **Correction Guidance:** Update Date of Birth on portal application to strictly match the Class 10 High School Certificate.
4. Review the governing legal reference: *UIDAI & Board of Secondary Education Regulation Clause 7*.

### Step 5: Remediate and Rerun (Screen 6)
1. Navigate to **"6. Document Replacement & Rerun"**.
2. Under **"1. Select Document to Replace"**, select `Marksheet (MARKSHEET)`.
3. Under **"2. Provide Remediated Document"**, select **"Auto-Generate Standard Corrected Version"**.
4. Click **"Generate & Re-Run Audit"**.
5. Observe the notification: *Re-audit completed! Temporary files purged.*
6. Return to **"1. Dashboard"**:
   - Notice the readiness score is now restored to **`100 / 100`**.
   - Determination is now **`🟢 READY TO SUBMIT`**.

### Step 6: Export Privacy-Redacted Report (Screen 5)
1. Navigate to **"5. Audit Results"**.
2. Under **"Export Audit Report"**, click:
   - **"💾 Download Redacted Report (JSON)"** to receive machine-readable audit data with masked snippets and PII.
   - **"📄 Download Redacted Summary (Markdown)"** to receive an applicant-facing readiness summary certificate.
3. Open the downloaded files and verify that citizen PII quotes are masked as `[REDACTED]` and raw snippets are masked as `[REDACTED EVIDENCE SNIPPET]`.

### Step 7: Clear Session Data
1. In the sidebar, click **"🧹 Clear Session Data"**.
2. Verify that all in-memory audit results and extracted document dictionaries are purged.

---

## 6. Known Prototype Limitations & Boundaries

1. **In-Process Parser Sandbox**:
   - PyMuPDF and Tesseract extract text in the main application process.
   - *Security Directive:* This prototype must be demonstrated strictly using synthetic documents. Untrusted citizen PDF uploads should not be processed in production without containerized sandboxing (e.g. gVisor, WebAssembly, or isolated runner workers).
2. **Deterministic Pre-Check Scope**:
   - DocuReady is an applicant-side consistency checker. It does not authenticate Aadhaar biometrics, query external portal APIs, or certify government stamps.
   - A `READY TO SUBMIT` finding indicates document package consistency; it does not guarantee scheme sanction or scholarship disbursement.
3. **OCR Availability**:
   - Clean digital PDFs extract instantly via PyMuPDF vector streams. Degraded scans require local Tesseract installation to parse low-confidence tokens.
