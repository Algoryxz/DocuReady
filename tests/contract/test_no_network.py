"""Contract test: verify zero network egress and telemetry suppression.

Ensures that:
1. Streamlit usage telemetry is suppressed via .streamlit/config.toml (gatherUsageStats = false).
2. .gitignore only ignores .streamlit/secrets.toml, preserving the committed configuration.
3. Socket operations (connect, getaddrinfo) are actively blocked during pipeline execution.
4. All 8 canonical packets and remediation workflows execute under complete network isolation.
"""

from __future__ import annotations

import pathlib
import socket
from typing import Dict, List, Tuple

import pytest

from docuready.domain.models import AuditResult, DocumentType
from docuready.pipeline import AuditPipeline

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
_SYNTHETIC_DIR = _REPO_ROOT / "synthetic_data"


class NetworkAccessBlockedError(RuntimeError):
    """Raised whenever unauthorized network egress is attempted."""


@pytest.fixture
def prohibit_network(monkeypatch):
    """
    Monkeypatch low-level socket operations to guarantee that any runtime attempt
    to resolve DNS or open a socket connection fails immediately.
    """

    def _blocked_connect(self, *args, **kwargs):
        raise NetworkAccessBlockedError(
            f"Unauthorized network egress attempted via socket.connect({args}, {kwargs})"
        )

    def _blocked_getaddrinfo(*args, **kwargs):
        raise NetworkAccessBlockedError(
            f"Unauthorized DNS lookup attempted via socket.getaddrinfo({args}, {kwargs})"
        )

    monkeypatch.setattr(socket.socket, "connect", _blocked_connect)
    monkeypatch.setattr(socket, "getaddrinfo", _blocked_getaddrinfo)
    yield


def test_streamlit_telemetry_disabled():
    """Verify that Streamlit usage telemetry is explicitly disabled in repo config."""
    config_path = _REPO_ROOT / ".streamlit" / "config.toml"
    assert config_path.is_file(), "Missing .streamlit/config.toml configuration"
    content = config_path.read_text(encoding="utf-8")
    assert "gatherUsageStats = false" in content, (
        "Expected gatherUsageStats = false under [browser] in .streamlit/config.toml"
    )


def test_gitignore_ignores_only_secrets_not_entire_streamlit_dir():
    """Verify .gitignore does not ignore .streamlit/ broadly, only secrets.toml."""
    gitignore_path = _REPO_ROOT / ".gitignore"
    assert gitignore_path.is_file(), "Missing .gitignore file in repository root"
    gitignore_text = gitignore_path.read_text(encoding="utf-8")
    lines = [
        line.strip()
        for line in gitignore_text.splitlines()
        if line.strip() and not line.startswith("#")
    ]

    assert ".streamlit/secrets.toml" in lines, (
        ".gitignore must explicitly ignore .streamlit/secrets.toml"
    )
    assert ".streamlit/" not in lines, (
        ".gitignore must not broadly ignore entire .streamlit/ directory"
    )


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
def test_audit_pipeline_zero_network_canonical_packet(
    prohibit_network, packet_id: str, folder_name: str
):
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
        "READY_TO_SUBMIT",
        "ACTION_REQUIRED",
        "REJECT_PRECHECK",
        "UNREADABLE_PACKET",
        "REVIEW_RECOMMENDED",
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
    assert initial_res.overall_status in ["ACTION_REQUIRED", "REJECT_PRECHECK"]
    assert initial_res.readiness_score == 75
    assert any(f.rule_id == "RULE-DOB-01" and f.status == "FAIL" for f in initial_res.findings)

    # Step 2: Remediate by replacing marksheet with clean marksheet
    corrected_marksheet_path = _SYNTHETIC_DIR / "pkt_01_clean" / "marksheet.pdf"
    assert corrected_marksheet_path.is_file(), f"Clean marksheet missing at {corrected_marksheet_path}"

    new_res, new_docs = pipeline.replace_document_and_reaudit(
        initial_docs,
        str(corrected_marksheet_path),
        DocumentType.MARKSHEET,
        packet_id="PKT_03_REMEDIATED",
    )

    # Step 3: Assert clean resolution
    assert new_res.overall_status == "READY_TO_SUBMIT"
    assert new_res.readiness_score == 100
    assert not any(f.status == "FAIL" for f in new_res.findings)
    assert any(f.rule_id == "RULE-DOB-PASS" and f.status == "PASS" for f in new_res.findings)


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
