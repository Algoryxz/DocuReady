# DOCUREADY — BENCHMARK GOVERNANCE & PROVENANCE STANDARD
## Rules for Dataset Integrity, Metric Rigor, Provenance & Experimentation

**Project:** DocuReady  
**Effective Date:** Loop 12 / Post-HackNation 2026  
**Scope:** All future research, benchmark suites, evaluation harnesses, and experimental validation branches.  

---

## 1. PURPOSE & CORE PRINCIPLE

A benchmark is not independent because it lives in a separate directory, a different branch, or bears a public dataset title. A benchmark is independent **only when its physical provenance, labels, comparison logic, execution environment, and failure classifications survive adversarial scrutiny.**

**The Golden Rule of DocuReady Benchmarking:**  
*Measure reality. Never manufacture confidence. Correct the ruler before measuring the system.*

---

## 2. DATASET TAXONOMY & PROVENANCE TIERS

Every document dataset introduced into DocuReady must be explicitly labeled with one of the following five mutually exclusive provenance tiers:

### Tier 1: `VERIFIED_EXTERNAL_OFFICIAL`
- **Definition:** Raw images or PDFs downloaded directly from official, authoritative public benchmark releases (e.g., Hugging Face, ICDAR official competition mirrors, University archives).
- **Requirements:** Must include exact upstream source URL, download timestamp, official release version, license terms, and SHA-256 checksums matching upstream manifests.
- **Restrictions:** Must respect commercial and redistribution licenses. Never commit copyrighted external datasets directly to source control if redistribution is prohibited.

### Tier 2: `VERIFIED_EXTERNAL_DERIVED`
- **Definition:** Documents derived from official public benchmarks via deterministic, documented transformations (e.g., cropping, resizing, rotation, format conversion).
- **Requirements:** Transformation scripts must be checked into the repository with fixed random seeds and verifiable input-output SHA-256 mappings.

### Tier 3: `VERIFIED_SYNTHETIC_MODEL`
- **Definition:** Synthetic documents created locally by programmatic generators (e.g., ReportLab, PIL, WeasyPrint) modeled after public dataset schemas or domain document types.
- **Requirements:** 
  1. Must be explicitly labeled as **SYNTHETIC** in all reports and manifests.
  2. Generator function and random seed must be documented.
  3. Ground-truth annotations must be generated simultaneously with rendering coordinates.
  4. Fonts must be verified to render all target glyphs (no fallback to Latin substitutions).

### Tier 4: `VERIFIED_INTERNAL_FIXTURE`
- **Definition:** Curated unit test fixtures, golden baseline packets, and regression artifacts crafted specifically for regression testing of DocuReady's engine.
- **Requirements:** Zero real PII. Fully committed under `tests/fixtures/`.

### Tier 5: `UNVERIFIED` (Prohibited in Benchmarks)
- Any dataset lacking origin tracking, generator functions, or checksums. Prohibited from being cited in engineering evaluations.

---

## 3. CORPUS SPLIT GOVERNANCE

All benchmark corpora must maintain strict, immutable splits to prevent data leakage:

1. **Development Set (`DEV` — 40%):** Available for exploratory analysis, parameter tuning, threshold calibration, and prompt/heuristic iteration.
2. **Validation Set (`VAL` — 30%):** Evaluated periodically to measure generalization and prevent overfitting to `DEV`.
3. **Challenge / Sealed Test Set (`CHALLENGE` — 30%):** Evaluated only once per engineering loop. Never inspected manually or tuned against directly.

---

## 4. METRIC INTEGRITY MANDATES

### 4.1 Strict Anti-Hardcoding Rule
- **Zero Simulated Metrics:** Under no circumstances may any evaluation runner simulate, approximate, or hardcode metric values (e.g., `table_ious.append(0.85)`).
- **Automated CI Guard:** Continuous integration must include static analysis checks that fail the build if constant floats are appended to metric accumulators.

### 4.2 Target Alignment Rule
- **String-to-String Scope Parity:** Levenshtein distance metrics (CER, WER) must compare strings of equivalent scope:
  - Page-level OCR text must only be compared against full-page ground truth text.
  - Field-level values (e.g., dates, amounts, names) must only be compared against targeted extracted field values.
  - Comparing a 20-character entity string against a 500-character page dump is strictly prohibited.

### 4.3 Unicode Normalization Mandate
- All strings must be normalized to Unicode **NFC** before computing character distances or evaluating token matches.

### 4.4 Real Geometric IoU Mandate
- Layout bounding box metrics must use bipartite greedy or Hungarian matching with exact intersection-over-union calculations. Degenerate or inverted bounding boxes must yield an IoU of 0.0.

### 4.5 Denominator Audit Rule
- All aggregations must verify that:
  $$\text{Total Evaluated} = \text{Passed} + \text{Failed} + \text{Abstained} = \text{Manifest Sample Count}$$
- Silent drops, skipped exceptions, or survivorship bias in denominators are strictly forbidden.

---

## 5. EXPERIMENTAL QUALIFICATION PROTOCOL

For an engineering experiment to qualify as valid evidence:
1. **Reproducibility:** A single CLI script must reproduce the reported results within $\pm 2\%$ tolerance.
2. **Control vs. Treatment:** Any proposed optimization must be evaluated against a qualified baseline on identical document inputs.
3. **No Regressions:** Must demonstrate zero degradation on existing golden baselines.
