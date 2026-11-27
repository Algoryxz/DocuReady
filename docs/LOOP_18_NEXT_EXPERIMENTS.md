# LOOP 18: Roadmap for Future Research & Engineering Experiments

## 1. Executive Summary

Based on the empirical findings, adversarial stress results, and benchmark integrity audit conducted in Loop 18, we outline prioritized technical experiments for subsequent research loops.

---

## 2. Prioritized Experiment Backlog

### Experiment 1: Pre-OCR Tabular Structure & Cell Boundary Detection
- **Motivation**: `STRESS_03_MULTICOLUMN_EMBEDDED_AMOUNTS` demonstrated that when numerical values are aligned horizontally in borderless columns, bounding box clustering occasionally merges adjacent cells.
- **Hypothesis**: Applying a morphological line detector (horizontal/vertical kernel dilation) to segment tabular cells prior to OCR will eliminate cross-column character bleed and increase multi-column critical-field extraction from 50% to > 90%.
- **Target Metric**: Critical-field exact match rate on tabular ledgers.

### Experiment 2: Automated Skew Detection & Rotation Normalization
- **Motivation**: `STRESS_04_SKEW_LOW_CONTRAST` showed that a 2.8° scan tilt causes minor baseline wander and degrades character recognition.
- **Hypothesis**: Implementing a fast Radon or Hough transform deskew step (constrained to < 100 ms runtime) will normalize document orientation before Tesseract binarization, recovering field accuracy on tilted scans.
- **Target Metric**: Field CER < 1.0% on scans tilted up to 5.0°.

### Experiment 3: Institutional Checksum & Format-Aware ID Disambiguation
- **Motivation**: `STRESS_01_SIMILAR_DIGIT_CONFUSION` proved that offline OCR models without dictionary priors confuse `1`, `I`, and `l` in random alphanumeric strings.
- **Hypothesis**: Integrating institution-specific validation rules (e.g., PAN checksum, PPO format syntax, Verhoeff checksum) will allow the rules engine to automatically correct single-character glyph confusions deterministically.
- **Target Metric**: Zero uncorrected character confusions on formatted civil ID numbers.

### Experiment 4: Multi-Channel Ink Filtering for Stamp De-occlusion
- **Motivation**: While translucent blue stamps (`STRESS_02`) did not disrupt OCR, opaque or dark rubber stamps can obscure text.
- **Hypothesis**: A targeted color-space transformation (filtering out blue, purple, and magenta ink channels in HSV space before binarization) will clean rubber stamp interference while preserving underlying black toner.
