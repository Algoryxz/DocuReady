# LOOP 21: Agentic Skills Research & Selection Report

## 1. Catalog Inspection & Background

Per the Loop 21 Engineering Directive, we surveyed playbooks and patterns from the **Agentic Awesome Skills (AAS)** repository ([github.com/sickn33/agentic-awesome-skills](https://github.com/sickn33/agentic-awesome-skills)), focusing on:
- Tabular header hierarchy resolution
- Image pre-processing and super-resolution techniques for OCR
- Small token / decimal point retention in text recognition
- Adversarial numeric verification and boundary testing
- Deterministic metric reconciliation matrices

---

## 2. Evaluation Matrix for Loop 21 Needs

| Candidate Domain / Skill Pattern | Relevance to Loop 21 Mission | Ponytail Alignment | Assessment & Adoption Decision |
| :--- | :--- | :--- | :--- |
| **Bicubic Interpolation for Low-DPI OCR** | **High**: Upscaling small text patches (DPI < 200, character height < 18px) to 300 DPI equivalent so OCR binarization retains single-pixel punctuation. | **High**: Uses existing Pillow `im.resize(..., Image.Resampling.BICUBIC)`. Zero new dependencies. | **Adopted as Pattern**: Targeted 2x bicubic pre-scaling on small numeric crops. |
| **Hierarchical Header Span Merging** | **High**: Resolves 2-tier headers by projecting parent header intervals over child column intervals and prefixing parent names (`"Quarter 1 Status / Q1 Actual"`). | **High**: Pure Python interval containment ($[c_{\text{left}}, c_{\text{right}}] \subset [p_{\text{left}}, p_{\text{right}}]$) in < 20 lines. | **Adopted as Pattern**: Header tier fusion in `table_association.py`. |
| **Deep Learning Super-Resolution (e.g. Real-ESRGAN / Waifu2x)** | **Incompatible / Prohibited**: Neural upscaling models requiring heavy weights (>60MB) and multi-second GPU inference. | **Zero**: Violates competition freeze, offline execution, and sub-second latency constraints. | **Rejected**: Heavyweight neural models strictly avoided. |
| **Metric Reconciliation Ledger** | **High**: Reconciles conflicting classification categories (coverage vs precision vs abstention) into a mutually exclusive and exhaustive contingency table. | **High**: Pure mathematical and tabular auditing. | **Adopted as Pattern**: Exhaustive field outcome ledger in `LOOP_21_LOOP20_METRIC_RECONCILIATION.md`. |

---

## 3. Skills Adoption Conclusion

In strict alignment with Ponytail:
- Zero external libraries or third-party skills were installed into the repository.
- The **Targeted Bicubic Pre-Scaling Pattern** was implemented directly using Pillow.
- The **Hierarchical Header Span Fusion Pattern** was integrated directly into `build_table_grid()` in `src/docuready/ingest/table_association.py`.
