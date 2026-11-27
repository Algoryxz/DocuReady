"""
Test Suite for Loop 07: Adversarial Corpus Expansion & Decision Generalization
Verifies the complete adversarial corpus against the DocuReady audit engine,
testing all 11 adversarial families, 3-way split performance, metamorphic invariants,
failure injection robustness, and zero false clearance.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
import pytest

from docuready.pipeline import AuditPipeline
from docuready.domain.enums import Readiness
from docuready.domain.models import FindingStatus, Severity
from docuready.rules.validator import DocuReadyValidator

REPO_ROOT = Path(__file__).resolve().parents[1]
CORPUS_DIR = REPO_ROOT / "synthetic_data" / "loop07_adversarial_corpus"
MANIFEST_PATH = CORPUS_DIR / "LOOP07_CORPUS_MANIFEST.json"
AS_OF = date(2026, 11, 16)


@pytest.fixture(scope="module")
def corpus_manifest():
    assert MANIFEST_PATH.exists(), f"Corpus manifest missing at {MANIFEST_PATH}"
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def audit_pipeline():
    return AuditPipeline(as_of=AS_OF)


class TestLoop07AdversarialCorpus:
    """Validates structure, splits, and content of the expanded adversarial corpus."""

    def test_corpus_scale_and_family_coverage(self, corpus_manifest):
        scenarios = corpus_manifest["scenarios"]
        assert len(scenarios) >= 120, f"Expected >= 120 scenarios, found {len(scenarios)}"

        families = {s["family"] for s in scenarios.values()}
        expected_families = {
            "CLEAN_CONTROLS",
            "DOCUMENT_COMPLETENESS",
            "SCAN_QUALITY",
            "GEOMETRY_DESKEW",
            "EXTRACTION_ADVERSARIAL",
            "IDENTITY_CONSISTENCY",
            "TEMPORAL_CONSISTENCY",
            "FINANCIAL_DATA",
            "DOMICILE_AND_SLOT",
            "INTERACTION",
            "RESERVATION_AND_PARITY",
        }
        assert expected_families.issubset(families), f"Missing families: {expected_families - families}"

    def test_three_way_split_distribution(self, corpus_manifest):
        splits = corpus_manifest["splits"]
        assert "development_count" in splits
        assert "validation_count" in splits
        assert "challenge_count" in splits
        assert splits["development_count"] >= 40
        assert splits["validation_count"] >= 30
        assert splits["challenge_count"] >= 30
        assert sum(splits.values()) == len(corpus_manifest["scenarios"])

    def test_clean_control_scenarios_pass(self, audit_pipeline, corpus_manifest):
        clean_scenarios = [
            sid for sid, meta in corpus_manifest["scenarios"].items()
            if meta["family"] == "CLEAN_CONTROLS"
        ]
        assert len(clean_scenarios) >= 10
        for sid in clean_scenarios:
            pdir = CORPUS_DIR / sid
            res, _ = audit_pipeline.load_and_audit_packet(str(pdir), packet_id=sid, as_of=AS_OF)
            assert res.readiness == Readiness.NO_ISSUES_FOUND, f"Clean scenario {sid} failed readiness: {res.readiness}"
            assert res.readiness_score == 100, f"Clean scenario {sid} score was {res.readiness_score}, expected 100"

    def test_zero_false_ready_clearance_across_corpus(self, audit_pipeline, corpus_manifest):
        """CRITICAL SAFETY INVARIANT: No defective or uncertain scenario may receive READY clearance."""
        false_ready_cases = []
        for sid, meta in corpus_manifest["scenarios"].items():
            if meta["expected_status"] != "NO_ISSUES_FOUND":
                pdir = CORPUS_DIR / sid
                res, _ = audit_pipeline.load_and_audit_packet(str(pdir), packet_id=sid, as_of=AS_OF)
                if res.readiness == Readiness.NO_ISSUES_FOUND:
                    false_ready_cases.append((sid, meta["description"], res.readiness_score))

        assert len(false_ready_cases) == 0, f"CRITICAL: False READY clearances detected: {false_ready_cases}"

    def test_metamorphic_determinism_invariant(self, audit_pipeline):
        """Metamorphic Invariant M1: Exactly identical outcomes across 5 repeated runs."""
        pdir = CORPUS_DIR / "SCN_A01_CLEAN_BASELINE_ODISHA"
        baseline_res, _ = audit_pipeline.load_and_audit_packet(str(pdir), packet_id="SCN_A01", as_of=AS_OF)
        for i in range(4):
            run_res, _ = audit_pipeline.load_and_audit_packet(str(pdir), packet_id="SCN_A01", as_of=AS_OF)
            assert run_res.readiness == baseline_res.readiness
            assert run_res.readiness_score == baseline_res.readiness_score
            assert len(run_res.findings) == len(baseline_res.findings)
            assert [f.rule_id for f in run_res.findings] == [f.rule_id for f in baseline_res.findings]

    def test_metamorphic_severity_monotonicity(self, audit_pipeline, corpus_manifest):
        """Metamorphic Invariant M2: Introducing defects never improves readiness score."""
        clean_dir = CORPUS_DIR / "SCN_A01_CLEAN_BASELINE_ODISHA"
        clean_res, _ = audit_pipeline.load_and_audit_packet(str(clean_dir), packet_id="SCN_A01", as_of=AS_OF)
        clean_score = clean_res.readiness_score

        # Sample defect scenarios
        defect_samples = [
            "SCN_B01_MISSING_INCOME_CERT",
            "SCN_F02_HARD_NAME_CONFLICT",
            "SCN_H02_INCOME_ABOVE_CEILING_CERTIFIED",
            "SCN_J01_NAME_CONFLICT_AND_MISSING_DOC",
        ]
        for sid in defect_samples:
            pdir = CORPUS_DIR / sid
            res, _ = audit_pipeline.load_and_audit_packet(str(pdir), packet_id=sid, as_of=AS_OF)
            assert res.readiness_score < clean_score, f"Defect scenario {sid} had score {res.readiness_score} >= {clean_score}"

    def test_metamorphic_fail_closed_corruption_abstention(self, audit_pipeline):
        """Metamorphic Invariant M3: Corrupted or unreadable files fail-closed to NEEDS_CHECKS or NOT_READY."""
        corrupted_cases = [
            "SCN_C01_UNREADABLE_INCOME_CERT",
            "SCN_C02_UNREADABLE_MARKSHEET",
            "SCN_C03_UNREADABLE_CASTE_CERT",
            "SCN_C04_CORRUPTED_STREAM",
            "SCN_C11_UNREADABLE_BANK",
        ]
        for sid in corrupted_cases:
            pdir = CORPUS_DIR / sid
            res, _ = audit_pipeline.load_and_audit_packet(str(pdir), packet_id=sid, as_of=AS_OF)
            assert res.readiness != Readiness.NO_ISSUES_FOUND, f"Corrupted scenario {sid} received false READY"
            assert any(f.rule_id == "RULE-DOC-02" for f in res.findings)

    def test_income_ceiling_statutory_enforcement(self, audit_pipeline):
        """Metamorphic Invariant M4: Incomes exceeding ceiling strictly trigger RULE-INC-01 and NOT_READY."""
        ceiling_cases = [
            "SCN_H02_INCOME_ABOVE_CEILING_CERTIFIED",
            "SCN_H03_INCOME_ABOVE_CEILING_SLIGHT",
            "SCN_H10_INCOME_HIGH_EXTREME",
        ]
        for sid in ceiling_cases:
            pdir = CORPUS_DIR / sid
            res, _ = audit_pipeline.load_and_audit_packet(str(pdir), packet_id=sid, as_of=AS_OF)
            assert res.readiness == Readiness.NOT_READY
            assert any(f.rule_id == "RULE-INC-01" for f in res.findings)

    def test_identity_conflict_and_variation_separation(self, audit_pipeline):
        """Metamorphic Invariant M5: Hard conflicts reject; compatible variations review."""
        # Hard conflict -> NOT_READY
        hard_pdir = CORPUS_DIR / "SCN_F02_HARD_NAME_CONFLICT"
        hard_res, _ = audit_pipeline.load_and_audit_packet(str(hard_pdir), packet_id="SCN_F02", as_of=AS_OF)
        assert hard_res.readiness == Readiness.NOT_READY
        assert any(f.rule_id == "RULE-NAME-01" for f in hard_res.findings)

        # Soft middle-name variation -> NEEDS_CHECKS
        soft_pdir = CORPUS_DIR / "SCN_F03_MIDDLE_NAME_OMISSION"
        soft_res, _ = audit_pipeline.load_and_audit_packet(str(soft_pdir), packet_id="SCN_F03", as_of=AS_OF)
        assert soft_res.readiness == Readiness.NEEDS_CHECKS
        assert any(f.rule_id == "RULE-NAME-02" for f in soft_res.findings)

    def test_temporal_future_date_anomaly(self, audit_pipeline):
        """Future issue date strictly flagged and rejected."""
        fut_pdir = CORPUS_DIR / "SCN_G11_FUTURE_ISSUE_DATE"
        fut_res, _ = audit_pipeline.load_and_audit_packet(str(fut_pdir), packet_id="SCN_G11", as_of=AS_OF)
        assert fut_res.readiness == Readiness.NOT_READY
        assert any(f.rule_id == "RULE-EXP-01" for f in fut_res.findings)

    def test_bank_details_validation(self, audit_pipeline):
        """Bank IFSC validation and account number cross-checking."""
        # Valid IFSC passes
        v_pdir = CORPUS_DIR / "SCN_I10_BANK_IFSC_VALID_SBIN"
        v_res, _ = audit_pipeline.load_and_audit_packet(str(v_pdir), packet_id="SCN_I10", as_of=AS_OF)
        assert v_res.readiness == Readiness.NO_ISSUES_FOUND
        assert any(f.rule_id == "RULE-BNK-IFSC-PASS" for f in v_res.findings)

        # Invalid IFSC triggers review under safety intercept
        inv_pdir = CORPUS_DIR / "SCN_I11_BANK_IFSC_INVALID_FORMAT"
        inv_res, _ = audit_pipeline.load_and_audit_packet(str(inv_pdir), packet_id="SCN_I11", as_of=AS_OF)
        assert inv_res.readiness == Readiness.NEEDS_CHECKS
        assert any(f.rule_id == "RULE-BNK-01" for f in inv_res.findings)

        # Account mismatch triggers failure
        acct_pdir = CORPUS_DIR / "SCN_I12_BANK_ACCOUNT_NO_MISMATCH"
        acct_res, _ = audit_pipeline.load_and_audit_packet(str(acct_pdir), packet_id="SCN_I12", as_of=AS_OF)
        assert acct_res.readiness == Readiness.NOT_READY
        assert any(f.rule_id == "RULE-BNK-02" for f in acct_res.findings)

    def test_evidence_provenance_and_statutory_references(self, audit_pipeline):
        """Every finding must carry complete document involvement and valid statutory citations."""
        sample_scenarios = [
            "SCN_A01_CLEAN_BASELINE_ODISHA",
            "SCN_B01_MISSING_INCOME_CERT",
            "SCN_F02_HARD_NAME_CONFLICT",
            "SCN_G05_EXPIRED_CERT_4YEARS",
            "SCN_H02_INCOME_ABOVE_CEILING_CERTIFIED",
        ]
        for sid in sample_scenarios:
            pdir = CORPUS_DIR / sid
            res, _ = audit_pipeline.load_and_audit_packet(str(pdir), packet_id=sid, as_of=AS_OF)
            for f in res.findings:
                assert f.rule_id, "Finding must have a rule_id"
                assert f.documents_involved, f"Finding {f.rule_id} missing documents_involved"
                assert f.statutory_reference, f"Finding {f.rule_id} missing statutory_reference"
                assert f.remediation, f"Finding {f.rule_id} missing remediation"
