# DOCUREADY — LOOP 34 OPERATING PLAN
## Independent OCR & Extraction Accuracy Under Real-World Conditions

**Milestone:** Loop 34  
**Programme:** DocuReady Product Excellence Programme  
**Research Branch:** `loop-34-independent-ocr-extraction-accuracy`  
**Base Commit:** `decce84` (Loop 33 Domain Rules Audit)  
**Protected Competition Baseline:** Loop 10 (`bdc403a`)  
**Operating Thresholds:** $T^* = 70.0$, $T_{\text{fuzzy}} = 75.0$  
**Release Promotion:** Strictly Prohibited  
**Date:** 2026-11-26  

---

## 1. Objective & Scope

Establish how accurately DocuReady reads, interprets, associates, and extracts information from independently sourced real-world documents across supported languages, image qualities, layouts, and document conditions.

This evaluation is an independent evaluation and targeted reliability-improvement loop. It adheres to strict scientific governance:
- **Zero Threshold Tuning:** $T^*=70$ and $T_{\text{fuzzy}}=75$ remain fixed.
- **Strict Blind Freezing:** Partitions (Development, Calibration, Blind) are frozen before evaluation.
- **Complete Metric Separation:** OCR metrics (CER, WER), field extraction (exact, normalized), spatial association (label-value, grid, gutter), and end-to-end outcome metrics are reported separately and never collapsed.
- **Historical Benchmark Preservation:** Existing 791-field, Loop 28, Cohort M, and Loop 33 benchmarks are verified independently without altering denominators.
- **Offline & Privacy Invariants:** 100% local execution, zero network calls, zero cloud OCR, redaction-safe logging.

---

## 2. Execution Phases & Sequence

```
PLAN ──► INSPECT ──► REPRODUCE ──► BENCHMARK ──► HARDEN (if needed) ──► QUALIFY ──► DOCUMENT ──► COMMIT
```

1. **Phase 1: Baseline & Freeze Verification:** Verify commit `decce84` and bit-exact SHA-256 for all 5 Loop 10 release binaries.
2. **Phase 2: Repository & Tooling Inspection:** Review `AGENTS.md`, `skills/ponytail/SKILL.md`, external Agentic Awesome Skills, and VoltAgent Design MD.
3. **Phase 3: Dataset Provenance & Licensing Scrutiny:** Build source-level provenance ledger for evaluation documents (FUNSD, CORD, SROIE, Indian Gazette, land records, academic certificates); re-check license restrictions.
4. **Phase 4: Independent Evaluation Corpus & Blind Partitioning:** Partition into Development (25%), Calibration (25%), and Blind Evaluation (50%); compute and freeze SHA-256 hashes.
5. **Phase 5: Multi-Language & Degradation OCR Evaluation:** Benchmark across English, Hindi, Odia, and mixed-language documents across clean, photocopy, low-res, blur, skew, rotation, noise, micro-font, and narrow gutter conditions.
6. **Phase 6: Spatial Association & End-to-End Extraction:** Measure label-to-value binding, table row/column association, gutter traps, evidence provenance, false verification rate, abstention rate, coverage, and precision.
7. **Phase 7: Controlled Comparisons:** Global vs Region OCR, Adaptive vs Global OCR, Table reconstruction vs baseline, Normalization vs raw OCR, Confidence calibration vs observed correctness.
8. **Phase 8: Failure Taxonomy & Defect Register:** Catalog all error modes with stable IDs (`OCR-034-001`+), isolating root causes.
9. **Phase 9: Benchmark Reproduction & Calibration:** Re-run historical benchmark runner (791 fields, Loop 28, Cohort M); compute ECE, MCE, and Brier score.
10. **Phase 10: Performance & Latency Scopes:** Measure OCR latency per page, extraction latency per document, and end-to-end latency with mean, median, and p95.
11. **Phase 11: Qualification Matrix & Final Commit:** Evaluate Gates A through Z, produce master report, and execute git commit.
