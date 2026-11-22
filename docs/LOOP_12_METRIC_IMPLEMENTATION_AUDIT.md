# DOCUREADY — LOOP 12 METRIC IMPLEMENTATION AUDIT
## Mathematical Integrity, Metric Logic & Forensic Defect Analysis

**Project:** DocuReady  
**Loop:** 12  
**Target:** `research/loop11_benchmark/harness/metrics.py` and `benchmark_runner.py`  
**Date:** 2026-11-22  
**Branch:** `loop-12-benchmark-integrity-audit`  

---

## 1. EXECUTIVE METRIC AUDIT OVERVIEW

An independent mathematical and code-level forensic audit was conducted on Loop 11's evaluation harness. Four critical flaws were identified that significantly distorted the reported benchmark outcomes:

1. **Hardcoded Simulated Layout Metrics:** In `run_doclaynet_benchmark`, `table_ious.append(0.85)` and `header_ious.append(0.92)` were hardcoded constants. No actual bounding box IoU was computed against OCR text.
2. **Gross Target Mismatch in String Metrics:** SROIE and Degradation suites computed Levenshtein Character Error Rate (CER) by comparing a short target string (e.g., 20-character applicant name or a single concatenated metadata line) against the full 300–500 character OCR page text. This guaranteed CER = 1.0 mathematically, even on 100% accurate OCR outputs.
3. **Multi-Column Reading Order Penalties:** In the FUNSD suite, ground-truth dictionary keys were concatenated in arbitrary key order and compared against raw OCR text that traversed across two-column table layouts horizontally, inflating CER to 0.5589.
4. **Lack of Unicode NFC Normalization:** Neither CER nor WER performed Unicode canonical decomposition or composition normalization, creating artificial character errors on non-ASCII diacritics.

---

## 2. METRIC FORMULA COMPARISON

### 2.1 Character Error Rate (CER)
$$\text{CER} = \frac{\text{Levenshtein}(S_{\text{ref}}, S_{\text{hyp}})}{\max(1, \text{len}(S_{\text{ref}}))}$$

- **Loop 11 Implementation:**
  ```python
  def compute_cer(reference: str, hypothesis: str) -> float:
      ref = reference.strip()
      hyp = hypothesis.strip()
      if not ref:
          return 0.0 if not hyp else 1.0
      dist = compute_levenshtein_distance(ref, hyp)
      return min(1.0, dist / len(ref))
  ```
- **Loop 12 Forensic Finding:** Clamping `min(1.0, dist / len(ref))` concealed catastrophic target mismatches. When `dist` was 300 and `len(ref)` was 20, the ratio was 15.0, clamped to 1.0. The test harness failed to detect that the reference and hypothesis were mismatched in scope.
- **Reference Replacement:** [reference_scorer.py](file:///c:/Users/smara/Desktop/New%20folder/research/loop12_audit/reference_scorer.py#L48-L80) introduces Unicode NFC normalization, explicit whitespace normalization, case sensitivity controls, and edge-case guards.

---

### 2.2 Word Error Rate (WER)
$$\text{WER} = \frac{\text{Levenshtein}_{\text{words}}(W_{\text{ref}}, W_{\text{hyp}})}{\max(1, \text{len}(W_{\text{ref}}))}$$

- **Loop 11 Implementation:** Split on `\s+` without stripping punctuation.
- **Loop 12 Forensic Finding:** Punctuation tokens attached to words (e.g. `1,80,000.` or `SCHOLARSHIP:`) triggered word substitution errors even when the underlying alphanumeric tokens were completely recognized.
- **Reference Replacement:** Strict whitespace tokenization with Unicode normalization and optional punctuation stripping.

---

### 2.3 Bounding Box Intersection over Union (IoU)
$$\text{IoU}(B_1, B_2) = \frac{\text{Area}(B_1 \cap B_2)}{\text{Area}(B_1 \cup B_2)}$$

- **Loop 11 Implementation:**
  `metrics.py` implemented a valid geometric IoU function. However, in `benchmark_runner.py`:
  ```python
  # Simulated IoU computation against line clustering
  table_ious.append(0.85)  # Baseline bounding box alignment
  header_ious.append(0.92)
  ```
- **Loop 12 Forensic Finding:** **INVALID & MISLEADING.** The metrics reported in Loop 11 (Mean Header IoU: 0.92, Mean Table IoU: 0.85) were **fabricated constants**. No predicted bounding boxes were matched against ground truth polygons.
- **Loop 12 Corrected Metric:** Real bipartite greedy maximum-IoU matching was implemented in `match_bboxes_greedy_iou`. The actual mean matched IoU between DocuReady OCR line boxes and layout regions across the 30 DocLayNet samples is **0.5186**.

---

## 3. HARNESS INVOCATION DEFECTS

| Benchmark Suite | Loop 11 Target String ($S_{\text{ref}}$) | Hypothesis String ($S_{\text{hyp}}$) | Flaw Type | Loop 11 Result | Corrected Result |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **SROIE** | Single concatenated string (Company, Date, Total) | Full raw OCR receipt text (with headers, item lines, whitespace) | Length & Layout Mismatch | CER: 1.0000 (60 failures) | Field Pass Rate: **65.0%** (Date: 100%, Amount: 100%) |
| **DEGRADATION** | Single applicant name (20 characters) | Full 300–500 character certificate text | Scale Mismatch | 0 Clean Passes (37 failures) | Adjusted Accuracy: **84.0%** (Skew: 100%, Blur: 100%) |
| **DOCLAYNET** | Layout element polygon bboxes | PageOCRData line boxes | Hardcoded Constant Injection | IoU: 0.92 / 0.85 (Hardcoded) | Audited Real IoU: **0.5186** |
| **FUNSD** | Dictionary key-value join | Multi-column raw OCR text | Reading Order & Missing Boilerplate | CER: 0.5589 (50 failures) | Field Coverage: **100.0%** (Reading order issue confirmed) |

---

## 4. DENOMINATOR & SURVIVORSHIP AUDIT

The denominator audit confirmed that no samples were dropped:
- Total samples in manifest: 230
- Total samples evaluated: 230
- Samples dropped: 0
- Denominator integrity: **VERIFIED**

Detailed audit records are archived in [loop12_metric_audit.json](file:///c:/Users/smara/Desktop/New%20folder/research/loop12_audit/loop12_metric_audit.json).
