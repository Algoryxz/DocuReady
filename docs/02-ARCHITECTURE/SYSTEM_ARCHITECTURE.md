# DocuReady — System Architecture Specification

## Ownership & Contribution Responsibilities

| Role | Assignee | Primary Scope & Focus |
|---|---|---|
| **Primary Owner** | **Akriti** (Platform, Privacy & Delivery Lead) | Modular decomposition, layer boundaries, component interfaces, packaging & deployment |
| **Supporting Contributor** | **Susmita** (Domain Rules & Evaluation Lead) | Validation engine interfaces, calibrator contracts, decision safety integration |
| **Supporting Contributor** | **Deeptiman** (Product Owner & Integration Lead) | Product contract compliance, user-facing workflow alignment, architectural acceptance |

### Detailed Responsibilities & Deliverables
- **Primary Owner (Akriti)**:
  - Maintain the high-level system architecture, subsystem decoupling, and clean boundary definitions across presentation, orchestration, extraction, validation, and safety layers.
  - Own `pyproject.toml`, packaging layout, CI/CD pipeline, and component dependency constraints.
  - Enforce zero cross-layer leakages (e.g. UI code directly invoking extraction internals without orchestration).
- **Domain Contributor (Susmita)**:
  - Define data transfer objects and interfaces for `ConfidenceCalibrator`, `DocuReadyValidator`, and `DecisionSafetyLayer`.
- **Product Contributor (Deeptiman)**:
  - Review that system architecture supports all defined product workflows and non-functional guarantees.

### Coordination & Review Gates
- Changes to module interfaces or package dependencies require Akriti's technical approval.
- Cross-cutting architectural changes require Deeptiman's acceptance under Architecture V2.
- Governed by [TEAM_RESPONSIBILITIES.md](../TEAM_RESPONSIBILITIES.md).

---

## 1. High-Level Modular Decomposition

DocuReady is organized into distinct, loosely-coupled layers following clean architecture and bounded contexts:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   PRESENTATION & WORKFLOW LAYER                        │
│   Streamlit Web Interface (ui.py)  │  Headless CLI (cli.py)            │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼────────────────────────────────────┐
│                  PIPELINE ORCHESTRATION LAYER                          │
│   AuditPipeline (pipeline.py)  │  ReportExporter (report_exporter.py)  │
└───────┬────────────────────────────────────────────────────────┬───────┘
        │                                                        │
┌───────▼────────────────────────┐      ┌────────────────────────▼───────┐
│     INGESTION & EXTRACTION     │      │     VALIDATION & AUDIT ENGINE  │
│  - DocumentExtractor           │      │  - DocuReadyValidator          │
│  - PyMuPDF Vector Engine       │      │  - SchemeConfig                │
│  - Local Tesseract OCR         │      │  - Deterministic Rule Engine   │
│  - Spatial Y-Clustering        │      │  - Normalizer (normalizer.py)  │
└───────┬────────────────────────┘      └────────────────────────┬───────┘
        │                                                        │
        ▼                                                        ▲
┌────────────────────────────────────────────────────────┐       │
│             CONFIDENCE CALIBRATION ENGINE              │       │
│  ConfidenceCalibrator (calibrator.py)                  │       │
│  - Syntactic Format Validation                         │       │
│  - Label Proximity & Candidate Multiplicity Scoring    │       │
│  - 7-State Evidence Lifecycle Assignment               │       │
└────────────────────────────────────────────────────────┴───────┘
                                                                 │
                                ┌────────────────────────────────┴───────┐
                                │        DECISION SAFETY FIREWALL        │
                                │   DecisionSafetyLayer (safety_layer.py)│
                                │   - Statutory Legal Verification       │
                                │   - Dual-Document Provenance Guarantee │
                                │   - Uncertainty Downgrade Firewall     │
                                └────────────────────────────────────────┘
```

---

## 2. Core Subsystems

### A. Presentation & Ingestion Layer
- **`src/ui.py`**: A 6-screen Streamlit application designed for applicants and CSC operators. Handles document packet uploads, live bounding box previews, relational consistency tables, readiness scores, and instant re-audit.
- **`src/cli.py`**: A lightweight CLI interface for headless batch processing in server environments or CI/CD pipelines.

### B. Ingestion & Extraction Engine (`src/extractor.py`)
- **Dual Extraction Modality**:
  1. *Native Vector Path*: Fast stream parsing via PyMuPDF (`fitz`), executing in ~4.4 ms per page with zero rendering overhead.
  2. *Local OCR Raster Path*: 200 DPI rendering via PyMuPDF, auto-orientation detection via Tesseract OSD, character recognition via Tesseract LSTM neural network, and spatial 12-pt Y-clustering.

### C. Field Calibration Engine (`src/calibrator.py`)
- Evaluates raw OCR tokens against semantic label coordinates, syntactic regular expressions, and candidate multiplicity.
- Assigns one of 7 discrete `EvidenceState` values and computes a calibrated correctness probability $\hat{p} \in [0.05, 0.99]$.

### D. Normalization Subsystem (`src/normalizer.py`)
- Pure, deterministic transformation functions:
  - Personal name tokenization, honorific removal, initials expansion, and permutation-invariant matching.
  - Date normalization to ISO-8601 strings and ambiguity detection.
  - Monetary expression parsing (INR float).
  - Verhoeff check-digit verification for Aadhaar identifiers.
  - RBI IFSC structural format enforcement.

### E. Validation Engine (`src/validator.py`)
- Implements scheme-specific configurations (`SchemeConfig`) including income ceiling limits, domicile state mandates, academic percentage cutoffs, and certificate validity windows.
- Emits structured `Finding` objects categorized as `PASS`, `REVIEW`, `FAIL`, or `UNKNOWN`.

### F. Decision Safety Firewall (`src/safety_layer.py`)
- Independent safety interception layer that inspects all findings before applicant presentation.
- Guarantees zero false statutory rejections on unconfirmed, ambiguous, or low-confidence evidence.
