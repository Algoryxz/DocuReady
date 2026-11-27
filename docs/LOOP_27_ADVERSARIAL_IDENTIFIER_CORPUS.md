# DOCUREADY LOOP 27 — ADVERSARIAL IDENTIFIER CORPUS
## Evaluation of 44 Systematic Adversarial Perturbations

---

### 1. Corpus Design & Composition
The Adversarial Identifier Corpus (`research/loop27/corpus/adversarial_identifier_corpus.json`) contains 44 meticulously crafted fixtures:
- 10 IFSC perturbations (O/0 confusions, length mutations, valid baselines)
- 10 PAN perturbations (prefix digits, numeric alphas, suffix digits)
- 8 Bank account perturbations (letter bleed, truncation)
- 4 Aadhaar check-digit mutations (Verhoeff single-digit errors, transpositions)
- 6 Punctuation and trailing bleed fixtures
- 6 Multi-token and garble edge fixtures

---

### 2. Ablation Comparison Across Policy Configurations

| Policy Mode | Evaluated ($T$) | Verified ($V$) | Exact ($E$) | False ($F$) | Precision | FVR | Coverage | 95% Risk Bound |
|---|---|---|---|---|---|---|---|---|
| Baseline (Loop 26) | 44 | 44 | 4 | 40 | 9.09% | 90.91% | 100.00% | 96.41% |
| Syntax-Only | 44 | 19 | 4 | 15 | 21.05% | 78.95% | 43.18% | 91.49% |
| Ambiguity + Syntax | 44 | 16 | 11 | 5 | 68.75% | 31.25% | 36.36% | 55.60% |
| **Full Policy (Loop 27)** | **44** | **16** | **11** | **5** | **68.75%** | **31.25%** | **36.36%** | **55.60%** |
