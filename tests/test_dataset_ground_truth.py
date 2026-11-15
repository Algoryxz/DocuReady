"""
Automated Ground-Truth Verification Suite
Verifies all 8 synthetic demonstration packets against ground_truth_manifest.json.
"""

import os
import json
import pytest
from pathlib import Path
from docuready.domain.enums import Readiness
from docuready.pipeline import AuditPipeline

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SYNTHETIC_DIR = _REPO_ROOT / "synthetic_data" if (_REPO_ROOT / "synthetic_data").is_dir() else Path.cwd() / "synthetic_data"

LEGACY_TO_V2_READINESS = {
    "READY_TO_SUBMIT": Readiness.NO_ISSUES_FOUND,
    "REVIEW_RECOMMENDED": Readiness.NEEDS_CHECKS,
    "ACTION_REQUIRED": Readiness.NOT_READY,
    "REJECT_PRECHECK": Readiness.NOT_READY,
    "UNREADABLE_PACKET": Readiness.NEEDS_CHECKS,
}


@pytest.fixture(scope="module")
def manifest():
    manifest_paths = [
        _SYNTHETIC_DIR / "ground_truth_manifest.json",
        Path.cwd() / "synthetic_data" / "ground_truth_manifest.json",
        Path.cwd() / "ground_truth_manifest.json",
    ]
    manifest_path = next((p for p in manifest_paths if p.is_file()), None)
    assert manifest_path is not None, "ground_truth_manifest.json must exist"
    with open(manifest_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def pipeline():
    return AuditPipeline()


@pytest.mark.parametrize("packet_id", [
    "PKT_01_CLEAN",
    "PKT_02_NAME_CONFLICT",
    "PKT_03_DOB_CONFLICT",
    "PKT_04_INCOME_CONFLICT",
    "PKT_05_MISSING_CERTIFICATE",
    "PKT_06_MULTIPLE_DEFECTS",
    "PKT_07_UNREADABLE_DOC",
    "PKT_08_AMBIGUOUS_EVIDENCE"
])
def test_packet_against_ground_truth(pipeline, manifest, packet_id):
    packet_meta = manifest["packets"][packet_id]
    folder = packet_meta["folder"]
    packet_dir = str(_SYNTHETIC_DIR / folder)

    result, _ = pipeline.load_and_audit_packet(packet_dir, packet_id=packet_id)

    # 1. Assert overall determination matches ground truth
    expected_readiness = LEGACY_TO_V2_READINESS[packet_meta["expected_status"]]
    assert result.overall_status == expected_readiness, (
        f"Status mismatch for {packet_id}: predicted {result.overall_status}, expected {expected_readiness}"
    )

    # 2. Assert score floor
    assert result.readiness_score >= packet_meta["expected_score_min"], (
        f"Score {result.readiness_score} is below expected min {packet_meta['expected_score_min']}"
    )

    # 3. Assert expected failure rules are triggered
    detected_rules = {f.rule_id for f in result.findings if f.status.value in ["FAIL", "REVIEW", "UNKNOWN", "MISSING", "WARN"]}
    for exp_rule in packet_meta["expected_failure_rules"]:
        assert exp_rule in detected_rules, f"Expected rule {exp_rule} was not triggered in {packet_id}"
