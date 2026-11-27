# LOOP 20: Prioritized Next Experiments for Loop 21 Backlog

## 1. Prioritized Engineering Backlog

Based on the empirical findings and failure analysis of Loop 20, the following experiments are prioritized for Loop 21:

| Priority | Initiative Name | Target Defect / Opportunity | Projected Impact | Complexity |
| :---: | :--- | :--- | :--- | :---: |
| **P1** | **Multi-Tier Header Fusion** | Resolve row index shifts in 2-tier merged header tables (`VAL_05`). | +3.0% SEM, 0% header shift | Low (Ponytail stdlib) |
| **P2** | **Bicubic Upscaling for Decimal Retention** | Eliminate decimal drop in financial and lab figures (`BLIND_06`: `'5.6'` vs `'56'`). | +1.5% SEM, higher numeric precision | Low (PIL `Image.Resampling.BICUBIC`) |
| **P3** | **Multi-Column Independent Page Partitioning** | Separate two side-by-side independent tables on a single page before row clustering (`TAB_09`). | +3.0% SEM on complex multi-table docs | Medium (NumPy horizontal split) |
| **P4** | **Cross-Document Semantic Normalization Registry** | Extend synonym and equivalence dictionary for Indian administrative terms (e.g. `PPO` = `Pension Payment Order`). | Enhanced cross-document matching recall | Low |

---

## 2. Research Hypothesis for Loop 21

> *Hypothesis*: By implementing a lightweight multi-tier header fusion step (<20 lines of Python) that detects when row 0 and row 1 both span multiple columns, DocuReady can unify composite headers without shifting data row indices, lifting Table Generalization SEM above 86% across all cohorts.
