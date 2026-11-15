"""Tests for redaction, safe logging, and secure temporary upload directories (Task T1.4)."""

from __future__ import annotations

import io
import json
import logging
import pathlib
import pytest
from unittest.mock import patch

from docuready.pipeline import AuditPipeline
from docuready.report.redact import (
    get_safe_logger,
    redact_aadhaar,
    redact_bank_account,
    redact_phone,
    redact_text_pii,
    secure_temporary_directory,
)
from docuready.report.exporter import (
    export_audit_report_json,
    generate_readiness_summary_markdown,
)
from docuready.interfaces.cli import main as cli_main

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_PACKET_DIR = _REPO_ROOT / "synthetic_data" / "pkt_01_clean"


# ---------------------------------------------------------------------------
# 1. PII Redaction Unit Tests
# ---------------------------------------------------------------------------

def test_redact_aadhaar():
    """Verify Aadhaar masking keeps only last 4 digits visible."""
    assert redact_aadhaar("2345 6789 0123") == "XXXX-XXXX-0123"
    assert redact_aadhaar("234567890123") == "XXXX-XXXX-0123"
    assert redact_aadhaar("2345-6789-0123") == "XXXX-XXXX-0123"


def test_redact_bank_account():
    """Verify bank account masking keeps only last 4 digits visible."""
    assert redact_bank_account("9876543210123") == "••••••••0123"
    assert redact_bank_account("1234") == "••••••••1234"


def test_redact_phone():
    """Verify mobile number masking keeps only last 2 digits visible."""
    assert redact_phone("9876543210") == "••••••••10"
    assert redact_phone("8123456789") == "••••••••89"


def test_redact_text_pii_masks_in_freeform_text():
    """Verify regex sanitizer catches identifiers inside audit messages."""
    raw_text = "Applicant Aadhaar 2345 6789 0123 with phone 9876543210 declared income ₹ 2,50,000 in 'Smruti Nayak'"
    sanitized = redact_text_pii(raw_text)
    assert "XXXX-XXXX-0123" in sanitized
    assert "••••••••10" in sanitized
    assert "₹[REDACTED]" in sanitized
    assert "'[REDACTED]'" in sanitized
    assert "2345 6789" not in sanitized
    assert "9876543210" not in sanitized


# ---------------------------------------------------------------------------
# 2. Exporter Redaction Tests (JSON & Markdown)
# ---------------------------------------------------------------------------

def test_exporters_redact_by_default(tmp_path):
    """Verify JSON and Markdown reports redact PII and raw snippets by default."""
    pipeline = AuditPipeline()
    result, _ = pipeline.load_and_audit_packet(str(_PACKET_DIR), packet_id="PKT_01_CLEAN")

    # JSON export
    json_path = tmp_path / "report.json"
    export_audit_report_json(result, str(json_path), redact=True)
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    for finding in data.get("findings", []):
        for ev in finding.get("evidence", []):
            if ev.get("raw_snippet"):
                assert ev["raw_snippet"] == "[REDACTED EVIDENCE SNIPPET]"

    # Markdown export
    md = generate_readiness_summary_markdown(result, redact=True)
    assert "Privacy Notice: This report has been redacted" in md
    assert "[REDACTED EVIDENCE SNIPPET]" in md or len(result.findings) > 0


def test_exporters_no_redact_mode(tmp_path):
    """Verify unredacted output is preserved when explicitly requested."""
    pipeline = AuditPipeline()
    result, _ = pipeline.load_and_audit_packet(str(_PACKET_DIR), packet_id="PKT_01_CLEAN")

    md_unredacted = generate_readiness_summary_markdown(result, redact=False)
    assert "Privacy Notice: This report has been redacted" not in md_unredacted


# ---------------------------------------------------------------------------
# 3. CLI --no-redact Flag & Warning Tests
# ---------------------------------------------------------------------------

def test_cli_audit_default_and_no_redact_warning(capsys):
    """Verify CLI requires explicit --no-redact flag and emits a privacy warning."""
    # Run with default redaction
    with patch("sys.argv", ["docuready", "audit", str(_PACKET_DIR)]):
        cli_main()
    captured = capsys.readouterr()
    assert "WARNING: --no-redact specified" not in captured.err

    # Run with --no-redact
    with patch("sys.argv", ["docuready", "audit", str(_PACKET_DIR), "--no-redact"]):
        cli_main()
    captured_no_redact = capsys.readouterr()
    assert "WARNING: --no-redact specified" in captured_no_redact.err


# ---------------------------------------------------------------------------
# 4. Safe Logging Inspection Tests
# ---------------------------------------------------------------------------

def test_safe_logger_intercepts_sensitive_identifiers():
    """Verify get_safe_logger masks sensitive identifiers in log messages."""
    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    logger = get_safe_logger("docuready.test_safe_log")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    logger.info("Auditing applicant with Aadhaar 2345 6789 0123 and phone 9876543210")
    handler.flush()
    log_output = log_stream.getvalue()

    assert "XXXX-XXXX-0123" in log_output
    assert "••••••••10" in log_output
    assert "2345 6789 0123" not in log_output
    assert "9876543210" not in log_output


# ---------------------------------------------------------------------------
# 5. Temporary Directory Cleanup Tests
# ---------------------------------------------------------------------------

def test_secure_temporary_directory_cleanup_on_success():
    """Verify secure_temporary_directory cleans up after normal exit."""
    captured_path = None
    with secure_temporary_directory(prefix="docuready_test_") as temp_dir:
        captured_path = temp_dir
        assert captured_path.is_dir()
        # Create a synthetic file inside
        test_file = captured_path / "test.txt"
        test_file.write_text("synthetic upload byte buffer", encoding="utf-8")
        assert test_file.is_file()

    assert captured_path is not None
    assert not captured_path.exists(), "Temporary directory must be deleted on exit"


def test_secure_temporary_directory_cleanup_on_exception():
    """Verify secure_temporary_directory cleans up in finally block when exceptions occur."""
    captured_path = None
    with pytest.raises(ZeroDivisionError):
        with secure_temporary_directory(prefix="docuready_test_") as temp_dir:
            captured_path = temp_dir
            assert captured_path.is_dir()
            (captured_path / "payload.bin").write_bytes(b"\x00\x01\x02")
            _ = 1 / 0

    assert captured_path is not None
    assert not captured_path.exists(), "Temporary directory must be deleted even if an exception occurs"
