# DOCUREADY — LOOP 11 BENCHMARK METHODOLOGY & EVALUATION CONTRACT
## Independent Dataset Benchmark, OCR Generalization & Performance Frontier

**Project:** DocuReady  
**Phase:** Phase 4 & 5 — Benchmark Design, Ground Truth & Splits  
**Author:** Antigravity Research Engineering (Loop 11)  
**Date:** 2026-11-22  
**Evaluation Target:** Sealed Production Baseline (`bdc403a`)  

---

## 1. INDEPENDENT BENCHMARK OBJECTIVES

The purpose of Loop 11 is to move beyond self-authored synthetic test sets and evaluate DocuReady against established external benchmarks and diverse document distributions.

To prevent confirmation bias:
1. **Separation of Concerns:** The benchmark harness evaluates OCR, Layout Analysis, Field Extraction, and Decision Engine reliability as independent, decoupled stages.
2. **Ground Truth Independence:** Ground truth annotations are derived from official schemas (FUNSD, SROIE, DocLayNet, IndicDLP, and DIBCO) rather than from the output of DocuReady's internal extractors.
3. **Sealed Release Invariance:** The benchmark executes strictly against the qualified Loop 10 release codebase without modifying production thresholds or rules.

---

## 2. BENCHMARK SUITE TAXONOMY

The benchmark corpus encompasses 230 independent test samples structured into 5 specialized evaluation suites:

```
+-----------------------------------------------------------------------------------------+
|                               LOOP 11 BENCHMARK CORPUS (230)                            |
+--------------------+---------------------+--------------------+--------------------+----+
| FUNSD Suite (50)   | SROIE Suite (60)    | Indic OCR (40)     | DocLayNet (30)     | Degradation (50)
| Form Understanding | Thermal Receipts    | Hindi & Odia       | Complex Layouts    | DIBCO Stresses
| - Word CER/WER     | - OCR Transcripts   | - Devanagari CER   | - Header IoU       | - Skew Breakdown
| - Line Grouping    | - Date Normalizing  | - Odia Script CER  | - Table IoU        | - Blur Threshold
| - Key-Value Links  | - Amount Extraction | - Multilingual Gap | - Column Ordering  | - Noise Abstention
+--------------------+---------------------+--------------------+--------------------+----+
```

---

## 3. EVALUATION METRICS & MATHEMATICAL FORMULATIONS

### 3.1. Optical Character Recognition (OCR) Accuracy
- **Character Error Rate (CER):**
  $$\text{CER} = \frac{\mathcal{L}_{\text{edit}}(S_{\text{ref}}, S_{\text{hyp}})}{\max(1, |S_{\text{ref}}|)}$$
  where $\mathcal{L}_{\text{edit}}$ represents the standard Levenshtein edit distance (substitutions, insertions, deletions) between the reference text and OCR hypothesis.
- **Word Error Rate (WER):**
  $$\text{WER} = \frac{\mathcal{L}_{\text{edit\_words}}(W_{\text{ref}}, W_{\text{hyp}})}{\max(1, |W_{\text{ref}}|)}$$
  where $W$ represents whitespace-tokenized word sequences.

### 3.2. Layout Analysis & Geometry
- **Bounding Box Intersection over Union (IoU):**
  $$\text{IoU}(B_1, B_2) = \frac{\text{Area}(B_1 \cap B_2)}{\text{Area}(B_1 \cup B_2)}$$
  where $B = [x_0, y_0, x_1, y_1]$ in standard PDF 72 DPI point coordinates.

### 3.3. Key Information Extraction (KIE)
- **Field Precision, Recall, and F1 Score:**
  $$\text{Precision} = \frac{\text{TP}}{\text{TP} + \text{FP}}, \quad \text{Recall} = \frac{\text{TP}}{\text{TP} + \text{FN}}, \quad F_1 = \frac{2 \cdot \text{Precision} \cdot \text{Recall}}{\text{Precision} + \text{Recall}}$$
  evaluated under both exact case-sensitive matching and normalized semantic matching.

### 3.4. Decision Engine Calibration
- **False READY Rate:** Defective or non-compliant applications mistakenly approved as `NO_ISSUES_FOUND` (Target: strictly 0.00%).
- **Conservative Abstention Rate:** Corrupted, blurry, or unreadable documents correctly flagged as `NEEDS_CHECKS` or `UNREADABLE` without hallucinated bounding boxes.

---

## 4. EVALUATION SPLITS & LEAKAGE PREVENTION

To eliminate training/tuning leakage, all datasets are strictly partitioned into three isolated splits using a fixed random seed (`20261122`):

| Partition | Allocation Ratio | Usage Policy | Leakage Controls |
| :--- | :--- | :--- | :--- |
| **DEVELOPMENT (DEV)** | 40% (92 samples) | Exploratory error analysis and diagnostic profiling | Open inspection |
| **VALIDATION (VAL)** | 35% (80 samples) | Threshold sanity checks and metamorphic verification | Immutable reference |
| **SEALED CHALLENGE** | 25% (58 samples) | Blind zero-shot final generalization assessment | Zero hyperparameter tuning |

---

## 5. REPRODUCIBILITY GUARANTEES

The benchmark runner (`research/loop11_benchmark/harness/benchmark_runner.py`) satisfies the following engineering guarantees:
1. **Deterministic Execution:** Fixed seeds, pinned OCR configurations, and zero randomness in metric calculations.
2. **Failure Preservation:** Every sample producing CER > 0.25, missing target fields, or abnormal status transitions is recorded in `loop11_failure_cases.json`.
3. **Offline Hermeticity:** All data loaders and image synthesizers execute locally with zero external network dependencies.
