# LOOP 20: Agentic Skills Research & Selection Report

## 1. Catalog Inspection & Background

Per the Loop 20 Engineering Directive, we researched candidate playbooks and methodologies from the **Agentic Awesome Skills (AAS)** repository ([github.com/sickn33/agentic-awesome-skills](https://github.com/sickn33/agentic-awesome-skills)), focusing on:
- Production-grade document evaluation and regression matrices
- Strict claim verification ("Evidence before claims")
- Calibration, confidence thresholds, and epistemic uncertainty handling
- Conformal prediction patterns and selective abstention
- Adversarial test generation for layout and field confusion

---

## 2. Evaluation Matrix for Loop 20 Needs

| Candidate Domain / Skill Pattern | Relevance to Loop 20 Mission | Ponytail Alignment | Assessment & Adoption Decision |
| :--- | :--- | :--- | :--- |
| **`verification-before-completion`**<br>(AAS Community Skill) | **Critical**: Establishes the iron law *"Evidence before claims, always."* Forbids marking any task or field verified without fresh, bound verification evidence. | **High**: Pure methodological discipline. Prohibits heuristic substring presence checks from declaring an extracted field "verified". | **Adopted as Core Policy**: A field value is only marked VERIFIED if it is bound to a specific row, column, and cell coordinate whose bounding box is traceably localized. |
| **`advanced-evaluation` & `AI Prompt Regression Test Matrix`** | **High**: Evaluates outputs across structured dimensions (factual consistency, format compliance, boundary handling) and prevents regression drift across revisions. | **High**: Informs the multi-cohort separation (Cohorts A, B, C, D) and deterministic metric reporting (micro/macro CER/WER, FVR, SEM). | **Adopted as Pattern**: Structured test harness with strict separation of dev, val, blind, and challenge cohorts. |
| **`docs-guard` & Fact-Checking Workflows** | **High**: Verifies symbols, flags, IDs, and cross-document claims against explicit source-of-truth registries to eliminate hallucinations and contradictions. | **High**: Reuses Python standard library dictionaries and sequence matching to cross-check document claims. | **Adopted as Pattern**: Cross-document verification model with discrete states: `AGREEMENT`, `MISMATCH`, `MISSING`, `UNREADABLE`, `AMBIGUOUS_ASSOCIATION`, `INSUFFICIENT_EVIDENCE`. |
| **Selective Classification / Abstention Pattern** | **Critical**: Principles from selective prediction—abstaining when epistemic uncertainty is high (e.g. multi-cell overlap, ambiguous column gutter, syntax invalidity). | **High**: Simple boolean checks (`is_ambiguous`, `cell.conf < tau_abstain`, syntax errors) rather than heavy neural calibrators. | **Adopted as Pattern**: Calibrated evidence gating in `table_association.py` and `safety_layer.py`. |
| **External Agent Evaluator / Cloud LLM Judge** | **Incompatible / Prohibited**: Calls external APIs to judge document outputs. | **Zero**: Violates competition freeze, offline execution guarantee, privacy rules, and zero-network mandate. | **Rejected**: All evaluation and verification must be 100% local, deterministic, and offline. |

---

## 3. Skills Adoption Conclusion

In strict alignment with Ponytail:
- Zero third-party playbooks were blindly installed into the repository.
- The **"Evidence Before Claims"** verification principle was formalized into the `FieldEvidence` verification contract.
- The **Selective Abstention Pattern** was embedded into the cell-association and cross-document verification algorithms.
- All implementations rely solely on the standard library and existing project dependencies.
