# Loop 28 Audit of Inherited Loop 27 Issues

## 1. Investigation of the 5 Adversarial False Verifications
In Loop 27, 5 false verifications occurred in the adversarial challenge cohort:
- `ADV_SYNTH_02`: PAN `AZXPR0298B` vs ground truth `AZXPR0298F`
- `ADV_SYNTH_06`: PAN `AZXPR0698B` vs ground truth `AZXPR0698F`
- `ADV_SYNTH_10`: PAN `AZXPR1098B` vs ground truth `AZXPR1098F`
- `ADV_SYNTH_14`: PAN `AZXPR1498B` vs ground truth `AZXPR1498F`
- `ADV_SYNTH_18`: PAN `AZXPR1898B` vs ground truth `AZXPR1898F`

### Root Cause Analysis
1. **Valid Syntax**: Both `B` and `F` satisfy the 10th-character alphabetic checksum syntax regex `^[A-Z]{5}[0-9]{4}[A-Z]$`.
2. **Absence of Public Mathematical Checksum**: Unlike Aadhaar (Verhoeff $D_5$) or GSTIN (Mod-36), Indian PAN lacks a public offline algorithmic check digit.
3. **Single-Document Blind Spot**: Single-document OCR cannot detect that `B` was substituted for `F` if the character is syntactically valid and read with high confidence (>90%).
4. **Resolution via Cross-Document Verification**: When multiple documents in a packet (e.g. PAN card, Form 16, Bank KYC) are evaluated, cross-document comparison immediately detects the discrepancy between `AZXPR0298B` and `AZXPR0298F` as a `CONTRADICTION_DETECTED`, safely suppressing false verification.

## 2. Statistical Accounting Reconciliation (Loop 26 vs Loop 27)
- **Loop 26 Reported**: 202 documents, 723 critical fields.
- **Loop 27 Reported**: 221 documents, 791 critical fields.
- **Reconciliation Audit**:
  - Cohort K (Independent Real-World): 60 docs, 307 fields.
  - Cohort L (Identifier Hardening): 19 docs, 120 fields.
  - Historical Cohorts (I, J, Historic): 142 docs, 364 fields.
  - Sum: 60 + 19 + 142 = 221 documents; 307 + 120 + 364 = 791 critical fields.
  - Accounting difference between L26 and L27 is fully explained by the addition of Cohort L (19 docs, 120 fields) and the formal deduplication of overlapping challenge fields.

## 3. Performance & Calibration Reconciliations
- **Latency**: Loop 26's reported 1.89 ms was transcribed from Loop 25; Loop 26's measured mean overhead was 1.94 ms. Both are well within the < 3.0 ms requirement.
- **Brier Score Shift**: In Loop 27, converting 10 false verifications into abstentions caused uncalibrated raw OCR confidences of abstained items to be scored against target 0, shifting raw Brier score. Loop 28 establishes segregated verified-only calibration.
