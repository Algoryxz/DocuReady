# Loop 31 — Deliverable 8: Packet-Clustered Statistical Analysis & Multi-Population Bounds

## 1. Distinction Between Evaluated Populations
To avoid conflating single-document field extraction with multi-document cross-verification, Loop 31 establishes separate statistical accounting across three distinct evaluation populations:

1. **Population 1: Single-Document Critical Fields ($N = 344$ verified / $791$ total)**
   - Context: Standalone forms, invoices, and ID cards evaluated individually.
2. **Population 2: Loop 28 Multi-Document Claims ($N = 42$ verified / $92$ total across $36$ packets)**
   - Context: Cross-document corroboration across 2–4 documents per packet.
3. **Population 3: Cohort M Synthetic Generalization Claims ($N = 76$ verified / $103$ total across $30$ packets)**
   - Context: Cross-document trade, clinical, and corporate packets.

---

## 2. Statistical Uncertainty Quantification

| Population | Sample Size ($n$) | Errors ($k$) | Clustered Bootstrap 95% CI | Hanley-Joplin Rule of Three (95% Risk Bound) | Wilson Score 95% Exact CI |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Pop 1: Field-Level (344 Verified)** | 344 | 0 | `[100.0%, 100.0%]` *(degenerate)* | **$\le 0.87\%$ Upper Risk** (Precision $\ge 99.13\%$) | **`[98.90%, 100.0%]`** |
| **Pop 2: L28 Claims (42 Verified)** | 42 | 0 | `[100.0%, 100.0%]` *(degenerate)* | **$\le 7.14\%$ Upper Risk** (Precision $\ge 92.86\%$) | **`[91.62%, 100.0%]`** |
| **Pop 3: Cohort M (76 Verified)** | 76 | 0 | `[100.0%, 100.0%]` *(degenerate)* | **$\le 3.95\%$ Upper Risk** (Precision $\ge 96.05\%$) | **`[95.19%, 100.0%]`** |
| **L28 Packets (21 Verified)** | 21 | 0 | `[100.0%, 100.0%]` *(degenerate)* | **$\le 14.29\%$ Upper Risk** (Precision $\ge 85.71\%$) | **`[84.05%, 100.0%]`** |
| **L28 Claim Coverage (92 Claims)** | 92 | — | **`[32.18%, 58.42%]`** | N/A | `[35.81%, 55.83%]` |
| **L28 Packet Coverage (36 Packets)**| 36 | — | **`[41.67%, 75.00%]`** | N/A | `[42.23%, 72.88%]` |

---

## 3. Methodological Audit: The Degenerate Bootstrap Interval

### Why the Bootstrap Precision Interval Collapses to `[100.0%, 100.0%]`
In any non-parametric bootstrap resampling procedure, sample packets are drawn with replacement from the observed empirical dataset.
Because the observed dataset contains **zero false verifications** ($k = 0$), every possible resampled batch drawn will necessarily contain only packets with zero false verifications.
Consequently:
$$\forall b \in \{1, \dots, B\}, \quad \text{Precision}^{(b)} = \frac{\text{Exact}^{(b)}}{\text{Verified}^{(b)}} \equiv 1.000$$
The resulting empirical sampling distribution has variance $\sigma^2 = 0$, causing both the 2.5th and 97.5th percentiles to equal exactly $100.0\%$.

### Scientific Sign-off & Risk Disclosure
Claiming zero prospective risk based on $[100\%, 100\%]$ is a statistical fallacy.
By applying the **Hanley-Joplin Rule of Three** and the **Wilson Score Exact Inversion**:
- For the 344-field population, we can state with 95% confidence that the true underlying error rate is at most **$0.87\%$** (precision is between **$98.90\%$** and **$100.0\%$**).
- For the 42-claim Loop 28 cross-document population, the true error rate is at most **$7.14\%$** (precision is between **$91.62\%$** and **$100.0\%$**).
- For the 76-claim Cohort M population, the true error rate is at most **$3.95\%$** (precision is between **$95.19\%$** and **$100.0\%$**).

This provides sound, defensible statistical sign-off.
