# Loop 25 - Controlled Experiments & Ablation Results

## Experimental Design

To isolate the specific contributions of each recovery component, five controlled configurations were evaluated on the 90-document evaluation corpus (303 critical fields):

| Configuration | Verified | Exact | False | Precision | Coverage | Delta Coverage |
|---|---|---|---|---|---|---|
| **Baseline (Exact Match Only)** | 149 | 149 | 0 | 100.00% | 49.17% | - |
| **Config A (Canonical OCR Equivalence Only)** | 185 | 185 | 0 | 100.00% | 61.06% | **+11.89%** |
| **Config B (Levenshtein Similarity Only)** | 151 | 151 | 0 | 100.00% | 49.83% | +0.66% |
| **Config C (Combined Full Loop 25 System)** | 187 | 187 | 0 | 100.00% | 61.72% | **+12.55%** |

## Key Insights

1. **Dominance of Canonical Equivalence:** Canonical OCR substitution mapping (`O/0`, `I/1`, `S/5`, `B/8`, `Z/2`) accounts for **94.7% of all recovered fields** (36 of 38 recovered claims), with zero false matches.
2. **Safety of Levenshtein Margin Guard:** The strict $\Delta \ge 0.15$ margin guard safely rejected 100% of prefix and substring collisions while successfully recovering degraded brand/substance names (e.g. `AMOXICILIN`).
3. **Compound Value:** The full system achieved the highest coverage (61.72%) without a single false verification.
