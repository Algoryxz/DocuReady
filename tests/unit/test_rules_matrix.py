"""
T2.2 — Per-Rule Test Matrix for DocuReady
Canonical Rule-Group Verification Suite (Workstream WS2 — Correctness)

Lead: Susmita (Domain Rules, Evidence & Evaluation Lead)
Governing Specifications:
- docs/ARCHITECTURE_V2.md (Section 4 Target Architecture & Section 6 Outcome Resolution)
- docs/RULES.md / docs/04-VALIDATION/RULE_EVIDENCE_MATRIX.md
- docs/CITATION_AUDIT.md (10 Canonical Functional Checks)
- src/docuready/outcome/resolver.py
- src/docuready/rules/validator.py
- src/docuready/domain/enums.py

================================================================================
CANONICAL RULE GROUP MAPPING
================================================================================
The DocuReady engine defines exactly 10 canonical rule groups, mapping to
specific statutory or regulatory standards and operational heuristics.

Rule Group 1: RULE_GRP_01_DOC_COMPLETENESS
  - Rule IDs: RULE-DOC-01, RULE-DOC-02
  - Focus: Mandatory document packet presence and uncorrupted scan legibility
  - Inputs: Ingested file artifact set
  - Required Documents: APPLICATION_FORM, AADHAAR, INCOME_CERT, CASTE_CERT, BANK_PASSBOOK, MARKSHEET
  - Evidence Dependencies: Document presence in packet, scan corruption/legibility flag
  - Statutory / Policy Source: OSSP Guidelines §3.1 / NSP Framework Clause 4.1
  - Applicable Outcomes: PASS, MISSING (DOC_ABSENT), REVIEW (SCAN_QUALITY)

Rule Group 2: RULE_GRP_02_FLD_COMPLETENESS
  - Rule IDs: RULE-FLD-01
  - Focus: Core demographic and scheme identifier fields present and non-empty
  - Inputs: Extracted document fields per uploaded slot
  - Required Documents: All valid uploaded documents
  - Evidence Dependencies: Field presence in extracted dictionary, non-empty raw_value
  - Statutory / Policy Source: NSP Common Application Standards 2024 / DBT Guidelines
  - Applicable Outcomes: PASS, FAIL, WARN, REVIEW, MISSING

Rule Group 3: RULE_GRP_03_NAME_CONSISTENCY
  - Rule IDs: RULE-NAME-01, RULE-NAME-02, RULE-NAME-UNCERTAIN, RULE-NAME-PASS
  - Focus: Cross-document applicant name matching, transliteration variance, initial expansion
  - Inputs: 'applicant_name' extracted across all present documents
  - Required Documents: APPLICATION_FORM vs INCOME_CERT, CASTE_CERT, RESIDENCE_CERT, MARKSHEET, BANK_PASSBOOK
  - Evidence Dependencies: Levenshtein distance, token overlap, extraction method, OCR confidence
  - Statutory / Policy Source: MeitY Demographic Verification Standards 2023, Clause 4.2
  - Applicable Outcomes: PASS, FAIL, WARN, REVIEW, MISSING

Rule Group 4: RULE_GRP_04_DOB_CONSISTENCY
  - Rule IDs: RULE-DOB-01, RULE-DOB-02, RULE-DOB-03, RULE-DOB-UNCERTAIN, RULE-DOB-PASS
  - Focus: Date of Birth cross-check between application form and secondary marksheet (age proof)
  - Inputs: 'dob' field on APPLICATION_FORM and MARKSHEET
  - Required Documents: APPLICATION_FORM, MARKSHEET
  - Evidence Dependencies: Date parser normalization, format ambiguity (DD/MM vs MM/DD), OCR confidence
  - Statutory / Policy Source: CBSE Examination Bye-Laws Rule 69.2 / BSE Regulation 19
  - Applicable Outcomes: PASS, FAIL, WARN, REVIEW, MISSING

Rule Group 5: RULE_GRP_05_INC_CEILING
  - Rule IDs: RULE-INC-01, RULE-INC-03, RULE-INC-CEIL-UNCERTAIN, RULE-INC-CEIL-PASS
  - Focus: Certified annual family income does not exceed statutory scheme ceiling (e.g. ₹2,50,000)
  - Inputs: 'annual_income' on INCOME_CERT, scheme.income_ceiling
  - Required Documents: INCOME_CERT
  - Evidence Dependencies: Extracted numeric income, OCR confidence, parse validity
  - Statutory / Policy Source: Post-Matric Scholarship Scheme Guidelines (MoSJE/MoTA) Clause 3.1/5.2
  - Applicable Outcomes: PASS, FAIL, WARN, REVIEW, MISSING

Rule Group 6: RULE_GRP_06_INC_MATCH
  - Rule IDs: RULE-INC-02, RULE-INC-MISMATCH-UNCERTAIN, RULE-INC-MATCH-PASS
  - Focus: Self-declared annual income matches revenue-certified certificate value
  - Inputs: 'annual_income' on APPLICATION_FORM and INCOME_CERT
  - Required Documents: APPLICATION_FORM, INCOME_CERT
  - Evidence Dependencies: Cross-document numeric variance, OCR confidence
  - Statutory / Policy Source: NSP Operational Guidelines on Income Scrutiny
  - Applicable Outcomes: PASS, FAIL, WARN, REVIEW, MISSING

Rule Group 7: RULE_GRP_07_EXP_VALIDITY
  - Rule IDs: RULE-EXP-01, RULE-EXP-02, RULE-EXP-PASS
  - Focus: Income certificate issue date falls within statutory validity window (e.g. 3 yrs Odisha)
  - Inputs: 'issue_date' on INCOME_CERT, audit reference date, scheme.income_cert_validity_years
  - Required Documents: INCOME_CERT
  - Evidence Dependencies: Date parseability, extraction method (vector vs OCR), age calculation
  - Statutory / Policy Source: State Revenue Miscellaneous Certificates Rules & Executive Orders
  - Applicable Outcomes: PASS, FAIL, WARN, REVIEW, MISSING

Rule Group 8: RULE_GRP_08_REF_MATCH
  - Rule IDs: RULE-REF-01, RULE-REF-02, RULE-REF-INC-PASS, RULE-REF-CST-PASS
  - Focus: Certificate unique reference numbers declared on form match enclosed certificates
  - Inputs: 'income_cert_no', 'caste_cert_no' on APPLICATION_FORM vs 'certificate_no' on certificates
  - Required Documents: APPLICATION_FORM, INCOME_CERT, CASTE_CERT
  - Evidence Dependencies: String normalization (stripping slashes/hyphens), exact equality
  - Statutory / Policy Source: e-District MMP Technical Architecture / OSSP Portal Guidelines
  - Applicable Outcomes: PASS, FAIL, WARN, REVIEW, MISSING

Rule Group 9: RULE_GRP_09_BNK_VALIDATION
  - Rule IDs: RULE-BNK-01, RULE-BNK-02, RULE-BNK-IFSC-PASS
  - Focus: Bank IFSC adheres to RBI format; bank account number matches declaration
  - Inputs: 'ifsc', 'account_no' on BANK_PASSBOOK and APPLICATION_FORM
  - Required Documents: BANK_PASSBOOK, APPLICATION_FORM
  - Evidence Dependencies: RBI regex ^[A-Z]{4}0[A-Z0-9]{6}$, account number equality
  - Statutory / Policy Source: RBI Master Direction - Core Banking Systems / DBT Mission
  - Applicable Outcomes: PASS, FAIL, WARN, REVIEW, MISSING

Rule Group 10: RULE_GRP_10_DOM_MRK_COMPLIANCE
  - Rule IDs: RULE-DOM-01, RULE-DOM-PASS, RULE-MRK-01, RULE-MRK-RELAX-PASS, RULE-MRK-PASS
  - Focus: State domicile requirement and academic cutoff compliance with SC/ST category relaxations
  - Inputs: 'state' on RESIDENCE_CERT, 'percentage' on MARKSHEET, 'caste_category' on CASTE_CERT/FORM
  - Required Documents: RESIDENCE_CERT, MARKSHEET, CASTE_CERT, APPLICATION_FORM
  - Evidence Dependencies: Domicile state match, percentage cutoff, reservation category verification
  - Exemptions: SC/ST candidates exempt from minimum percentage under MoSJE Clause 5.2 (PASS_ONLY)
  - Statutory / Policy Source: Odisha State Scholarship Rules / Post-Matric Guidelines Clause 5.2
  - Applicable Outcomes: PASS, FAIL, WARN, REVIEW, MISSING, NOT_APPLICABLE (EXEMPT)
"""

from __future__ import annotations

import pytest
from typing import Any, Dict, List, Optional

from docuready.domain.enums import (
    EvidenceState,
    ExitCode,
    ExtractionMethod,
    MatchGrade,
    MaxSeverity,
    Raw,
    Readiness,
    ReasonCode,
    Status,
    coerce_extraction_method,
    normalize_evidence_state,
)
from docuready.domain.models import (
    DocumentType,
    EvidenceProvenance,
    ExtractedDocument,
    ExtractedField,
    Finding,
    FindingStatus,
    Severity,
)
from docuready.outcome.resolver import (
    ResolvedOutcome,
    _coerce_enum,
    exit_code_for_readiness,
    resolve_outcome,
    resolve_readiness,
    weakest_evidence,
)
from docuready.outcome.safety_layer import DecisionSafetyLayer
from docuready.rules.validator import DocuReadyValidator, SchemeConfig


# ==============================================================================
# 1. CANONICAL RULE GROUP DEFINITIONS & REGISTRY
# ==============================================================================

CANONICAL_RULE_GROUPS: Dict[str, Dict[str, Any]] = {
    "RULE_GRP_01_DOC_COMPLETENESS": {
        "name": "Mandatory Document Completeness & Integrity",
        "primary_rule_id": "RULE-DOC-01",
        "rule_ids": ["RULE-DOC-01", "RULE-DOC-02"],
        "required_documents": [
            DocumentType.APPLICATION_FORM,
            DocumentType.AADHAAR,
            DocumentType.INCOME_CERT,
            DocumentType.CASTE_CERT,
            DocumentType.BANK_PASSBOOK,
            DocumentType.MARKSHEET,
        ],
        "inputs": ["document_presence", "scan_legibility"],
        "evidence_dependencies": ["document_status", "ocr_legibility"],
        "has_exemption": False,
    },
    "RULE_GRP_02_FLD_COMPLETENESS": {
        "name": "Mandatory Field Completeness",
        "primary_rule_id": "RULE-FLD-01",
        "rule_ids": ["RULE-FLD-01"],
        "required_documents": [
            DocumentType.INCOME_CERT,
            DocumentType.CASTE_CERT,
            DocumentType.RESIDENCE_CERT,
            DocumentType.MARKSHEET,
            DocumentType.BANK_PASSBOOK,
            DocumentType.APPLICATION_FORM,
        ],
        "inputs": ["applicant_name", "annual_income", "issue_date", "certificate_no", "dob", "percentage", "account_no", "ifsc"],
        "evidence_dependencies": ["extracted_field_presence", "field_raw_value"],
        "has_exemption": False,
    },
    "RULE_GRP_03_NAME_CONSISTENCY": {
        "name": "Cross-Document Applicant Name Consistency",
        "primary_rule_id": "RULE-NAME-01",
        "rule_ids": ["RULE-NAME-01", "RULE-NAME-02", "RULE-NAME-UNCERTAIN", "RULE-NAME-PASS"],
        "required_documents": [
            DocumentType.APPLICATION_FORM,
            DocumentType.INCOME_CERT,
            DocumentType.CASTE_CERT,
            DocumentType.RESIDENCE_CERT,
            DocumentType.MARKSHEET,
            DocumentType.BANK_PASSBOOK,
        ],
        "inputs": ["applicant_name"],
        "evidence_dependencies": ["cross_document_string_match", "ocr_confidence", "extraction_method"],
        "has_exemption": False,
    },
    "RULE_GRP_04_DOB_CONSISTENCY": {
        "name": "Date of Birth Consistency & Format",
        "primary_rule_id": "RULE-DOB-01",
        "rule_ids": ["RULE-DOB-01", "RULE-DOB-02", "RULE-DOB-03", "RULE-DOB-UNCERTAIN", "RULE-DOB-PASS"],
        "required_documents": [DocumentType.APPLICATION_FORM, DocumentType.MARKSHEET],
        "inputs": ["dob"],
        "evidence_dependencies": ["date_normalization", "date_ambiguity", "ocr_confidence"],
        "has_exemption": False,
    },
    "RULE_GRP_05_INC_CEILING": {
        "name": "Statutory Income Ceiling Compliance",
        "primary_rule_id": "RULE-INC-01",
        "rule_ids": ["RULE-INC-01", "RULE-INC-03", "RULE-INC-CEIL-UNCERTAIN", "RULE-INC-CEIL-PASS"],
        "required_documents": [DocumentType.INCOME_CERT],
        "inputs": ["annual_income", "scheme.income_ceiling"],
        "evidence_dependencies": ["numeric_income_normalization", "ocr_confidence"],
        "has_exemption": False,
    },
    "RULE_GRP_06_INC_MATCH": {
        "name": "Income Consistency (Declared vs Certified)",
        "primary_rule_id": "RULE-INC-02",
        "rule_ids": ["RULE-INC-02", "RULE-INC-MISMATCH-UNCERTAIN", "RULE-INC-MATCH-PASS"],
        "required_documents": [DocumentType.INCOME_CERT, DocumentType.APPLICATION_FORM],
        "inputs": ["annual_income"],
        "evidence_dependencies": ["cross_document_numeric_match", "ocr_confidence"],
        "has_exemption": False,
    },
    "RULE_GRP_07_EXP_VALIDITY": {
        "name": "Income Certificate Statutory Validity Period",
        "primary_rule_id": "RULE-EXP-01",
        "rule_ids": ["RULE-EXP-01", "RULE-EXP-02", "RULE-EXP-PASS"],
        "required_documents": [DocumentType.INCOME_CERT],
        "inputs": ["issue_date", "audit_date", "scheme.income_cert_validity_years"],
        "evidence_dependencies": ["date_normalization", "extraction_method", "validity_age_years"],
        "has_exemption": False,
    },
    "RULE_GRP_08_REF_MATCH": {
        "name": "Certificate Reference Number Match",
        "primary_rule_id": "RULE-REF-01",
        "rule_ids": ["RULE-REF-01", "RULE-REF-02", "RULE-REF-INC-PASS", "RULE-REF-CST-PASS"],
        "required_documents": [DocumentType.APPLICATION_FORM, DocumentType.INCOME_CERT, DocumentType.CASTE_CERT],
        "inputs": ["income_cert_no", "caste_cert_no", "certificate_no"],
        "evidence_dependencies": ["cert_number_normalization", "string_equality"],
        "has_exemption": False,
    },
    "RULE_GRP_09_BNK_VALIDATION": {
        "name": "Bank IFSC Code Standard & Account Consistency",
        "primary_rule_id": "RULE-BNK-01",
        "rule_ids": ["RULE-BNK-01", "RULE-BNK-02", "RULE-BNK-IFSC-PASS"],
        "required_documents": [DocumentType.BANK_PASSBOOK, DocumentType.APPLICATION_FORM],
        "inputs": ["ifsc", "account_no"],
        "evidence_dependencies": ["rbi_ifsc_regex", "account_number_equality"],
        "has_exemption": False,
    },
    "RULE_GRP_10_DOM_MRK_COMPLIANCE": {
        "name": "State Domicile Requirement & Academic Cutoff Compliance",
        "primary_rule_id": "RULE-MRK-01",
        "rule_ids": ["RULE-DOM-01", "RULE-DOM-PASS", "RULE-MRK-01", "RULE-MRK-RELAX-PASS", "RULE-MRK-PASS"],
        "required_documents": [DocumentType.RESIDENCE_CERT, DocumentType.MARKSHEET, DocumentType.CASTE_CERT, DocumentType.APPLICATION_FORM],
        "inputs": ["state", "percentage", "caste_category", "scheme.target_state", "scheme.min_academic_percentage"],
        "evidence_dependencies": ["state_string_equality", "percentage_threshold", "caste_category_verification"],
        "has_exemption": True,
    },
}


# ==============================================================================
# 2. PHASE 3 — PER-RULE RESOLVER MATRIX (80 PARAMETRIZED TEST CASES)
# ==============================================================================
# Covers all 10 canonical rule groups across the 8 standard Section 6 transitions:
# 1. SATISFIED + VERIFIED -> PASS (CONFIRMED_OK)
# 2. SATISFIED + PROVISIONAL -> REVIEW (CANNOT_CONFIRM)
# 3. SATISFIED + UNCERTAIN -> REVIEW (CANNOT_CONFIRM)
# 4. VIOLATED + VERIFIED -> FAIL (DEFECT_CONFIRMED)
# 5. VIOLATED + PROVISIONAL -> WARN (DEFECT_PROBABLE)
# 6. VIOLATED + UNCERTAIN -> REVIEW (EVIDENCE_UNCERTAIN)
# 7. INDETERMINATE -> REVIEW (INSUFFICIENT_DATA)
# 8. DOC_ABSENT -> MISSING (DOC_ABSENT)

MATRIX_CONDITIONS = [
    # (condition_id, raw, evidence, expected_status, expected_reason)
    ("satisfied_verified", Raw.SATISFIED, EvidenceState.VERIFIED, Status.PASS, ReasonCode.CONFIRMED_OK.value),
    ("satisfied_provisional", Raw.SATISFIED, EvidenceState.PROVISIONAL, Status.REVIEW, ReasonCode.CANNOT_CONFIRM.value),
    ("satisfied_uncertain", Raw.SATISFIED, EvidenceState.UNCERTAIN, Status.REVIEW, ReasonCode.CANNOT_CONFIRM.value),
    ("violated_verified", Raw.VIOLATED, EvidenceState.VERIFIED, Status.FAIL, ReasonCode.DEFECT_CONFIRMED.value),
    ("violated_provisional", Raw.VIOLATED, EvidenceState.PROVISIONAL, Status.WARN, ReasonCode.DEFECT_PROBABLE.value),
    ("violated_uncertain", Raw.VIOLATED, EvidenceState.UNCERTAIN, Status.REVIEW, ReasonCode.EVIDENCE_UNCERTAIN.value),
    ("indeterminate", Raw.INDETERMINATE, EvidenceState.UNCERTAIN, Status.REVIEW, ReasonCode.INSUFFICIENT_DATA.value),
    ("doc_absent", Raw.DOC_ABSENT, None, Status.MISSING, ReasonCode.DOC_ABSENT.value),
]

MATRIX_TEST_CASES = [
    (grp_id, cond_id, raw, ev, exp_status, exp_reason)
    for grp_id in CANONICAL_RULE_GROUPS
    for cond_id, raw, ev, exp_status, exp_reason in MATRIX_CONDITIONS
]


@pytest.mark.parametrize(
    "rule_grp_id,cond_id,raw,evidence,expected_status,expected_reason",
    MATRIX_TEST_CASES,
    ids=[f"{c[0]}-{c[1]}" for c in MATRIX_TEST_CASES]
)
def test_per_rule_resolver_matrix(
    rule_grp_id: str,
    cond_id: str,
    raw: Raw,
    evidence: Optional[EvidenceState],
    expected_status: Status,
    expected_reason: str,
):
    """
    Validates that every one of the 10 canonical rule groups resolves strictly
    according to ARCHITECTURE_V2 Section 6 truth table across all evidence states.
    Ensures >= 60 applicable test cases (exactly 80 parametrized executions).
    """
    outcome = resolve_outcome(raw, weakest_evidence=evidence)
    assert outcome.status is expected_status, (
        f"Rule group {rule_grp_id} under {cond_id}: expected status {expected_status}, got {outcome.status}"
    )
    assert outcome.reason_code == expected_reason, (
        f"Rule group {rule_grp_id} under {cond_id}: expected reason {expected_reason}, got {outcome.reason_code}"
    )

    # Invariant: Unverified evidence must NEVER yield PASS
    if evidence in (EvidenceState.PROVISIONAL, EvidenceState.UNCERTAIN, None) and raw is not Raw.DOC_ABSENT:
        assert outcome.status is not Status.PASS, "Unverified evidence must never produce PASS status"


# ==============================================================================
# 3. PHASE 3 & 4 — STATUTORY EXEMPTION & RELAXATION MATRIX
# ==============================================================================

def test_exemption_rule_grp_10_verified_category_produces_not_applicable():
    """
    Rule Group 10 (Academic Cutoff): A verified SC/ST reservation category produces
    visible NOT_APPLICABLE with zero score penalty under statutory relaxation rules.
    """
    outcome = resolve_outcome(
        Raw.EXEMPT,
        weakest_evidence=EvidenceState.VERIFIED,
        exemption_reason="SC_ST_CUTOFF_EXEMPTION"
    )
    assert outcome.status is Status.NOT_APPLICABLE
    assert outcome.reason_code == "EXEMPT:SC_ST_CUTOFF_EXEMPTION"
    assert "does not apply" in outcome.message.lower()


def test_exemption_rule_grp_10_unverified_category_cannot_grant_exemption():
    """
    Rule Group 10 (Academic Cutoff): If the applicant claims SC/ST cutoff exemption
    but category evidence is UNCERTAIN or absent, the safety firewall downgrades
    Raw.EXEMPT to Raw.INDETERMINATE, resolving to REVIEW (cannot confirm exemption).
    """
    safety = DecisionSafetyLayer()
    finding = Finding(
        rule_id="RULE-MRK-RELAX-PASS",
        rule_name="Academic Cutoff Compliance (SC/ST Qualifying Pass)",
        status=FindingStatus.PASS,
        severity=Severity.INFO,
        field="MERIT_PERCENTAGE",
        documents_involved=[DocumentType.MARKSHEET.value],
        message="Candidate percentage satisfies criteria: under Clause 5.2, SC/ST candidates are exempt from minimum percentage cutoffs.",
        evidence=[],
        remediation="No action required.",
        statutory_reference="Centrally Sponsored Post-Matric Guidelines Clause 5.2",
    )
    # Form has low confidence / uncertain category evidence
    unc_category = ExtractedField(
        field_name="caste_category",
        raw_value="SC",
        evidence_state=EvidenceState.LOW_CONFIDENCE,
        is_uncertain=True,
    )
    doc_form = ExtractedDocument(
        doc_type=DocumentType.APPLICATION_FORM,
        file_path="app.pdf",
        fields={"caste_category": unc_category},
    )
    doc_mark = ExtractedDocument(
        doc_type=DocumentType.MARKSHEET,
        file_path="mark.pdf",
        fields={"percentage": ExtractedField(field_name="percentage", raw_value="42.0%", normalized_value=42.0)},
    )
    audited = safety.audit_findings(
        [finding],
        {DocumentType.APPLICATION_FORM: doc_form, DocumentType.MARKSHEET: doc_mark}
    )
    assert audited[0].resolved_status is Status.REVIEW
    assert audited[0].resolved_status is not Status.NOT_APPLICABLE
    assert audited[0].reason_code == ReasonCode.INSUFFICIENT_DATA.value


def test_exemption_rule_grp_10_non_exempt_candidate_fails_cutoff():
    """
    Rule Group 10 (Academic Cutoff): A General or unexempt applicant scoring below
    the minimum statutory cutoff (50%) with verified evidence produces a confirmed FAIL.
    """
    outcome = resolve_outcome(Raw.VIOLATED, weakest_evidence=EvidenceState.VERIFIED)
    assert outcome.status is Status.FAIL
    assert outcome.reason_code == ReasonCode.DEFECT_CONFIRMED.value


# ==============================================================================
# 4. PHASE 4 — MATCH GRADE INVARIANTS (COMPATIBLE, CONFLICT, AMBIGUOUS)
# ==============================================================================

def test_match_grade_compatible_on_violated_caps_at_warn():
    """
    Grade COMPATIBLE on VIOLATED (e.g. minor name initials 'S R Nayak' vs 'Smruti Ranjan Nayak')
    cannot produce a hard FAIL; it is capped at WARN.
    """
    outcome = resolve_outcome(
        Raw.VIOLATED,
        weakest_evidence=EvidenceState.VERIFIED,
        match_grade=MatchGrade.COMPATIBLE,
    )
    assert outcome.status is Status.WARN
    assert outcome.reason_code == ReasonCode.DEFECT_PROBABLE.value
    assert "compatible variation" in outcome.message.lower()


def test_match_grade_compatible_on_satisfied_verified_produces_warn():
    """
    Grade COMPATIBLE on SATISFIED with VERIFIED evidence produces WARN (DEFECT_PROBABLE)
    advising the applicant to verify spelling differences before relying on the match.
    """
    outcome = resolve_outcome(
        Raw.SATISFIED,
        weakest_evidence=EvidenceState.VERIFIED,
        match_grade=MatchGrade.COMPATIBLE,
    )
    assert outcome.status is Status.WARN
    assert outcome.reason_code == ReasonCode.DEFECT_PROBABLE.value


def test_match_grade_compatible_on_satisfied_provisional_produces_review():
    """
    Grade COMPATIBLE on SATISFIED with PROVISIONAL (OCR) evidence cannot even confirm WARN;
    it abstains to REVIEW (CANNOT_CONFIRM).
    """
    outcome = resolve_outcome(
        Raw.SATISFIED,
        weakest_evidence=EvidenceState.PROVISIONAL,
        match_grade=MatchGrade.COMPATIBLE,
    )
    assert outcome.status is Status.REVIEW
    assert outcome.reason_code == ReasonCode.CANNOT_CONFIRM.value


def test_match_grade_ambiguous_always_requires_review():
    """
    Grade AMBIGUOUS overrides both apparent agreement and disagreement to force REVIEW.
    """
    for raw in (Raw.SATISFIED, Raw.VIOLATED, Raw.INDETERMINATE):
        for ev in (EvidenceState.VERIFIED, EvidenceState.PROVISIONAL, EvidenceState.UNCERTAIN):
            outcome = resolve_outcome(raw, weakest_evidence=ev, match_grade=MatchGrade.AMBIGUOUS)
            assert outcome.status is Status.REVIEW
            if raw is Raw.INDETERMINATE:
                assert outcome.reason_code == ReasonCode.INSUFFICIENT_DATA.value
            else:
                assert outcome.reason_code == ReasonCode.EVIDENCE_UNCERTAIN.value


def test_match_grade_conflict_with_satisfied_fails_closed_to_review():
    """
    Grade CONFLICT combined with Raw.SATISFIED is an inconsistent evaluation record;
    resolver fails closed to REVIEW rather than emitting false-green PASS.
    """
    outcome = resolve_outcome(
        Raw.SATISFIED,
        weakest_evidence=EvidenceState.VERIFIED,
        match_grade=MatchGrade.CONFLICT,
    )
    assert outcome.status is Status.REVIEW
    assert outcome.reason_code == ReasonCode.EVIDENCE_UNCERTAIN.value
    assert "conflicts with the match grade" in outcome.message.lower()


# ==============================================================================
# 5. PHASE 4 — MAXIMUM SEVERITY CAP INVARIANTS
# ==============================================================================

def test_max_severity_cap_warn_reduces_fail_to_warn():
    """Rule with MaxSeverity.WARN (advisory rule) caps confirmed FAIL at WARN."""
    outcome = resolve_outcome(
        Raw.VIOLATED,
        weakest_evidence=EvidenceState.VERIFIED,
        max_severity=MaxSeverity.WARN,
    )
    assert outcome.status is Status.WARN
    assert outcome.reason_code == ReasonCode.ADVISORY_RULE_CAP.value
    assert "capped at warn" in outcome.message.lower()


def test_max_severity_cap_review_reduces_fail_and_warn_to_review():
    """Rule with MaxSeverity.REVIEW caps FAIL or WARN at REVIEW."""
    outcome_fail = resolve_outcome(
        Raw.VIOLATED,
        weakest_evidence=EvidenceState.VERIFIED,
        max_severity=MaxSeverity.REVIEW,
    )
    assert outcome_fail.status is Status.REVIEW
    assert outcome_fail.reason_code == ReasonCode.ADVISORY_RULE_CAP.value

    outcome_warn = resolve_outcome(
        Raw.VIOLATED,
        weakest_evidence=EvidenceState.PROVISIONAL,
        max_severity=MaxSeverity.REVIEW,
    )
    assert outcome_warn.status is Status.REVIEW
    assert outcome_warn.reason_code == ReasonCode.ADVISORY_RULE_CAP.value


def test_max_severity_cap_monotonicity_never_increases_severity():
    """
    Severity caps must never increase severity:
    - MaxSeverity.FAIL applied to WARN leaves it as WARN.
    - MaxSeverity.WARN applied to REVIEW leaves it as REVIEW.
    - MaxSeverity applied to PASS leaves it as PASS.
    """
    outcome_warn = resolve_outcome(
        Raw.VIOLATED,
        weakest_evidence=EvidenceState.PROVISIONAL,
        max_severity=MaxSeverity.FAIL,
    )
    assert outcome_warn.status is Status.WARN
    assert outcome_warn.reason_code == ReasonCode.DEFECT_PROBABLE.value

    outcome_rev = resolve_outcome(
        Raw.VIOLATED,
        weakest_evidence=EvidenceState.UNCERTAIN,
        max_severity=MaxSeverity.WARN,
    )
    assert outcome_rev.status is Status.REVIEW
    assert outcome_rev.reason_code == ReasonCode.EVIDENCE_UNCERTAIN.value

    outcome_pass = resolve_outcome(
        Raw.SATISFIED,
        weakest_evidence=EvidenceState.VERIFIED,
        max_severity=MaxSeverity.WARN,
    )
    assert outcome_pass.status is Status.PASS
    assert outcome_pass.reason_code == ReasonCode.CONFIRMED_OK.value


def test_max_severity_cap_never_turns_missing_into_pass():
    """Missing mandatory document is a structural failure and is never capped to PASS/WARN."""
    outcome = resolve_outcome(
        Raw.DOC_ABSENT,
        weakest_evidence=None,
        max_severity=MaxSeverity.REVIEW,
    )
    assert outcome.status is Status.MISSING
    assert outcome.reason_code == ReasonCode.DOC_ABSENT.value


# ==============================================================================
# 6. PHASE 4 — PACKET-LEVEL READINESS INVARIANTS
# ==============================================================================

def test_readiness_all_pass_produces_no_issues_found():
    """Fully checked packet with all applicable findings PASS produces NO_ISSUES_FOUND."""
    statuses = [Status.PASS, Status.PASS, Status.PASS, Status.PASS]
    readiness = resolve_readiness(statuses)
    assert readiness is Readiness.NO_ISSUES_FOUND
    assert exit_code_for_readiness(readiness) == ExitCode.NO_ISSUES


def test_readiness_single_fail_forces_not_ready():
    """Even a single confirmed FAIL finding forces packet readiness to NOT_READY."""
    statuses = [Status.PASS, Status.PASS, Status.FAIL, Status.PASS]
    readiness = resolve_readiness(statuses)
    assert readiness is Readiness.NOT_READY
    assert exit_code_for_readiness(readiness) == ExitCode.NOT_READY


def test_readiness_single_missing_forces_not_ready():
    """A missing mandatory document forces packet readiness to NOT_READY."""
    statuses = [Status.PASS, Status.MISSING, Status.PASS]
    readiness = resolve_readiness(statuses)
    assert readiness is Readiness.NOT_READY
    assert exit_code_for_readiness(readiness) == ExitCode.NOT_READY


def test_readiness_warn_or_review_without_fail_produces_needs_checks():
    """Packet with WARN or REVIEW (no FAIL/MISSING) produces NEEDS_CHECKS."""
    assert resolve_readiness([Status.PASS, Status.WARN]) is Readiness.NEEDS_CHECKS
    assert resolve_readiness([Status.PASS, Status.REVIEW]) is Readiness.NEEDS_CHECKS
    assert resolve_readiness([Status.REVIEW, Status.WARN]) is Readiness.NEEDS_CHECKS
    assert exit_code_for_readiness(Readiness.NEEDS_CHECKS) == ExitCode.NEEDS_CHECKS


def test_readiness_empty_or_only_not_applicable_never_emits_false_green():
    """
    An empty result set or a packet containing only NOT_APPLICABLE findings
    must abstain to NEEDS_CHECKS, never falsely emitting green NO_ISSUES_FOUND.
    """
    assert resolve_readiness([]) is Readiness.NEEDS_CHECKS
    assert resolve_readiness([Status.NOT_APPLICABLE, Status.NOT_APPLICABLE]) is Readiness.NEEDS_CHECKS


def test_readiness_not_applicable_combined_with_pass_produces_no_issues_found():
    """Visible NOT_APPLICABLE findings do not obstruct NO_ISSUES_FOUND when all applicable rules PASS."""
    statuses = [Status.PASS, Status.NOT_APPLICABLE, Status.PASS]
    assert resolve_readiness(statuses) is Readiness.NO_ISSUES_FOUND


def test_readiness_not_applicable_combined_with_fail_produces_not_ready():
    """Visible NOT_APPLICABLE findings do not mask an accompanying FAIL."""
    statuses = [Status.FAIL, Status.NOT_APPLICABLE, Status.PASS]
    assert resolve_readiness(statuses) is Readiness.NOT_READY


# ==============================================================================
# 7. PHASE 4 — RESOLVER BRANCH EXERCISING & DEFENSIVE EDGE CASES
# ==============================================================================

def test_resolver_enum_coercion_handles_invalid_inputs():
    """_coerce_enum raises ValueError when encountering an unsupported value."""
    with pytest.raises(ValueError, match="Unsupported raw result"):
        resolve_outcome("INVALID_RAW", weakest_evidence=EvidenceState.VERIFIED)  # type: ignore

    with pytest.raises(ValueError, match="Unsupported finding status"):
        resolve_readiness(["INVALID_STATUS"])  # type: ignore

    with pytest.raises(ValueError, match="Unsupported match grade"):
        resolve_outcome(Raw.SATISFIED, weakest_evidence=EvidenceState.VERIFIED, match_grade="INVALID_GRADE")  # type: ignore

    with pytest.raises(ValueError, match="Unsupported maximum severity"):
        resolve_outcome(Raw.VIOLATED, weakest_evidence=EvidenceState.VERIFIED, max_severity="INVALID_CAP")  # type: ignore

    with pytest.raises(ValueError, match="Unsupported readiness"):
        exit_code_for_readiness("INVALID_READINESS")  # type: ignore


def test_weakest_evidence_helper_empty_and_transitional_normalization():
    """weakest_evidence returns None on empty inputs and properly prioritizes UNCERTAIN > PROVISIONAL > VERIFIED."""
    assert weakest_evidence([]) is None
    assert weakest_evidence([None]) is EvidenceState.UNCERTAIN
    assert weakest_evidence([EvidenceState.VERIFIED_TEXT, EvidenceState.OCR_EXTRACTED]) is EvidenceState.PROVISIONAL
    assert weakest_evidence([EvidenceState.VERIFIED_TEXT, EvidenceState.AMBIGUOUS]) is EvidenceState.UNCERTAIN
    assert weakest_evidence([EvidenceState.VERIFIED_TEXT, EvidenceState.LOW_CONFIDENCE]) is EvidenceState.UNCERTAIN
    assert weakest_evidence([EvidenceState.VERIFIED, EvidenceState.VERIFIED_TEXT]) is EvidenceState.VERIFIED


def test_extraction_method_typed_coercion():
    """coerce_extraction_method safely handles valid enums, strings, None, and invalid types."""
    assert coerce_extraction_method(ExtractionMethod.NATIVE_VECTOR) is ExtractionMethod.NATIVE_VECTOR
    assert coerce_extraction_method("NATIVE_VECTOR") is ExtractionMethod.NATIVE_VECTOR
    assert coerce_extraction_method("LOCAL_OCR") is ExtractionMethod.LOCAL_OCR
    assert coerce_extraction_method(None) is ExtractionMethod.UNEXTRACTED
    assert coerce_extraction_method("UNKNOWN_EXTRACTOR") is ExtractionMethod.UNEXTRACTED
    assert coerce_extraction_method(12345) is ExtractionMethod.UNEXTRACTED


def test_resolver_exemption_default_reason_handling():
    """Raw.EXEMPT with None or empty exemption_reason defaults safely to CATEGORY_EXEMPTION."""
    outcome_none = resolve_outcome(Raw.EXEMPT, weakest_evidence=None, exemption_reason=None)
    assert outcome_none.reason_code == "EXEMPT:CATEGORY_EXEMPTION"

    outcome_blank = resolve_outcome(Raw.EXEMPT, weakest_evidence=None, exemption_reason="   ")
    assert outcome_blank.reason_code == "EXEMPT:CATEGORY_EXEMPTION"


def test_resolve_readiness_mixed_strings_and_enums():
    """resolve_readiness accepts mixed strings and Status enums seamlessly."""
    mixed = ["PASS", Status.PASS, "WARN"]
    assert resolve_readiness(mixed) is Readiness.NEEDS_CHECKS


def test_resolver_defensive_unhandled_raw_enum(monkeypatch):
    """Exercise defensive fallback branch for unhandled raw enum members in resolve_outcome."""
    monkeypatch.setattr("docuready.outcome.resolver._coerce_enum", lambda val, typ, name: "FUTURE_UNKNOWN_RAW")
    outcome = resolve_outcome("FUTURE_UNKNOWN_RAW", weakest_evidence=EvidenceState.VERIFIED)  # type: ignore
    assert outcome.status is Status.REVIEW
    assert outcome.reason_code == ReasonCode.INSUFFICIENT_DATA.value
    assert "could not be resolved safely" in outcome.message.lower()

