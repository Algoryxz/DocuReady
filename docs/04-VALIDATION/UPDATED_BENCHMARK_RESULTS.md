# Updated Benchmark Results: Expanded 40-Packet Forensic Evaluation

**Evaluation Date:** 2026-11-13  
**Corpus Size:** 40 Multi-Document Packets (240 Physical PDF Documents on Disk)  
**Execution Runtime:** Python 3.12.10 (Single-threaded CPU, Offline Air-Gapped)  
**Manifest:** [`docuready-mvp/synthetic_data/corpus_40_manifest.json`](file:///c:/Users/smara/Desktop/New%20folder/docuready-mvp/synthetic_data/corpus_40_manifest.json)  
**Raw Results:** [`docuready-mvp/synthetic_data/benchmark_40_evaluation.json`](file:///c:/Users/smara/Desktop/New%20folder/docuready-mvp/synthetic_data/benchmark_40_evaluation.json)

---

## 1. Multi-Tier Evaluation Architecture

To evaluate the system rigorously, testing is segregated into four distinct tiers:

### Tier 1: Extraction Tests
- **Objective:** Verify physical PDF vector parsing, line grouping, and bounding box localization across varied layouts and multi-page documents.
- **Coverage:** Tested single-page, multi-page (2–5 pages), unusual margin alignments, and corrupted headers.
- **Result:** **100% Extraction Fidelity** on all valid synthetic and external canvas PDFs. Bounding boxes correspond directly to text coordinates.

### Tier 2: Normalization Tests
- **Objective:** Verify deterministic field canonicalization algorithms.
- **Coverage:** Evaluated 18 string normalization cases (salutations, token permutations, initials expansions, Levenshtein typos), 8 date patterns with DD/MM ambiguity flags, currency conversions ("LPA", "Lakh", "Rs.", "₹"), and ISO/IEC 7064 Verhoeff check digits.
- **Result:** **100% Deterministic Correctness**. Zero regex crashes on malformed inputs (`"NIL"`, `"Not Disclosed"` safely return `None`).

### Tier 3: Individual Rule Unit Tests
- **Objective:** Verify that each statutory rule triggers independently without unintended cascade effects.
- **Coverage:** 11 statutory rules tested in isolation in `tests/test_validator.py` and `tests/test_adversarial.py`.
- **Result:** All rules trigger corresponding penalties and status classifications (`PASS`, `REVIEW`, `FAIL`, `UNKNOWN`).

### Tier 4: End-to-End Packet Ingestion & Audit Tests
- **Objective:** Full workflow execution across 40 independently synthesized citizen packets.
- **Coverage:** Clean packets (15), Name variations (8), DOB mismatches & ambiguities (5), Income ceiling breaches (4), Missing certificates (3), Unreadable scans (2), Multiple simultaneous defects (3).

---

## 2. Confusion Matrix & Performance Metrics

| Evaluation Metric | Measured Value | Operational Meaning |
|---|---|---|
| **True Positives (TP)** | **25** | Defective packets correctly identified as requiring action or rejection |
| **True Negatives (TN)** | **15** | Fully consistent clean packets correctly identified as `READY_TO_SUBMIT` |
| **False Positives (FP)** | **0** | Clean packets erroneously blocked or failed |
| **False Negatives (FN)** | **0** | Defective packets erroneously passed as ready |
| **Precision** | **1.0000 (100.0%)** | $\frac{TP}{TP + FP} = \frac{25}{25 + 0}$ |
| **Recall (Sensitivity)** | **1.0000 (100.0%)** | $\frac{TP}{TP + FN} = \frac{25}{25 + 0}$ |
| **F1-Score** | **1.0000** | $2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}}$ |
| **False Positive Rate (FPR)** | **0.0000 (0.0%)** | Clean application disruption rate |
| **False Negative Rate (FNR)** | **0.0000 (0.0%)** | Defect leakage rate to government portal |

---

## 3. Latency & Resource Footprint

Measurements reflect full pipeline latency: reading 6 physical PDF files from disk, vector text parsing via PyMuPDF, field normalization, bipartite consistency graph construction, rule compilation, and scoring.

| Latency Metric | Measured Value | Target Kiosk SLA |
|---|---|---|
| **Mean End-to-End Latency** | **221.56 ms** | $< 1,000\text{ ms}$ |
| **Median Latency** | **216.29 ms** | $< 500\text{ ms}$ |
| **p95 Latency** | **317.40 ms** | $< 1,500\text{ ms}$ |
| **Minimum Latency** | **177.73 ms** | Packet with 5 documents (missing cert) |
| **Maximum Latency** | **393.77 ms** | Multi-page dense packet |
| **Peak RAM Consumption** | **< 4.2 MB** | Standard low-spec kiosk PC ready |
| **Cloud Network Calls** | **0** | 100% offline air-gapped |

---

## 4. Breakdown by Test Group

| Packet Group | Packets Tested | Ground Truth Determination | Predicted Determination | Status Match Rate |
|---|---|---|---|---|
| **1. Consistent Clean Packets** | 15 | `READY_TO_SUBMIT` | `READY_TO_SUBMIT` (Score: 100) | **100% (15/15)** |
| **2. Name Variations** | 8 | `ACTION_REQUIRED` (4) / `REVIEW` (4) | `ACTION_REQUIRED` (4) / `REVIEW` (4) | **100% (8/8)** |
| **3. DOB Discrepancies** | 5 | `ACTION_REQUIRED` (3) / `REVIEW` (2) | `ACTION_REQUIRED` (3) / `REVIEW` (2) | **100% (5/5)** |
| **4. Income Ceiling Breaches** | 4 | `REJECT_PRECHECK` | `REJECT_PRECHECK` (Score: 40) | **100% (4/4)** |
| **5. Missing Mandatory Certs** | 3 | `REJECT_PRECHECK` | `REJECT_PRECHECK` (Score: 65) | **100% (3/3)** |
| **6. Unreadable / Corrupted Scans** | 2 | `UNREADABLE_PACKET` | `UNREADABLE_PACKET` (Score: 75) | **100% (2/2)** |
| **7. Multiple Defects Combined** | 3 | `ACTION_REQUIRED` | `ACTION_REQUIRED` (Score: 0) | **100% (3/3)** |
| **Total** | **40** | — | — | **100% (40/40)** |

---

## 5. Methodological Note: Synthetic vs Real-World Accuracy

> [!CAUTION]
> **Synthetic benchmark accuracy is NOT real-world accuracy.**  
> While DocuReady achieves 100% precision and recall on the 40-packet synthetic dataset, real-world deployment across rural citizen service centres involves:
> - Low-contrast, skewed mobile phone camera snapshots.
> - Hand-stamped tahsil seals overlapping critical text.
> - Regional vernacular languages (Odia, Hindi, Bengali) requiring OCR models.
> - Torn, wrinkled, or low-resolution photocopies.
>
> In real-world operation, extraction confidence will vary, and DocuReady is designed to gracefully degrade to `UNKNOWN` or `REVIEW` rather than making unjustified binary reject decisions.
