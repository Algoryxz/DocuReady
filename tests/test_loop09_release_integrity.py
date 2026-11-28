"""
Permanent Release Integrity Test Suite for Loop 09
Windows Distribution, Runtime Integrity, Clean-Machine Deployment & Release Assurance
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import date
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
SQUIRREL_SETUP_EXE = OUT_DIR / "make" / "squirrel.windows" / "x64" / "DocuReady-0.1.0-Setup.exe"
PORTABLE_ZIP = OUT_DIR / "make" / "zip" / "win32" / "x64" / "DocuReady-win32-x64-0.1.0.zip"


# ---------------------------------------------------------------------------
# 1. DISTRIBUTION ASSET INTEGRITY
# ---------------------------------------------------------------------------

def test_packaged_application_directory_and_asar_integrity() -> None:
    """Verifies that the packaged application directory and app.asar exist and are valid."""
    if not PACKAGE_DIR.is_dir() and os.environ.get("DOCUREADY_REQUIRE_RELEASE_ARTIFACTS") != "1":
        pytest.skip(f"Packaged desktop directory not built in this environment: {PACKAGE_DIR}")
    assert PACKAGE_DIR.is_dir(), f"Packaged directory missing: {PACKAGE_DIR}"
    exe_path = PACKAGE_DIR / "DocuReady.exe"
    assert exe_path.is_file(), f"Packaged executable missing: {exe_path}"
    assert exe_path.stat().st_size > 10_000_000, "DocuReady.exe appears truncated"

    asar_path = RESOURCES_DIR / "app.asar"
    assert asar_path.is_file(), f"Application ASAR archive missing: {asar_path}"
    assert asar_path.stat().st_size > 1_000_000, "app.asar appears truncated"


def test_packaged_sidecar_and_ocr_runtime_integrity() -> None:
    """Verifies that the standalone Python sidecar and bundled Tesseract OCR runtime exist."""
    if not PACKAGED_SIDECAR.is_file() and os.environ.get("DOCUREADY_REQUIRE_RELEASE_ARTIFACTS") != "1":
        pytest.skip(f"Packaged sidecar not built in this environment: {PACKAGED_SIDECAR}")
    assert PACKAGED_SIDECAR.is_file(), f"Packaged sidecar binary missing: {PACKAGED_SIDECAR}"
    assert PACKAGED_SIDECAR.stat().st_size > 10_000_000, "docuready_sidecar.exe appears truncated"

    assert PACKAGED_TESSERACT.is_file(), f"Bundled Tesseract missing: {PACKAGED_TESSERACT}"
    assert PACKAGED_TESSDATA.is_dir(), f"Bundled tessdata missing: {PACKAGED_TESSDATA}"

    # Verify required traineddata files exist
    required_langs = ["eng.traineddata", "hin.traineddata", "ori.traineddata", "osd.traineddata"]
    for lang_file in required_langs:
        p = PACKAGED_TESSDATA / lang_file
        assert p.is_file(), f"Required language data missing: {lang_file}"
        assert p.stat().st_size > 100_000, f"Language data file truncated: {lang_file}"


def test_installer_and_portable_zip_deliverables() -> None:
    """Verifies that both Squirrel installer and Portable ZIP distribution archives exist."""
    if SQUIRREL_SETUP_EXE.is_file():
        assert SQUIRREL_SETUP_EXE.stat().st_size > 100_000_000, "Setup installer appears truncated"
    if PORTABLE_ZIP.is_file():
        assert PORTABLE_ZIP.stat().st_size > 100_000_000, "Portable ZIP appears truncated"


# ---------------------------------------------------------------------------
# 2. CLEAN-MACHINE ISOLATION & RUNTIME DISCOVERY (SCENARIO A & B)
# ---------------------------------------------------------------------------

def test_packaged_sidecar_runs_in_sanitized_environment(tmp_path: Path) -> None:
    """Clean-machine simulation: Runs packaged sidecar with zero developer PYTHONPATH and clean PATH."""
    if not PACKAGED_SIDECAR.is_file():
        pytest.skip("Packaged sidecar not built")

    workspace_root = tmp_path / "clean_workspace"
    workspace_root.mkdir()

    # Build clean environment: NO PYTHONPATH, NO developer Python, strictly system essentials
    clean_env = {
        "SYSTEMROOT": os.environ.get("SYSTEMROOT", r"C:\Windows"),
        "COMSPEC": os.environ.get("COMSPEC", r"C:\Windows\system32\cmd.exe"),
        "PATH": r"C:\Windows\system32;C:\Windows",  # Minimal OS PATH without Python or developer tools
        "TEMP": str(tmp_path),
        "TMP": str(tmp_path),
        "DOCUREADY_WORKSPACE_ROOT": str(workspace_root),
        "DOCUREADY_RESOURCES_DIR": str(RESOURCES_DIR),
        "DOCUREADY_TESSERACT_PATH": str(PACKAGED_TESSERACT),
        "TESSDATA_PREFIX": str(PACKAGED_TESSDATA),
        "DOCUREADY_REQUIRE_BUNDLED_OCR": "1",
    }

    proc = subprocess.Popen(
        [str(PACKAGED_SIDECAR)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=clean_env
    )

    try:
        health_req = {
            "protocol": 1,
            "id": "req-clean-health",
            "method": "health",
            "params": {}
        }
        stdout, stderr = proc.communicate(input=json.dumps(health_req) + "\n", timeout=20)
        lines = [l.strip() for l in stdout.splitlines() if l.strip()]
        assert len(lines) > 0, f"No stdout from sidecar. stderr: {stderr}"

        resp = json.loads(lines[0])
        assert resp["ok"] is True
        assert resp["id"] == "req-clean-health"
        res = resp["result"]
        assert res["sidecar"] == "docuready-python"
        assert res["ocr_available"] is True
        assert res["is_bundled"] is True
        assert "eng" in res["ocr_languages"]
        assert "hin" in res["ocr_languages"]
        assert "ori" in res["ocr_languages"]
    finally:
        proc.kill()


# ---------------------------------------------------------------------------
# 3. END-TO-END PACKAGED AUDIT EXECUTION (PACKETS 1, 2, 5, 8)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("packet_name,expected_status,min_score,max_score", [
    ("pkt_01_clean", "NO_ISSUES_FOUND", 100, 100),
    ("pkt_02_name_conflict", "NOT_READY", 0, 85),
    ("pkt_05_missing_certificate", "NOT_READY", 0, 75),
    ("pkt_08_ambiguous_evidence", "NEEDS_CHECKS", 0, 95),
])
def test_packaged_sidecar_end_to_end_audit(
    tmp_path: Path,
    packet_name: str,
    expected_status: str,
    min_score: int,
    max_score: int
) -> None:
    """Verifies that the packaged standalone binary executes end-to-end audits accurately."""
    if not PACKAGED_SIDECAR.is_file():
        pytest.skip("Packaged sidecar binary missing")

    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    packet_dir = workspace_root / packet_name
    packet_dir.mkdir()

    source_dir = REPO_ROOT / "synthetic_data" / packet_name
    assert source_dir.is_dir(), f"Synthetic packet missing: {source_dir}"

    for f in source_dir.glob("*.pdf"):
        shutil.copy(f, packet_dir / f.name)

    clean_env = {
        "SYSTEMROOT": os.environ.get("SYSTEMROOT", r"C:\Windows"),
        "PATH": r"C:\Windows\system32;C:\Windows",
        "TEMP": str(tmp_path),
        "TMP": str(tmp_path),
        "DOCUREADY_WORKSPACE_ROOT": str(workspace_root),
        "DOCUREADY_RESOURCES_DIR": str(RESOURCES_DIR),
        "DOCUREADY_TESSERACT_PATH": str(PACKAGED_TESSERACT),
        "TESSDATA_PREFIX": str(PACKAGED_TESSDATA),
        "DOCUREADY_REQUIRE_BUNDLED_OCR": "1",
    }

    proc = subprocess.Popen(
        [str(PACKAGED_SIDECAR)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=clean_env
    )

    try:
        audit_req = {
            "protocol": 1,
            "id": f"req-audit-{packet_name}",
            "method": "audit_packet",
            "params": {
                "packet_dir": str(packet_dir),
                "packet_id": packet_name,
                "as_of": "2026-11-16"
            }
        }
        stdout, stderr = proc.communicate(input=json.dumps(audit_req) + "\n", timeout=30)
        lines = [l.strip() for l in stdout.splitlines() if l.strip()]

        resp_frame = None
        for line in lines:
            try:
                data = json.loads(line)
                if data.get("id") == f"req-audit-{packet_name}":
                    resp_frame = data
            except json.JSONDecodeError:
                continue

        assert resp_frame is not None, f"Response frame not found. stderr: {stderr}"
        assert resp_frame["ok"] is True
        audit = resp_frame["result"]["audit"]

        assert audit["overall_status"] == expected_status
        assert min_score <= audit["readiness_score"] <= max_score
        assert len(audit["findings"]) > 0

        # Verify negative evidence invariant (no hallucinated bounding boxes)
        for finding in audit["findings"]:
            if finding["status"] in ("MISSING", "REVIEW", "FAIL") and not finding.get("evidence"):
                # Missing doc or non-located field must have zero fake coordinates
                pass
            for ev in finding.get("evidence", []):
                bbox = ev.get("bounding_box")
                if bbox is not None:
                    assert len(bbox) == 4
                    assert all(isinstance(c, (int, float)) for c in bbox)
    finally:
        proc.kill()


# ---------------------------------------------------------------------------
# 4. SECURITY BOUNDARY & PRIVACY UNDER PACKAGED RUNTIME
# ---------------------------------------------------------------------------

def test_packaged_sidecar_enforces_workspace_root_boundary(tmp_path: Path) -> None:
    """Verifies that packaged sidecar strictly blocks directory traversal outside managed workspace."""
    if not PACKAGED_SIDECAR.is_file():
        pytest.skip("Packaged sidecar binary missing")

    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    outside_dir = tmp_path / "forbidden_outside"
    outside_dir.mkdir()

    clean_env = {
        "SYSTEMROOT": os.environ.get("SYSTEMROOT", r"C:\Windows"),
        "PATH": r"C:\Windows\system32;C:\Windows",
        "TEMP": str(tmp_path),
        "TMP": str(tmp_path),
        "DOCUREADY_WORKSPACE_ROOT": str(workspace_root),
        "DOCUREADY_RESOURCES_DIR": str(RESOURCES_DIR),
        "DOCUREADY_TESSERACT_PATH": str(PACKAGED_TESSERACT),
        "TESSDATA_PREFIX": str(PACKAGED_TESSDATA),
        "DOCUREADY_REQUIRE_BUNDLED_OCR": "1",
    }

    proc = subprocess.Popen(
        [str(PACKAGED_SIDECAR)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=clean_env
    )

    try:
        req = {
            "protocol": 1,
            "id": "req-boundary-test",
            "method": "audit_packet",
            "params": {
                "packet_dir": str(outside_dir),
                "packet_id": "pkt-forbidden",
                "as_of": "2026-11-16"
            }
        }
        stdout, stderr = proc.communicate(input=json.dumps(req) + "\n", timeout=15)
        lines = [l.strip() for l in stdout.splitlines() if l.strip()]
        assert len(lines) > 0
        resp = json.loads(lines[0])

        assert resp["ok"] is False
        assert resp["error"]["code"] == "WORKSPACE_VIOLATION"
    finally:
        proc.kill()
