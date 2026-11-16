from __future__ import annotations

import pytest

from sidecar.docuready_sidecar import PROTOCOL_VERSION, _handle, _workspace_path


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
