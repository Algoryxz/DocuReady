# Loop 25 - Threshold Selection & Policy Freezing

## Calibration Evidence

The operating threshold sweep was conducted across $T \in [40.0, 90.0]$ on the 30 Development and Calibration documents (100 critical fields).

- **False Verification Disappearance:** At $T \le 65.0$, one false verification occurred due to low-contrast OCR noise. At $T=70.0$, false verifications dropped to exactly zero.
- **Brier Score Minimization:** Brier score dropped from $0.0278$ at $T=40.0$ to $0.0190$ at $T=70.0$.
- **Pareto Optimal Point:** $T=70.0$ represents the exact boundary where precision reaches 100.00% while retaining the highest possible coverage (84.00%).

## Frozen Operating Policy

$$T^* = 70.0$$
$$T_{\text{fuzzy}} = 75.0$$

This policy was frozen prior to unlocking and evaluating the Blind Evaluation cohort.
