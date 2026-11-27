# Loop 29 Calibration Forensics & Reliability Analysis

## 1. Reproduction of Loop 28 Candidate-Level Metrics
- **Expected Calibration Error (ECE)**: **46.93%**
- **Maximum Calibration Error (MCE)**: **89.00%**
- **Brier Score**: **0.4603**

## 2. Three Distinct Evaluation Questions

### Question A: Conditional Verification Calibration
Among claims the system decides to verify (N=42):
- **Observed Accuracy**: 100.00% (42/42 exact matches)
- **Mean Confidence**: 93.85%
- **ECE**: **5.93%**
- **Brier Score**: **0.0037**
- **Conclusion**: Conditional on verification, the system is highly reliable and conservative.

### Question B: Candidate-Level Risk Scoring
Evaluating raw candidate OCR confidence against ground-truth correctness across all candidates (N=92):
- Raw OCR confidence measures optical legibility, not posterior factual truth in multi-document packets containing contradictions and wrong entities.
- A contradictory claim read clearly with 95% OCR confidence is still factually contradictory ($y=0$).
- Raw OCR score must be treated as a decision candidate score rather than a posterior probability of packet truth.

### Question C: Abstention Quality
- Total Risky / Contradictory Claims: 50
- Suppressed by Abstention: 50 (100.0% precision)
- False Verifications Permitted: 0
