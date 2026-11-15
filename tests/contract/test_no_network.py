"""
No-Network and Telemetry Suppression Contract Test Suite for DocuReady (Task T1.2).

Verifies that:
1. Streamlit telemetry is explicitly disabled via committed .streamlit/config.toml.
2. .streamlit/secrets.toml is ignored by Git while .streamlit/config.toml is tracked.
3. Socket network tripwires (socket.socket.connect, socket.getaddrinfo, socket.create_connection)
   immediately intercept and prevent any outbound network calls.
4. The full AuditPipeline runs completely across all eight canonical demo packets
   without attempting any network access.
5. The document replacement and re-audit workflow executes completely under zero-network conditions.
"""

from __future__ import annotations

import socket
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple
import pytest

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

from docuready.domain.enums import Readiness, Status
from docuready.domain.models import DocumentType, AuditResult
from docuready.pipeline import AuditPipeline

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SYNTHETIC_DIR = _REPO_ROOT / "synthetic_data"


class NetworkAccessBlockedError(RuntimeError):
    """Raised whenever outbound network access or DNS resolution is attempted."""
    pass


@pytest.fixture
def prohibit_network(monkeypatch):
    """
    Tripwire fixture that monkeypatches network entry points to immediately raise
    NetworkAccessBlockedError if any socket connection or address resolution is attempted.
    """
    def blocked_connect(self, *args, **kwargs):
        raise NetworkAccessBlockedError(
            f"Prohibited network connection attempt intercepted: socket.connect(args={args}, kwargs={kwargs})"
        )

    def blocked_getaddrinfo(*args, **kwargs):
        raise NetworkAccessBlockedError(
            f"Prohibited DNS resolution attempt intercepted: socket.getaddrinfo(args={args}, kwargs={kwargs})"
        )

    def blocked_create_connection(*args, **kwargs):
        raise NetworkAccessBlockedError(
            f"Prohibited socket connection attempt intercepted: socket.create_connection(args={args}, kwargs={kwargs})"
        )

    monkeypatch.setattr(socket.socket, "connect", blocked_connect)
    monkeypatch.setattr(socket, "getaddrinfo", blocked_getaddrinfo)
    monkeypatch.setattr(socket, "create_connection", blocked_create_connection)
    return True


def test_streamlit_telemetry_disabled():
    """
    Contract test: Verify that .streamlit/config.toml is present, correctly configured
    to suppress usage telemetry, and repository ignore rules correctly distinguish config
    from secrets.
    """
    config_path = _REPO_ROOT / ".streamlit" / "config.toml"
    assert config_path.is_file(), f"Expected committed .streamlit/config.toml at {config_path}"

    with open(config_path, "rb") as f:
        config = tomllib.load(f)

    assert "browser" in config, "Missing [browser] section in .streamlit/config.toml"
    assert config["browser"].get("gatherUsageStats") is False, (
        f"Expected browser.gatherUsageStats = false, got {config['browser'].get('gatherUsageStats')}"
    )

    # Verify .gitignore properly targets secrets and does not ignore config.toml
    gitignore_path = _REPO_ROOT / ".gitignore"
    assert gitignore_path.is_file(), "Missing .gitignore file in repository root"
    gitignore_text = gitignore_path.read_text(encoding="utf-8")
    lines = [line.strip() for line in gitignore_text.splitlines() if line.strip() and not line.startswith("#")]

    assert ".streamlit/secrets.toml" in lines, ".gitignore must explicitly ignore .streamlit/secrets.toml"
    assert ".streamlit/" not in lines, ".gitignore must not broadly ignore entire .streamlit/ directory"


def test_network_tripwire_intercepts_unauthorized_network_calls(prohibit_network):
    """
    Verify that our socket tripwire actively blocks socket calls without permitting
    any actual outbound packet transmission.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        with pytest.raises(NetworkAccessBlockedError, match="socket.connect"):
            s.connect(("127.0.0.1", 8080))
    finally:
        s.close()

    with pytest.raises(NetworkAccessBlockedError, match="socket.getaddrinfo"):
        socket.getaddrinfo("example.com", 80)


CANONICAL_PACKETS: List[Tuple[str, str]] = [
    ("PKT_01_CLEAN", "pkt_01_clean"),
    ("PKT_02_NAME_CONFLICT", "pkt_02_name_conflict"),
    ("PKT_03_DOB_CONFLICT", "pkt_03_dob_conflict"),
    ("PKT_04_INCOME_CONFLICT", "pkt_04_income_conflict"),
    ("PKT_05_MISSING_CERTIFICATE", "pkt_05_missing_certificate"),
    ("PKT_06_MULTIPLE_DEFECTS", "pkt_06_multiple_defects"),
    ("PKT_07_UNREADABLE_DOC", "pkt_07_unreadable_doc"),
    ("PKT_08_AMBIGUOUS_EVIDENCE", "pkt_08_ambiguous_evidence"),
]


@pytest.mark.parametrize("packet_id,folder_name", CANONICAL_PACKETS)
def test_audit_pipeline_zero_network_canonical_packet(prohibit_network, packet_id: str, folder_name: str):
    """
    Verify that AuditPipeline audits each canonical demo packet completely
    with zero outbound network activity.
    """
    packet_dir = _SYNTHETIC_DIR / folder_name
    assert packet_dir.is_dir(), f"Packet directory missing at {packet_dir}"

    pipeline = AuditPipeline()
    result, docs = pipeline.load_and_audit_packet(str(packet_dir), packet_id=packet_id)

    assert isinstance(result, AuditResult)
    assert result.packet_id == packet_id
    assert len(docs) > 0, f"Expected extracted documents for packet {packet_id}"
    assert result.overall_status in (
        Readiness.NO_ISSUES_FOUND,
        Readiness.NEEDS_CHECKS,
        Readiness.NOT_READY,
    )
    assert isinstance(result.readiness_score, (int, float))
    assert 0 <= result.readiness_score <= 100


def test_document_replacement_and_reaudit_zero_network(prohibit_network):
    """
    Verify that the document replacement and instant re-audit workflow
    executes completely without any outbound network calls.
    """
    pipeline = AuditPipeline()

    # Step 1: Ingest defective packet (DOB mismatch in pkt_03_dob_conflict)
    packet_dir = _SYNTHETIC_DIR / "pkt_03_dob_conflict"
    initial_res, initial_docs = pipeline.load_and_audit_packet(
        str(packet_dir), packet_id="PKT_03_DOB_CONFLICT"
    )
    assert initial_res.overall_status is Readiness.NOT_READY
    assert initial_res.readiness_score == 75
    assert any(f.rule_id == "RULE-DOB-01" and f.status in ("FAIL", Status.FAIL) for f in initial_res.findings)

    # Step 2: Remediate by replacing marksheet with clean marksheet
    corrected_marksheet_path = _SYNTHETIC_DIR / "pkt_01_clean" / "marksheet.pdf"
    assert corrected_marksheet_path.is_file(), f"Clean marksheet missing at {corrected_marksheet_path}"

    new_res, new_docs = pipeline.replace_document_and_reaudit(
        initial_docs,
        str(corrected_marksheet_path),
        DocumentType.MARKSHEET,
        packet_id="PKT_03_REMEDIATED"
    )

    # Step 3: Assert clean resolution
    assert new_res.overall_status is Readiness.NO_ISSUES_FOUND
    assert new_res.readiness_score == 100
    assert not any(f.status in ("FAIL", Status.FAIL) for f in new_res.findings)
    assert any(f.rule_id == "RULE-DOB-PASS" and f.status in ("PASS", Status.PASS) for f in new_res.findings)


def test_audit_all_eight_packets_aggregate_zero_network(prohibit_network):
    """
    Aggregate verification: Run all eight canonical demo packets sequentially through
    the pipeline to prove batch auditing operates under full network isolation.
    """
    pipeline = AuditPipeline()
    audited_results: Dict[str, AuditResult] = {}

    for packet_id, folder_name in CANONICAL_PACKETS:
        packet_dir = _SYNTHETIC_DIR / folder_name
        res, docs = pipeline.load_and_audit_packet(str(packet_dir), packet_id=packet_id)
        assert isinstance(res, AuditResult)
        assert res.packet_id == packet_id
        audited_results[packet_id] = res

    assert len(audited_results) == 8
    expected_ids = {pid for pid, _ in CANONICAL_PACKETS}
    assert set(audited_results.keys()) == expected_ids
