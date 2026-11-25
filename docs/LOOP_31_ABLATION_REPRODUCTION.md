# Loop 31 — Deliverable 9: 10-Mode Ablation Reproduction & Component Attribution

## 1. Ablation Reproduction Across Corpora
The 10 ablation modes were independently executed across both the Loop 28 (36 packets, 92 claims) and Cohort M (30 packets, 103 claims) corpora.

### A. Quantitative Ablation Results

| Mode | Component Disabled / Policy | L28 False Claims | L28 Precision | Cohort M False Claims | Cohort M Precision | Attribution Verdict |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Mode A** | Naive Baseline (Verify if OCR $\ge 70.0$) | 50 | 45.65% | 25 | 75.73% | Catastrophic failure |
| **Mode B** | Entity Resolution Only | 47 | 47.19% | 24 | 76.47% | No contradiction guard |
| **Mode C** | Independence Detection Only | 27 | 50.00% | 13 | 79.69% | Partial suppression |
| **Mode D** | Contradiction Detection Only | 19 | 67.24% | 4 | 94.94% | Substantial improvement |
| **Mode E** | Conservative Abstention Only | 23 | 56.60% | 12 | 80.95% | Single-doc heuristic only |
| **Mode F** | **Full Policy (Production Engine)** | **0** | **100.00%** | **0** | **100.00%** | **Perfect Precision** |
| **Mode G** | **LOO-Entity** (Disable Entity Matching) | 0 | 100.00% | 0 | 100.00% | Coverage drops (39 / 75 claims) |
| **Mode H** | **LOO-Duplicate** (Disable Duplicate Suppression)| 0 | 100.00% | 0 | 100.00% | Unchanged exact matches & precision |
| **Mode I** | **LOO-Contradiction** (Disable Contradictions) | **35** | **54.55%** | **23** | **77.23%** | **Catastrophic Failure** |
| **Mode J** | **LOO-Missing** (Disable Missing Evidence) | **5** | **89.36%** | **1** | **98.70%** | Permitted missing certificates |

---

## 2. In-Depth Component Attribution Analysis

### Why Mode H (LOO-Duplicate) Yields Unchanged Precision and Exact Matches
A prominent finding across Loops 29, 30, and 31 is that disabling duplicate detection (Mode H) produces the exact same number of verified exact matches and zero false verifications as the Full Policy (Mode F).

**Forensic Explanation:**
1. **Nature of Corpus Duplicates:** In both evaluation suites, duplicate files represent identical copies or re-scans of genuine documents that already carry correct ground-truth values.
2. **Role of Duplicate Detection:** In the production engine, duplicate detection exists to prevent granting an *artificial corroboration bonus*. When two files are duplicates, the engine treats them as a single source rather than independent multi-source corroboration.
3. **Single-Source Validity:** Under the full policy, if an individual document extraction is already clean, unambiguous, and possesses confidence $\ge T^* = 70.0$, it is already verifiable as a valid claim.
4. **Conclusion:** Disabling duplicate detection allows duplicate files to act as corroborating sources, but because the extracted values are factually correct, this never produces a false verification on clean test sets. Mode H demonstrates that duplicate detection prevents unwarranted corroboration inflation without altering valid single-source truths.

### The Critical Necessity of Contradiction Detection (Mode I)
Disabling contradiction detection (Mode I) triggers the most severe failure mode in the system:
- In Loop 28, false verifications surge from 0 to 35, causing precision to collapse from $100.0\%$ to $54.55\%$.
- In Cohort M, false verifications surge from 0 to 23, causing precision to collapse from $100.0\%$ to $77.23\%$.
This confirms that contradiction detection is the primary algorithmic pillar defending the system against conflicting evidence.
