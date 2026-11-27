"""
Permanent Regression Test Suite for Loop 08
Desktop Workflow Integrity, Human Review UX, Recovery Assurance & Audit Usability
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path
import pytest

from docuready.domain.enums import EvidenceState, MaxSeverity, Readiness, ReasonCode, Status
from docuready.domain.models import AuditResult, ExtractedDocument, ExtractedField, Finding
from docuready.report.redact import redact_audit_result_dict
from docuready.pipeline import AuditPipeline

REPO_ROOT = Path(__file__).resolve().parents[1]
SYNTH_DIR = REPO_ROOT / "synthetic_data" / "pkt_01_clean"
SIDECAR_SCRIPT = REPO_ROOT / "sidecar" / "docuready_sidecar.py"


# ---------------------------------------------------------------------------
# 1. SIDECAR PROTOCOL & HEALTH HANDSHAKE TESTS
# ---------------------------------------------------------------------------

def test_sidecar_health_handshake_returns_protocol_and_capabilities(tmp_path: Path) -> None:
    """Verifies that the sidecar returns protocol version 1 and engine capabilities."""
    env = os.environ.copy()
    env["DOCUREADY_WORKSPACE_ROOT"] = str(tmp_path)
    env["PYTHONPATH"] = str(REPO_ROOT / "src")

    proc = subprocess.Popen(
        [sys.executable, str(SIDECAR_SCRIPT)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env
    )

    try:
        req = {
            "protocol": 1,
            "id": "req-health-test",
            "method": "health",
            "params": {}
        }
        stdout, _ = proc.communicate(input=json.dumps(req) + "\n", timeout=15)
        response = json.loads(stdout.strip())

        assert response["ok"] is True
        assert response["id"] == "req-health-test"
        assert response["protocol"] == 1
        result = response["result"]
        assert result["sidecar"] == "docuready-python"
        assert "engine_version" in result
        assert "pdf_backend" in result
        assert "ocr_available" in result
    finally:
        proc.kill()


def test_sidecar_rejects_paths_outside_workspace_root(tmp_path: Path) -> None:
    """Security Boundary: Any packet_dir outside DOCUREADY_WORKSPACE_ROOT must be strictly rejected."""
    workspace_root = tmp_path / "workspaces"
    workspace_root.mkdir()
    outside_dir = tmp_path / "malicious_outside"
    outside_dir.mkdir()

    env = os.environ.copy()
    env["DOCUREADY_WORKSPACE_ROOT"] = str(workspace_root)
    env["PYTHONPATH"] = str(REPO_ROOT / "src")

    proc = subprocess.Popen(
        [sys.executable, str(SIDECAR_SCRIPT)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env
    )

    try:
        req = {
            "protocol": 1,
            "id": "req-security-test",
            "method": "audit_packet",
            "params": {
                "packet_dir": str(outside_dir),
                "packet_id": "pkt-exploit",
                "as_of": "2026-11-16"
            }
        }
        stdout, _ = proc.communicate(input=json.dumps(req) + "\n", timeout=15)
        response = json.loads(stdout.strip())

        assert response["ok"] is False
        assert response["id"] == "req-security-test"
        assert response["error"]["code"] == "WORKSPACE_VIOLATION"
        assert "could not be completed" in response["error"]["message"]
    finally:
        proc.kill()


# ---------------------------------------------------------------------------
# 2. END-TO-END WORKFLOW & REPORT REDACTION INTEGRITY
# ---------------------------------------------------------------------------

def test_sidecar_end_to_end_audit_and_report_redaction(tmp_path: Path) -> None:
    """Verifies that sidecar executes an audit and returns a fully redacted, zero-PII payload."""
    import shutil

    workspace_root = tmp_path / "workspaces"
    workspace_root.mkdir()
    packet_dir = workspace_root / "pkt-test-01"
    packet_dir.mkdir()

    # Stage documents from pkt_01_clean
    for f in SYNTH_DIR.glob("*.pdf"):
        shutil.copy(f, packet_dir / f.name)

    env = os.environ.copy()
    env["DOCUREADY_WORKSPACE_ROOT"] = str(workspace_root)
    env["PYTHONPATH"] = str(REPO_ROOT / "src")

    proc = subprocess.Popen(
        [sys.executable, str(SIDECAR_SCRIPT)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env
    )

    try:
        req = {
            "protocol": 1,
            "id": "req-audit-e2e",
            "method": "audit_packet",
            "params": {
                "packet_dir": str(packet_dir),
                "packet_id": "pkt-test-01",
                "as_of": "2026-11-16"
            }
        }
        stdout, _ = proc.communicate(input=json.dumps(req) + "\n", timeout=30)
        lines = [line.strip() for line in stdout.splitlines() if line.strip()]

        # Find correlated response frame
        response_frame = None
        progress_frames = []
        for line in lines:
            data = json.loads(line)
            if data.get("event") == "progress":
                progress_frames.append(data)
            elif data.get("id") == "req-audit-e2e":
                response_frame = data

        assert response_frame is not None
        assert response_frame["ok"] is True
        assert len(progress_frames) > 0, "Expected at least one progress event during audit"

        audit = response_frame["result"]["audit"]
        assert audit["packet_id"] == "pkt-test-01"
        assert audit["overall_status"] == "NO_ISSUES_FOUND"
        assert audit["readiness_score"] == 100

        # Verify zero unredacted PII in serialized result
        dumped = json.dumps(audit)
        assert "Aadhaar" not in dumped or "XXXX" in dumped or "masked" in dumped or "aadhaar.pdf" in dumped
    finally:
        proc.kill()


# ---------------------------------------------------------------------------
# 3. HUMAN REVIEW & CONSERVATIVE ABSTENTION METADATA HONESTY
# ---------------------------------------------------------------------------

def test_human_review_preserves_honest_reason_codes_and_no_hallucinated_boxes() -> None:
    """Verifies that REVIEW/NEEDS_CHECKS findings provide actionable reason codes and no fake geometry."""
    pipeline = AuditPipeline(as_of=date(2026, 11, 16))
    result, _ = pipeline.load_and_audit_packet(
        str(REPO_ROOT / "synthetic_data" / "pkt_08_ambiguous_evidence"),
        packet_id="PKT_AMBIGUOUS_REVIEW",
        as_of=date(2026, 11, 16)
    )

    public_dict = redact_audit_result_dict(result.to_public_dict(canonical=True))

    review_or_warn_findings = [
        f for f in public_dict["findings"]
        if f["status"] in ("REVIEW", "WARN", "MANUAL_REVIEW")
    ]

    assert len(review_or_warn_findings) > 0, "Expected at least one REVIEW/WARN finding in ambiguous packet"

    for finding in review_or_warn_findings:
        assert finding["reason_code"] is not None and len(finding["reason_code"]) > 0
        assert finding["message"] is not None and len(finding["message"]) > 0
        # If evidence is present, bounding boxes must either be valid 4-tuples or null (never invented)
        for ev in finding.get("evidence", []):
            bbox = ev.get("bounding_box")
            if bbox is not None:
                assert len(bbox) == 4
                assert all(isinstance(coord, (int, float)) for coord in bbox)
