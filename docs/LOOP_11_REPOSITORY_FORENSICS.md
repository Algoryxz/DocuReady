# DOCUREADY — LOOP 11 REPOSITORY FORENSICS & ARCHITECTURAL AUDIT
## Independent Dataset Benchmark, OCR Generalization & Performance Frontier

**Repository:** Algoryxz/DocuReady  
**Evaluation Target:** Production Python Engine & Standalone Desktop Sidecar  
**Sealed Release Baseline:** Loop 10 (`bdc403a`)  
**Branch:** `loop-11-independent-dataset-benchmark`  
**Date:** 2026-11-22  
**Purpose:** Comprehensive forensic audit of ingestion, OCR, extraction, decision, and runtime communication pathways to inform independent dataset benchmarking without modifying the sealed production release.

---

## 1. ARCHITECTURE OVERVIEW

DocuReady is designed as a hybrid local desktop application comprising an Electron frontend (React 19 + TypeScript + Vite) paired over a secure, sandboxed JSON-RPC pipe to a native standalone sidecar process executing Python 3.12, PyMuPDF, and a bundled Tesseract 5.5.0 OCR engine.

```
+-----------------------------------------------------------------------------------+
|                            ELECTRON FRONTEND (DESKTOP)                            |
|  - Dropzone File Intake & Magic-Byte Signature Validation (validateFileSignature) |
|  - Ephemeral Workspace Staging (WorkspaceManager)                                 |
|  - Dual-View PDF Canvas + Coordinate-Accurate Bounding Box Overlay                |
|  - Review Callout & Zero-PII Findings Presentation                                |
+------------------------------------------+----------------------------------------+
                                           | Local Stdio IPC (JSON-RPC v1)
                                           v
+-----------------------------------------------------------------------------------+
|                        STANDALONE PYTHON SIDECAR RUNTIME                          |
|  - docuready_sidecar.py (PyInstaller One-Dir/One-File Native Binary)              |
|  - Protocol v1 Dispatcher (health, audit_packet, audit_documents, shutdown)       |
|  - Workspace Boundary Enforcement (DOCUREADY_WORKSPACE_ROOT)                      |
|  - Privacy Redaction Engine (redact_audit_result_dict)                            |
+------------------------------------------+----------------------------------------+
                                           | Internal Ingestion Calls
                                           v
+-----------------------------------------------------------------------------------+
|                           INGESTION & RASTERIZATION LAYER                         |
|  - PyMuPDF / PDFium Document Loader (pymupdf_backend.py)                          |
|  - Page Bomb Protection: Dimension clamp (< 4096 px)                              |
|  - Direct Pixel Buffer Allocation (PIL.Image.frombytes RGB samples)               |
+------------------------------------------+----------------------------------------+
                                           | Unprocessed Page Images
                                           v
+-----------------------------------------------------------------------------------+
|                     OCR, DESKEW & ORIENTATION RECOVERY PIPELINE                   |
|  - Step 1: Speculative 0° Token OCR (pytesseract.image_to_data)                   |
|  - Step 2: Conservative Upright Gate (_is_demonstrably_upright)                   |
|  - Step 3: Skew Estimation & Sub-Degree Deskewing (estimate_skew_angle, Rad/Hough) |
|  - Step 4: Orthogonal Orientation Fallback (image_to_osd at 0.6x downsampling)    |
|  - Bundled Tesseract 5.5.0 Runtime (tessdata: eng, hin, ori, osd)                |
+------------------------------------------+----------------------------------------+
                                           | PageOCRData (Lines, Words, Geometry)
                                           v
+-----------------------------------------------------------------------------------+
|                        EXTRACTION & NORMALIZATION ENGINE                          |
|  - Slot Classification & Header Anchor Detection (classify_document_content)      |
|  - Regex & Token Geometry Clustering (Horizontal Line Bounding)                   |
|  - Canonical Normalizers: Name, Date (DD/MM/YYYY vs ISO), Income, IFSC, Cert Num  |
|  - Confidence Calibration (EvidenceProvenance, EvidenceState, ExtractionMethod)   |
+------------------------------------------+----------------------------------------+
                                           | ExtractedDocument & ExtractedField
                                           v
+-----------------------------------------------------------------------------------+
|                       STATUTORY AUDIT & DECISION ENGINE                           |
|  - Declarative Scheme Pack Architecture (ARCHITECTURE_V2 §7)                      |
|  - 9 Closed Primitives (EQUALS, RANGE, DATE_DIFF, REGEX, etc. - Zero eval/exec)    |
|  - Three-Valued Outcome Resolver (NO_ISSUES_FOUND, NEEDS_CHECKS, NOT_READY)       |
|  - Calibrated Severity & Penalty Matrix (Fatal, Critical, Major, Review, Warning) |
|  - Negative Evidence Integrity (Empty [] evidence for missing docs, bbox: None)   |
+-----------------------------------------------------------------------------------+
```

---

## 2. DETAILED PIPELINE STAGES & EXECUTION FLOW

### Stage 1: Document Intake & PDF Rasterization
- **Implementation:** `src/docuready/ingest/extractor.py` (`_ocr_page`) and `src/docuready/ingest/pdf_backend/pymupdf_backend.py`.
- **Mechanism:** PDF pages are rendered to memory pixmaps via PyMuPDF at default 200 DPI (`pix = page.get_pixmap(dpi=dpi)`).
- **Memory Optimization:** Uses direct buffer decoding (`PIL.Image.frombytes("RGB", [pix.width, pix.height], pix.samples)`), bypassing intermediate PNG file encoding/decoding.
- **Security Guard:** Dimension threshold clamp (`rect.width > 4096` or `rect.height > 4096` falls back to 72 DPI to prevent decompression bombs).

### Stage 2: Fast-Path Upright Gate & Speculative OCR
- **Implementation:** `src/docuready/ingest/extractor.py` (`_is_demonstrably_upright`).
- **Mechanism:** Initial pass runs `pytesseract.image_to_data(img, output_type=DICT)`.
- **Gating Metric:** Evaluates valid token count, average word confidence, and horizontal baseline consistency. If >= 8 high-confidence tokens exist with mean confidence >= 75% and horizontal alignment, the page bypasses expensive orientation/deskew steps entirely.

### Stage 3: Non-Orthogonal Skew Estimation & Deskewing
- **Implementation:** `src/docuready/ingest/deskew.py` (`estimate_skew_angle`, `deskew_image`, `transform_bbox_inverse`).
- **Mechanism:**
  - Token baseline slope extraction from adjacent OCR bounding boxes (`extract_token_baseline_slope`).
  - Radon transform / Hough line detection on binarized edge contours for fallback angle estimation.
  - Sub-pixel affine rotation (`PIL.Image.rotate`) for angles $\theta \in [1.0^\circ, 45.0^\circ]$ with confidence $\ge 5.0$.
  - Secondary OCR pass on deskewed image; accepted only if valid token count increases or upright gate passes.
  - Coordinate back-projection maps deskewed bounding boxes back to original document coordinate space.

### Stage 4: Orthogonal Orientation Detection (OSD)
- **Implementation:** `src/docuready/ingest/extractor.py` (lines 380–415).
- **Mechanism:** Two-tier orientation fallback for 90°, 180°, 270° rotated pages:
  - Tier A: Fast downsampled OSD (0.60x scale) to reduce processing time by ~30%.
  - Tier B: Full-resolution OSD if downsampled detection is inconclusive.
  - Rotate image by $360^\circ - \text{rot}$, expand canvas, and re-run token OCR.

### Stage 5: Layout Analysis & Field Extraction
- **Implementation:** `src/docuready/ingest/extractor.py` (`_find_field_in_ocr_page`, `PageOCRData._build_lines`).
- **Mechanism:**
  - Tokens are grouped into visual lines based on vertical overlap and horizontal proximity.
  - Regular expressions target anchor labels (e.g., "Name of Student", "Annual Family Income", "Date of Birth").
  - Value extraction leverages inline captures or spatial proximity (right-adjacent tokens or below-label tokens).
  - Exact bounding boxes $[x_0, y_0, x_1, y_1]$ are calculated by bounding all matching word tokens.

### Stage 6: Field Normalization & Cross-Document Reconciler
- **Implementation:** `src/docuready/normalize/normalizer.py`.
- **Mechanism:**
  - Names: Tokenized, case-normalized, title honorifics removed (Sri, Smt, Dr, etc.), initials flagged.
  - Dates: Multi-format parsing (DD/MM/YYYY, YYYY-MM-DD, DD-Mon-YYYY, textual months). Ambiguous dates (e.g., 04/05/2004) flagged for human review.
  - Incomes: Numeric extraction, currency symbol stripping, ceiling comparison against statutory limit (₹2,50,000).
  - Banking: Regex validation for 11-character IFSC codes against RBI national bank clearing master.

### Stage 7: Statutory Decision Engine & Outcome Resolver
- **Implementation:** `src/docuready/rules/engine.py` and `src/docuready/outcome/resolver.py`.
- **Mechanism:**
  - Evaluates scheme pack rules against cross-document extracted entities.
  - Outcomes resolved deterministically into `NO_ISSUES_FOUND` (100), `NEEDS_CHECKS` (60–99), or `NOT_READY` (0–85).
  - Hard failure invariants: Fatal/Critical defects (e.g., name conflict, missing mandatory doc) strictly force `NOT_READY` regardless of other passing scores.
  - Negative Evidence Guard: Missing documents yield `evidence: []` with zero hallucinated bounding boxes. Degraded unreadable documents trigger conservative abstention with `bbox: None`.

---

## 3. EXISTING TEST INFRASTRUCTURE & BENCHMARK TOOLING

The repository currently possesses a rich testing apparatus across unit, integration, property, and system levels:

| Test Harness | File Path | Focus Area | Scope |
| :--- | :--- | :--- | :--- |
| **Release Integrity Suite** | `tests/test_loop09_release_integrity.py` | Packaged binaries, clean-machine sandbox, ASAR integrity | 9 tests |
| **Demonstration Reliability Suite** | `tests/test_loop10_demo_reliability.py` | 5-run demo packet determinism, score invariance, PII redaction | 11 tests |
| **Golden Baseline Suite** | `tests/test_golden_baseline.py` & `test_pack_golden_baseline.py` | Bit-exact parity against legacy and pack engines | 22 tests |
| **Adversarial Generalization Suite** | `tests/test_loop07_adversarial_generalization.py` | Metamorphic testing, monotonic penalty scaling, zero false-READY | 12 tests |
| **Decision Engine Safety** | `tests/test_loop06_decision_engine.py` | 10 formal invariants, duplicate deduplication, exception safety | 20 tests |
| **Desktop Workflow Suite** | `apps/desktop/tests/` (Node.js) | IPC protocol, sidecar lifecycle, crash recovery, session purge | 25 tests |
| **Independent Validation Runner** | `tests/independent_validation_runner.py` | Ground-truth oracle comparison on synthetic validation corpus | 16 docs |
| **Sidecar Performance Benchmark** | `tests/benchmark_loop4_performance.py` | Sidecar cold start, RSS memory tracking, throughput | System |

### Existing Performance Measurement Methods:
- `time.perf_counter()` latency timers wrapped around pipeline stages (`audit_result.execution_time_ms`).
- `psutil.Process().memory_info().rss` for monitoring resident set size (RSS) memory before/after audits.
- Sequential repetition loops (5–10 iterations) measuring min, mean, and max execution times.

---

## 4. ARCHITECTURAL BOTTLENECK ANALYSIS

Forensic inspection reveals key architectural trade-offs and latency drivers:

1. **Sequential Multi-Pass OCR on Unindexed Pages:**
   - If a page fails the fast-path upright gate, the pipeline executes:
     1. Initial 0° token pass (~800–1200ms)
     2. Skew estimation + affine rotation
     3. Deskewed token pass (~800–1200ms)
     4. (If still unaligned) Downsampled OSD + rotated token pass (~1500ms)
   - On heavily degraded or multi-page documents, cumulative latency can reach 3.0–3.5s per page.
2. **Hardcoded OCR Language Configuration:**
   - In `extractor.py`, `pytesseract.image_to_data(img, output_type=...)` omits the `lang` parameter entirely.
   - Consequently, Tesseract defaults strictly to `eng` during extraction, ignoring bundled `hin` (Hindi) and `ori` (Odia) trained models unless explicitly overridden or configured.
   - Testing non-English Indian documents will reveal character substitution or deletion errors unless multilingual recognition is evaluated.
3. **Regex-Bound Field Extraction:**
   - Extractors rely on predefined keyword anchors ("Name", "Income", "Father's Name").
   - Novel form layouts, unlabelled tables, or non-standard government certificate formats that diverge from expected syntaxes will suffer recall drops.
4. **Single-Threaded Page Rasterization:**
   - Multi-page documents are rasterized and OCR'd serially within a single process.

---

## 5. RISKS OF MODIFYING PRODUCTION CODE

Because Loop 10 is the sealed competition release:
- **Zero Production Edits:** Any modification to `src/docuready/`, `sidecar/`, `apps/desktop/`, or `package.json` violates the competition feature freeze.
- **Risk of Overfitting / Regressions:** Changing OCR thresholds or regexes to pass external benchmarks risks degrading the 714 passing unit tests or breaking the 22 bit-exact golden baseline assertions.
- **Isolation Mandate:** All Loop 11 benchmark harnesses, dataset loaders, evaluators, and experimental optimizations must reside exclusively in isolated research modules (`research/` or `benchmarks/loop11/`).

---

## 6. RECOMMENDED BENCHMARK ARCHITECTURE

To achieve an authoritative, unbiased evaluation without compromising the production release, the Loop 11 benchmark harness will be structured as follows:

```
research/loop11_benchmark/
├── datasets/                 # Approved public datasets & metadata manifests
│   ├── dataset_catalog.json
│   └── loaders/              # Dataset-specific adapters (FUNSD, SROIE, Indian forms)
├── ground_truth/             # Independent external annotations (unaltered)
├── harness/
│   ├── ocr_evaluator.py      # Character Error Rate (CER), Word Error Rate (WER)
│   ├── field_evaluator.py    # Precision, Recall, F1 for Key-Value extraction
│   ├── layout_evaluator.py   # Bounding Box Intersection over Union (IoU)
│   ├── decision_evaluator.py # Audit Decision Engine confusion matrix (False READY rate)
│   └── perf_profiler.py      # Cold/Warm latency, stage profiling, RSS memory
├── experiments/              # Isolated experimental optimizations (A/B testing)
│   ├── exp_multilang_ocr.py  # Evaluation of eng vs eng+hin vs eng+ori
│   └── exp_deskew_fastpath.py# Optimized single-pass skew recovery
└── results/                  # Machine-readable output JSONs and failure taxonomy
    ├── loop11_baseline_results.json
    └── loop11_failure_cases.json
```

---

## 7. FORENSICS CONCLUSION

The DocuReady production architecture is stable, deterministic, and highly optimized for its target synthetic domain. However, independent benchmark evaluation against public datasets (FUNSD, SROIE, Indian multilingual documents, and real-world scanned degradation) will rigorously challenge its OCR generalization, multiline reading order, language coverage, and keyword-dependent extraction boundaries.

Phase 1 Forensics is complete. Proceeding to Phase 2: External Dataset Discovery.
