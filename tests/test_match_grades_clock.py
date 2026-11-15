"""
Comprehensive tests for Task T2.3: Match Grades and Injected Clock (as_of).
Verifies:
1. Replaying a saved packet with the same as_of gives byte-for-byte identical reports.
2. Injected clock shifts certificate validity deterministically across expiration boundaries.
3. Conflicting as_of and audit_date parameters raise ValueError.
4. No datetime.now() or date.today() calls exist in rules/, outcome/, or normalize/.
5. MatchGrade rules: COMPATIBLE caps at WARN, AMBIGUOUS forces REVIEW, CONFLICT fails.
6. AuditResult.to_public_dict() exposes as_of and match_grade while model_dump() excludes them.
7. Income tolerance configuration in SchemeConfig.
"""

import ast
import json
import os
import tempfile
from datetime import date
from pathlib import Path
import pytest

from docuready.domain.enums import (
    EvidenceState,
    MatchGrade,
    Raw,
    Readiness,
    Status,
)
from docuready.domain.models import (
    AuditResult,
    DocumentType,
    EvidenceProvenance,
    ExtractedDocument,
    ExtractedField,
    Finding,
    FindingStatus,
    Severity,
)
from docuready.outcome.resolver import resolve_outcome
from docuready.pipeline import AuditPipeline
from docuready.report.exporter import (
    export_audit_report_json,
    generate_readiness_summary_markdown,
)
from docuready.rules.validator import DocuReadyValidator, SchemeConfig

_REPO_ROOT = Path(__file__).resolve().parents[1]


def test_injected_clock_reproducibility():
    """Replaying a packet with the same as_of gives byte-for-byte identical reports via canonical projection."""
    packet_dir = str(_REPO_ROOT / "synthetic_data" / "pkt_01_clean")
    as_of_date = date(2026, 11, 13)

    pipeline = AuditPipeline(as_of=as_of_date)
    res1, _ = pipeline.load_and_audit_packet(packet_dir, packet_id="PKT_01_CLEAN", as_of=as_of_date)
    res2, _ = pipeline.load_and_audit_packet(packet_dir, packet_id="PKT_01_CLEAN", as_of=as_of_date)

    assert res1.as_of == "2026-11-13"
    assert res2.as_of == "2026-11-13"
    # Generation timestamp is actual execution time, distinct from deterministic as_of date
    assert res1.timestamp != "2026-11-13T00:00:00"
    assert res2.timestamp != "2026-11-13T00:00:00"
    assert "T" in res1.timestamp
    assert "T" in res2.timestamp

    # Canonical projection excludes volatile runtime metrics (latency, execution timestamp)
    # without mutating the result instances
    assert res1.to_canonical_dict() == res2.to_canonical_dict()

    with tempfile.TemporaryDirectory() as tmpdir:
        path1 = os.path.join(tmpdir, "report1.json")
        path2 = os.path.join(tmpdir, "report2.json")

        export_audit_report_json(res1, path1, redact=False, canonical=True)
        export_audit_report_json(res2, path2, redact=False, canonical=True)

        with open(path1, "r", encoding="utf-8") as f:
            content1 = f.read()
        with open(path2, "r", encoding="utf-8") as f:
            content2 = f.read()

        assert content1 == content2

    md1 = generate_readiness_summary_markdown(res1, redact=False, canonical=True)
    md2 = generate_readiness_summary_markdown(res2, redact=False, canonical=True)

    assert md1 == md2
    assert "**Effective As Of:** `2026-11-13`" in md1
    assert "Audit Generation Timestamp" not in md1  # Excluded in canonical replay
    assert "Execution Latency" not in md1

    md_live = generate_readiness_summary_markdown(res1, redact=False, canonical=False)
    assert "**Effective As Of:** `2026-11-13`" in md_live
    assert "**Audit Generation Timestamp:**" in md_live
    assert "**Execution Latency:**" in md_live


def test_injected_clock_boundary_crossing():
    """Shifting as_of across the 3-year validity window deterministically flips certificate expiration."""
    packet_dir = str(_REPO_ROOT / "synthetic_data" / "pkt_01_clean")
    pipeline = AuditPipeline(as_of=date(2026, 11, 13))

    # On Nov 13, 2026: certificate issued 2025-01-10 is ~1.8 years old <= 3 years -> PASS
    res_valid, _ = pipeline.load_and_audit_packet(
        packet_dir, packet_id="PKT_01_CLEAN", as_of=date(2026, 11, 13)
    )
    exp_pass = [f for f in res_valid.findings if f.rule_id == "RULE-EXP-PASS"]
    assert len(exp_pass) == 1
    assert exp_pass[0].resolved_status == Status.PASS

    # On Nov 13, 2029: certificate issued 2025-01-10 is ~4.8 years old > 3 years -> FAIL
    res_expired, _ = pipeline.load_and_audit_packet(
        packet_dir, packet_id="PKT_01_CLEAN", as_of=date(2029, 11, 13)
    )
    exp_fail = [f for f in res_expired.findings if f.rule_id == "RULE-EXP-01"]
    assert len(exp_fail) == 1
    assert exp_fail[0].resolved_status == Status.FAIL
    assert res_expired.readiness == Readiness.NOT_READY


def test_conflicting_clock_parameters_raise_value_error():
    """Providing conflicting as_of and audit_date raises ValueError."""
    d1 = date(2026, 11, 13)
    d2 = date(2026, 11, 15)

    with pytest.raises(ValueError, match="Conflicting"):
        AuditPipeline(as_of=d1, audit_date=d2)

    pipeline = AuditPipeline(as_of=d1)
    with pytest.raises(ValueError, match="Conflicting"):
        pipeline.load_and_audit_packet("synthetic_data/pkt_01_clean", as_of=d1, audit_date=d2)

    with pytest.raises(ValueError, match="Conflicting"):
        DocuReadyValidator(as_of=d1, audit_date=d2)

    validator = DocuReadyValidator(as_of=d1)
    with pytest.raises(ValueError, match="Conflicting"):
        validator.validate_packet("TEST", {}, as_of=d1, audit_date=d2)


def test_no_prohibited_clock_calls_in_subsystems():
    """Verify rules/, outcome/, and normalize/ contain zero calls to datetime.now() or date.today()."""
    target_dirs = [
        _REPO_ROOT / "src" / "docuready" / "rules",
        _REPO_ROOT / "src" / "docuready" / "outcome",
        _REPO_ROOT / "src" / "docuready" / "normalize",
    ]

    violations = []
    for d in target_dirs:
        for py_file in d.rglob("*.py"):
            with open(py_file, "r", encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source, filename=str(py_file))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    func = node.func
                    if isinstance(func, ast.Attribute) and func.attr in ("now", "today"):
                        # Check if attribute owner is datetime or date
                        val = func.value
                        owner_name = getattr(val, "id", None) or getattr(val, "attr", None)
                        if owner_name in ("datetime", "date"):
                            violations.append(f"{py_file.name}:{node.lineno} calls {owner_name}.{func.attr}()")

    assert not violations, f"Prohibited clock calls found:\n" + "\n".join(violations)


def test_match_grade_resolver_enforcement():
    """Test outcome resolution rules with MatchGrade inputs per ARCHITECTURE_V2 §4.2 and §6."""
    # COMPATIBLE caps FAIL at WARN
    outcome_comp_viol = resolve_outcome(
        raw=Raw.VIOLATED,
        weakest_evidence=EvidenceState.VERIFIED,
        match_grade=MatchGrade.COMPATIBLE,
    )
    assert outcome_comp_viol.status == Status.WARN
    assert outcome_comp_viol.reason_code == "DEFECT_PROBABLE"

    # COMPATIBLE on SATISFIED with VERIFIED evidence produces WARN (check difference)
    outcome_comp_sat = resolve_outcome(
        raw=Raw.SATISFIED,
        weakest_evidence=EvidenceState.VERIFIED,
        match_grade=MatchGrade.COMPATIBLE,
    )
    assert outcome_comp_sat.status == Status.WARN
    assert outcome_comp_sat.reason_code == "DEFECT_PROBABLE"

    # AMBIGUOUS forces REVIEW regardless of raw result
    outcome_amb_sat = resolve_outcome(
        raw=Raw.SATISFIED,
        weakest_evidence=EvidenceState.VERIFIED,
        match_grade=MatchGrade.AMBIGUOUS,
    )
    assert outcome_amb_sat.status == Status.REVIEW
    assert outcome_amb_sat.reason_code == "EVIDENCE_UNCERTAIN"

    outcome_amb_viol = resolve_outcome(
        raw=Raw.VIOLATED,
        weakest_evidence=EvidenceState.VERIFIED,
        match_grade=MatchGrade.AMBIGUOUS,
    )
    assert outcome_amb_viol.status == Status.REVIEW
    assert outcome_amb_viol.reason_code == "EVIDENCE_UNCERTAIN"

    # CONFLICT with VIOLATED produces FAIL on VERIFIED evidence
    outcome_conf_viol = resolve_outcome(
        raw=Raw.VIOLATED,
        weakest_evidence=EvidenceState.VERIFIED,
        match_grade=MatchGrade.CONFLICT,
    )
    assert outcome_conf_viol.status == Status.FAIL
    assert outcome_conf_viol.reason_code == "DEFECT_CONFIRMED"

    # CONFLICT with SATISFIED fails closed to REVIEW
    outcome_conf_sat = resolve_outcome(
        raw=Raw.SATISFIED,
        weakest_evidence=EvidenceState.VERIFIED,
        match_grade=MatchGrade.CONFLICT,
    )
    assert outcome_conf_sat.status == Status.REVIEW
    assert outcome_conf_sat.reason_code == "EVIDENCE_UNCERTAIN"


def test_public_dict_exposes_as_of_and_match_grade():
    """Verify AuditResult.to_public_dict() exposes as_of and finding match_grade while model_dump() excludes them."""
    finding = Finding(
        rule_id="RULE-NAME-02",
        rule_name="Name Variation",
        status=FindingStatus.REVIEW,
        severity=Severity.REVIEW,
        penalty=10,
        field="APPLICANT_NAME_VARIATION",
        documents_involved=["APPLICATION_FORM", "MARKSHEET"],
        message="Initials expansion",
        evidence=[EvidenceProvenance(document_type="APPLICATION_FORM", file_name="app.pdf", raw_snippet="A. Sharma")],
        remediation="Check name",
        statutory_reference="UIDAI",
        match_grade=MatchGrade.COMPATIBLE,
    )
    finding.set_resolution(Raw.VIOLATED, Status.WARN, "DEFECT_PROBABLE", match_grade=MatchGrade.COMPATIBLE)

    res = AuditResult(
        packet_id="TEST_PKT",
        scheme_name="Test Scheme",
        readiness_score=90,
        overall_status="ACTION_REQUIRED",
        findings=[finding],
        summary_counts={"PASS": 0, "REVIEW": 0, "FAIL": 0, "UNKNOWN": 0},
        execution_time_ms=1.5,
        timestamp="2026-11-13T00:00:00",
        as_of="2026-11-13",
    )

    # model_dump() excludes excluded fields (preserving golden snapshot schema)
    dumped = res.model_dump(mode="json")
    assert "as_of" not in dumped
    assert "match_grade" not in dumped["findings"][0]

    # to_public_dict() includes as_of and match_grade
    pub = res.to_public_dict()
    assert pub["as_of"] == "2026-11-13"
    assert pub["findings"][0]["match_grade"] == "COMPATIBLE"
    assert pub["findings"][0]["status"] == "WARN"
    assert pub["findings"][0]["reason_code"] == "DEFECT_PROBABLE"


def test_income_tolerance_in_scheme_config():
    """Verify that setting income_tolerance in SchemeConfig is stored and used."""
    cfg = SchemeConfig(income_tolerance=5000.0)
    assert cfg.income_tolerance == 5000.0

    validator = DocuReadyValidator(scheme_config=cfg)
    assert validator.scheme.income_tolerance == 5000.0


# ---------------------------------------------------------------------------
# VALIDATOR-LEVEL MATCH GRADE & ROUTING INTEGRATION TESTS
# ---------------------------------------------------------------------------

from tests.integration.test_validator_rule_matrix import (
    _make_clean_packet,
    _make_field,
    _find_finding,
)
from docuready.domain.enums import ExtractionMethod, ReasonCode


def test_validator_name_exact_match_resolves_pass():
    """Exact character match across all documents yields RULE-NAME-PASS with EXACT and Status.PASS."""
    packet = _make_clean_packet(applicant_name="Aarav Sharma")
    validator = DocuReadyValidator(SchemeConfig(), as_of=date(2026, 11, 15))
    res = validator.validate_packet("NAME_EXACT", packet)

    f = _find_finding(res.findings, "RULE-NAME-PASS")
    assert f is not None
    assert f.match_grade is MatchGrade.EXACT
    assert f.status is Status.PASS
    assert f.reason_code == ReasonCode.CONFIRMED_OK.value


def test_validator_name_token_reorder_resolves_warn():
    """Token permutation (reordered tokens) must preserve MatchGrade.COMPATIBLE and resolve to Status.WARN, never PASS."""
    packet = _make_clean_packet(applicant_name="Aarav Sharma")
    # Marksheet has reordered name "Sharma Aarav"
    packet[DocumentType.MARKSHEET].fields["applicant_name"] = _make_field(
        DocumentType.MARKSHEET, "applicant_name", "Sharma Aarav"
    )

    validator = DocuReadyValidator(SchemeConfig(), as_of=date(2026, 11, 15))
    res = validator.validate_packet("NAME_REORDERED", packet)

    f = _find_finding(res.findings, "RULE-NAME-PASS")
    assert f is not None
    assert f.match_grade is MatchGrade.COMPATIBLE
    # Must NOT resolve to PASS; resolver maps SATISFIED + COMPATIBLE -> WARN / DEFECT_PROBABLE
    assert f.status is Status.WARN
    assert f.reason_code == ReasonCode.DEFECT_PROBABLE.value
    assert res.readiness is Readiness.NEEDS_CHECKS


def test_validator_bank_account_exact_with_formatting():
    """Bank accounts with formatting differences (spaces/dashes) match identically via compare_identifiers."""
    packet = _make_clean_packet()
    packet[DocumentType.APPLICATION_FORM].fields["account_no"] = _make_field(
        DocumentType.APPLICATION_FORM, "account_no", "123456789012"
    )
    packet[DocumentType.BANK_PASSBOOK].fields["account_no"] = _make_field(
        DocumentType.BANK_PASSBOOK, "account_no", "1234 5678 9012"
    )

    validator = DocuReadyValidator(SchemeConfig(), as_of=date(2026, 11, 15))
    res = validator.validate_packet("BNK_ACC_FORMAT", packet)

    f = _find_finding(res.findings, "RULE-BNK-02")
    assert f is None  # Matches after normalization, no discrepancy finding


def test_validator_bank_account_conflict_and_uncertain():
    """Bank account discrepancy routes through compare_identifiers producing CONFLICT (FAIL) or AMBIGUOUS (REVIEW)."""
    # Conflicting accounts
    packet = _make_clean_packet()
    packet[DocumentType.APPLICATION_FORM].fields["account_no"] = _make_field(
        DocumentType.APPLICATION_FORM, "account_no", "123456789012"
    )
    packet[DocumentType.BANK_PASSBOOK].fields["account_no"] = _make_field(
        DocumentType.BANK_PASSBOOK, "account_no", "987654321098"
    )

    validator = DocuReadyValidator(SchemeConfig(), as_of=date(2026, 11, 15))
    res_conf = validator.validate_packet("BNK_ACC_CONFLICT", packet)
    f_conf = _find_finding(res_conf.findings, "RULE-BNK-02")
    assert f_conf is not None
    assert f_conf.match_grade is MatchGrade.CONFLICT
    assert f_conf.status is Status.FAIL
    assert f_conf.reason_code == ReasonCode.DEFECT_CONFIRMED.value

    # Uncertain extraction
    packet[DocumentType.BANK_PASSBOOK].fields["account_no"] = _make_field(
        DocumentType.BANK_PASSBOOK,
        "account_no",
        "987654321098",
        evidence_state=EvidenceState.UNCERTAIN,
        extraction_method=ExtractionMethod.LOCAL_OCR,
        is_uncertain=True,
    )
    res_unc = validator.validate_packet("BNK_ACC_UNCERTAIN", packet)
    f_unc = _find_finding(res_unc.findings, "RULE-BNK-02")
    assert f_unc is not None
    assert f_unc.match_grade is MatchGrade.AMBIGUOUS
    assert f_unc.status is Status.REVIEW
    assert f_unc.reason_code == ReasonCode.INSUFFICIENT_DATA.value


def test_validator_cert_ref_formatting_and_uncertain():
    """Certificate references normalize formatting differences and handle extraction uncertainty via compare_identifiers."""
    packet = _make_clean_packet()
    packet[DocumentType.APPLICATION_FORM].fields["income_cert_no"] = _make_field(
        DocumentType.APPLICATION_FORM, "income_cert_no", "E-INC/2025/104928"
    )
    packet[DocumentType.INCOME_CERT].fields["certificate_no"] = _make_field(
        DocumentType.INCOME_CERT, "certificate_no", "E INC 2025 104928"
    )

    validator = DocuReadyValidator(SchemeConfig(), as_of=date(2026, 11, 15))
    res_fmt = validator.validate_packet("CERT_REF_FMT", packet)
    f_pass = _find_finding(res_fmt.findings, "RULE-REF-INC-PASS")
    assert f_pass is not None
    assert f_pass.match_grade is MatchGrade.EXACT
    assert f_pass.status is Status.PASS

    # Uncertain extraction on certificate number
    packet[DocumentType.INCOME_CERT].fields["certificate_no"] = _make_field(
        DocumentType.INCOME_CERT,
        "certificate_no",
        "E-INC/2025/999999",
        evidence_state=EvidenceState.UNCERTAIN,
        is_uncertain=True,
    )
    res_unc = validator.validate_packet("CERT_REF_UNC", packet)
    f_unc = _find_finding(res_unc.findings, "RULE-REF-01")
    assert f_unc is not None
    assert f_unc.match_grade is MatchGrade.AMBIGUOUS
    assert f_unc.status is Status.REVIEW


def test_validator_dob_match_grades():
    """Cross-document Date of Birth routes through compare_dates() verifying EXACT, AMBIGUOUS, and CONFLICT outcomes."""
    validator = DocuReadyValidator(SchemeConfig(), as_of=date(2026, 11, 15))

    # 1. Exact match
    packet_exact = _make_clean_packet(dob="14/05/2003")
    res_exact = validator.validate_packet("DOB_EXACT", packet_exact)
    f_exact = _find_finding(res_exact.findings, "RULE-DOB-PASS")
    assert f_exact is not None
    assert f_exact.match_grade is MatchGrade.EXACT
    assert f_exact.status is Status.PASS

    # 2. Ambiguous format (03/04/2005) -> MatchGrade.AMBIGUOUS & Status.REVIEW
    packet_amb = _make_clean_packet(dob="03/04/2005")
    res_amb = validator.validate_packet("DOB_AMB", packet_amb)
    f_amb = _find_finding(res_amb.findings, "RULE-DOB-02")
    assert f_amb is not None
    assert f_amb.match_grade is MatchGrade.AMBIGUOUS
    assert f_amb.status is Status.REVIEW
    assert f_amb.reason_code == ReasonCode.INSUFFICIENT_DATA.value

    # 3. Conflicting dates
    packet_conf = _make_clean_packet(dob="14/05/2003")
    packet_conf[DocumentType.MARKSHEET].fields["dob"] = _make_field(
        DocumentType.MARKSHEET, "dob", "20/09/2004"
    )
    res_conf = validator.validate_packet("DOB_CONF", packet_conf)
    f_conf = _find_finding(res_conf.findings, "RULE-DOB-01")
    assert f_conf is not None
    assert f_conf.match_grade is MatchGrade.CONFLICT
    assert f_conf.status is Status.FAIL

    # 4. OCR uncertain on conflict
    packet_conf[DocumentType.MARKSHEET].fields["dob"] = _make_field(
        DocumentType.MARKSHEET,
        "dob",
        "20/09/2004",
        evidence_state=EvidenceState.UNCERTAIN,
        is_uncertain=True,
    )
    res_ocr_unc = validator.validate_packet("DOB_OCR_UNC", packet_conf)
    f_ocr_unc = _find_finding(res_ocr_unc.findings, "RULE-DOB-UNCERTAIN")
    assert f_ocr_unc is not None
    assert f_ocr_unc.match_grade is MatchGrade.AMBIGUOUS
    assert f_ocr_unc.status is Status.REVIEW


def test_validator_name_initials_expansion_resolves_warn():
    """Initials expansion ('A. Sharma' vs 'Aarav Sharma') retains COMPATIBLE, penalty <= 5, and resolves to Status.WARN."""
    packet = _make_clean_packet(applicant_name="Aarav Sharma")
    packet[DocumentType.BANK_PASSBOOK].fields["applicant_name"] = _make_field(
        DocumentType.BANK_PASSBOOK, "applicant_name", "A. Sharma"
    )

    validator = DocuReadyValidator(SchemeConfig(), as_of=date(2026, 11, 15))
    res = validator.validate_packet("NAME_INITIALS", packet)

    f = _find_finding(res.findings, "RULE-NAME-02")
    assert f is not None
    assert f.match_grade is MatchGrade.COMPATIBLE
    assert f.penalty <= 5
    assert f.penalty == 5
    assert f.status is Status.WARN
    assert f.reason_code == ReasonCode.DEFECT_PROBABLE.value
    assert res.readiness is Readiness.NEEDS_CHECKS
    assert res.readiness_score == 95


def test_validator_name_minor_spelling_variation_resolves_warn():
    """Minor transliteration/spelling edit distance retains COMPATIBLE, penalty <= 5, and resolves to Status.WARN."""
    packet = _make_clean_packet(applicant_name="Aarav Sharma")
    packet[DocumentType.MARKSHEET].fields["applicant_name"] = _make_field(
        DocumentType.MARKSHEET, "applicant_name", "Arav Sharma"
    )

    validator = DocuReadyValidator(SchemeConfig(), as_of=date(2026, 11, 15))
    res = validator.validate_packet("NAME_TYPO", packet)

    f = _find_finding(res.findings, "RULE-NAME-02")
    assert f is not None
    assert f.match_grade is MatchGrade.COMPATIBLE
    assert f.penalty <= 5
    assert f.penalty == 5
    assert f.status is Status.WARN
    assert f.reason_code == ReasonCode.DEFECT_PROBABLE.value
    assert res.readiness is Readiness.NEEDS_CHECKS


def test_validator_name_genuine_conflict_resolves_fail():
    """Genuine conflict ('Rohan Sharma' vs 'Aarav Sharma') retains CONFLICT, penalty 25, and resolves to Status.FAIL."""
    packet = _make_clean_packet(applicant_name="Aarav Sharma")
    packet[DocumentType.MARKSHEET].fields["applicant_name"] = _make_field(
        DocumentType.MARKSHEET, "applicant_name", "Rohan Sharma"
    )

    validator = DocuReadyValidator(SchemeConfig(), as_of=date(2026, 11, 15))
    res = validator.validate_packet("NAME_CONFLICT", packet)

    f = _find_finding(res.findings, "RULE-NAME-01")
    assert f is not None
    assert f.match_grade is MatchGrade.CONFLICT
    assert f.penalty == 25
    assert f.status is Status.FAIL
    assert f.reason_code == ReasonCode.DEFECT_CONFIRMED.value
    assert res.readiness is Readiness.NOT_READY


def test_validator_name_single_token_ambiguity_resolves_review():
    """Single token ('Aarav' vs 'Aarav Sharma') is AMBIGUOUS, penalty 10, and resolves to Status.REVIEW."""
    packet = _make_clean_packet(applicant_name="Aarav Sharma")
    packet[DocumentType.MARKSHEET].fields["applicant_name"] = _make_field(
        DocumentType.MARKSHEET, "applicant_name", "Aarav"
    )

    validator = DocuReadyValidator(SchemeConfig(), as_of=date(2026, 11, 15))
    res = validator.validate_packet("NAME_SINGLE_TOKEN", packet)

    f = _find_finding(res.findings, "RULE-NAME-02")
    assert f is not None
    assert f.match_grade is MatchGrade.AMBIGUOUS
    assert f.penalty == 10
    assert f.status is Status.REVIEW
    assert f.reason_code == ReasonCode.INSUFFICIENT_DATA.value
    assert res.readiness is Readiness.NEEDS_CHECKS


def test_validator_name_uncertain_ocr_fails_closed_to_review():
    """Uncertain OCR on a name variation fails closed to Status.REVIEW (never elevated to WARN or PASS)."""
    packet = _make_clean_packet(applicant_name="Aarav Sharma")
    packet[DocumentType.MARKSHEET].fields["applicant_name"] = _make_field(
        DocumentType.MARKSHEET,
        "applicant_name",
        "A. Sharma",
        evidence_state=EvidenceState.UNCERTAIN,
        is_uncertain=True,
    )

    validator = DocuReadyValidator(SchemeConfig(), as_of=date(2026, 11, 15))
    res = validator.validate_packet("NAME_UNCERTAIN_OCR", packet)

    f = _find_finding(res.findings, "RULE-NAME-02")
    assert f is not None
    # OCR uncertainty preserves fail-closed Status.REVIEW
    assert f.status is Status.REVIEW
    assert f.reason_code == ReasonCode.EVIDENCE_UNCERTAIN.value
    assert res.readiness is Readiness.NEEDS_CHECKS


def test_non_comparison_rules_have_no_match_grade():
    """Single-field format checks, numeric thresholds, and date validity checks do not assign MatchGrade."""
    packet = _make_clean_packet()
    validator = DocuReadyValidator(SchemeConfig(), as_of=date(2026, 11, 15))
    res = validator.validate_packet("NON_COMPARISON_CHECKS", packet)

    # 1. Single-field IFSC format check
    f_ifsc = _find_finding(res.findings, "RULE-BNK-IFSC-PASS")
    assert f_ifsc is not None
    assert f_ifsc.match_grade is None

    # 2. Income ceiling threshold check
    f_inc_ceil = _find_finding(res.findings, "RULE-INC-CEIL-PASS")
    assert f_inc_ceil is not None
    assert f_inc_ceil.match_grade is None

    # 3. Income certificate expiry check
    f_exp = _find_finding(res.findings, "RULE-EXP-PASS")
    assert f_exp is not None
    assert f_exp.match_grade is None
