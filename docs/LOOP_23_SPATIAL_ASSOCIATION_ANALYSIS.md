# Loop 23 Spatial Association Analysis

## 1. Mechanics of Narrow-Gutter Column Bleed

In document processing, table segmentation algorithms traditionally project word occupancy across the full page height or region height:
$$P(x) = \sum_{r \in \text{rows}} \sum_{w \in r} \mathbb{I}(w.\text{left} \le x < w.\text{right})$$

When adjacent columns have:
1. Wide compound column headers (e.g. `Base Tax (INR) _ Penalty (INR)` spanning $x \in [280, 508]$), and
2. Narrow data gutters ($< 20\text{ px}$ separation in the numbers below),
the projection $P(x)$ remains strictly $> 0$ across the entire horizontal span $[280, 508]$.
As a result:
- The global table constructor cannot place a column boundary between the two columns.
- The two columns collapse into a single composite column.
- Cells in data rows inherit multiple space-separated tokens ($w_1, w_2$).

---

## 2. Localized Spatial Association Resolution

Loop 23 solves this through localized sub-column association:

### 2.1 Sub-Header Extraction
When a compound header is encountered, it is parsed into constituent sub-headers:
$$\text{SubHeaders} = \text{re.split}(r"[_|/]|(?<=[)])\s+(?=[A-Z])", \text{header\_text})$$
For example, `"Base Tax (INR) _ Penalty (INR)"` yields:
1. `"Base Tax (INR)"` (Target Index 0)
2. `"Penalty (INR)"` (Target Index 1)

### 2.2 Semantic Sub-Header Alignment
Given a target field request with `col_pattern` (e.g. `"Base Tax"`):
The algorithm matches the target pattern against the sub-headers to determine the semantic column index $k \in \{0, 1\}$.

### 2.3 Interior Gap Verification & Token Binding
Inside the composite cell, words are sorted left-to-right.
The horizontal gap between adjacent tokens is computed:
$$\text{Gap} = w_{k+1}.\text{left} - w_k.\text{right}$$
If $\text{Gap} \ge 8\text{ px}$:
The token $w_k$ is bound to the target field with high confidence ($\ge 70.0$).
If $\text{Gap} < 8\text{ px}$ or tokens are fused into an unbroken single word (e.g. `'125001250'`), the algorithm rejects the candidate and safely abstains.

---

## 3. Comparative Stability Evaluation

| Condition | Baseline Pipeline | Loop 23 Localized Spatial Association |
| :--- | :---: | :---: |
| **Separated Tokens (`ASSOC_03`, `COHORT_H_04`)** | Abstained (Unresolved bleed) | **Resolved & Verified (Exact Match)** |
| **Fused Unbroken Tokens (`COHORT_H_03`)** | Abstained | **Abstained (Safe Failure Mode)** |
| **Adversarial Empty Gutter Trap (`COHORT_H_05`)**| `PASS_EMPTY_CORRECT` | **`PASS_EMPTY_CORRECT`** |
| **False Verification Risk** | 0.00% | **0.00%** |
| **Execution Overhead** | 0.00ms | **< 0.05ms** |
