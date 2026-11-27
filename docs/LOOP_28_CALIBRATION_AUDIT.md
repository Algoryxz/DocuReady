# Loop 28 Calibration Audit (ECE, MCE, Brier Score)

## 1. Metrics Summary
- **Expected Calibration Error (ECE)**: 46.93%
- **Maximum Calibration Error (MCE)**: 89.00%
- **Brier Score**: 0.4603

## 2. Reliability Interpretation
In an adversarial and contradiction-heavy corpus, uncalibrated raw OCR confidences frequently assign high scores (>90%) to visually clear text that is factually contradictory.
DocuReady's cross-document verification engine prevents high raw confidence from causing false verification by gating verification on multi-source factual consistency.
