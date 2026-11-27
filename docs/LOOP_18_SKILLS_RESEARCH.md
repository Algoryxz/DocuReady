# LOOP 18: Agentic Skills Research & Selection Report

## 1. Catalog Inspection & Background

In accordance with the Loop 18 Engineering Directive, we conducted a systematic evaluation of the **Agentic Awesome Skills (AAS)** repository ([github.com/sickn33/agentic-awesome-skills](https://github.com/sickn33/agentic-awesome-skills)), an independent index comprising 3,055+ installable `SKILL.md` skill definitions for AI engineering and coding environments.

Per governance guidelines:
- We strictly avoid installing speculative, bloated, or irrelevant skills.
- Candidate skills must directly address the core objectives of Loop 18: independent validation, benchmark scoring integrity, critical-field extraction reliability, stress testing, and failure taxonomy classification.
- Any adopted skill must adhere to the Ponytail minimalism philosophy (YAGNI, standard library first, zero external runtime baggage).

---

## 2. Evaluation Matrix for Loop 18 Needs

| Candidate Domain / Skill Pattern | Relevance to Loop 18 Mission | Ponytail Alignment | Assessment & Adoption Decision |
| :--- | :--- | :--- | :--- |
| **OCR Ground Truth Alignment & Levenshtein Scorer** | High: Independent audit of character & word error rates, Levenshtein distance metrics, and reading order alignment. | High: Can be implemented cleanly in Python standard library (`difflib`, `collections`) without heavy dependencies like `jiwer` or `Levenshtein` C-extensions. | **Adopted as Pattern**: Audited alignment and macro vs corpus-level calculation implemented directly in standard library Python. |
| **Critical Field & RegEx Robustness Validator** | High: Testing numeric stability, date parsing, alphanumeric ID parsing, and character confusion (e.g. 0 vs O, 1 vs I). | High: Pure regex and string tokenization; zero external dependencies. | **Adopted as Pattern**: Used to structure the adversarial stress fixtures and field verification logic. |
| **Adversarial Noise & Distortion Generators** | Medium-High: Simulating rubber stamps, contrast loss, and rotational skew to stress test critical fields. | High: Uses existing PIL / Pillow capabilities already in the DocuReady environment. | **Adopted as Pattern**: Controlled Pillow scripts for synthetic adversarial generation. |
| **Statistical Abstention / Rejection Calibration** | High: Determining optimal confidence thresholds for abstaining rather than silently hallucinating on degraded text. | High: Pure statistical computation over confidence distributions. | **Adopted as Pattern**: Calibrated threshold analysis comparing precision vs coverage. |
| **Heavy Deep Learning / LLM Post-Correction Skills** | Low / Disallowed: Cloud OCR correction, LLM-based hallucination filling, or external API wrappers. | Zero: Violates competition freeze, offline requirements, and low-latency desktop constraints. | **Rejected**: Violates offline and runtime constraints. |

---

## 3. Skills Adoption Conclusion

For Loop 18, no external third-party agentic skills required direct installation into the global repository or desktop runtime. Instead:
1. The **Benchmark Integrity & Dual-Scoring Pattern** (Macro Mean Per-Document CER + Micro Corpus-Level CER) was implemented in `research/loop18/benchmark/run_strategy_benchmark.py`.
2. The **Critical Field Stress Pipeline** was implemented using native Pillow and regex evaluators, maintaining 100% offline, zero-dependency reproducibility.
3. Ponytail minimalism was rigorously maintained throughout.
