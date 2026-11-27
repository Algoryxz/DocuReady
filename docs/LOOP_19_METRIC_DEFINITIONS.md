# LOOP 19: Comprehensive Metric Definitions & Evaluation Harness Specification

## 1. Overview & Evaluation Scope

In Loop 19, evaluation moves from full-page string presence to structured spatial evidence association. This document formally defines all metrics employed across the benchmark suites.

---

## 2. OCR & Text Recognition Metrics

### A. Micro Corpus Character Error Rate (Micro CER)
$$\text{Micro CER} = \frac{\sum_{i=1}^N \text{Levenshtein}(H_i, R_i)}{\sum_{i=1}^N |R_i|}$$
Measures the aggregate character-level symbol error rate across the entire corpus.

### B. Macro Per-Document Character Error Rate (Macro CER)
$$\text{Macro CER} = \frac{1}{N} \sum_{i=1}^N \frac{\text{Levenshtein}(H_i, R_i)}{|R_i|}$$
Measures the unweighted arithmetic mean of per-document error rates.

### C. Reading-Order Inversion Rate
$$\text{Inversion Rate} = \frac{\sum_{i < j} \mathbf{1}[\text{Rank}(L_i) > \text{Rank}(L_j)]}{\binom{K}{2}} \times 100\%$$
Where $L_1, \dots, L_K$ are the spatial lines reconstructed by vertical clustering and $\text{Rank}(L_i)$ is their order in reference ground truth.

---

## 3. Spatial Structure & Table Metrics

### A. Column Detection Accuracy
The proportion of ground-truth table columns whose horizontal bounds $[X_{\min}, X_{\max}]$ are identified within an Intersection-over-Union (IoU) threshold of 0.70.

### B. Row Detection Accuracy
The proportion of ground-truth table rows whose vertical bounds $[Y_{\min}, Y_{\max}]$ are identified within an IoU threshold of 0.70.

### C. Cell Detection F1-Score
$$P = \frac{\text{True Positive Cells}}{\text{Total Detected Cells}}, \quad R = \frac{\text{True Positive Cells}}{\text{Total Ground Truth Cells}}, \quad F_1 = \frac{2PR}{P + R}$$
A detected cell is a True Positive if its spatial bounding box achieves $\text{IoU} \ge 0.60$ with a ground-truth cell.

### D. Word-to-Cell Assignment Accuracy
$$\text{Word Assignment Accuracy} = \frac{\text{Words assigned to correct }(R_i, C_j)}{\text{Total detected words in table region}}$$

---

## 4. Critical Field & Association Metrics

### A. Spatial Exact Match (SEM)
$$\text{SEM} = \mathbf{1}[(\text{Value}(F) == \text{Expected}) \land (\text{Col}(F) == \text{ExpectedCol}) \land (\text{Row}(F) == \text{ExpectedRow})]$$
A field is ONLY considered an exact match if its value is correct AND it is bound to the correct spatial row and column.

### B. Wrong-Column Assignment Rate
$$\text{WCR} = \frac{\text{Fields where value is correct but assigned to wrong column}}{\text{Total correctly recognized fields}}$$

### C. Wrong-Row Assignment Rate
$$\text{WRR} = \frac{\text{Fields where value is correct but assigned to wrong row/record}}{\text{Total correctly recognized fields}}$$

### D. Field CER
$$\text{Field CER} = \frac{\text{Levenshtein}(\text{ExtractedValue}, \text{ExpectedValue})}{|\text{ExpectedValue}|}$$

---

## 5. Traceability & Abstention Metrics

### A. Evidence Traceability Rate
Percentage of extracted fields maintaining an unbroken spatial provenance contract:
$$\text{Traceable} \iff \{\text{doc\_id}, \text{page}, \text{bbox}, \text{cell\_id}, \text{raw\_tokens}, \text{conf}\} \ne \emptyset$$

### B. Association Abstention Precision
$$\text{Abstention Precision} = \frac{\text{True Ambiguous / Overlapping Regions Abstained}}{\text{Total Abstentions Triggered}}$$
Measures whether the system abstains only when geometric evidence is genuinely ambiguous (preventing false rejections of valid records).
