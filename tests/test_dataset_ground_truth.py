"""
Automated Ground-Truth Verification Suite
Verifies all 8 synthetic demonstration packets against ground_truth_manifest.json.
"""

import os
import json
import pytest
from src.pipeline import AuditPipeline


@pytest.fixture(scope="module")
def manifest():
    manifest_paths = [
        "synthetic_data/ground_truth_manifest.json",
        "docuready-mvp/ground_truth_manifest.json",
        "ground_truth_manifest.json"
    ]
    manifest_path = next((p for p in manifest_paths if os.path.exists(p)), None)
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
    if os.path.exists("synthetic_data"):
        packet_dir = os.path.join("synthetic_data", folder)
    else:
        packet_dir = os.path.join("docuready-mvp/synthetic_data", folder)

    result, _ = pipeline.load_and_audit_packet(packet_dir, packet_id=packet_id)

    # 1. Assert overall determination matches ground truth
    assert result.overall_status == packet_meta["expected_status"], (
        f"Status mismatch for {packet_id}: predicted {result.overall_status}, expected {packet_meta['expected_status']}"
    )

    # 2. Assert score floor
    assert result.readiness_score >= packet_meta["expected_score_min"], (
        f"Score {result.readiness_score} is below expected min {packet_meta['expected_score_min']}"
    )

    # 3. Assert expected failure rules are triggered
    detected_rules = {f.rule_id for f in result.findings if f.status.value in ["FAIL", "REVIEW", "UNKNOWN"]}
    for exp_rule in packet_meta["expected_failure_rules"]:
        assert exp_rule in detected_rules, f"Expected rule {exp_rule} was not triggered in {packet_id}"
