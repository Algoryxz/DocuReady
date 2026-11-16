# DOCUREADY — AUDITED CLAIMS & EVIDENCE REGISTER

**Event:** HackNation 2026  
**Document:** `presentation/research/CLAIMS_AND_EVIDENCE.md`  
**Purpose:** Forensic verification of every quantitative metric, performance claim, and technical statement proposed for presentation.

---

## 1. Audited Quantitative Presentation Metrics

| # | Presentation Claim | Metric Value | Original Source File | Test Script / Benchmark | Dataset Size & Nature | Test Environment | Validation Type |
| :-: | :--- | :---: | :--- | :--- | :--- | :--- | :--- |
| **1** | **Audit Speed** | **60.63 ms** | `docs/benchmark_results.json` | `tests/benchmark_loop4_performance.py` | 2-document vector packet (Application + Income) | Windows 11 x64, 16 Cores, NVMe SSD | Synthetic Benchmark |
| **2** | **Memory Consumption** | **191.39 MB Peak RSS** | `docs/LOOP_4_PERFORMANCE_RESULTS.md` | `tests/benchmark_loop4_performance.py` | 20 documents with multi-page OCR rasterization | Windows 11 x64, 16 GB RAM | Synthetic Stress Benchmark |
| **3** | **Defect Detection Precision** | **100.0%** | `docs/accuracy_audit_results.json` | `tests/audit_validation_corpus_accuracy.py` | 16 synthetic validation documents across 5 workflows | Ground Truth: 2 TP, 0 FP, 18 TN, 0 FN | Automated Ground Truth Test |
| **4** | **Defect Detection Recall** | **100.0%** | `docs/accuracy_audit_results.json` | `tests/audit_validation_corpus_accuracy.py` | 16 synthetic validation documents across 5 workflows | Ground Truth: 2 TP, 0 FP, 18 TN, 0 FN | Automated Ground Truth Test |
| **5** | **Field Value Extraction Accuracy** | **100.0%** (28/28 fields) | `docs/independent_validation_results.json` | `tests/independent_validation_runner.py` | 11 representative documents, 28 fields checked | External Human Auditor Ground Truth Oracle | **Independently Validated** |
| **6** | **Consecutive Demonstration Cycles** | **10/10 Passed (100.0%)** | `docs/demo_reliability_results.json` | `tests/test_demo_reliability_10_cycles.py` | 10 full cycles (boot, import, audit, export, cleanup) | Mean duration: 1,547.32 ms | Automated Reliability Test |
| **7** | **Ephemeral Directory Cleanup Latency**| **5.32 ms** | `docs/demo_reliability_results.json` | `tests/test_demo_reliability_10_cycles.py` | 10 cycle directory deletions | Sub-directory under `%TEMP%` | Automated Benchmark |
| **8** | **Automated Python Tests Passed** | **450 / 452 (0 failed)** | Pytest execution log (`task-1742`) | `python -m pytest tests/` | 452 collected tests across 28 test modules | Windows 11, Python 3.12.10 | Automated Test Suite |
| **9** | **Desktop TypeScript Tests Passed** | **21 / 21 (0 failed)** | Desktop test log (`task-1726`) | `npm --prefix apps/desktop test` | 21 end-to-end and unit tests | Node.js v24, Electron 45.3.2 | Automated Test Suite |
| **10**| **Outbound Network Telemetry** | **0 Requests (100% Offline)**| `apps/desktop/src/main/index.ts` | `apps/desktop/tests/security.test.ts` | Complete desktop application runtime | CSP `connect-src 'none'` | Architecture & Security Test |
| **11**| **Golden Baseline Preservation** | **Bit-for-Bit Identical** | `tests/golden/legacy_v0/GOLDEN_BASELINE_HASHES.txt` | `scripts/verify_loop4_evidence.py` | 47 golden synthetic PDFs and JSON baseline | SHA-256: `e8fb1a6b842a...` | Cryptographic Checksum |

---

## 2. Audited Qualitative Capabilities & Features

| Capability Statement | Technical Implementation Location | Verification Evidence | Status |
| :--- | :--- | :--- | :---: |
| **Multi-document cross-checking** | `src/docuready/rules/validator.py` | Cross-checks names, DOBs, incomes, and categories across 6 certificates simultaneously. | **Verified in Code** |
| **Physical PDF Bounding Box Highlighting** | `apps/desktop/src/renderer/components/PdfViewer.tsx` | Visual bounding boxes drawn directly on rendered PDF.js canvas. | **Verified in UI** |
| **Rotation-Aware Coordinate Algebra** | `apps/desktop/src/renderer/utils/bbox.ts` | Matrix transforms map 72-DPI points across 90°, 180°, and 270° orientations without drift. | **Verified in Math Unit Test** |
| **Zero-PII Diagnostic Exports** | `apps/desktop/src/main/ipc.ts` | Diagnostic reports strictly omit applicant names, certificate IDs, and bank accounts. | **Verified in Security Test** |
| **Process Crash Resilience** | `apps/desktop/src/main/sidecar.ts` | Auto-recovers from abrupt child process crashes without crashing Electron main. | **Verified in Crash Test** |
| **Hostile Input Perimeter Trapping** | `src/docuready/ingest/extractor.py` | 0-byte, corrupted header, and encrypted PDFs safely trapped without application crashes. | **Verified in Adversarial Test** |

---

## 3. Explicit Negative Assurances & Excluded Claims

To prevent unsubstantiated statements during the competition, the following claims are **STRICTLY EXCLUDED**:

1. **No Claims of Government Partnership:** DocuReady is an independent pre-submission compliance audit tool built for HackNation 2026. It is not officially endorsed by or integrated with MeitY, UIDAI, or the Government of Odisha.
2. **No Claims of Official Approval:** DocuReady determines document readiness; official legal sanction remains under the authority of scheme administrators.
3. **No Unsubstantiated Market Sizing:** The presentation will not cite arbitrary "100-billion dollar market" or unverified user adoption figures. All statistics are strictly confined to published scheme rules and internal empirical benchmarks.
4. **No Claims of Full Multi-Language OCR:** The current production sidecar operates in English (`eng`). Multi-language Indian regional OCR (Odia, Hindi) is transparently identified as a roadmap item.
5. **No Claims of Proprietary Legal Clearance:** Commercial redistribution remains appropriately disclosed as gated by PyMuPDF AGPL-3.0 licensing options.

---
*Claims & Evidence Register Certified for HackNation 2026 Presentation.*
