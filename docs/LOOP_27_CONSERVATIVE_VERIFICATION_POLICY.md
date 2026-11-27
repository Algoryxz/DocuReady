# DOCUREADY LOOP 27 — CONSERVATIVE VERIFICATION POLICY
## Risk-Calibrated Abstention Over High-Confidence False Verification

---

### 1. Fundamental Verification Invariants
1. **Raw OCR confidence alone is insufficient for verification**: High OCR confidence (>90%) frequently accompanies visually plausible OCR misrecognitions (such as `O` for `0`).
2. **Structural validation is mandatory for structured identifiers**: Any identifier that violates its formal grammar MUST ABSTAIN.
3. **Ambiguity gating strictly supersedes verification**: If a candidate matches a known glyph confusable pattern that cannot be corroborated, the system emits `ABSTAIN` with an explicit reason.
4. **Mutually Exclusive Accounting**:
   $$T = E + F + A$$
   $$V = E + F$$
   $$\text{Precision} = \frac{E}{V}, \quad \text{FVR} = \frac{F}{V}, \quad \text{Coverage} = \frac{V}{T}$$
