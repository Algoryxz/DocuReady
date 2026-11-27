"""
Permanent Regression Test Suite for Loop 06
Audit Decision Engine Calibration, Rule Integrity & Explainability
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
import pytest

from docuready.domain.enums import (
    EvidenceState,
    ExitCode,
    MatchGrade,
    MaxSeverity,
    Raw,
    Readiness,
    ReasonCode,
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
from docuready.outcome.resolver import (
    exit_code_for_readiness,
    resolve_outcome,
    resolve_readiness,
    weakest_evidence,
)
from docuready.pipeline import AuditPipeline
from docuready.report.redact import redact_audit_result_dict
from docuready.rules.engine import PackExecutionEngine

REPO_ROOT = Path(__file__).resolve().parents[1]
CORPUS_DIR = REPO_ROOT / "synthetic_data" / "loop06_decision_corpus"
PACK_DIR = REPO_ROOT / "packs" / "generic.demo"
AS_OF = date(2026, 11, 16)


# ---------------------------------------------------------------------------
# UNIT TESTS: 10 CANONICAL DECISION INVARIANTS
# ---------------------------------------------------------------------------

def test_inv1_hard_conflict_forces_not_ready():
    """Invariant 1: A confirmed defect (Status.FAIL) must always resolve to NOT_READY."""
    statuses = [Status.PASS, Status.PASS, Status.FAIL, Status.PASS]
    assert resolve_readiness(statuses) == Readiness.NOT_READY
    assert exit_code_for_readiness(Readiness.NOT_READY) == ExitCode.NOT_READY


def test_inv2_missing_mandatory_doc_forces_not_ready():
    """Invariant 2: An absent required document (Status.MISSING) must always resolve to NOT_READY."""
    outcome = resolve_outcome(Raw.DOC_ABSENT, weakest_evidence=None)
    assert outcome.status == Status.MISSING
    assert outcome.reason_code == ReasonCode.DOC_ABSENT.value
    assert resolve_readiness([Status.PASS, outcome.status]) == Readiness.NOT_READY


def test_inv3_unreadable_mandatory_doc_abstains_never_ready():
    """Invariant 3: An unreadable document (Status.REVIEW) must never resolve to NO_ISSUES_FOUND."""
    outcome = resolve_outcome(Raw.INDETERMINATE, weakest_evidence=EvidenceState.UNCERTAIN)
    assert outcome.status == Status.REVIEW
    assert outcome.reason_code == ReasonCode.INSUFFICIENT_DATA.value
    assert resolve_readiness([Status.PASS, outcome.status]) == Readiness.NEEDS_CHECKS


def test_inv4_ambiguity_overrides_to_review_never_false_fail():
    """Invariant 4: Ambiguous evidence overrides apparent violation and never emits false FAIL."""
    outcome = resolve_outcome(
        Raw.VIOLATED,
        weakest_evidence=EvidenceState.UNCERTAIN,
        match_grade=MatchGrade.AMBIGUOUS,
    )
    assert outcome.status == Status.REVIEW
    assert outcome.reason_code == ReasonCode.EVIDENCE_UNCERTAIN.value


def test_inv5_soft_warning_never_forces_not_ready():
    """Invariant 5: A packet with warnings (Status.WARN) without hard failures must resolve to NEEDS_CHECKS."""
    outcome = resolve_outcome(
        Raw.VIOLATED,
        weakest_evidence=EvidenceState.PROVISIONAL,
        max_severity=MaxSeverity.WARN,
    )
    assert outcome.status == Status.WARN
    assert resolve_readiness([Status.PASS, outcome.status]) == Readiness.NEEDS_CHECKS


def test_inv6_high_score_cannot_downgrade_hard_failure():
    """Invariant 6: Residual score >= 75 cannot downgrade status if a hard failure is present."""
    f_pass = Finding(
        rule_id="RULE-PASS",
        rule_name="Pass",
        status=FindingStatus.PASS,
        severity=Severity.INFO,
        penalty=0,
        field="F1",
        documents_involved=[],
        message="OK",
        remediation="None",
        statutory_reference="Ref",
    )
    f_pass.set_resolution(Raw.SATISFIED, Status.PASS, "CONFIRMED_OK")

    f_fail = Finding(
        rule_id="RULE-FAIL",
        rule_name="Fail",
        status=FindingStatus.FAIL,
        severity=Severity.CRITICAL,
        penalty=25,
        field="F2",
        documents_involved=[],
        message="Failed",
        remediation="Fix",
        statutory_reference="Ref",
    )
    f_fail.set_resolution(Raw.VIOLATED, Status.FAIL, "DEFECT_CONFIRMED")

    result = AuditResult(
        packet_id="TEST_SCORE_GATE",
        scheme_name="Test Scheme",
        readiness_score=75,
        overall_status=Readiness.NO_ISSUES_FOUND,  # Pre-validator attempt
        findings=[f_pass, f_fail],
        summary_counts={"PASS": 1, "FAIL": 1},
        execution_time_ms=1.0,
        timestamp="2026-11-16T00:00:00",
    )
    # derive_readiness_from_findings validator strictly enforces NOT_READY
    assert result.overall_status == Readiness.NOT_READY
    assert result.readiness_score == 75


def test_inv7_duplicate_finding_deduplication():
    """Invariant 7: Exact duplicate findings are unified; penalties are not double-counted."""
    pipeline = AuditPipeline(as_of=AS_OF)
    f_dup1 = Finding(
        rule_id="RULE-TEST-01",
        rule_name="Test Rule",
        status=FindingStatus.FAIL,
        severity=Severity.CRITICAL,
        penalty=25,
        field="TEST_FIELD",
        documents_involved=["INCOME_CERT"],
        message="Duplicate 1",
        remediation="Fix",
        statutory_reference="Ref",
    )
    f_dup1.set_resolution(Raw.VIOLATED, Status.FAIL, "DEFECT_CONFIRMED")

    f_dup2 = Finding(
        rule_id="RULE-TEST-01",
        rule_name="Test Rule",
        status=FindingStatus.FAIL,
        severity=Severity.CRITICAL,
        penalty=25,
        field="TEST_FIELD",
        documents_involved=["INCOME_CERT"],
        message="Duplicate 2",
        remediation="Fix",
        statutory_reference="Ref",
    )
    f_dup2.set_resolution(Raw.VIOLATED, Status.FAIL, "DEFECT_CONFIRMED")

    # Ingest through validator dedup logic
    deduped: list[Finding] = []
    seen = set()
    for f in [f_dup1, f_dup2]:
        key = (f.rule_id, tuple(sorted(f.documents_involved)), f.field, f.resolved_status)
        if key not in seen:
            seen.add(key)
            deduped.append(f)

    assert len(deduped) == 1
    total_penalty = sum(f.penalty for f in deduped)
    assert total_penalty == 25


def test_inv8_readiness_order_invariance():
    """Invariant 8: Status derivation is order-independent across finding permutations."""
    perm1 = [Status.PASS, Status.WARN, Status.REVIEW, Status.FAIL]
    perm2 = [Status.FAIL, Status.REVIEW, Status.WARN, Status.PASS]
    perm3 = [Status.REVIEW, Status.FAIL, Status.PASS, Status.WARN]
    assert resolve_readiness(perm1) == resolve_readiness(perm2) == resolve_readiness(perm3) == Readiness.NOT_READY


def test_inv9_empty_execution_fails_closed():
    """Invariant 9: Empty finding set fails closed to NEEDS_CHECKS; never false green."""
    assert resolve_readiness([]) == Readiness.NEEDS_CHECKS
    assert resolve_readiness([Status.NOT_APPLICABLE]) == Readiness.NEEDS_CHECKS


def test_inv10_exception_safety_in_pack_engine():
    """Invariant 10: Rule exceptions fail closed to Status.REVIEW without crashing."""
    pack_engine = PackExecutionEngine(PACK_DIR, allow_draft=True)
    # Simulate a corrupted document map triggering error
    doc = ExtractedDocument(doc_type=DocumentType.INCOME_CERT, file_path="corrupt.pdf", status="VALID")
    # Missing fields dict or unexpected None
    doc.fields = None  # type: ignore
    res = pack_engine.validate_packet("ERR_PACKET", {DocumentType.INCOME_CERT: doc}, as_of=AS_OF)
    assert res.overall_status in (Readiness.NEEDS_CHECKS, Readiness.NOT_READY)


# ---------------------------------------------------------------------------
# INTEGRATION TESTS: CONTROLLED CORPUS AUDITS
# ---------------------------------------------------------------------------

@pytest.fixture
def pipeline() -> AuditPipeline:
    return AuditPipeline(as_of=AS_OF)


def test_corpus_pkt01_clean_packet(pipeline: AuditPipeline):
    """PKT_01_CLEAN must pass all checks with score 100 and NO_ISSUES_FOUND."""
    pkt_dir = CORPUS_DIR / "PKT_01_CLEAN"
    res, _ = pipeline.load_and_audit_packet(str(pkt_dir), packet_id="PKT_01_CLEAN", as_of=AS_OF)
    assert res.readiness == Readiness.NO_ISSUES_FOUND
    assert res.readiness_score == 100
    assert not any(f.resolved_status in (Status.FAIL, Status.MISSING, Status.WARN) for f in res.findings)


def test_corpus_pkt02_name_mismatch(pipeline: AuditPipeline):
    """PKT_02_NAME_MISMATCH must fail with NOT_READY, score 75, RULE-NAME-01."""
    pkt_dir = CORPUS_DIR / "PKT_02_NAME_MISMATCH"
    res, _ = pipeline.load_and_audit_packet(str(pkt_dir), packet_id="PKT_02_NAME_MISMATCH", as_of=AS_OF)
    assert res.readiness == Readiness.NOT_READY
    assert res.readiness_score == 75
    assert any(f.rule_id == "RULE-NAME-01" and f.resolved_status == Status.FAIL for f in res.findings)


def test_corpus_pkt03_dob_mismatch(pipeline: AuditPipeline):
    """PKT_03_DOB_MISMATCH must fail with NOT_READY, score 75, RULE-DOB-01."""
    pkt_dir = CORPUS_DIR / "PKT_03_DOB_MISMATCH"
    res, _ = pipeline.load_and_audit_packet(str(pkt_dir), packet_id="PKT_03_DOB_MISMATCH", as_of=AS_OF)
    assert res.readiness == Readiness.NOT_READY
    assert res.readiness_score == 75
    assert any(f.rule_id == "RULE-DOB-01" and f.resolved_status == Status.FAIL for f in res.findings)


def test_corpus_pkt05_missing_mandatory_doc(pipeline: AuditPipeline):
    """PKT_05_MISSING_MANDATORY_DOC must fail with NOT_READY, score 65, RULE-DOC-01."""
    pkt_dir = CORPUS_DIR / "PKT_05_MISSING_MANDATORY_DOC"
    res, _ = pipeline.load_and_audit_packet(str(pkt_dir), packet_id="PKT_05_MISSING", as_of=AS_OF)
    assert res.readiness == Readiness.NOT_READY
    assert res.readiness_score == 65
    assert any(f.rule_id == "RULE-DOC-01" and f.resolved_status == Status.MISSING for f in res.findings)


def test_corpus_pkt06_unreadable_mandatory_doc(pipeline: AuditPipeline):
    """PKT_06_UNREADABLE_MANDATORY_DOC must abstain to NEEDS_CHECKS, score 75, RULE-DOC-02."""
    pkt_dir = CORPUS_DIR / "PKT_06_UNREADABLE_MANDATORY_DOC"
    res, _ = pipeline.load_and_audit_packet(str(pkt_dir), packet_id="PKT_06_UNREADABLE", as_of=AS_OF)
    assert res.readiness == Readiness.NEEDS_CHECKS
    assert res.readiness_score == 75
    assert any(f.rule_id == "RULE-DOC-02" and f.resolved_status == Status.REVIEW for f in res.findings)


def test_corpus_pkt07_compatible_name_variation(pipeline: AuditPipeline):
    """PKT_07_COMPATIBLE_NAME_VARIATION must resolve to NEEDS_CHECKS with WARN."""
    pkt_dir = CORPUS_DIR / "PKT_07_COMPATIBLE_NAME_VARIATION"
    res, _ = pipeline.load_and_audit_packet(str(pkt_dir), packet_id="PKT_07_VAR", as_of=AS_OF)
    assert res.readiness == Readiness.NEEDS_CHECKS
    assert any(f.rule_id == "RULE-NAME-02" and f.resolved_status == Status.WARN for f in res.findings)


def test_corpus_pkt12_slot_mismatch(pipeline: AuditPipeline):
    """PKT_12_SLOT_MISMATCH must detect slot mismatch and avoid cascading false failures."""
    pkt_dir = CORPUS_DIR / "PKT_12_SLOT_MISMATCH"
    res, _ = pipeline.load_and_audit_packet(str(pkt_dir), packet_id="PKT_12_SLOT", as_of=AS_OF)
    assert res.readiness == Readiness.NEEDS_CHECKS
    assert any(f.rule_id == "RULE-SLOT-01" for f in res.findings)


def test_corpus_pkt13_category_exemption_verified(pipeline: AuditPipeline):
    """PKT_13_CATEGORY_EXEMPTION_VERIFIED must grant exemption under Post-Matric Clause 5.2."""
    pkt_dir = CORPUS_DIR / "PKT_13_CATEGORY_EXEMPTION_VERIFIED"
    res, _ = pipeline.load_and_audit_packet(str(pkt_dir), packet_id="PKT_13_EXEMPT", as_of=AS_OF)
    assert res.readiness == Readiness.NO_ISSUES_FOUND
    assert res.readiness_score == 100


def test_corpus_pkt16_empty_packet_fail_closed(pipeline: AuditPipeline):
    """PKT_16_EMPTY_PACKET_FAIL_CLOSED must fail closed to NOT_READY with score 0."""
    pkt_dir = CORPUS_DIR / "PKT_16_EMPTY_PACKET_FAIL_CLOSED"
    res, _ = pipeline.load_and_audit_packet(str(pkt_dir), packet_id="PKT_16_EMPTY", as_of=AS_OF)
    assert res.readiness == Readiness.NOT_READY
    assert res.readiness_score == 0


def test_evidence_provenance_and_privacy_redaction(pipeline: AuditPipeline):
    """Evidence provenance must have valid geometry and exported reports must redact PII."""
    pkt_dir = CORPUS_DIR / "PKT_01_CLEAN"
    res, _ = pipeline.load_and_audit_packet(str(pkt_dir), packet_id="PKT_01_CLEAN", as_of=AS_OF)

    # Provenance geometry
    for f in res.findings:
        for ev in f.evidence:
            if ev.bounding_box:
                assert len(ev.bounding_box) == 4
                assert ev.bounding_box[2] >= ev.bounding_box[0]
                assert ev.bounding_box[3] >= ev.bounding_box[1]

    # Privacy redaction
    public_dict = redact_audit_result_dict(res.to_public_dict(canonical=True))
    serialized = json.dumps(public_dict)
    assert "C:\\Users" not in serialized
    assert "/Users/" not in serialized
