# Loop 30 — Ablation Study Reproduction & Component Attribution

## 1. Executive Summary
This document provides the independent reproduction of the 10-mode ablation study evaluating the attribution and safety necessity of each component in DocuReady's multi-document verification architecture.

The study was evaluated across both the **Loop 28 Corpus** (36 packets, 92 claims) and the **Independent Cohort M Corpus** (30 packets, 103 claims).

---

## 2. Quantitative Ablation Results

### A. Loop 28 Corpus (36 Packets / 92 Claims)

| Mode | Evaluated Claims | Verified Claims | Exact Matches | False Verifications | Precision | Coverage | Packet False |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Mode A: Naive Baseline** | 92 | 92 | 42 | 50 | 45.65% | 100.00% | 30 |
| **Mode B: Entity Resolution Only** | 92 | 89 | 42 | 47 | 47.19% | 96.74% | 27 |
| **Mode C: Independence Only** | 92 | 54 | 27 | 27 | 50.00% | 58.70% | 27 |
| **Mode D: Contradiction Only** | 92 | 58 | 39 | 19 | 67.24% | 63.04% | 13 |
| **Mode E: Conservative Abstention Only** | 92 | 53 | 30 | 23 | 56.60% | 57.61% | 23 |
| **Mode F: Full Policy (Production)** | **92** | **42** | **42** | **0** | **100.00%** | **45.65%** | **0** |
| **Mode G: LOO-Entity** | 92 | 39 | 39 | 0 | 100.00% | 42.39% | 0 |
| **Mode H: LOO-Duplicate** | 92 | 42 | 42 | 0 | 100.00% | 45.65% | 0 |
| **Mode I: LOO-Contradiction** | 92 | 77 | 42 | **35** | 54.55% | 83.70% | 19 |
| **Mode J: LOO-Missing** | 92 | 47 | 42 | **5** | 89.36% | 51.09% | 5 |

### B. Cohort M Corpus (30 Packets / 103 Claims)

| Mode | Evaluated Claims | Verified Claims | Exact Matches | False Verifications | Precision | Coverage | Packet False |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Mode A: Naive Baseline** | 103 | 103 | 78 | 25 | 75.73% | 100.00% | 14 |
| **Mode B: Entity Resolution Only** | 103 | 102 | 78 | 24 | 76.47% | 99.03% | 13 |
| **Mode C: Independence Only** | 103 | 64 | 51 | 13 | 79.69% | 62.14% | 13 |
| **Mode D: Contradiction Only** | 103 | 79 | 75 | 4 | 94.94% | 76.70% | 3 |
| **Mode E: Conservative Abstention Only** | 103 | 63 | 51 | 12 | 80.95% | 61.17% | 12 |
| **Mode F: Full Policy (Production)** | **103** | **76** | **76** | **0** | **100.00%** | **73.79%** | **0** |
| **Mode G: LOO-Entity** | 103 | 75 | 75 | 0 | 100.00% | 72.82% | 0 |
| **Mode H: LOO-Duplicate** | 103 | 76 | 76 | 0 | 100.00% | 73.79% | 0 |
| **Mode I: LOO-Contradiction** | 103 | 101 | 78 | **23** | 77.23% | 98.06% | 12 |
| **Mode J: LOO-Missing** | 103 | 77 | 76 | **1** | 98.70% | 74.76% | 1 |

---

## 3. In-Depth Attribution Analysis

### A. The Critical Role of Contradiction Detection (LOO-Contradiction)
Removing contradiction detection (Mode I) is catastrophic across both datasets:
- In Loop 28, false verifications spike from 0 to 35, cutting precision nearly in half (100% $\to$ 54.55%).
- In Cohort M, false verifications spike from 0 to 23 (100% $\to$ 77.23%).
- This demonstrates that contradiction detection is the foundational barrier preventing conflicting evidence from being mistakenly accepted.

### B. Understanding LOO-Duplicate Behavior
In both corpora, Mode H (LOO-Duplicate) achieves metrics identical to Mode F (Full Policy):
- In the benchmark corpora, duplicate documents contain true identical values.
- Duplication suppression prevents granting a false multi-source *corroboration confidence bonus* to duplicated files.
- However, when duplication suppression is disabled, the valid claim is still verified as an accurate single-source extraction with valid ground truth.
- Thus, disabling duplicate suppression does not induce false verifications on genuine matching files, explaining why metrics match Mode F.

### C. Missing Evidence Enforcement (LOO-Missing)
Disabling mandatory document type checks permits claims to be verified even when required supporting certificates are completely absent, introducing 5 false verifications in Loop 28 and 1 in Cohort M.
