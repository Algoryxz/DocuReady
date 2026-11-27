# Loop 29 Source & Evidence Audit of Loop 28 Implementation

## 1. Source Modules Inspected
- `src/docuready/evidence/cross_document.py` (Entity resolution, independence, contradiction detection)
- `src/docuready/ingest/identifier_validation.py` (Check-digit algorithms, confusable detection, token sanitization)
- `src/docuready/ingest/table_association.py` (Spatial reading order, header hierarchy, cell association)

## 2. Findings & Hardening Applied
1. **Generic Filename Duplication**: In Loop 28, matching filenames triggered duplicate classification even when content hashes differed. Fixed: Generic filenames (`invoice.pdf`, `form.pdf`) with distinct content hashes are now recognized as independent documents.
2. **Standardized Government Boilerplate (>96% similarity)**: In Loop 28, two applicants submitting the same standardized government form were flagged as duplicates due to >96% boilerplate text. Fixed: Distinct content hashes on shared form templates are classified as `INDEPENDENT`.
3. **Semantic Unit Conversion**: 1 MT vs 1,000 KG represents identical physical mass. Added `evaluate_semantic_claim_equivalence` to classify metric unit equivalence as `EQUIVALENT_AFTER_NORMALIZATION`.
