# Loop 22 — Comparative Evaluation: Loop 21 vs Loop 22

**Comparison Scope:** Direct Matched Cohort (40 Documents) and Full Benchmark (46 Documents)  
**Historical Commit:** Loop 21 (`4a6a46e`)  
**Research Commit:** Loop 22 (`HEAD`)

---

## 1. Direct Matched Cohort Comparison (40 Common Documents, 83 Critical Fields)

To isolate algorithm changes from dataset expansion, the table below compares performance strictly on the identical 40 documents evaluated in Loop 21:

| Metric | Loop 21 Baseline | Loop 22 Matched | Delta ($\Delta$) | Impact Assessment |
| :--- | :---: | :---: | :---: | :--- |
| **Total Critical Fields** | 83 | 83 | 0 | Identical denominator |
| **Verified Claims** | 73 | 62 | -11 | Risk-calibrated abstentions on degraded cells |
| **Verified Exact Matches** | 59 | 59 | 0 | Exact matches preserved |
| **False Verifications** | **14** | **3** | **-11 (-78.6%)** | **Massive reduction in dangerous false claims** |
| **Abstentions** | 10 | 21 | +11 | Transparent human review triggers |
| **Critical Field Precision (CFP)** | **80.82%** | **95.16%** | **+14.34%** | **Near-flawless trust on verified claims** |
| **False Verification Rate (FVR)** | **19.18%** | **4.84%** | **-14.34%** | **Down by nearly four-fifths** |
| **Coverage Rate** | 87.95% | 74.70% | -13.25% | Healthy trade-off eliminating 11 errors |
| **Mean Latency** | 539.29 ms | 511.45 ms | -27.84 ms | 5.2% faster execution |
| **Mean Grid Overhead** | 2.23 ms | 2.05 ms | -0.18 ms | Well below $< 3.0$ ms budget |

---

## 2. Full Benchmark Comparison (Including Cohort G)

| Metric | Loop 21 (40 Docs) | Loop 22 Full (46 Docs) | Assessment |
| :--- | :---: | :---: | :--- |
| **Total Documents** | 40 | **46** | +6 Adversarial stress fixtures |
| **Total Critical Fields** | 83 | **95** | +12 Challenging critical fields |
| **Spatial Exact Matches (SEM)** | 62 (74.70%) | **75 (78.95%)** | +4.25% overall spatial accuracy |
| **Verified Claims** | 73 (87.95%) | **70 (73.68%)** | Risk-calibrated coverage |
| **Verified Exact Matches** | 59 | **67** | +8 more verified exact values |
| **False Verifications** | **14 (19.18%)** | **3 (4.29%)** | **77.6% reduction in FVR** |
| **Critical Field Precision** | **80.82%** | **95.71%** | **+14.89% precision gain** |
| **Mean Pipeline Latency** | 539.29 ms | **507.71 ms** | Consistent sub-second performance |
| **Mean Table Overhead** | 2.23 ms | **2.03 ms** | Zero computational bloat |

---

## 3. Cohort Precision Evolution

```
Cohort Precision Comparison (L21 -> L22):
  A (Development)   :  93.75% -> 100.00%  (+6.25%)
  B (Validation)    : 100.00% -> 100.00%  (Stable 100%)
  C (Blind General) :  71.43% -> 100.00%  (+28.57%)
  D (Challenge)     :  36.36% -> 100.00%  (+63.64%)
  E (Hierarchical)  : 100.00% -> 100.00%  (Stable 100%)
  F (Decimal)       : 100.00% ->  66.67%  (3 low-res OCR limits)
  G (Adversarial)   :    N/A  -> 100.00%  (New Cohort)
```
Across 6 out of 7 cohorts, Loop 22 achieves a **perfect 100.00% precision rate with zero false verifications**.
