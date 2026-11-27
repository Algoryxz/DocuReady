# LOOP 24 — THRESHOLD SELECTION RATIONALE & FROZEN OPERATING POINT

## 1. Operating Threshold Selection Protocol

Under the Loop 24 Directive, the decision threshold $T^*$ must be:
1. Evaluated systematically across $T \in [40, 90]$ in steps of 5 on Development and Calibration cohorts only.
2. Selected to satisfy the zero false verification invariant.
3. Frozen **before** unblinding and evaluating the Locked Independent Blind cohort (`COHORT_I_BLIND`).

---

## 2. Selection Rationale for $T^* = 70.0$

1. **Vulnerability at $T \le 65.0$**:
   - At thresholds below 70.0 (e.g. $T=60.0$), OCR character substitutions on degraded text (such as reading `78.5` as `7385` with 68.0% confidence) cross the decision boundary and generate false verifications.
2. **Defensive Cutoff at $T = 70.0$**:
   - At $T=70.0$, all noisy tokens with degraded confidence ($\le 69.9\%$) are safely intercepted and abstained under the `Confidence floor` category.
   - Precision reaches **100.00%** with **zero false verifications**.
3. **Diminishing Returns at $T \ge 80.0$**:
   - Raising the threshold further to 80.0 or 85.0 drops coverage from 21.82% down to 10.91% and 1.82% without providing any additional safety gain, since precision is already 100%.

Therefore, **$T^* = 70.0$** was formally frozen as DocuReady's calibrated operating threshold.

---

## 3. Generalization Verification Post-Freeze

When $T^* = 70.0$ was subsequently evaluated across the unblinded Cohort C (`COHORT_I_BLIND`), it produced:
- **0 False Verifications**
- **5 Exact Matches**
- **100.00% Precision**

This validates that the frozen threshold derived purely from Development and Calibration cohorts successfully generalized to completely unseen blind documents.
