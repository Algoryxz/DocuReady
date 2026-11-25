# DOCUREADY — LOOP 33 RULE INVENTORY
## Comprehensive Audit of Rules, Primitives, Decisions & Safety Invariants

**Milestone:** Loop 33 — Independent Domain Rule Audit & Decision Integrity  
**Operating Verification Threshold:** $T^* = 70.0$  
**Operating Fuzzy Threshold:** $T_{\text{fuzzy}} = 75.0$  
**Total Rules Audited:** 64  

---

### Summary by Rule Family

| Family | Description | Rule Count | Subsystems Involved |
| :--- | :--- | :--- | :--- |
| **Family A** | Identity & Identifier Integrity | 19 | Identifier Validation, Pack Rules, Normalizer |
| **Family B** | Date & Chronology Semantics | 10 | Date Normalizer, Pack Rules, Expiration Engine |
| **Family C** | Numeric & Financial Calculations | 13 | Amount Normalizer, Academic Percentage, Ceiling Caps |
| **Family D** | Table & Field Association Semantics | 2 | Field Completeness, Slot Validator, Table Association |
| **Family E** | Cross-Document Verification Policy | 3 | Entity Resolution, Contradiction Detection, Independence |
| **Family F** | Document & Scheme Pack Rules | 7 | Mandatory Completeness, Legibility, Domicile |
| **Family G** | Confidence & Abstention Policy | 0 | Threshold Floors, OCR Confusable Abstention |
| **Family H** | Safety Layer Invariants | 10 | DecisionSafetyLayer Invariants 1–10 |

---

### Detailed Rule Catalog

| Rule ID | Name | Subsystem | Family | Primitive / Method | Source Citation | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `RULE-DOC-01` | Mandatory Document Completeness | Declarative Scheme Pack (generic.demo) | F | `require_document` | SRC-DOC-01 | **VERIFIED** |
| `RULE-DOC-02` | Document Legibility & Evidence Integrity | Declarative Scheme Pack (generic.demo) | F | `legible` | SRC-DOC-02 | **UNVERIFIED** |
| `RULE-FLD-01` | Mandatory Field Completeness | Declarative Scheme Pack (generic.demo) | D | `field_present` | SRC-FLD-01 | **UNVERIFIED** |
| `RULE-NAME-01` | Cross-Document Applicant Name Consistency | Declarative Scheme Pack (generic.demo) | A | `match_across` | SRC-NAME-01 | **UNVERIFIED** |
| `RULE-DOB-01` | Cross-Document Date of Birth Consistency | Declarative Scheme Pack (generic.demo) | B | `match_across` | SRC-DOB-01 | **VERIFIED** |
| `RULE-INC-01` | Statutory Income Ceiling Compliance | Declarative Scheme Pack (generic.demo) | C | `numeric_cap` | SRC-INC-01 | **VERIFIED** |
| `RULE-INC-02` | Cross-Document Income Declaration Match | Declarative Scheme Pack (generic.demo) | C | `numeric_consistency` | SRC-INC-02 | **UNVERIFIED** |
| `RULE-EXP-01` | Income Certificate Validity Period | Declarative Scheme Pack (generic.demo) | B | `within_validity` | SRC-EXP-01 | **UNVERIFIED** |
| `RULE-REF-01` | Certificate Reference Number Match | Declarative Scheme Pack (generic.demo) | A | `match_across` | SRC-REF-01 | **UNVERIFIED** |
| `RULE-REF-02` | RULE-REF-02 | Declarative Scheme Pack (generic.demo) | A | `match_across` | SRC-REF-01 | **UNVERIFIED** |
| `RULE-BNK-01` | Bank IFSC Code Standard Format | Declarative Scheme Pack (generic.demo) | A | `match_across` | SRC-BNK-01 | **VERIFIED** |
| `RULE-BNK-02` | Bank Account Number Consistency | Declarative Scheme Pack (generic.demo) | A | `match_across` | SRC-BNK-02 | **UNVERIFIED** |
| `RULE-DOM-01` | State Domicile Requirement | Declarative Scheme Pack (generic.demo) | F | `enum_in` | SRC-DOM-01 | **UNVERIFIED** |
| `RULE-MRK-01` | Academic Cutoff Compliance & Category Relaxations | Declarative Scheme Pack (generic.demo) | C | `numeric_cap` | SRC-MRK-01 | **VERIFIED** |
| `RULE-DOC-01_PROCEDURAL` | Mandatory Document Completeness | Procedural Validator (DocuReadyValidator) | F | `procedural_code` | SRC-DOC-01 | **VERIFIED** |
| `RULE-DOC-02_PROCEDURAL` | Document Legibility & Evidence Integrity | Procedural Validator (DocuReadyValidator) | F | `procedural_code` | SRC-DOC-02 | **UNVERIFIED** |
| `RULE-NAME-UNCERTAIN_PROCEDURAL` | Cross-Document Name Verification (Uncertain OCR) | Procedural Validator (DocuReadyValidator) | A | `procedural_code` | N/A | **UNVERIFIED** |
| `RULE-NAME-01_PROCEDURAL` | Cross-Document Applicant Name Consistency | Procedural Validator (DocuReadyValidator) | A | `procedural_code` | SRC-NAME-01 | **UNVERIFIED** |
| `RULE-NAME-PASS_PROCEDURAL` | Cross-Document Applicant Name Consistency | Procedural Validator (DocuReadyValidator) | A | `procedural_code` | N/A | **UNVERIFIED** |
| `RULE-DOB-03_PROCEDURAL` | Date of Birth Format Validity | Procedural Validator (DocuReadyValidator) | B | `procedural_code` | N/A | **UNVERIFIED** |
| `RULE-DOB-02_PROCEDURAL` | Date of Birth Ambiguity | Procedural Validator (DocuReadyValidator) | B | `procedural_code` | N/A | **UNVERIFIED** |
| `RULE-DOB-UNCERTAIN_PROCEDURAL` | Cross-Document Date of Birth (Uncertain OCR) | Procedural Validator (DocuReadyValidator) | B | `procedural_code` | N/A | **UNVERIFIED** |
| `RULE-DOB-01_PROCEDURAL` | Cross-Document Date of Birth Consistency | Procedural Validator (DocuReadyValidator) | B | `procedural_code` | SRC-DOB-01 | **VERIFIED** |
| `RULE-DOB-PASS_PROCEDURAL` | Date of Birth Consistency | Procedural Validator (DocuReadyValidator) | B | `procedural_code` | N/A | **UNVERIFIED** |
| `RULE-INC-03_PROCEDURAL` | Income Extraction | Procedural Validator (DocuReadyValidator) | C | `procedural_code` | N/A | **UNVERIFIED** |
| `RULE-INC-CEIL-UNCERTAIN_PROCEDURAL` | Statutory Income Ceiling Compliance (Uncertain OCR) | Procedural Validator (DocuReadyValidator) | C | `procedural_code` | N/A | **UNVERIFIED** |
| `RULE-INC-01_PROCEDURAL` | Statutory Income Ceiling Compliance | Procedural Validator (DocuReadyValidator) | C | `procedural_code` | SRC-INC-01 | **VERIFIED** |
| `RULE-INC-CEIL-PASS_PROCEDURAL` | Statutory Income Ceiling Compliance | Procedural Validator (DocuReadyValidator) | C | `procedural_code` | N/A | **UNVERIFIED** |
| `RULE-INC-MISMATCH-UNCERTAIN_PROCEDURAL` | Income Consistency (Uncertain OCR) | Procedural Validator (DocuReadyValidator) | C | `procedural_code` | N/A | **UNVERIFIED** |
| `RULE-INC-02_PROCEDURAL` | Income Consistency (Declared vs Certified) | Procedural Validator (DocuReadyValidator) | C | `procedural_code` | SRC-INC-02 | **UNVERIFIED** |
| `RULE-INC-MATCH-PASS_PROCEDURAL` | Income Consistency (Declared vs Certified) | Procedural Validator (DocuReadyValidator) | C | `procedural_code` | N/A | **UNVERIFIED** |
| `RULE-EXP-02_PROCEDURAL` | Certificate Date Parseability | Procedural Validator (DocuReadyValidator) | B | `procedural_code` | N/A | **UNVERIFIED** |
| `RULE-EXP-01_PROCEDURAL` | Income Certificate Statutory Validity Period | Procedural Validator (DocuReadyValidator) | B | `procedural_code` | SRC-EXP-01 | **UNVERIFIED** |
| `RULE-EXP-PASS_PROCEDURAL` | Income Certificate Statutory Validity Period | Procedural Validator (DocuReadyValidator) | B | `procedural_code` | N/A | **UNVERIFIED** |
| `RULE-REF-01_PROCEDURAL` | Income Certificate Number Reference Match | Procedural Validator (DocuReadyValidator) | A | `procedural_code` | SRC-REF-01 | **UNVERIFIED** |
| `RULE-REF-INC-PASS_PROCEDURAL` | Income Certificate Number Reference Match | Procedural Validator (DocuReadyValidator) | A | `procedural_code` | N/A | **UNVERIFIED** |
| `RULE-REF-02_PROCEDURAL` | Caste Certificate Number Reference Match | Procedural Validator (DocuReadyValidator) | A | `procedural_code` | N/A | **UNVERIFIED** |
| `RULE-REF-CST-PASS_PROCEDURAL` | Caste Certificate Number Reference Match | Procedural Validator (DocuReadyValidator) | A | `procedural_code` | N/A | **UNVERIFIED** |
| `RULE-BNK-01_PROCEDURAL` | Bank IFSC Code Standard Format | Procedural Validator (DocuReadyValidator) | A | `procedural_code` | SRC-BNK-01 | **VERIFIED** |
| `RULE-BNK-IFSC-PASS_PROCEDURAL` | Bank IFSC Code Format | Procedural Validator (DocuReadyValidator) | A | `procedural_code` | N/A | **UNVERIFIED** |
| `RULE-BNK-02_PROCEDURAL` | Bank Account Number Consistency | Procedural Validator (DocuReadyValidator) | A | `procedural_code` | SRC-BNK-02 | **UNVERIFIED** |
| `RULE-DOM-01_PROCEDURAL` | State Domicile Requirement | Procedural Validator (DocuReadyValidator) | F | `procedural_code` | SRC-DOM-01 | **UNVERIFIED** |
| `RULE-DOM-PASS_PROCEDURAL` | State Domicile Requirement | Procedural Validator (DocuReadyValidator) | F | `procedural_code` | N/A | **UNVERIFIED** |
| `RULE-MRK-RELAX-PASS_PROCEDURAL` | Academic Eligibility Compliance (SC/ST Qualifying Pass) | Procedural Validator (DocuReadyValidator) | C | `procedural_code` | N/A | **UNVERIFIED** |
| `RULE-MRK-01_PROCEDURAL` | Academic Cutoff Compliance (SC/ST Relaxed) | Procedural Validator (DocuReadyValidator) | C | `procedural_code` | SRC-MRK-01 | **VERIFIED** |
| `RULE-MRK-PASS_PROCEDURAL` | Academic Cutoff Compliance | Procedural Validator (DocuReadyValidator) | C | `procedural_code` | N/A | **UNVERIFIED** |
| `RULE-SLOT-01` | Document Slot Classification & Semantic Match | Document Slot Validator | D | `validate_packet_slots` | SRC-DOC-01 | **VERIFIED** |
| `RULE-ID-VERHOEFF` | Aadhaar / National ID Dihedral D5 Checksum Verification | Identifier Integrity Engine | A | `validate_verhoeff` | SRC-ID-AADHAAR | **VERIFIED** |
| `RULE-ID-PAN` | Permanent Account Number (PAN) Strict Structure Validation | Identifier Integrity Engine | A | `validate_pan_syntax` | SRC-ID-PAN | **VERIFIED** |
| `RULE-ID-IFSC` | Indian Financial System Code (IFSC) Strict Format Validation | Identifier Integrity Engine | A | `validate_ifsc_code` | SRC-BNK-01 | **VERIFIED** |
| `RULE-ID-CONFUSABLE-GLYPH` | Identifier OCR Confusable Character Ambiguity Abstention | Identifier Integrity Engine | A | `detect_confusable_glyphs` | SRC-ENG-ABSTAIN | **VERIFIED** |
| `RULE-XDOC-ENTITY-RES` | Multi-Attribute Applicant Entity Resolution | Cross-Document Engine | E | `resolve_entity_match` | SRC-XDOC-01 | **VERIFIED** |
| `RULE-XDOC-CONTRADICTION` | Cross-Document Fact Contradiction Detection | Cross-Document Engine | E | `evaluate_semantic_claim_equivalence` | SRC-XDOC-02 | **VERIFIED** |
| `RULE-XDOC-INDEPENDENCE` | Document Provenance & OCR Pipeline Independence | Cross-Document Engine | E | `detect_document_independence` | SRC-XDOC-03 | **VERIFIED** |
| `RULE-SAFETY-INV-01` | Decision Safety Invariant 1: No Unsupported Pass on Missing Evidence | Decision Safety Layer | H | `DecisionSafetyLayer.enforce` | SRC-SAFETY-01 | **VERIFIED** |
| `RULE-SAFETY-INV-02` | Decision Safety Invariant 2: No Unsupported Fail on Ambiguous Evidence | Decision Safety Layer | H | `DecisionSafetyLayer.enforce` | SRC-SAFETY-01 | **VERIFIED** |
| `RULE-SAFETY-INV-03` | Decision Safety Invariant 3: Date Ambiguity Expiration Invariant | Decision Safety Layer | H | `DecisionSafetyLayer.enforce` | SRC-SAFETY-01 | **VERIFIED** |
| `RULE-SAFETY-INV-04` | Decision Safety Invariant 4: Single Source Verification Bar | Decision Safety Layer | H | `DecisionSafetyLayer.enforce` | SRC-SAFETY-01 | **VERIFIED** |
| `RULE-SAFETY-INV-05` | Decision Safety Invariant 5: Traceable Provenance Mandate | Decision Safety Layer | H | `DecisionSafetyLayer.enforce` | SRC-SAFETY-01 | **VERIFIED** |
| `RULE-SAFETY-INV-06` | Decision Safety Invariant 6: Slot Mismatch Quarantine | Decision Safety Layer | H | `DecisionSafetyLayer.enforce` | SRC-SAFETY-01 | **VERIFIED** |
| `RULE-SAFETY-INV-07` | Decision Safety Invariant 7: Confidence Floor Enforcement | Decision Safety Layer | H | `DecisionSafetyLayer.enforce` | SRC-SAFETY-01 | **VERIFIED** |
| `RULE-SAFETY-INV-08` | Decision Safety Invariant 8: Category Exemption Preservation | Decision Safety Layer | H | `DecisionSafetyLayer.enforce` | SRC-SAFETY-01 | **VERIFIED** |
| `RULE-SAFETY-INV-09` | Decision Safety Invariant 9: Weakest-Evidence Outcome Propagation | Decision Safety Layer | H | `DecisionSafetyLayer.enforce` | SRC-SAFETY-01 | **VERIFIED** |
| `RULE-SAFETY-INV-10` | Decision Safety Invariant 10: Deterministic Clock Invariance | Decision Safety Layer | H | `DecisionSafetyLayer.enforce` | SRC-SAFETY-01 | **VERIFIED** |

---

### Key Architectural Insights
1. **Declarative vs Procedural Division:** DocuReady maintains a declarative primitive engine (`src/docuready/rules/engine.py`) alongside an imperative legacy procedural validator (`src/docuready/rules/validator.py`). The declarative engine maps cleanly to statutory citations, while procedural code contains embedded business logic and heuristic penalties.
2. **Evidence-Grounded Abstention:** Rules in Family A (Identifiers) and Family B (Dates) strictly abstain on OCR ambiguities (e.g. O/0 confusion, ambiguous DD/MM vs MM/DD representations) unless invariant decision rules hold.
3. **Physical vs Policy Decoupling:** Family C and E cleanly decouple physical unit conversion (`1 MT == 1000 KG`) from cross-document compliance policies requiring documentary proof.