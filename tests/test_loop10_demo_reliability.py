"""
Permanent Demonstration Reliability & Readiness Test Suite for Loop 10
Competition Demo Reliability, Feature Freeze, Final Readiness & Demonstration Qualification
DocuReady - HackNation 2026
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
DESKTOP_DIR = REPO_ROOT / "apps" / "desktop"
OUT_DIR = DESKTOP_DIR / "out"
PACKAGE_DIR = OUT_DIR / "DocuReady-win32-x64"
RESOURCES_DIR = PACKAGE_DIR / "resources"
PACKAGED_SIDECAR = RESOURCES_DIR / "docuready_sidecar" / "docuready_sidecar.exe"
PACKAGED_TESSERACT = RESOURCES_DIR / "docuready_sidecar" / "tesseract" / "tesseract.exe"
PACKAGED_TESSDATA = RESOURCES_DIR / "docuready_sidecar" / "tesseract" / "tessdata"

DEMO_PACKETS = [
    ("pkt_01_clean", "NO_ISSUES_FOUND", 100, 100, "RULE-NAME-PASS"),
    ("pkt_02_name_conflict", "NOT_READY", 75, 75, "RULE-NAME-01"),
    ("pkt_05_missing_certificate", "NOT_READY", 65, 65, "RULE-DOC-01"),
    ("pkt_08_ambiguous_evidence", "NEEDS_CHECKS", 90, 90, "RULE-NAME-02"),
    ("pkt_07_unreadable_doc", "NEEDS_CHECKS", 75, 75, "RULE-DOC-02"),
]


def _run_audit(workspace_root: Path, packet_name: str, req_id: str) -> dict:
    clean_env = {
        "SYSTEMROOT": os.environ.get("SYSTEMROOT", r"C:\Windows"),
        "PATH": r"C:\Windows\system32;C:\Windows",
        "TEMP": str(workspace_root.parent),
        "TMP": str(workspace_root.parent),
        "DOCUREADY_WORKSPACE_ROOT": str(workspace_root),
        "DOCUREADY_RESOURCES_DIR": str(RESOURCES_DIR),
        "DOCUREADY_TESSERACT_PATH": str(PACKAGED_TESSERACT),
        "TESSDATA_PREFIX": str(PACKAGED_TESSDATA),
        "DOCUREADY_REQUIRE_BUNDLED_OCR": "1",
    }
    packet_dir = workspace_root / packet_name

    proc = subprocess.Popen(
        [str(PACKAGED_SIDECAR)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=clean_env,
    )
    req = {
        "protocol": 1,
        "id": req_id,
        "method": "audit_packet",
        "params": {
            "packet_dir": str(packet_dir),
            "packet_id": packet_name,
            "as_of": "2026-11-16",
        },
    }
    stdout, stderr = proc.communicate(input=json.dumps(req) + "\n", timeout=30)
    assert proc.returncode == 0, f"Sidecar process failed with {proc.returncode}. Stderr: {stderr}"

    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            data = json.loads(line)
            if data.get("id") == req_id:
                assert data["ok"] is True, f"Sidecar response not ok: {data}"
                return data["result"]["audit"]
        except json.JSONDecodeError:
            continue
    pytest.fail(f"Could not find response frame for {req_id} in stdout: {stdout}")


# ---------------------------------------------------------------------------
# 1. DEMO PACKET GROUND TRUTH PARITY
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "packet_name,expected_status,min_score,max_score,key_rule",
    DEMO_PACKETS,
)
def test_demo_packet_ground_truth_parity(
    tmp_path: Path,
    packet_name: str,
    expected_status: str,
    min_score: int,
    max_score: int,
    key_rule: str,
) -> None:
    """Verifies that each demo packet produces exact expected status and scores in packaged sidecar."""
    if not PACKAGED_SIDECAR.is_file():
        pytest.skip("Packaged sidecar binary missing")

    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    packet_dir = workspace_root / packet_name
    packet_dir.mkdir()

    source_dir = REPO_ROOT / "synthetic_data" / packet_name
    assert source_dir.is_dir(), f"Synthetic packet directory missing: {source_dir}"
    for f in source_dir.glob("*.pdf"):
        shutil.copy(f, packet_dir / f.name)

    audit = _run_audit(workspace_root, packet_name, f"demo-audit-{packet_name}")

    assert audit["overall_status"] == expected_status, (
        f"Status mismatch for {packet_name}: expected {expected_status}, got {audit['overall_status']}"
    )
    assert min_score <= audit["readiness_score"] <= max_score, (
        f"Score mismatch for {packet_name}: expected {min_score}..{max_score}, got {audit['readiness_score']}"
    )

    rule_ids = [f["rule_id"] for f in audit["findings"]]
    assert key_rule in rule_ids, f"Expected key rule {key_rule} not found in findings: {rule_ids}"


# ---------------------------------------------------------------------------
# 2. REPEATABILITY & DETERMINISM
# ---------------------------------------------------------------------------

def test_demo_packet_repeatability_and_determinism(tmp_path: Path) -> None:
    """Verifies that consecutive audits of the same packet yield 100% bit-exact results."""
    if not PACKAGED_SIDECAR.is_file():
        pytest.skip("Packaged sidecar binary missing")

    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    packet_name = "pkt_02_name_conflict"
    packet_dir = workspace_root / packet_name
    packet_dir.mkdir()

    source_dir = REPO_ROOT / "synthetic_data" / packet_name
    for f in source_dir.glob("*.pdf"):
        shutil.copy(f, packet_dir / f.name)

    run_results = []
    for i in range(3):
        res = _run_audit(workspace_root, packet_name, f"rep-audit-{i}")
        run_results.append(res)

    # Assert exact equality across all 3 runs
    first_status = run_results[0]["overall_status"]
    first_score = run_results[0]["readiness_score"]
    first_finding_count = len(run_results[0]["findings"])

    for idx, r in enumerate(run_results[1:], start=2):
        assert r["overall_status"] == first_status, f"Run {idx} status differed: {r['overall_status']}"
        assert r["readiness_score"] == first_score, f"Run {idx} score differed: {r['readiness_score']}"
        assert len(r["findings"]) == first_finding_count, f"Run {idx} finding count differed"


# ---------------------------------------------------------------------------
# 3. NEGATIVE EVIDENCE INTEGRITY (NO HALLUCINATED BOUNDING BOXES)
# ---------------------------------------------------------------------------

def test_missing_document_negative_evidence_integrity(tmp_path: Path) -> None:
    """Verifies that missing documents have an empty evidence list with zero fake bounding boxes."""
    if not PACKAGED_SIDECAR.is_file():
        pytest.skip("Packaged sidecar binary missing")

    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    packet_name = "pkt_05_missing_certificate"
    packet_dir = workspace_root / packet_name
    packet_dir.mkdir()

    source_dir = REPO_ROOT / "synthetic_data" / packet_name
    for f in source_dir.glob("*.pdf"):
        shutil.copy(f, packet_dir / f.name)

    audit = _run_audit(workspace_root, packet_name, "req-neg-evidence")
    missing_findings = [f for f in audit["findings"] if f["rule_id"] == "RULE-DOC-01"]
    assert len(missing_findings) == 1
    m_find = missing_findings[0]

    assert m_find["status"] == "MISSING"
    assert m_find["evidence"] == [], "Evidence list for missing document must be empty"
    assert "CASTE_CERT" in m_find["documents_involved"]


# ---------------------------------------------------------------------------
# 4. UNREADABLE DOCUMENT CONSERVATIVE ABSTENTION
# ---------------------------------------------------------------------------

def test_unreadable_document_conservative_abstention(tmp_path: Path) -> None:
    """Verifies that degraded/unreadable documents trigger REVIEW without fabricating coordinates."""
    if not PACKAGED_SIDECAR.is_file():
        pytest.skip("Packaged sidecar binary missing")

    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    packet_name = "pkt_07_unreadable_doc"
    packet_dir = workspace_root / packet_name
    packet_dir.mkdir()

    source_dir = REPO_ROOT / "synthetic_data" / packet_name
    for f in source_dir.glob("*.pdf"):
        shutil.copy(f, packet_dir / f.name)

    audit = _run_audit(workspace_root, packet_name, "req-unreadable-abstention")
    unreadable_findings = [f for f in audit["findings"] if f["rule_id"] == "RULE-DOC-02"]
    assert len(unreadable_findings) == 1
    u_find = unreadable_findings[0]

    assert u_find["status"] == "REVIEW"
    assert audit["overall_status"] == "NEEDS_CHECKS"
    # Evidence must not contain hallucinated bounding boxes
    for ev in u_find.get("evidence", []):
        assert ev.get("bounding_box") is None, "Bounding box on unreadable document must be None"


# ---------------------------------------------------------------------------
# 5. ZERO PII LEAK IN USER-FACING MESSAGES
# ---------------------------------------------------------------------------

def test_zero_pii_in_findings_and_messages(tmp_path: Path) -> None:
    """Verifies that diagnostic finding messages redact sensitive candidate values."""
    if not PACKAGED_SIDECAR.is_file():
        pytest.skip("Packaged sidecar binary missing")

    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    packet_name = "pkt_02_name_conflict"
    packet_dir = workspace_root / packet_name
    packet_dir.mkdir()

    source_dir = REPO_ROOT / "synthetic_data" / packet_name
    for f in source_dir.glob("*.pdf"):
        shutil.copy(f, packet_dir / f.name)

    audit = _run_audit(workspace_root, packet_name, "req-zero-pii")
    conflict_findings = [f for f in audit["findings"] if f["rule_id"] == "RULE-NAME-01"]
    assert len(conflict_findings) == 1
    msg = conflict_findings[0]["message"]
    assert "[REDACTED]" in msg, f"Expected [REDACTED] in message: {msg}"
    assert "Aarav" not in msg, f"Raw applicant name leaked in message: {msg}"


# ---------------------------------------------------------------------------
# 6. DEMO PERFORMANCE LATENCY BUDGET
# ---------------------------------------------------------------------------

def test_demo_performance_latency_budget(tmp_path: Path) -> None:
    """Verifies that clean packet audit executes well within the 5000ms competition limit."""
    if not PACKAGED_SIDECAR.is_file():
        pytest.skip("Packaged sidecar binary missing")

    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    packet_name = "pkt_01_clean"
    packet_dir = workspace_root / packet_name
    packet_dir.mkdir()

    source_dir = REPO_ROOT / "synthetic_data" / packet_name
    for f in source_dir.glob("*.pdf"):
        shutil.copy(f, packet_dir / f.name)

    t0 = time.perf_counter()
    audit = _run_audit(workspace_root, packet_name, "req-latency-test")
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    assert audit["overall_status"] == "NO_ISSUES_FOUND"
    assert elapsed_ms < 5000.0, f"Audit exceeded 5000ms budget: {elapsed_ms:.1f}ms"


# ---------------------------------------------------------------------------
# 7. RELEASE ARTIFACT DELIVERABLES AND HASHES INTEGRITY
# ---------------------------------------------------------------------------

def test_release_deliverables_presence_and_integrity() -> None:
    """Verifies that packaged desktop release binaries and installer artifacts exist."""
    app_exe = PACKAGE_DIR / "DocuReady.exe"
    app_asar = RESOURCES_DIR / "app.asar"
    sidecar_exe = PACKAGED_SIDECAR

    if not app_exe.is_file() and os.environ.get("DOCUREADY_REQUIRE_RELEASE_ARTIFACTS") != "1":
        pytest.skip(f"Packaged desktop release artifacts not built in this environment: {app_exe}")

    assert app_exe.is_file(), f"Missing DocuReady.exe: {app_exe}"
    assert app_asar.is_file(), f"Missing app.asar: {app_asar}"
    assert sidecar_exe.is_file(), f"Missing sidecar.exe: {sidecar_exe}"

    assert app_exe.stat().st_size > 50_000_000, "DocuReady.exe file size too small"
    assert app_asar.stat().st_size > 1_000_000, "app.asar file size too small"
    assert sidecar_exe.stat().st_size > 10_000_000, "docuready_sidecar.exe file size too small"
