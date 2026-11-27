# DOCUREADY — LOOP 34 LIMITATIONS & UNSUPPORTED REAL-WORLD CONDITIONS

**Milestone:** Loop 34  
**Date:** 2026-11-26  

---

## 1. Explicitly Unsupported Document Conditions

In strict adherence to scientific and engineering honesty, DocuReady discloses the following unsupported conditions:

1. **Unconstrained Cursive Handwriting:**
   - DocuReady is an engine for printed and semi-structured government certificates, circulars, receipts, and forms.
   - Freeform handwritten notes and unconstrained cursive signatures are **strictly unsupported** for automated verification. When encountered, the system safely abstains with `Status.REVIEW`.
2. **Severe Physical Damage (> 40% Torn / Water Damaged):**
   - Documents with torn text blocks or severe ink bleed-through fail legibility checks (`RULE-DOC-02`), prompting mandatory human scanning re-upload.
3. **Extreme Low Resolution (< 150 DPI):**
   - Scans below 150 DPI lack sufficient pixel density for reliable Devanagari and Odia ligature separation. The engine abstains rather than inventing characters.
4. **Non-Supported Languages:**
   - Languages outside English, Hindi, and Odia (e.g. Tamil, Telugu, Bengali) are unsupported in the current release and trigger `SCRIPT_UNSUPPORTED` abstention.
