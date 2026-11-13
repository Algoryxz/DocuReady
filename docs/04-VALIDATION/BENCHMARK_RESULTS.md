# DocuReady MVP — Benchmark Results & Evaluation Methodology

**Evaluation Date:** 2026-11-13  
**Hardware Environment:** Intel Core i7 / Windows 11 (64-bit)  
**Execution Runtime:** Python 3.12.10 (Offline, Single-threaded CPU)  
**Test Suite:** 8 Multi-Document Synthetic Applicant Packets (47 Total PDF Files)

---

## 1. Summary Performance Metrics

| Metric | Measured Value | Methodology / Notes |
|---|---|---|
| **Dataset Size** | 8 Packets (47 PDFs) | Synthetic PDF documents generated via ReportLab |
| **Prediction Accuracy** | **100.0% (8 / 8)** | Packet overall determination vs `ground_truth_manifest.json` |
| **Rule Precision** | **100.0%** | Zero false-positive statutory rule violations on clean packet |
| **Rule Recall** | **100.0%** | Detected all planted defects across 7 defective packets |
| **Mean Ingestion & Audit Latency** | **46.47 ms** | Complete pipeline: PyMuPDF file read + field extract + audit |
| **Min Audit Latency** | **35.49 ms** | 5-document packet (`PKT_05_MISSING_CERTIFICATE`) |
| **Max Audit Latency** | **63.96 ms** | 6-document clean packet (`PKT_01_CLEAN`) |
| **Memory Footprint** | **< 3.2 MB** | In-memory document models and PyMuPDF document handles |
| **Network Requests** | **0 (Zero)** | 100% offline, air-gapped deterministic computation |

---

## 2. Per-Packet Benchmark Breakdown

Results measured from direct CLI benchmark execution (`python docuready-mvp/src/cli.py benchmark`):

| Packet ID | Documents Ingested | Ground Truth Status | Predicted Status | Predicted Score | Execution Latency | Verdict |
|---|---|---|---|---|---|---|
| `PKT_01_CLEAN` | 6 PDFs | `READY_TO_SUBMIT` | `READY_TO_SUBMIT` | 100 / 100 | 63.96 ms | **MATCH** |
| `PKT_02_NAME_CONFLICT` | 6 PDFs | `ACTION_REQUIRED` | `ACTION_REQUIRED` | 75 / 100 | 46.73 ms | **MATCH** |
| `PKT_03_DOB_CONFLICT` | 6 PDFs | `ACTION_REQUIRED` | `ACTION_REQUIRED` | 75 / 100 | 43.60 ms | **MATCH** |
| `PKT_04_INCOME_CONFLICT` | 6 PDFs | `REJECT_PRECHECK` | `REJECT_PRECHECK` | 40 / 100 | 49.79 ms | **MATCH** |
| `PKT_05_MISSING_CERTIFICATE`| 5 PDFs | `REJECT_PRECHECK` | `REJECT_PRECHECK` | 65 / 100 | 35.49 ms | **MATCH** |
| `PKT_06_MULTIPLE_DEFECTS` | 6 PDFs | `ACTION_REQUIRED` | `ACTION_REQUIRED` | 0 / 100 | 50.00 ms | **MATCH** |
| `PKT_07_UNREADABLE_DOC` | 6 PDFs | `UNREADABLE_PACKET` | `UNREADABLE_PACKET` | 75 / 100 | 37.64 ms | **MATCH** |
| `PKT_08_AMBIGUOUS_EVIDENCE`| 6 PDFs | `REVIEW_RECOMMENDED`| `REVIEW_RECOMMENDED`| 85 / 100 | 44.59 ms | **MATCH** |

---

## 3. Automated Test Suite Metrics

Ran 19 tests across normalizers, PyMuPDF extractor, statutory rules, ground truth, and document replacement rerun:

```
============================= test session starts =============================
platform win32 -- Python 3.12.10, pytest-8.3.3, pluggy-1.6.0
collected 19 items

docuready-mvp/tests/test_dataset_ground_truth.py::test_packet_against_ground_truth[PKT_01_CLEAN] PASSED
docuready-mvp/tests/test_dataset_ground_truth.py::test_packet_against_ground_truth[PKT_02_NAME_CONFLICT] PASSED
docuready-mvp/tests/test_dataset_ground_truth.py::test_packet_against_ground_truth[PKT_03_DOB_CONFLICT] PASSED
docuready-mvp/tests/test_dataset_ground_truth.py::test_packet_against_ground_truth[PKT_04_INCOME_CONFLICT] PASSED
docuready-mvp/tests/test_dataset_ground_truth.py::test_packet_against_ground_truth[PKT_05_MISSING_CERTIFICATE] PASSED
docuready-mvp/tests/test_dataset_ground_truth.py::test_packet_against_ground_truth[PKT_06_MULTIPLE_DEFECTS] PASSED
docuready-mvp/tests/test_dataset_ground_truth.py::test_packet_against_ground_truth[PKT_07_UNREADABLE_DOC] PASSED
docuready-mvp/tests/test_dataset_ground_truth.py::test_packet_against_ground_truth[PKT_08_AMBIGUOUS_EVIDENCE] PASSED
docuready-mvp/tests/test_extractor.py::test_extractor_income_cert PASSED
docuready-mvp/tests/test_extractor.py::test_extractor_unreadable_file PASSED
docuready-mvp/tests/test_extractor.py::test_extractor_missing_file PASSED
docuready-mvp/tests/test_normalizer.py::test_verhoeff_checksum PASSED
docuready-mvp/tests/test_normalizer.py::test_name_normalization_and_comparison PASSED
docuready-mvp/tests/test_normalizer.py::test_date_parsing_and_ambiguity PASSED
docuready-mvp/tests/test_normalizer.py::test_income_normalization PASSED
docuready-mvp/tests/test_normalizer.py::test_ifsc_code_validation PASSED
docuready-mvp/tests/test_replacement_rerun.py::test_document_replacement_workflow PASSED
docuready-mvp/tests/test_validator.py::test_validator_mandatory_document_missing PASSED
docuready-mvp/tests/test_validator.py::test_validator_income_ceiling_breach PASSED

============================= 19 passed in 0.75s ==============================
```

---

## 4. Reproducible Verification Commands

To reproduce these benchmark numbers independently:

```powershell
$env:PYTHONPATH="docuready-mvp"
python docuready-mvp/src/cli.py benchmark
pytest docuready-mvp/tests/ -v
```
