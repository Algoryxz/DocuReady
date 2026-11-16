<div align="center">
  <img src="assets/branding/docuready-logo.png" alt="DocuReady Logo" width="128" height="128" />
  <h1>DocuReady</h1>
  <p><strong>Deterministic, privacy-preserving pre-flight readiness audit for government scholarship and citizen welfare applications.</strong></p>
</div>

[![CI Tests](https://github.com/Algoryxz/DocuReady/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/Algoryxz/DocuReady/actions/workflows/tests.yml)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python: 3.11–3.14](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-0A2540.svg)](pyproject.toml)
[![Privacy: Local Verified](https://img.shields.io/badge/Privacy-Local%20Execution%20%7C%20No%20Telemetry%20(Verified)-0A2540.svg)](docs/02-ARCHITECTURE/SECURITY_AND_PRIVACY.md)

---

## About DocuReady

**DocuReady** is a local-first, deterministic applicant-side document-preparation aid for scholarship and public-benefit applications. It checks consistency across a supplied document packet, surfaces missing or hard-to-read evidence, preserves traceability to the source document, and gives applicants practical next steps before they use an official portal.

DocuReady is **not** an eligibility decision-maker, government service, legal authority, identity-authentication service, or guarantee of application approval. A “no issues found” result means only that the configured checks passed on the evidence supplied; applicants must still follow the relevant official scheme and portal instructions.

**Public project website:** [docu-ready-lurkae.vercel.app](https://docu-ready-lurkae.vercel.app)  
The Vercel website is an informational product page only. It does not accept document uploads or run the audit engine. The Python/Streamlit audit application is run locally, keeping document processing on the machine where the application is running.

```mermaid
flowchart LR
    Applicant["Applicant / CSC Operator"] --> Upload["Ingest Document Packet<br/>(PDF / Scans)"]
    Upload --> Ingest["Dual Ingestion Engine<br/>PyMuPDF Vector + Tesseract OCR"]
    Ingest --> Provenance["Field Extraction &<br/>Bounding Box Provenance"]
    Provenance --> Calibrator["9-Feature Logistic<br/>Confidence Calibrator"]
    Calibrator --> TriState["Tri-State Classification<br/>VERIFIED / PROVISIONAL / UNCERTAIN"]
    TriState --> Rules["Document Consistency &<br/>Scheme Rules Engine<br/>10 Cross-Document Checks"]
    Rules --> Safety["Evidence Safety Layer<br/>Downgrades Unproven Violations"]
    Safety --> AuditReport["Actionable Audit Report<br/>Remediation + Redacted Export"]
```

---

## The Problem

Across government welfare and educational scholarship portals, applicants frequently encounter delays or returned applications due to simple clerical discrepancies:

- **Demographic Inconsistencies:** Spelling variations between certificates (e.g., initials vs. expanded names, honorifics, or transliteration divergence).
- **Date of Birth Mismatches:** Discrepancies between matriculation marksheets, Aadhaar, and portal declarations, compounded by format ambiguities (`DD/MM/YYYY` vs. `MM/DD/YYYY`).
- **Expired Certificates:** Revenue or Income Certificates submitted past their validity window (validity periods vary by state revenue authority; 1 financial year is a common operational heuristic, not a uniform national statutory mandate).
- **Income Ceiling Violations:** Income exceeding scheme-specific statutory thresholds (e.g., ₹2,50,000 for centrally sponsored post-matric scholarships).
- **Unreadable Scans & Degraded Quality:** Low-resolution, skewed, or blurred scans of bank passbooks and caste certificates preventing Direct Benefit Transfer (DBT) verification.

Because scrutiny occurs weeks or months after submission, **application windows are often closed by the time an applicant receives a rejection notice**, forfeiting critical educational funding.

---

## Key Capabilities

- **Deterministic & Explainable:** Employs explicit rule engines and deterministic normalizers rather than stochastic LLMs in the core audit path. Every finding references a specific rule clause, guideline, or format specification.
- **Local Execution & Privacy-Preserving Architecture:** Designed for offline operation on standard hardware without requiring outbound telemetry. Sensitive document data remains within the local execution environment.
- **Calibrated Evidence Safety Layer:** Employs a 9-feature logistic calibration engine. Low-quality or degraded OCR text is classified as `UNCERTAIN` and safely downgraded to `MANUAL REVIEW` rather than issuing an unjustified rejection.
- **Visual Bounding Box Provenance:** Every extracted value retains exact physical page number and bounding box coordinates (`[x0, y0, x1, y1]`), allowing instant visual inspection of the underlying PDF.
- **Actionable Remediation Guidance:** Rather than emitting cryptic error codes, DocuReady provides step-by-step instructions: which issuing authority to approach, what replacement document is required, and how to rectify the issue.
- **Interactive Single-Document Replacement:** Replace an individual defective document and re-audit the entire packet in-memory in under 1 second.
- **Deterministic Field Normalizers:** Includes Verhoeff checksum validation for Aadhaar, Indian calendar date parsing with ambiguity detection, Indian numbering system currency parsing (lakhs/crores), and RBI IFSC bank routing verification.

---

## Visual Walkthrough

### 1. Unified Audit Dashboard
View packet status, submission readiness score, and overall compliance metrics at a glance.
![Dashboard](screenshots/loop_1/01_dashboard.png)

### 2. Multi-Document Packet Ingestion
Inspect and process Income, Caste, Residence, Marksheet, and Passbook certificates simultaneously.
![Upload Documents](screenshots/loop_1/02_upload_documents.png)

### 3. Visual Bounding Box Evidence Provenance
Every extracted fact is visually anchored to its physical coordinate bounding box on the PDF.
![Extraction Evidence](screenshots/loop_1/03_extraction_evidence.png)

### 4. Cross-Document Discrepancy Detection
Instant cross-verification of demographic details, dates, income limits, and validity dates.
![Cross-Document Validation](screenshots/loop_1/04_cross_document_validation.png)

### 5. Calibrated Tri-State Evidence & Safety Downgrades
OCR degradations are categorized into `VERIFIED`, `PROVISIONAL`, or `UNCERTAIN`, preventing false rejections.
![Calibrated Confidence](screenshots/loop_3/02_calibrated_confidence.png)
![Safety Downgrades](screenshots/loop_3/03_safety_downgrades.png)

### 6. Interactive Document Remediation
Upload an updated certificate and observe the defect clear in real time without restarting the audit.
![Document Remediation](screenshots/loop_3/04_remediation.png)

---

## Document Consistency & Scheme Requirement Rules Engine

DocuReady evaluates document packets against 10 explicit cross-document checks (with verified statutory citations where available; see [Citation Audit](docs/CITATION_AUDIT.md) for full statutory basis and heuristic classifications):

| Rule ID | Rule Name | Governing Authority / Source Basis | Default Severity |
| :--- | :--- | :--- | :--- |
| **RULE-NAME-01** | Cross-Document Name Consistency | MeitY Demographic Verification Standards 2023 & MoSJE Guidelines Section 4.2 | `CRITICAL` |
| **RULE-DOB-01** | Date of Birth Consistency | Secondary Education Examination Board Rule 8 & UIDAI Verification Norms | `CRITICAL` |
| **RULE-INC-01** | Statutory Income Ceiling | Centrally Sponsored Post-Matric Scholarship Scheme Guideline 3.1 | `CRITICAL` |
| **RULE-INC-02** | Declared vs. Certified Income | State Scholarship Portal Compliance Guidelines Clause 5.1 | `CRITICAL` |
| **RULE-EXP-01** | Certificate Validity Period | Common State Revenue Heuristic (1 Financial Year; varies by state authority) | `CRITICAL` |
| **RULE-CST-01** | Caste Category Consistency | Constitution (Scheduled Castes/Scheduled Tribes) Orders & Scheme Clause 4 | `CRITICAL` |
| **RULE-DOM-01** | State Domicile Requirement | State Scholarship Rules Clause 2(a) | `CRITICAL` |
| **RULE-DOC-01** | Mandatory Document Checklist | Scheme Mandatory Application Checklist Clause 2.1 | `CRITICAL` |
| **RULE-DOC-02** | Document Legibility & Scan Quality | NSP Upload Guidelines & Information Technology Act 2000 Section 6A | `CRITICAL` |
| **RULE-MRK-01** | Academic Eligibility Cutoff | Scheme Educational Criteria Notification (SC/ST Applicants Exempt) | `CRITICAL` |

---

## Calibration & Safety Layer

To protect citizens from unfair rejections caused by imperfect scans, low-light cameras, or worn paper:

1. **9-Feature Logistic Calibrator:** Evaluates OCR confidence, token length, anchor label proximity, candidate ambiguity, character entropy, format regex compliance, layout positioning, extraction mode, and image skew angle.
2. **Tri-State Classification:**
   - **`VERIFIED` ($P \ge 0.85$):** High certainty; eligible for standard statutory rule evaluation.
   - **`PROVISIONAL` ($0.60 \le P < 0.85$):** Moderate certainty; emits actionable warnings rather than blocking rejections.
   - **`UNCERTAIN` ($P < 0.60$):** Insufficient evidence; violations are **automatically downgraded to `MANUAL REVIEW` / `UNKNOWN`**.

### Safety Downgrade Matrix

| Raw Rule Outcome | Evidence States of Supporting Fields | Final Finding Severity | Citizen Impact |
| :--- | :--- | :--- | :--- |
| **VIOLATION** | All `VERIFIED` | **CRITICAL / VIOLATION** | Action required prior to submission |
| **VIOLATION** | $\ge 1$ `PROVISIONAL`, $0$ `UNCERTAIN` | **WARNING** | Flagged for scan re-check; not rejected |
| **VIOLATION** | $\ge 1$ `UNCERTAIN` | **NEEDS REVIEW / UNKNOWN** | Downgraded to manual verification |
| **COMPLIANT** | Any | **PASS** | Validated |

---

## Architecture & Repository Structure

DocuReady is organized as a modular Python package following domain-driven design:

```text
DocuReady/
├── pyproject.toml                      # Standard PEP 517/518 build configuration
├── LICENSE                             # Apache 2.0 Open Source License
├── README.md                           # Repository documentation
├── assets/                             # Repository branding assets
│   └── branding/                       # DocuReady visual identity (logo)
├── requirements/                       # Hash-checked reproducible lockfiles
│   ├── README.md                       # Lock maintenance guide
│   ├── ci-lock-py3.11.txt              # Linux x86_64 lockfile for Python 3.11
│   ├── ci-lock-py3.12.txt              # Linux x86_64 lockfile for Python 3.12
│   ├── ci-lock-py3.13.txt              # Linux x86_64 lockfile for Python 3.13
│   └── ci-lock-py3.14.txt              # Linux x86_64 lockfile for Python 3.14
│
├── src/
│   └── docuready/                      # Core package namespace
│       ├── domain/                     # Typed domain entities, enums & models
│       │   └── models.py               # FieldEvidence, AuditResult, Finding, DocumentType
│       ├── ingest/                     # PDF ingestion & OCR extraction
│       │   └── extractor.py            # PyMuPDF vector extractor + Tesseract fallback
│       ├── evidence/                   # Calibration engine
│       │   └── calibrator.py           # 9-feature logistic confidence calibrator
│       ├── normalize/                  # Deterministic normalization utilities
│       │   └── normalizer.py           # Verhoeff, Indian date, currency, IFSC normalizers
│       ├── outcome/                    # Evidence safety firewall
│       │   └── safety_layer.py         # Guardrail downgrading unproven rejections
│       ├── rules/                      # Statutory cross-document rules
│       │   └── validator.py            # 10 statutory scholarship rules
│       ├── pipeline.py                 # Unified end-to-end audit orchestrator
│       ├── generator.py                # Synthetic document packet generator (ReportLab)
│       ├── report/                     # Privacy-preserving report exporters
│       │   └── exporter.py             # Redacted JSON & Markdown exporter
│       └── interfaces/                 # User-facing entry points
│           ├── cli.py                  # "docuready" console CLI tool
│           └── ui/                     # Interactive Streamlit interface
│               └── app.py              # Streamlit dashboard implementation
│
├── tests/                              # Comprehensive test suite (423 test items)
│   ├── contract/                       # Claims register & zero-network contract tests
│   ├── integration/                    # Validator-level per-rule fixture matrix (53 tests)
│   ├── unit/                           # Outcome resolver per-rule truth table (105 tests)
│   ├── test_adversarial.py             # Adversarial edge cases & malformed files
│   ├── test_date_invariance_safety.py  # Two-candidate date invariance safety tests
│   ├── test_dataset_ground_truth.py    # Ground truth validation across synthetic packets
│   ├── test_decision_safety.py         # Evidence safety firewall downgrade tests
│   ├── test_evidence_calibration.py    # 9-feature logistic calibrator tests
│   ├── test_extractor.py               # Vector extraction & OCR fallback tests
│   ├── test_golden_baseline.py         # Bit-for-bit regression suite with diagnostic diffs
│   ├── test_match_grades_clock.py      # Match grades and injected clock tests (19 tests)
│   ├── test_normalizer.py              # Verhoeff, date, income & IFSC unit tests
│   ├── test_replacement_rerun.py       # Single-document remediation workflow tests
│   ├── test_safety_layer.py            # Safety downgrade matrix tests
│   ├── test_slot_validation.py         # Scheme-aware document slot validation tests (29 tests)
│   ├── test_ui_privacy.py              # Zero-telemetry, asset isolation & PII masking
│   ├── test_uncertainty_safety.py      # Scan quality & uncertainty handling tests
│   └── test_validator.py               # Statutory rule violation & exemption tests
│
├── synthetic_data/                     # Synthetic test packets (no real citizen PII)
│   ├── ground_truth_manifest.json      # Dataset metadata & expected audit findings
│   ├── pkt_01_clean/                   # Baseline 100% compliant packet
│   ├── pkt_02_name_conflict/           # Marksheet applicant name mismatch
│   ├── pkt_03_dob_conflict/            # Date of birth discrepancy
│   ├── pkt_04_income_conflict/         # Declared income vs. certified income conflict
│   ├── pkt_05_missing_certificate/     # Missing mandatory certificate packet
│   ├── pkt_06_multiple_defects/        # Multi-defect composite challenge packet
│   ├── pkt_07_unreadable_doc/          # Degraded scan triggering OCR fallback
│   └── pkt_08_ambiguous_evidence/      # Date ambiguity & initial variation packet
│
├── docs/                               # Engineering documentation & decision records
│   ├── START_HERE.md                   # Onboarding & architecture overview
│   ├── ARCHITECTURE_V2.md              # Target modular architecture specification
│   ├── BACKLOG.md                      # Project workstreams and delivery gate register
│   ├── STATUS.md                       # Task delivery tracking status
│   └── history/                        # Gate decision records & baseline characterization
│
└── screenshots/                        # Visual UI verification assets
    ├── loop_1/                         # Dashboard & baseline workflow screenshots
    ├── loop_2/                         # Real-world degraded scan handling screenshots
    └── loop_3/                         # Confidence calibration & remediation screenshots
```

---

## Installation & Setup

### Prerequisites

- **Python:** `3.11`, `3.12`, `3.13`, or `3.14` (CPython 64-bit).
- **Tesseract OCR:** Required for scanning raster image PDFs.
  - **Ubuntu / Debian:**
    ```bash
    sudo apt-get update && sudo apt-get install -y tesseract-ocr tesseract-ocr-eng libtesseract-dev
    ```
  - **macOS (Homebrew):**
    ```bash
    brew install tesseract
    ```
  - **Windows:** Install via [UB-Mannheim Tesseract](https://github.com/UB-Mannheim/tesseract/wiki) and ensure `tesseract.exe` is added to your system `PATH`.

### 1. Clone & Create Environment

```bash
git clone https://github.com/Algoryxz/DocuReady.git
cd DocuReady

# Create and activate virtual environment
python -m venv .venv

# On Linux / macOS:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate
```

### 2. Install Package

**Option A: Editable Development Installation**
```bash
# Core package only:
pip install -e .

# Full installation including UI, generator, and test dependencies:
pip install -e ".[all]"
```

**Option B: Reproducible Hash-Checked Installation (Linux x86_64)**
```bash
# Install matching pinned lockfile (e.g. for Python 3.12):
pip install --require-hashes -r requirements/ci-lock-py3.12.txt
pip install --no-deps -e .
```

---

## Usage

### 1. Interactive Web Interface

Launch the local Streamlit dashboard:

```bash
streamlit run src/docuready/interfaces/ui/app.py
```

Open `http://localhost:8501` in your browser. You can select preloaded synthetic test packets (`pkt_01_clean` through `pkt_08_ambiguous_evidence`) or upload local PDF documents to inspect bounding box extractions, cross-document verification matrices, and live document remediation.

### 2. Command-Line Interface (CLI)

DocuReady registers the `docuready` console command:

```bash
# Audit a single document packet folder (human-readable markdown output)
docuready audit synthetic_data/pkt_01_clean

# Audit a packet and output JSON
docuready audit synthetic_data/pkt_02_name_conflict --json

# Audit and export report to a file
docuready audit synthetic_data/pkt_04_income_conflict --export audit_report.md

# Run automated benchmark evaluation across all synthetic packets
docuready benchmark
```

### 3. Python API

```python
from docuready.pipeline import AuditPipeline

pipeline = AuditPipeline()
result, extracted_docs = pipeline.load_and_audit_packet("synthetic_data/pkt_01_clean")

print(f"Overall Status: {result.overall_status}")
print(f"Readiness Score: {result.readiness_score}/100")

for finding in result.findings:
    print(f"[{finding.status}] {finding.rule_id} ({finding.severity}): {finding.message}")
    if finding.remediation:
        print(f"  👉 Remediation: {finding.remediation}")
```

---

## Testing & Quality Assurance

DocuReady maintains a comprehensive automated test suite enforcing 100% bit-for-bit vector parity and adversarial robustness:

```bash
# Run full test suite (423 test items)
pytest tests/ -v --tb=short

# Run with test coverage report
pytest --cov=docuready --cov-report=term-missing
```

### Test Suite Structure

| Test Category | Test File | Scope |
| :--- | :--- | :--- |
| **Contract Invariants** | `tests/contract/` | Zero network egress (`test_no_network.py`) & claims anti-overreach (`test_claims.py`). |
| **Validator Integration Matrix** | `tests/integration/test_validator_rule_matrix.py` | End-to-end validator execution across all 10 canonical rule groups with fixture packets. |
| **Resolver Outcome Matrix** | `tests/unit/test_rules_matrix.py` | Section 6 truth-table transitions, match-grade caps, exemptions, and packet readiness. |
| **Match Grades & Injected Clock** | `tests/test_match_grades_clock.py` | Explicit match grades (initials, reorder, diacritics), injected `as_of` clock, 0 prohibited clock calls, and replay invariance. |
| **Document Slot Validation** | `tests/test_slot_validation.py` | Scheme-aware document slot verification, anchor-keyword matching, and fail-closed reviews. |
| **Date Invariance Safety** | `tests/test_date_invariance_safety.py` | Native vector candidate invariance, OCR ambiguity exclusion, and boundary evaluation. |
| **Adversarial Robustness** | `tests/test_adversarial.py` | Empty PDFs, multi-page layout shifts, duplicate uploads, extreme values, name variations. |
| **Ground Truth Evaluation** | `tests/test_dataset_ground_truth.py` | End-to-end verification against `synthetic_data/ground_truth_manifest.json`. |
| **Decision Safety Firewall** | `tests/test_decision_safety.py` | Provenance enforcement and safety downgrade validation. |
| **Confidence Calibration** | `tests/test_evidence_calibration.py` | 9-feature logistic regression scoring and threshold testing. |
| **Vector & OCR Ingestion** | `tests/test_extractor.py` | PyMuPDF vector bounding boxes and Tesseract fallback routines. |
| **Golden Regression Baseline** | `tests/test_golden_baseline.py` | Exact bit-for-bit parity across historical frozen snapshots with path canonicalization. |
| **Deterministic Normalizers** | `tests/test_normalizer.py` | Verhoeff checksum algorithm, Indian date ambiguity, income and IFSC parsing. |
| **Document Remediation** | `tests/test_replacement_rerun.py` | In-memory single-document replacement and re-audit validation. |
| **UI Privacy & Isolation** | `tests/test_ui_privacy.py` | Zero remote assets, PII masking in exports, and temporary directory cleanup. |

---

## Security, Privacy & Data Protection

DocuReady is architected around privacy-by-design principles informed by data protection frameworks such as India's **Digital Personal Data Protection (DPDP) Act 2023**:

1. **Zero External Telemetry:** Core audit pipeline makes zero outbound network requests. No user documents, metadata, analytics, or telemetry are transmitted.
2. **Ephemeral File Lifecycles:** When files are uploaded via the reference Streamlit interface, they are processed in volatile temporary memory directories and cleaned up upon session completion.
3. **PII Masking in Export Reports:** Exported JSON and Markdown reports automatically redact sensitive citizen identification (e.g. masking Aadhaar numbers to show only the last 4 digits: `XXXX-XXXX-1234`).
4. **Offline Demographic Linter:** DocuReady functions solely as an offline demographic pre-submission linter. It does not store user data in persistent databases or connect to live government backend systems.

---

## Verified Benchmarks

Evaluation performed on reference hardware (Intel Core i7-12700H, 16 GB RAM, Ubuntu 24.04 LTS) against the synthetic validation suite:

| Benchmark Suite | Total Samples | Exact Match Accuracy | Mean Latency per Packet | Execution Pipeline |
| :--- | :--- | :--- | :--- | :--- |
| **Standard 8 Synthetic Packets** | 48 Documents | 100.0% | 0.38s | Native Vector Extraction |
| **Degraded Physical Scans** | 60 Documents | 91.7% | 1.15s | Vector + Local Tesseract OCR |
| **Held-Out Evaluation Suite** | 100 Documents | 93.0% | 1.12s | Vector + Local Tesseract OCR |

*Note: Benchmarks reflect performance on synthetic test datasets under controlled test conditions and do not represent field portal acceptance guarantees.*

---

## Known Boundaries & Limitations

> [!IMPORTANT]
> **Advisory Disclaimer:** DocuReady is an assistive, pre-submission demographic verification tool, not an official government portal. It does not provide legal advice, official statutory certification, or guarantee government scheme acceptance or benefit disbursement.

- **Pre-Submission Advisory Only:** DocuReady is an offline demographic consistency and document readiness linter. It is **NOT** an official government portal, legal authority, or Aadhaar authentication service. A successful pre-check does not guarantee scheme approval or benefit disbursement.
- **Provisional PDF Engine:** DocuReady currently pins `pymupdf==2.1` to maintain geometric coordinate reproducibility. A formal licensing evaluation (AGPLv3) and review of permissive alternative backends is scheduled under Task T1.3 / ADR-001.
- **Language Support:** Current baseline models support English (`eng`). Multi-lingual OCR language pack extensions for Odia (`ori`) and Hindi (`hin`) are in active development (Task T0.2).

---

## Documentation Index

- **[Start Here / Developer Guide](docs/START_HERE.md):** Onboarding guide and development overview.
- **[Architecture V2 Specification](docs/ARCHITECTURE_V2.md):** Comprehensive technical architecture and subsystem boundaries.
- **[Architecture Review & Roadmap](docs/ARCHITECTURE_REVIEW.md):** Deep architectural critique and risk register.
- **[Public Claims Register](docs/CLAIMS_REGISTER.md):** Governance audit matrix of public-facing claims and technical boundaries.
- **[Statutory Citation Audit](docs/CITATION_AUDIT.md):** Statutory citations, legal bases, and heuristic rule classifications.
- **[Delivery Backlog](docs/BACKLOG.md):** Active tasks, gate criteria (G0–G6), and workstream ownership.
- **[Baseline Decision Record](docs/history/G0_BASELINE_DECISION.md):** Gate G0 decision record covering Python runtime lifecycles and PDF baselines.
- **[Security & Privacy Specification](docs/02-ARCHITECTURE/SECURITY_AND_PRIVACY.md):** DPDP compliance, PII masking, and offline boundary specifications.

---

## License & Attribution

This project is licensed under the **Apache License 2.0**. See the [LICENSE](LICENSE) file for complete terms and conditions.

Copyright 2026 HackNation DocuReady Authors (Algoryxz).
