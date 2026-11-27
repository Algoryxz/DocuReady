# Loop 23 Authoritative Metric Definitions & Mathematical Taxonomy

## 1. Disjoint Outcomes Partition

For any evaluated critical field in a document, the system's outcome maps to exactly one disjoint category in the verification partition:
$$\text{Total Evaluated Fields} = V_{\text{exact}} + V_{\text{false}} + A$$

Where:
- $V_{\text{exact}}$ (**Exact Verified Matches**): The field was claimed as verified, and the normalized extracted text exactly matched the normalized expected value ($\text{norm}(\text{extracted}) == \text{norm}(\text{expected})$) with spatial row/column alignment.
- $V_{\text{false}}$ (**False Verifications**): The field was claimed as verified, but the extracted text contradicted the ground truth or inherited a value into an empty cell.
- $A$ (**Abstentions**): The system refused to verify the field due to confidence below floor ($T < 60.0$), multi-row ambiguity, multi-token bleed, label-echo, or syntax garble.

The total number of claims made by the engine is:
$$V = V_{\text{exact}} + V_{\text{false}}$$

---

## 2. Core Verification Metrics

### 2.1 Critical Field Precision (CFP)
$$\text{CFP} = \frac{V_{\text{exact}}}{V} = \frac{V_{\text{exact}}}{V_{\text{exact}} + V_{\text{false}}}$$
Measures the reliability of verified claims. A precision of 100% means every claim made by the engine is factually true.

### 2.2 False Verification Rate (FVR)
$$\text{FVR} = \frac{V_{\text{false}}}{V} = 1 - \text{CFP}$$
Measures the proportion of false claims among all claims made. Must be minimized to 0.00% in statutory audits.

### 2.3 Coverage
$$\text{Coverage} = \frac{V}{N} = \frac{V_{\text{exact}} + V_{\text{false}}}{N}$$
Where $N$ is the total number of evaluated fields across the benchmark.

### 2.4 Abstention Rate
$$\text{Abstention Rate} = \frac{A}{N} = 1 - \text{Coverage}$$

### 2.5 Exact Verified Yield (Overall Accuracy)
$$\text{Exact Verified Yield} = \frac{V_{\text{exact}}}{N}$$
Measures the fraction of all document fields in the universe that were successfully verified with exact ground-truth agreement.

---

## 3. Secondary Spatial Extraction Metrics

### 3.1 Spatial Extraction Match Rate (SEM)
$$\text{SEM Rate} = \frac{\text{SEM Passes}}{N}$$
Where:
$$\text{SEM Passes} = V_{\text{exact}} + \text{PASS\_EMPTY\_CORRECT} + A_{\text{spatial\_exact}}$$
Measures the raw spatial detection capability of the table extraction engine, including cases where the correct text was extracted from the cell but the system deliberately abstained from verification due to conservative risk calibration.
