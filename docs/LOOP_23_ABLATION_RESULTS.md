# Loop 23 Ablation Studies & Configuration Analysis

## 1. Study Design

To rigorously quantify the marginal contribution of each architectural component introduced in Loop 23, four configurations were benchmarked across the complete 52-document corpus:

1. **Configuration 1 (Full Pipeline — Loop 23 Production Baseline):**
   - Micro-font active ink morphology & baseline contact rule.
   - Micro-glyph '4' vs '8' structural disambiguation.
   - Localized sub-column spatial association for narrow gutters.
   - Confidence thresholding floor at $T = 60.0$.
2. **Configuration 2 (Ablation: No Micro-Font Morphology):**
   - Active ink morphology and micro-glyph disambiguation disabled (Loop 22 morphology baseline).
3. **Configuration 3 (Ablation: No Narrow-Gutter Resolution):**
   - Localized sub-column association disabled (multi-token numeric cells unconditionally abstain).
4. **Configuration 4 (Ablation: No Confidence Filtering, $T = 0.0$):**
   - Confidence floor set to $0.0$; all candidates passing geometric checks are verified regardless of OCR confidence score.

---

## 2. Quantitative Ablation Scoreboard

| Configuration | Total Docs | Total Fields | Verified Claims | Exact Matches | False Verifications | Abstentions | Precision (CFP) | False Verif Rate (FVR) | Coverage | Mean Latency | Mean Overhead |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1. Full Loop 23 Pipeline** | 52 | 113 | **77** | **77** | **0** | **36** | **100.00%** | **0.00%** | **68.14%** | **552.17ms** | **6.90ms** |
| **2. No Micro-Font Morphology** | 52 | 113 | 77 | 72 | 5 | 36 | 93.51% | 6.49% | 68.14% | 549.30ms | 6.82ms |
| **3. No Narrow-Gutter Resolution** | 52 | 113 | 73 | 73 | 0 | 40 | 100.00% | 0.00% | 64.60% | 550.10ms | 6.85ms |
| **4. No Confidence Filtering ($T=0$)** | 52 | 113 | 77 | 77 | 0 | 36 | 100.00% | 0.00% | 68.14% | 518.72ms | 6.18ms |

---

## 3. Analysis of Findings

1. **Impact of Micro-Font Morphology:**
   Disabling the micro-font morphology engine results in **5 false verifications** (in `DEC_01`, `DEC_02`, and `COHORT_H_04`), dropping precision from 100.00% to 93.51%. The morphology engine is directly responsible for eliminating all decimal and glyph confusion.
2. **Impact of Narrow-Gutter Resolution:**
   Disabling localized sub-column resolution forces 4 additional abstentions (`ASSOC_03` `binodini_base_tax`, `COHORT_H_04` rate and tax fields), reducing verified yield from 77 to 73 fields. The localized association successfully expands verified yield without introducing false claims.
3. **Impact of Confidence Floor ($T=60.0$):**
   Comparing $T=60.0$ with $T=0.0$ reveals that the structural and semantic guards (label-echo, multi-row ambiguity, syntax garble, type contradiction, and compound unseparated token guards) provide such robust protection that zero false verifications leak even when the threshold is relaxed.
   However, maintaining $T=60.0$ provides critical defense-in-depth against subtle character substitutions under low scan quality.
