# Changelog — odisha.subhadra Scheme Pack

All notable changes to the `odisha.subhadra` scheme pack are documented in this file.

## [2024.1] - 2024-09-05 (Demonstration Snapshot Baseline)

### Added
- Initial declarative scheme pack implementation representing the FY 2024–25 Phase-I operational guidelines of the Odisha SUBHADRA Yojana.
- Grounded in Odisha Gazette Resolution No. 1637 (05.09.2024), W&CD Guidelines (Letter No. 19188/WCD dated 29.08.2024), and English SOP (Letter No. 26139/WCD dated 11.11.2024).
- Configured declarative `aadhaar_card` identity slot (`required: false` in `doc_slots`) and optional `bank_passbook`, `income_certificate`, and `ration_card` slots.
- Implemented `RULE-SUB-DOC-01` (pack-specific `require_document` rule for digital pre-check, distinguishing online automated scan verification from in-person Mo Seva Kendra assisted e-KYC per SOP Section 2; missing scan yields `Status.MISSING` without implying government rejection).
- Implemented `RULE-SUB-FLD-01` (Aadhaar legal name completeness).
- Implemented `RULE-SUB-AGE-01` (statutory age verification: ≥21 and <60 completed years as of `2024-07-01`, requiring DOB between `1964-07-02` and `2003-07-01`).
- Implemented `RULE-SUB-NAME-01` (Aadhaar vs Passbook demographic name match, capped at `REVIEW`).
- Configured `as_of_required: true` for clock-injected deterministic age evaluation.

### Added (Disclaimer & Exporter Integration)
- Applied the Product Owner-approved `DEMO SNAPSHOT — FY 2024–25 REFERENCE MATERIALS` historical disclaimer in `docs/BACKLOG.md`, `packs/odisha.subhadra/pack.yaml`, `docs/04-VALIDATION/SUBHADRA_SOURCE_VERIFICATION_MATRIX.md`, and the production report exporter (`src/docuready/report/exporter.py`).
- Clarified that `effective.to: 2025-03-31` is historical demo-snapshot metadata only and not an officially verified Government application closing date.
- Pending gates preserved: Akriti's source-review confirmation (`RULE-SUB-DOC-01`) and shared `field_present` cross-pack technical review remain open/blocked.

### Architecture Demarcation & Unimplemented Eligibility Rules
- The Subhadra family-income ceiling of ₹2,50,000 applies only to households without NFSA/SFSS coverage. The current DocuReady implementation has no trusted government database verification interface for NFSA/SFSS coverage. Therefore, the conditional income eligibility test is intentionally unimplemented. Applicant declarations and OCR-extracted values cannot establish household coverage or determine whether the income ceiling applies.
