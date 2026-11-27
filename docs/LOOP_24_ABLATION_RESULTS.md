# LOOP 24 — ABLATION EXPERIMENTS & SYSTEM COMPONENT ATTRIBUTION

## 1. Experimental Setup

To isolate the specific contribution of each engineering component introduced or refined in Loops 23 and 24, four distinct ablation variants were evaluated across the 30-document Cohort I dataset:

1. **Ablation 1: No Decimal / Glyph Morphology**:
   - Disables `refine_cell_decimal_point`. Reverts strictly to raw Tesseract string extraction.
2. **Ablation 2: No Narrow-Gutter Disambiguation**:
   - Disables `resolve_narrow_gutter_cell_token`. Multi-token cells are not decomposed.
3. **Ablation 3: Low-Threshold Policy ($T=50.0$)**:
   - Reduces the verification confidence floor from $T^*=70.0$ to $T=50.0$.
4. **Ablation 4: Full Loop 24 Baseline ($T^*=70.0$, Lazy Refinement, Narrow Gutter, Decimal Recovery)**.

---

## 2. Quantitative Ablation Comparison

| Configuration | Verified Claims | Exact Matches | False Verifications | Abstentions | Critical Field Precision | Coverage (%) | Mean Overhead |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Ablation 1 (No Decimal Morphology)** | 19 | 18 | 1 (`v91_vol=100`) | 83 | 94.74% | 18.63% | 1.88 ms |
| **Ablation 2 (No Narrow Gutter Resolution)**| 17 | 17 | 0 | 85 | 100.00% | 16.67% | 1.89 ms |
| **Ablation 3 (Low Threshold T=50)** | 27 | 25 | 2 | 75 | 92.59% | 26.47% | 1.90 ms |
| **Full Baseline (Loop 24 Production)** | **19** | **19** | **0** | **83** | **100.00%** | **18.63%** | **1.90 ms** |

---

## 3. Analysis & Key Takeaways

1. **Decimal Morphology is Essential for Safety**: Without isolated baseline dot recovery, `10.0` was read as `100`, introducing a severe decimal truncation error in pharmaceutical batch auditing.
2. **Narrow Gutter Resolution Adds Valid Coverage**: Resolving adjacent sub-columns without bleed recovered valid claims that otherwise had to be rejected as multi-token ambiguities.
3. **High Threshold ($T=70$) Guarantees Zero False Verifications**: Dropping $T$ to 50 increased raw coverage by ~8 percentage points but allowed 2 false verifications to pollute the verified claims, violating DocuReady's non-negotiable safety mandate.
