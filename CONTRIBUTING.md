# Contributing to DocuReady

Thank you for your interest in contributing to DocuReady! We welcome contributions from developers, researchers, civic technologists, and legal/policy experts.

---

## Code of Conduct

We are committed to providing a friendly, safe, and welcoming environment for all contributors, regardless of background, identity, or experience level. Please treat everyone with respect and empathy.

---

## How to Contribute

### 1. Reporting Bugs
- Search existing GitHub Issues before opening a new issue.
- Provide a clear, descriptive title.
- Include complete reproduction steps, operating system details, Python version, and relevant log excerpts.
- **NEVER attach real applicant documents or live personal PII.** Use synthetic documents only.

### 2. Suggesting New Statutory Rules
- When proposing a new validation rule, cite the official Government of India Gazette notification, Ministry Scheme Guideline, or State Revenue Department rule.
- Specify:
  - Scheme name and issuing authority.
  - Clause or Section number.
  - Required document types and target fields.
  - Exact condition for violation vs. warning.
  - Actionable remediation advice for the citizen.

### 3. Submitting Code Changes (Pull Requests)
- Fork the repository and create a descriptive branch: `git checkout -b feature/indic-ocr-support` or `fix/pincode-regex`.
- Adhere to PEP 8 styling conventions.
- All new extraction or validation logic must include corresponding pytest unit and integration tests under `tests/`.
- Ensure all tests pass locally:
  ```bash
  python -m pytest tests/ -v
  ```
- Write clear, concise git commit messages.

---

## Development Setup

1. Clone your fork:
   ```bash
   git clone https://github.com/<your-username>/DocuReady.git
   cd DocuReady
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Linux/macOS:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Install local Tesseract binary if testing OCR pipelines:
   - Ubuntu/Debian: `sudo apt-get install tesseract-ocr`
   - macOS: `brew install tesseract`
   - Windows: Install from UB-Mannheim Tesseract installer and ensure `tesseract.exe` is in your `PATH`.
5. Run the test suite:
   ```bash
   pytest tests/ -v
   ```
6. Launch the Streamlit application:
   ```bash
   streamlit run src/ui.py
   ```
