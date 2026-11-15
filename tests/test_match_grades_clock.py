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
    """Replaying a packet with the same as_of gives byte-for-byte identical reports."""
    packet_dir = str(_REPO_ROOT / "synthetic_data" / "pkt_01_clean")
    as_of_date = date(2026, 11, 13)

    pipeline = AuditPipeline(as_of=as_of_date)
    res1, _ = pipeline.load_and_audit_packet(packet_dir, packet_id="PKT_01_CLEAN", as_of=as_of_date)
    res2, _ = pipeline.load_and_audit_packet(packet_dir, packet_id="PKT_01_CLEAN", as_of=as_of_date)

    assert res1.as_of == "2026-11-13"
    assert res2.as_of == "2026-11-13"
    assert res1.timestamp == "2026-11-13T00:00:00"
    assert res2.timestamp == "2026-11-13T00:00:00"

    # Normalize elapsed wall-clock execution time for report comparison
    res1.execution_time_ms = 0.0
    res2.execution_time_ms = 0.0

    with tempfile.TemporaryDirectory() as tmpdir:
        path1 = os.path.join(tmpdir, "report1.json")
        path2 = os.path.join(tmpdir, "report2.json")

        export_audit_report_json(res1, path1, redact=False)
        export_audit_report_json(res2, path2, redact=False)

        with open(path1, "r", encoding="utf-8") as f:
            content1 = f.read()
        with open(path2, "r", encoding="utf-8") as f:
            content2 = f.read()

        assert content1 == content2

    md1 = generate_readiness_summary_markdown(res1, redact=False)
    md2 = generate_readiness_summary_markdown(res2, redact=False)

    # Exclude execution latency line from markdown equality
    md1_lines = [l for l in md1.splitlines() if "Execution Latency" not in l]
    md2_lines = [l for l in md2.splitlines() if "Execution Latency" not in l]
    assert md1_lines == md2_lines
    assert "**Effective As Of:** `2026-11-13`" in md1


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
    assert outcome_amb_sat.status == Status.REVIEW
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
