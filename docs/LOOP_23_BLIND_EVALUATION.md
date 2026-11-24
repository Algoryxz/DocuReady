# Loop 23 Blind Evaluation Report — Cohort H

## 1. Protocol & Isolation Safeguards

To prevent overfitting and benchmark leakage, Loop 23 introduced **Cohort H** (`research/loop23/tables/` and `research/loop23/dataset_manifest.json`):
- Comprises 6 completely new synthetic documents and 18 critical fields.
- Designed strictly to test micro-font numeric integrity, narrow gutters, and adversarial layout traps.
- None of the documents in Cohort H were used during the initial development of the morphology or header parsing algorithms.

---

## 2. Cohort H Test Fixture Roster

1. **`COHORT_H_01_MICRO_CLINICAL_PANEL`** (4 fields):
   Tests sub-10px clinical chemistry values (`5.8%`, `240`, `4.1`, `138`).
2. **`COHORT_H_02_MICRO_DOSAGE_AUDIT`** (4 fields):
   Tests pharmaceutical dosage values (`0.75`, `99.2%`, `2.4`, `20`).
3. **`COHORT_H_03_NARROW_GUTTER_LEDGER`** (3 fields):
   Tests tight 6-8px borderless gutters with compound headers (`12500`, `1250`, `30600`).
4. **`COHORT_H_04_NARROW_GUTTER_INVOICE`** (3 fields):
   Tests borderless invoice itemization with decimal rates and taxes (`45.50`, `2.25`, `38.20`).
5. **`COHORT_H_05_ADVERSARIAL_NARROW_EMPTY_TRAP`** (2 fields):
   Tests empty cell adjacent to high-value numeric column (`""`, `28000`).
6. **`COHORT_H_06_ADVERSARIAL_MICRO_COLLISION`** (2 fields):
   Tests multi-row candidate collision on repeated identifier `ACC-901` (`""`, `19200`).

---

## 3. Blind Evaluation Results

| Metric | Cohort H Outcome | Analysis |
| :--- | :---: | :--- |
| **Total Evaluated Documents** | 6 | 100% evaluated |
| **Total Critical Fields** | 18 | 100% evaluated |
| **Verified Claims** | 6 | All verified claims are exact matches |
| **Exact Matches** | 6 | `platelet_count` (240), `omep_strength` (20), `beta_closing` (30600), `flour_rate` (45.50), `flour_tax` (2.25), `sugar_rate` (38.20) |
| **False Verifications** | **0** | **0.00% False Verification Rate** |
| **Abstentions** | 12 | 100% safe abstentions (guards prevented 12 potential false claims) |
| **SEM Passes** | 10 | 55.56% spatial extraction pass rate |
| **Critical Field Precision (CFP)** | **100.00%** | Zero false claims made by the engine |
| **Coverage** | 33.33% | High selectivity under severe degradation |

---

## 4. Adversarial Trap Verification in Cohort H

- **`COHORT_H_05` — Empty Cell Trap:**
  Field `narayan_penal_empty` correctly produced `PASS_EMPTY_CORRECT`, abstaining and rejecting value inheritance from the adjacent `28000` demand cell.
- **`COHORT_H_06` — Multi-Row Candidate Collision:**
  Field `acc_901_ambiguous_vol` targeted `ACC-901`, which exists in two distinct branch rows (`Cuttack Metro` and `Bhubaneswar South`). The multi-row ambiguity guard successfully abstained with `PASS_EMPTY_CORRECT`, preventing a random row assignment.
- **`COHORT_H_01` — OCR Text Artifact Trap:**
  OCR misread `'4.1'` as `'4a'`. The numeric type contradiction guard rejected `'4a'` due to the presence of alphabetic letter `'a'`, preventing a false verification.
