# DocuReady Loop 32 Dataset & Benchmark Regression Report

**Programme:** DocuReady Product Excellence  
**Milestone:** Loop 32  
**Verification Script:** `research/loop31/run_independent_audit.py`  
**Execution Timestamp:** 2026-11-25T06:12:47Z  

---

## 1. Absolute Preservation of Benchmark Invariants

The Loop 32 bug fixes were rigorously evaluated against the comprehensive 221-document, 791-field empirical benchmark corpus.

### Benchmark Results
- **Total Evaluated Fields:** **791**
- **Exact Verified Claims:** **344**
- **False Verifications:** **0** (Zero false verifications across all historical cohorts)
- **Abstentions:** **447**
- **Observed Critical Field Precision:** **100.0%** ($344 / 344$)
- **Combined Coverage:** **43.49%** ($344 / 791$)

### Independent Cohort Evaluations
- **Loop 28 Cross-Document Corpus (36 packets, 92 claims):**
  - Verified Claims: **42**
  - Exact Verified: **42**
  - False Verifications: **0**
- **Cohort M Independent Real-World Corpus (30 packets, 103 claims):**
  - Verified Claims: **76**
  - Exact Verified: **76**
  - False Verifications: **0**

---

## 2. Statistical Qualification Bounds

- **Population 1 (791-Field Benchmark, $N=344$ accepted):**
  - Rule of Three Upper Risk: **0.87%** (Lower bound precision: **99.13%**)
  - Wilson Score 95% Exact CI: **[98.90%, 100.00%]**
- **Population 2 (Loop 28 Cross-Doc, $N=42$ accepted):**
  - Rule of Three Upper Risk: **7.14%** (Lower bound precision: **92.86%**)
  - Wilson Score 95% Exact CI: **[91.62%, 100.00%]**
- **Population 3 (Cohort M Independent, $N=76$ accepted):**
  - Rule of Three Upper Risk: **3.95%** (Lower bound precision: **96.05%**)
  - Wilson Score 95% Exact CI: **[95.19%, 100.00%]**
