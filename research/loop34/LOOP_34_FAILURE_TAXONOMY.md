# DOCUREADY — LOOP 34 FAILURE TAXONOMY & ERROR CODES

**Milestone:** Loop 34  
**Date:** 2026-11-26  

---

## 1. Standardized Failure Taxonomy

DocuReady classifies real-world OCR and extraction errors into 12 distinct root categories:

1. `OCR_RECOGNITION_ERROR`: Low-level character misread or substitution.
2. `SCRIPT_ROUTING_ERROR`: Wrong language model applied to mixed text.
3. `LAYOUT_SEGMENTATION_ERROR`: Multi-column gutter or reading order confusion.
4. `TABLE_RECONSTRUCTION_ERROR`: Row/column bounding grid misplacement.
5. `LABEL_VALUE_ASSOCIATION_ERROR`: Inverted or displaced label-to-value keying.
6. `NUMERIC_DECIMAL_CORRUPTION`: Decimal point drop or comma misgrouping.
7. `IDENTIFIER_CONFUSABLE_GLYPH`: Confusable character substitution (O/0, I/1).
8. `DATE_CHRONOLOGY_AMBIGUITY`: Unresolvable DD/MM vs MM/DD ambiguity.
9. `CONFIDENCE_MISCALIBRATION`: High confidence assigned to incorrect candidate.
10. `UNNECESSARY_ABSTENTION`: False rejection of legible evidence.
11. `GROUND_TRUTH_AMBIGUITY`: Indeterminate source image text.
12. `UNSUPPORTED_CONDITION`: Handwriting or unconstrained free-form cursive.

---

## 2. Registered Loop 34 Defects Summary

Total Defects Registered: **3** (Details in `LOOP_34_DEFECT_REGISTER.json`):
- `OCR-034-001`: Odia low-resolution ligature segmentation (Mitigated via adaptive pre-scaling).
- `OCR-034-002`: Narrow vertical gutter bleed in dense multi-column gazettes.
- `OCR-034-003`: Confusable glyphs in micro-font bank passbooks (Retained conservative invariant).
