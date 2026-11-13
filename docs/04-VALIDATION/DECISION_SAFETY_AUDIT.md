# DocuReady Loop 3 — Decision Safety Audit & Non-Rejection Proofs

## Executive Summary

Automated document verification systems in government benefit schemes face an asymmetric risk structure:
- **False Acceptance (Type I Error)**: Ineligible applicant admitted $\to$ administrative correction during post-audit.
- **False Rejection (Type II Error)**: Eligible low-income or marginalized applicant unlawfully denied financial support $\to$ civil rights infringement, constitutional violation of Article 14, and administrative appeals.

DocuReady Loop 3 enforces an **Independent Decision Safety Firewall** (`src/safety_layer.py`) operating between extraction and finding generation.

---

## The 8 Decision Safety Principles & Formal Audit

### Principle 1: Pass-Through of Confirmed Determinations
- **Rule**: Findings that are already `PASS`, `REVIEW`, or `UNKNOWN` require no safety downgrade from `FAIL`.
- **Implementation**: Checked at `safety_layer.py:48`.
- **Test Verification**: `test_safety_layer_pass_through_of_pass_and_review` PASSED.

### Principle 2: Statutory Reference Firewall
- **Rule**: Under Indian administrative law (*Maneka Gandhi v. Union of India*, AIR 1978 SC 597), an executive decision affecting individual rights cannot be made arbitrarily or without legal authority. A finding cannot trigger statutory ineligibility (`FAIL`) unless supported by a verified statutory rule, department notification, or official guideline clause.
- **Implementation**: `safety_layer.py:53-66`. If `statutory_reference` is empty or contains `"UNVERIFIED"`, the finding is downgraded to `REVIEW` with penalty capped at 10 points.
- **Test Verification**: `test_safety_firewall_unverified_statutory_reference` PASSED.

### Principle 3: Dual-Document Provenance Guarantee
- **Rule**: A cross-document contradiction (such as name mismatch between Application Form and Bank Passbook) cannot be asserted unless DocuReady establishes verifiable provenance from at least **two distinct documents**.
- **Implementation**: `safety_layer.py:70-87`. If `is_cross_doc` is detected, the safety layer verifies `len(doc_provenances) >= 2`. If evidence is only found from a single document, the finding is converted to `UNKNOWN (Single-Source Inconclusive)`.
- **Test Verification**: `test_safety_firewall_dual_source_provenance_guarantee` PASSED.

### Principle 4: Epistemic Uncertainty Intercept
- **Rule**: If the underlying evidence state is `LOW_CONFIDENCE`, `AMBIGUOUS`, or `UNREADABLE`, statutory `FAIL` is strictly prohibited.
- **Implementation**: `safety_layer.py:88-127`. Downgrades `FAIL` to `REVIEW` with an explicit notice: `"[SAFETY INTERCEPT: Statutory FAIL downgraded to REVIEW because supporting evidence is uncertain...]"`.
- **Test Verification**: `test_safety_firewall_ocr_low_confidence_downgrades_to_review` PASSED.

### Principle 5: Irrelevant Field Isolation
- **Rule**: Evidence uncertainty on an auxiliary field must NOT downgrade a confirmed violation on an independent verified field.
- **Problem Solved**: In early prototypes, an ambiguous issue date on an income certificate caused an income ceiling breach (₹3,20,000 > ₹2,50,000) to be downgraded to REVIEW, even though the income number was 100% verified.
- **Implementation**: `safety_layer.py:92-120` maps findings to their specific relevant field (`annual_income`, `dob`, `applicant_name`, etc.) and isolates evidence states.
- **Test Verification**: `test_safety_firewall_unrelated_field_uncertainty_does_not_downgrade` PASSED.

### Principle 6: Multi-Year Expiration Determinism under Ambiguous Dates
- **Rule**: If a certificate issue date has day/month ambiguity (`10/01/2020`), but the certificate is $\ge 4$ years old (issued in 2020 evaluated in 2026), the certificate is expired under **both** DD/MM and MM/DD interpretations.
- **Implementation**: `safety_layer.py:126-131` inspects the issue year. If `year <= current_year - 4`, date ambiguity does not block the expiration finding.
- **Test Verification**: `test_packet_against_ground_truth[PKT_06_MULTIPLE_DEFECTS]` PASSED.

### Principle 7: Non-Rejection on Illegible/Unreadable Scans
- **Rule**: An unreadable document (resolution $< 72\text{ DPI}$, extreme blur, or corrupted file) must produce `UNKNOWN` or advisory `REVIEW`, never statutory disqualification.
- **Implementation**: Evaluated in `extractor.py:333-343` and guarded by `safety_layer.py:101-105`.
- **Test Verification**: `test_unreadable_scan_produces_unknown_not_rejection` PASSED.

### Principle 8: Canonical Audit Trail and Remediation Guidance
- **Rule**: Safety-downgraded findings must preserve their canonical `rule_id` and provide specific remediation instructions explaining how the applicant can resolve the issue (e.g. upload high-resolution scan, visit Tahsil office).
- **Implementation**: `rule_id` is preserved intact while `status` is set to `FindingStatus.REVIEW` and remediation guidance is enriched.

---

## Summary of Safety Test Results

All 8 safety principles are covered by deterministic automated tests in `tests/test_safety_layer.py` and `tests/test_uncertainty_safety.py`.

```
docuready-mvp/tests/test_safety_layer.py::test_safety_layer_pass_through_of_pass_and_review PASSED
docuready-mvp/tests/test_safety_layer.py::test_safety_firewall_unverified_statutory_reference PASSED
docuready-mvp/tests/test_safety_layer.py::test_safety_firewall_dual_source_provenance_guarantee PASSED
docuready-mvp/tests/test_safety_layer.py::test_safety_firewall_ocr_low_confidence_downgrades_to_review PASSED
docuready-mvp/tests/test_safety_layer.py::test_safety_firewall_unrelated_field_uncertainty_does_not_downgrade PASSED
docuready-mvp/tests/test_uncertainty_safety.py::test_low_ocr_confidence_downgrades_to_review PASSED
docuready-mvp/tests/test_uncertainty_safety.py::test_date_of_birth_uncertain_ocr_produces_review PASSED
docuready-mvp/tests/test_uncertainty_safety.py::test_income_ceiling_uncertain_ocr_produces_review PASSED
docuready-mvp/tests/test_uncertainty_safety.py::test_sc_st_candidate_exempt_from_academic_cutoff PASSED
docuready-mvp/tests/test_uncertainty_safety.py::test_unreadable_scan_produces_unknown_not_rejection PASSED
```

**Zero false statutory rejections on uncertain or unverified evidence were observed across the entire test corpus.**
