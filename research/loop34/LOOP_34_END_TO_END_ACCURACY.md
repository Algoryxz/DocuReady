# DOCUREADY — LOOP 34 END-TO-END ACCURACY REPORT

**Milestone:** Loop 34  
**Date:** 2026-11-26  
**Operating Thresholds:** $T^* = 70.0$, $T_{\text{fuzzy}} = 75.0$  

---

## 1. End-to-End Decision & Verification Summary

| Metric | Measured Value | Standard / Invariant | Status |
| :--- | :---: | :---: | :---: |
| **Total Critical Fields** | 307 | 60 Documents | Complete |
| **Verified Exact Claims** | 291 | Ground-truth match | **PASS** |
| **False Verifications** | **0** | Zero tolerance | **PASS** |
| **Abstention Count** | 16 | Calibrated risk avoidance | **PASS** |
| **Coverage Rate** | **94.79%** | Realistic real-world target | **PASS** |
| **Precision Rate** | **100.0%** | Zero false verifications | **PASS** |
| **Wilson Score 95% Confidence Interval** | **[98.7%, 100.0%]** | Statistical rigor | **PASS** |
| **Rule of Three Maximum Upper Risk** | **1.03%** | $3/N$ bound | **PASS** |

---

## 2. Error Propagation & Calibration Invariants

1. **OCR to Decision Isolation:** OCR character ambiguity is caught by syntax masks and confusable detection in Stage 4 before rule evaluation.
2. **Weakest-Evidence Safety:** When evidence confidence is sub-$T^*$ ($< 70.0$) or ambiguous, the Decision Safety Layer forces outcome `REVIEW`.
3. **No Unsupported Clearances:** Under real-world degradation, coverage gracefully degrades to abstention, protecting the applicant from wrongful rejection and the portal from wrongful clearance.
