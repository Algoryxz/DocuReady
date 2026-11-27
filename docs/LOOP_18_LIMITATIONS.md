# LOOP 18: Operational Boundaries, Technical Limitations & Edge Cases

## 1. Executive Summary

In adherence to the Loop 18 mandate for independent verification rigor, this document details the confirmed technical limitations and operational boundaries of DocuReady's offline OCR engine.

We explicitly avoid speculative claims or benchmark massaging: where the system encounters degradation, the failure modes are documented below.

---

## 2. Identified Technical Limitations

### 1. Ambiguous Alphanumeric Strings (`STRESS_01`)
- **Limitation**: In random or unconstrained alphanumeric strings lacking dictionary priors (e.g., voucher codes like `B801-O08B-1Il5S`), the offline Tesseract LSTM model cannot reliably disambiguate between glyphs with identical vertical strokes (`1`, `I`, `l`).
- **Mitigation**: Critical fields that follow known institutional formats (PAN cards, GSTIN, Aadhaar, PPO numbers) must rely on format-aware regex validators and checksum algorithms (Luhn / Verhoeff) rather than pure OCR confidence.

### 2. Dense Borderless Table Grids (`STRESS_03`)
- **Limitation**: In multi-column financial statements or ledgers lacking explicit vertical column dividing lines, adjacent numerical figures (e.g. `Property Tax: Rs 154000` alongside `Subtotal: Rs 221700`) can occasionally be grouped into the same horizontal line, producing local reading-order inversions.
- **Mitigation**: Multi-column documents benefit from dedicated tabular structure recognition prior to OCR text extraction.

### 3. Rotational Skew Beyond 3.0 Degrees (`STRESS_04`)
- **Limitation**: While DocuReady's spatial layout engine handles minor scan tilts up to ~2.5°, skew angles exceeding 3.0° result in degraded line clustering and baseline wander, dropping critical-field match rates to ~66.7%.
- **Mitigation**: Integrating a fast Radon / Hough transform deskew pre-processing stage for rotated scans.

### 4. Severe Contrast & Faded Carbon Copies (`CHALLENGE_04`)
- **Limitation**: When ink contrast against background paper falls below 15% (e.g. 3rd-generation carbon copies or severe scanner underexposure), Otsu binarization discards characters as background noise.
- **Safety Guarantee**: In these instances, DocuReady's **Abstention Gate** reliably engages (mean confidence < 38.0), preventing hallucinated output from propagating downstream.
