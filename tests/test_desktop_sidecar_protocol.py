from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

import pytest

from sidecar.docuready_sidecar import (
    MAX_REQUEST_BYTES,
    PROTOCOL_VERSION,
    _handle,
    _workspace_path,
    main,
)


class MockStdin:
    def __init__(self, data: bytes):
        self.buffer = io.BytesIO(data)


def test_health_protocol_response_is_versioned() -> None:
    response = _handle(
        {
            "protocol": PROTOCOL_VERSION,
            "id": "health-test",
            "method": "health",
            "params": {},
        }
    )

    assert response["protocol"] == PROTOCOL_VERSION
    assert response["id"] == "health-test"
    assert response["ok"] is True
    assert response["result"]["sidecar"] == "docuready-python"
    assert response["result"]["protocol"] == PROTOCOL_VERSION
    assert response["result"]["engine_version"] == "0.1.0"
    assert "python" in response["result"]
    assert "pdf_backend" in response["result"]
    assert "ocr_available" in response["result"]


def test_protocol_version_mismatch_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unsupported protocol version"):
        _handle(
            {
                "protocol": PROTOCOL_VERSION + 1,
                "id": "bad-version",
                "method": "health",
                "params": {},
            }
        )


def test_workspace_path_must_be_inside_managed_root(tmp_path, monkeypatch) -> None:
    managed = tmp_path / "managed"
    outside = tmp_path / "outside"
    managed.mkdir()
    outside.mkdir()
    monkeypatch.setenv("DOCUREADY_WORKSPACE_ROOT", str(managed))

    with pytest.raises(ValueError, match="outside the managed workspace"):
        _workspace_path(str(outside))


def test_workspace_path_accepts_managed_packet_directory(tmp_path, monkeypatch) -> None:
    managed = tmp_path / "managed"
    packet = managed / "packet-001"
    packet.mkdir(parents=True)
    monkeypatch.setenv("DOCUREADY_WORKSPACE_ROOT", str(managed))

    assert _workspace_path(str(packet)) == packet.resolve()


def test_workspace_path_rejects_empty_or_non_string() -> None:
    with pytest.raises(ValueError, match="staged packet directory is required"):
        _workspace_path("")
    with pytest.raises(ValueError, match="staged packet directory is required"):
        _workspace_path(None)


def test_workspace_path_rejects_root_itself(tmp_path, monkeypatch) -> None:
    managed = tmp_path / "managed"
    managed.mkdir()
    monkeypatch.setenv("DOCUREADY_WORKSPACE_ROOT", str(managed))

    with pytest.raises(ValueError, match="outside the managed workspace"):
        _workspace_path(str(managed))


def test_unsupported_method_raises() -> None:
    with pytest.raises(ValueError, match="Unsupported sidecar method"):
        _handle(
            {
                "protocol": PROTOCOL_VERSION,
                "id": "unknown-test",
                "method": "unknown_action",
                "params": {},
            }
        )


def test_shutdown_method_response() -> None:
    res = _handle(
        {
            "protocol": PROTOCOL_VERSION,
            "id": "shutdown-test",
            "method": "shutdown",
            "params": {},
        }
    )
    assert res["ok"] is True
    assert res["result"]["status"] == "shutting_down"


def test_audit_packet_requires_as_of_date(tmp_path, monkeypatch) -> None:
    managed = tmp_path / "managed"
    packet = managed / "packet-001"
    packet.mkdir(parents=True)
    monkeypatch.setenv("DOCUREADY_WORKSPACE_ROOT", str(managed))

    with pytest.raises(ValueError, match="explicit ISO date is required"):
        _handle(
            {
                "protocol": PROTOCOL_VERSION,
                "id": "audit-no-date",
                "method": "audit_packet",
                "params": {
                    "packet_dir": str(packet),
                    "packet_id": "TEST_PKT",
                },
            }
        )


def test_stdio_jsonl_oversized_request_handling(monkeypatch) -> None:
    large_line = (b"x" * (MAX_REQUEST_BYTES + 10)) + b"\n"
    monkeypatch.setattr(sys, "stdin", MockStdin(large_line))

    out_capture = io.StringIO()
    monkeypatch.setattr(sys.stdout, "write", out_capture.write)
    monkeypatch.setattr(sys.stdout, "flush", lambda: None)

    exit_code = main()
    assert exit_code == 0
    raw_output = out_capture.getvalue().strip()
    frame = json.loads(raw_output)
    assert frame["ok"] is False
    assert frame["error"]["code"] == "REQUEST_TOO_LARGE"


def test_stdio_jsonl_malformed_json_handling(monkeypatch) -> None:
    bad_line = b"{not-valid-json\n"
    monkeypatch.setattr(sys, "stdin", MockStdin(bad_line))

    out_capture = io.StringIO()
    monkeypatch.setattr(sys.stdout, "write", out_capture.write)
    monkeypatch.setattr(sys.stdout, "flush", lambda: None)

    exit_code = main()
    assert exit_code == 0
    raw_output = out_capture.getvalue().strip()
    frame = json.loads(raw_output)
    assert frame["ok"] is False
    assert frame["error"]["code"] == "REQUEST_FAILED"


def test_stdio_jsonl_shutdown_exits_cleanly(monkeypatch) -> None:
    req = json.dumps(
        {
            "protocol": PROTOCOL_VERSION,
            "id": "req-sd",
            "method": "shutdown",
            "params": {},
        }
    ).encode("utf-8") + b"\n"
    monkeypatch.setattr(sys, "stdin", MockStdin(req))

    out_capture = io.StringIO()
    monkeypatch.setattr(sys.stdout, "write", out_capture.write)
    monkeypatch.setattr(sys.stdout, "flush", lambda: None)

    exit_code = main()
    assert exit_code == 0
    raw_output = out_capture.getvalue().strip()
    frame = json.loads(raw_output)
    assert frame["ok"] is True
    assert frame["result"]["status"] == "shutting_down"


def test_audit_packet_full_synthetic_parity(tmp_path, monkeypatch) -> None:
    managed = tmp_path / "managed"
    packet = managed / "packet-001"
    managed.mkdir()
    
    # Stage synthetic packet
    repo_root = Path(__file__).resolve().parent.parent
    src_clean = repo_root / "synthetic_data" / "pkt_01_clean"
    import shutil
    shutil.copytree(src_clean, packet)

    monkeypatch.setenv("DOCUREADY_WORKSPACE_ROOT", str(managed))

    res = _handle(
        {
            "protocol": PROTOCOL_VERSION,
            "id": "synthetic-test",
            "method": "audit_packet",
            "params": {
                "packet_dir": str(packet),
                "packet_id": "SYNTH_01",
                "as_of": "2026-11-16",
            },
        }
    )

    assert res["ok"] is True
    assert res["id"] == "synthetic-test"
    audit = res["result"]["audit"]
    assert audit["packet_id"] == "SYNTH_01"
    assert audit["overall_status"] == "NO_ISSUES_FOUND"
    assert audit["readiness_score"] == 100
    assert len(audit["findings"]) > 0

    # Verify document summaries and provenance
    docs = res["result"]["documents"]
    assert len(docs) >= 5
    for doc in docs:
        assert "document_type" in doc
        assert doc["page_count"] >= 1
        for f in doc["fields"]:
            assert "field" in f
            assert "evidence_state" in f
            if f["page"] is not None:
                assert isinstance(f["page"], int)
            if f["bounding_box"] is not None:
                assert len(f["bounding_box"]) == 4
