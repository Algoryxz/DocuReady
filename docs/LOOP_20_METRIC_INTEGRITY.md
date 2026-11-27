# LOOP 20: Metric Integrity & Evaluation Methodology

## 1. Governance & Formula Definitions

All metrics in Loop 20 are defined with explicit numerators, denominators, and cohorts to prevent ambiguity or misleading summaries:

### 1.1 Spatial Exact Match (SEM) Rate
$$\text{SEM Rate} = \frac{\sum_{i=1}^{N} \mathbb{I}(\text{val}_i == \text{exp\_val}_i \land \text{row}_i == \text{exp\_row}_i \land \text{col}_i == \text{exp\_col}_i)}{N}$$
- *Numerator*: Count of fields whose extracted value, logical row index, and logical column index match ground truth exactly.
- *Denominator ($N$)*: Total eligible critical fields evaluated.
- *Normalization*: Currency symbols (`₹`, `Rs.`), commas, and leading/trailing whitespace removed before string comparison.

### 1.2 Baseline Substring Match (BSM) Rate
$$\text{BSM Rate} = \frac{\sum_{i=1}^{N} \mathbb{I}(\text{exp\_val}_i \in \text{page\_text})}{N}$$
- *Purpose*: Measures the naive Loop 18 check to quantify the "Substring Presence Fallacy".

### 1.3 False Verification Rate (FVR)
$$\text{FVR} = \frac{\text{Incorrect Fields Marked Verified}}{\text{All Fields Marked Verified}} = \frac{7}{61} = 11.48\%$$

### 1.4 Critical Field Precision (CFP)
$$\text{CFP} = \frac{\text{Correct Fields Marked Verified}}{\text{All Fields Marked Verified}} = \frac{54}{61} = 88.52\%$$

### 1.5 Verification Coverage
$$\text{Coverage} = \frac{\text{All Fields Marked Verified}}{\text{Total Eligible Critical Fields}} = \frac{61}{65} = 93.85\%$$

### 1.6 Abstention Rate
$$\text{Abstention Rate} = \frac{\text{Fields Abstained by System}}{\text{Total Eligible Critical Fields}} = \frac{7}{65} = 10.77\%$$

---

## 2. Integrity Protections Applied in Loop 20

1. **No Ground Truth at Runtime**: Engine receives only image bytes, page dimensions, and field query parameters (`field_name`, `target_pattern`, `col_idx`, `expected_type`). Expected values are strictly isolated in the benchmark evaluation harness.
2. **Double Accounting Prohibited**: A field that is abstained cannot count toward False Verification.
3. **Empty Cell Discipline**: When expected value is empty (`""`), an extraction returning non-empty text is classified as a False Verification (`FAIL_SPURIOUS_VALUE`).
