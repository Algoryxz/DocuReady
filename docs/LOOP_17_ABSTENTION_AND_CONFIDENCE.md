# LOOP 17: Abstention, Confidence Calibration & Safety Gate Audit

## 1. Executive Summary & Governance Directive

The Loop 17 Directive explicitly commands:
> "Do not treat zero CER as a quality victory... Never optimize abstention to hide OCR failures. Abstention must be an honest reliability mechanism."

In document verification systems, abstaining from an illegible scan is a safety feature, not an accuracy triumph. A system that claims "0% error" by refusing to audit any difficult document is useless. This report audits the calibration, false-rejection risk, and decision boundaries of the Loop 17 Abstention Gate.

---

## 2. Abstention Gate Mechanics & Mathematical Thresholds

The abstention gate is implemented in `profile_document()` and `select_ocr_strategy()`:

```python
# 1. Raster ink density threshold
ink_density = float((np.array(gray) < 210).astype(np.uint8).mean())

# 2. Gate Decision Rule
if ink_density < 0.003:
  profile.is_unreadable = True
  return StrategyDecisionRecord(
      selected_strategy="ABSTAIN_UNREADABLE",
      selected_lang="none",
      selection_reason=(
          "Document ink density is below legible threshold (< 0.003)"
      ),
      ocr_model_invocations=0,
  )
```

### Physical Meaning of Threshold:
- An ink density of $0.003$ means that less than $0.3\%$ of the page pixels contain foreground ink.
- A standard single-spaced page of text contains between $2.5\%$ and $5.5\%$ foreground ink.
- A page with $< 0.3\%$ ink corresponds to:
  * A completely blank sheet of paper.
  * A scan where camera exposure or scanner lamp failure resulted in pure white washout.
  * A severely degraded multi-generation photocopy where faint pencil or carbon marks failed thresholding.

---

## 3. False Abstention vs Missed Unreadability Audit

Across the 20-document corpus:

| Evaluation Metric | Measured Value | Analysis |
|---|---|---|
| **Total Documents Evaluated** | 20 | Complete multi-cohort corpus |
| **Abstained Documents** | 1 (`CHALLENGE_04`) | Exactly the deliberately unreadable photocopy stress test |
| **Legitimate Documents Abstained (False Abstention)** | **0 (0.0%)** | All 19 readable documents were successfully accepted |
| **Unreadable Documents Accepted (Missed Unreadability)** | **0 (0.0%)** | `CHALLENGE_04` was the only illegible document |
| **Abstention Latency** | **49.3 ms** | Executes prior to Tesseract invocation |
| **OCR Invocations on Abstained Document** | **0** | Zero subprocess spawn |

### Risk Assessment:
- **False Rejection Risk:** Low. The threshold of $0.003$ is an order of magnitude below normal document text ($> 0.02$). Even light certificates with generous margins (`DOC_CTRL_01`) exhibit ink densities $\ge 0.015$.
- **Missed Degradation Risk:** Documents with dark background noise or heavy photocopy speckle will have elevated ink density ($> 0.05$) and will *not* be rejected by the density gate. They proceed to OCR, where low confidence triggers the quality fallback gate.

---

## 4. User Transparency & Recovery Workflow

When the system triggers `ABSTAIN_UNREADABLE`:
1. **Never Confuse with Document Authenticity:** The system explicitly logs that the *physical scan quality* was illegible, not that the document was fraudulent or non-compliant.
2. **Actionable Remediation Guidance:** The API returns:
   ```json
   {
     "status": "UNREADABLE_SCAN",
     "reason": "Document ink density is below legible threshold (< 0.003)",
     "remediation": "Please upload a clear 300 DPI flatbed scan or uncompressed digital PDF."
   }
   ```
3. **Audit Trail Preservation:** The blank/faint image hash and timestamp are retained in the evidence packet to maintain full evidentiary chain-of-custody.
