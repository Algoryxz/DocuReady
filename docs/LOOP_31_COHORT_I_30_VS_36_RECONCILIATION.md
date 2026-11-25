# Loop 31 — Deliverable 4: Cohort I 30-versus-36 Document Reconciliation

## 1. The Discrepancy Statement
- **Prior Problem Statement:**
  Earlier reports described Cohort I as "30 documents, 120 fields", while Loop 30's reconciliation reported Cohort I as "36 documents, 120 fields".
- **Objective:** Determine whether this represents document splitting, packet regrouping, deduplication, or a reporting error.

---

## 2. Root-Cause Analysis & Provenance Audit

An exhaustive forensic comparison of `research/loop24/dataset_manifest.json`, `research/loop23/dataset_manifest.json`, and `research/loop27/results/benchmark_results.json` reveals the exact provenance:

### A. The 30-Document Origin (Loop 24 Manifest)
In Loop 24, `research/loop24/dataset_manifest.json` registered exactly **30 documents** containing **102 critical fields**:
- `COHORT_I_DEV_01` through `_08` (8 documents, 27 fields)
- `COHORT_I_CAL_01` through `_08` (8 documents, 28 fields)
- `COHORT_I_BLIND_01` through `_10` (10 documents, 34 fields)
- `COHORT_I_ADV_01` through `_04` (4 documents, 13 fields)
- **Subtotal:** 30 documents, 102 fields.

### B. The 6-Document Origin (Loop 23 Cohort H)
In Loop 23, `research/loop23/dataset_manifest.json` introduced **6 documents** containing **18 critical fields** specifically designed for micro-font and narrow-gutter table evaluation:
- `COHORT_H_01_MICRO_CLINICAL_PANEL` (4 fields)
- `COHORT_H_02_MICRO_DOSAGE_AUDIT` (4 fields)
- `COHORT_H_03_NARROW_GUTTER_LEDGER` (3 fields)
- `COHORT_H_04_NARROW_GUTTER_INVOICE` (3 fields)
- `COHORT_H_05_ADVERSARIAL_NARROW_EMPTY_TRAP` (2 fields)
- `COHORT_H_06_ADVERSARIAL_MICRO_COLLISION` (2 fields)
- **Subtotal:** 6 documents, 18 fields.

### C. The Benchmark Consolidation (Loop 27 Benchmark Results)
When compiling the unified 791-field multi-cohort benchmark in `research/loop27/results/benchmark_results.json`:
- The 6 `COHORT_H_*` documents were grouped alongside the 30 `COHORT_I_*` documents under the partition name **`Cohort_I_Blind`**.
- Combined Document Count: $30 + 6 = \mathbf{36\text{ documents}}$.
- Combined Critical Field Count: $102 + 18 = \mathbf{120\text{ fields}}$.

---

## 3. Definitive Resolution
> [!NOTE]
> The apparent discrepancy was a **reporting conflation**:
> - Earlier report authors cited the **30 document count** from the Loop 24 `COHORT_I_*` manifest alongside the **120 field count** of the combined `Cohort_I_Blind` partition.
> - The benchmark dataset has always contained **36 physical document files** (30 `COHORT_I` + 6 `COHORT_H`) and **120 evaluated fields**.
> - No files were added, deleted, or split. Both figures describe the exact same underlying files.

The machine-readable reconciliation record is preserved at [cohort_i_reconciliation.json](file:///c:/Users/smara/Desktop/New folder/research/loop31/reconciliation/cohort_i_reconciliation.json).
