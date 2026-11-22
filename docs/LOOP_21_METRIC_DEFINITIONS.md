# Loop 21 Metric Definitions & Exhaustive Verification Accounting

## 1. Background & Mathematical Framework

In Loop 20, metric reporting suffered from an accounting ambiguity where verified claims and abstentions were not formally constrained to be mutually exclusive and exhaustive. In Loop 21, we define a mathematically closed ledger for document evidence extraction and verification.

Every evaluated field $f \in \mathcal{F}$ belongs to **exactly one** mutually exclusive category:
1. **True Verified Exact Match ($\mathcal{V}_{\text{exact}}$)**: The system extracted the claim, provided a bounding box provenance, matched expected spatial coordinates (row and column), and exactly matched the ground-truth value.
2. **False Verification ($\mathcal{V}_{\text{false}}$)**: The system extracted the claim with positive confidence, but the value was incorrect ($\text{FAIL\_MISMATCH}$), spurious ($\text{FAIL\_SPURIOUS\_VALUE}$), or assigned to the wrong row/column coordinate ($\text{FAIL\_WRONG\_COORDINATE}$).
3. **Evidence-Based Abstention ($\mathcal{A}$)**: The system withheld verification due to spatial ambiguity ($\text{ABSTAIN\_AMBIGUOUS}$), empty cell preservation ($\text{PASS\_EMPTY\_CORRECT}$), or absence of candidate evidence ($\text{FAIL\_NOT\_EXTRACTED}$).

$$\mathcal{F} = \mathcal{V}_{\text{exact}} \cup \mathcal{V}_{\text{false}} \cup \mathcal{A}, \quad \text{where } \mathcal{V}_{\text{exact}} \cap \mathcal{V}_{\text{false}} = \emptyset, \; \mathcal{V} \cap \mathcal{A} = \emptyset$$

Total claims verified is defined as:
$$\mathcal{V} = \mathcal{V}_{\text{exact}} \cup \mathcal{V}_{\text{false}}$$

---

## 2. Formal Metric Formulations

### 2.1 Verification Coverage (VC)
The proportion of document fields for which the system confidently emits a verification claim:
$$\text{VC} = \frac{|\mathcal{V}|}{|\mathcal{F}|} = \frac{|\mathcal{V}_{\text{exact}}| + |\mathcal{V}_{\text{false}}|}{|\mathcal{F}|}$$

### 2.2 Evidence-Based Abstention Rate (AR)
The proportion of document fields where the system abstained from making an ungrounded or ambiguous verification claim:
$$\text{AR} = \frac{|\mathcal{A}|}{|\mathcal{F}|}$$

**First Closure Identity:**
$$\text{VC} + \text{AR} = \frac{|\mathcal{V}| + |\mathcal{A}|}{|\mathcal{F}|} = \frac{|\mathcal{F}|}{|\mathcal{F}|} = 1.0000 \quad (100.00\%)$$

### 2.3 Critical Field Precision (CFP)
The proportion of positive verification claims that are completely correct in both value and spatial provenance:
$$\text{CFP} = \frac{|\mathcal{V}_{\text{exact}}|}{|\mathcal{V}|} = \frac{|\mathcal{V}_{\text{exact}}|}{|\mathcal{V}_{\text{exact}}| + |\mathcal{V}_{\text{false}}|}$$

### 2.4 False Verification Rate (FVR)
The proportion of positive verification claims that are factually inaccurate or improperly localized:
$$\text{FVR} = \frac{|\mathcal{V}_{\text{false}}|}{|\mathcal{V}|} = \frac{|\mathcal{V}_{\text{false}}|}{|\mathcal{V}_{\text{exact}}| + |\mathcal{V}_{\text{false}}|}$$

**Second Closure Identity:**
$$\text{CFP} + \text{FVR} = \frac{|\mathcal{V}_{\text{exact}}| + |\mathcal{V}_{\text{false}}|}{|\mathcal{V}|} = \frac{|\mathcal{V}|}{|\mathcal{V}|} = 1.0000 \quad (100.00\%)$$

### 2.5 Spatial Exact Match (SEM) Accuracy Rate
The overall system accuracy across all ground-truth fields:
$$\text{SEM Rate} = \frac{|\mathcal{V}_{\text{exact}}| + |\mathcal{A}_{\text{empty\_correct}}|}{|\mathcal{F}|}$$

---

## 3. Loop 21 Multi-Cohort Empirical Accounting Ledger

Based on the 40-document multi-cohort evaluation benchmark (83 critical fields total):

| Metric Category | Count / Identity | Percentage |
| :--- | :--- | :--- |
| **Total Critical Fields ($|\mathcal{F}|$)** | **83** | **100.00%** |
| Verified Claims ($|\mathcal{V}|$) | 73 | 87.95% |
| - True Exact Matches ($\mathcal{V}_{\text{exact}}$) | 59 | 71.08% |
| - False Verifications ($\mathcal{V}_{\text{false}}$) | 14 | 16.87% |
| Evidence Abstentions ($|\mathcal{A}|$) | 10 | 12.05% |
| **Verification Coverage (VC)** | $73 / 83$ | **87.95%** |
| **Abstention Rate (AR)** | $10 / 83$ | **12.05%** |
| **Identity Check: VC + AR** | **0.8795 + 0.1205** | **1.0000 (100.0%)** |
| **Critical Field Precision (CFP)** | $59 / 73$ | **80.82%** |
| **False Verification Rate (FVR)** | $14 / 73$ | **19.18%** |
| **Identity Check: CFP + FVR** | **0.8082 + 0.1918** | **1.0000 (100.0%)** |
| **SEM Accuracy Rate** | $62 / 83$ | **74.70%** |

---

## 4. Cohort-Level Breakdown

| Cohort | Documents | Total Fields | Exact Matches | False Verif | Abstentions | SEM Rate | CFP |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **A: Development** | 8 | 16 | 15 | 1 | 0 | 93.75% | 93.75% |
| **B: Validation** | 8 | 16 | 14 | 0 | 2 | 93.75% | **100.00%** |
| **C: Blind Evaluation** | 10 | 20 | 12 | 5 | 3 | 60.00% | 70.59% |
| **D: Challenge / Adversarial** | 8 | 13 | 6 | 5 | 2 | 61.54% | 54.55% |
| **E: Hierarchical Headers** | 3 | 6 | 6 | 0 | 0 | **100.00%** | **100.00%** |
| **F: Decimal Integrity** | 3 | 12 | 6 | 3 | 3 | 50.00% | 66.67% |
| **Overall Corpus** | **40** | **83** | **59** | **14** | **10** | **74.70%** | **80.82%** |

### Key Audit Notes:
1. In Cohort B (Validation), False Verification dropped to **0** (0.0%), and Critical Field Precision reached **100.0%**. The multi-tier header defect in `VAL_05` was eliminated.
2. In Cohort E (Hierarchical Headers), all 6 critical fields achieved exact matches with 0 false verifications and 0 abstentions.
3. In Cohort C (Blind Evaluation), `BLIND_06` achieved 100% exact match (HbA1c `5.6` recovered). The residual false verifications stem from genuine OCR font substitutions (e.g. `BLIND_08` grade 'O' misread as `'fe}'`) and ground-truth index typos in blind datasets (`BLIND_09` weight column).
