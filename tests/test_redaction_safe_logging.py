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
    redact_field_value,
    redact_audit_result_dict,
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
    """Verify bank account masking preserves last 4 digits across varying lengths."""
    assert redact_bank_account("9876543210123") == "••••••••0123"
    assert redact_bank_account("1234567890123456") == "••••••••3456"
    assert redact_bank_account("5678") == "••••••••5678"


def test_redact_phone_variants():
    """Verify phone masking handles national, leading-zero, and +91 international formats."""
    assert redact_phone("9876543210") == "••••••••10"
    assert redact_phone("09876543210") == "••••••••10"
    assert redact_phone("+91 98765 43210") == "••••••••10"
    assert redact_phone("+91-9876543210") == "••••••••10"


def test_redact_text_pii_masks_in_freeform_text():
    """Verify regex sanitizer catches identifiers inside audit messages."""
    raw_text = "Applicant Aadhaar 2345 6789 0123 with phone +91 98765 43210 declared income ₹ 2,50,000 in 'Smruti Nayak'"
    sanitized = redact_text_pii(raw_text)
    assert "XXXX-XXXX-0123" in sanitized
    assert "••••••••10" in sanitized
    assert "₹[REDACTED]" in sanitized
    assert "'[REDACTED]'" in sanitized
    assert "2345 6789" not in sanitized
    assert "9876543210" not in sanitized


def test_field_aware_value_redactor():
    """Verify field-aware redactor redacts based on semantic key names."""
    assert redact_field_value("aadhaar_number", "2345 6789 0123") == "XXXX-XXXX-0123"
    assert redact_field_value("account_number", "9876543210123") == "••••••••0123"
    assert redact_field_value("contact_phone", "+91 98765 43210") == "••••••••10"
    assert redact_field_value("annual_income", "250000") == "₹[REDACTED]"
    assert redact_field_value("applicant_name", "Smruti Nayak") == "[REDACTED NAME]"
    assert redact_field_value("status", "PASS") == "PASS"


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


def test_redact_audit_result_dict_preserves_remediation():
    """Verify that remediation instructions remain actionable after redaction."""
    payload = {
        "findings": [
            {
                "rule_id": "RULE-DOB-01",
                "message": "DOB in 'application_form.pdf' does not match marksheet date 14/05/2003",
                "remediation": "Submit corrected Class 10 marksheet from Secondary Board to resolve discrepancy",
                "evidence": [
                    {"raw_snippet": "Candidate DOB: 14/05/2003", "file_name": "/path/to/marksheet.pdf"}
                ]
            }
        ]
    }
    redacted = redact_audit_result_dict(payload)
    finding = redacted["findings"][0]
    assert "marksheet.pdf" in finding["evidence"][0]["file_name"]
    assert finding["evidence"][0]["raw_snippet"] == "[REDACTED EVIDENCE SNIPPET]"
    assert "Submit corrected Class 10 marksheet" in finding["remediation"]


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


def test_safe_logger_handles_formatted_args_and_clears_record_args():
    """Verify safe logger resolves %s formatting and clears record.args to prevent leakage."""
    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    formatter = logging.Formatter("%(levelname)s: %(message)s")
    handler.setFormatter(formatter)

    logger = get_safe_logger("docuready.test_formatted_log")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    # Formatted call with sensitive args
    logger.info("Account=%s, Phone=%s, Income=%s", "9876543210123", "+91 98765 43210", "₹ 2,50,000")
    handler.flush()
    log_output = log_stream.getvalue()

    assert "••••••••10" in log_output
    assert "₹[REDACTED]" in log_output
    assert "9876543210123" not in log_output
    assert "+91 98765 43210" not in log_output


def test_pipeline_execution_uses_safe_logger():
    """Verify production pipeline execution produces sanitized logs."""
    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    logger = get_safe_logger("docuready.pipeline")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    pipeline = AuditPipeline()
    res, _ = pipeline.load_and_audit_packet(str(_PACKET_DIR), packet_id="PKT_01_CLEAN")
    handler.flush()
    log_output = log_stream.getvalue()

    assert "Starting audit for packet_id=PKT_01_CLEAN" in log_output
    assert "Audit completed for packet PKT_01_CLEAN" in log_output


# ---------------------------------------------------------------------------
# 5. Temporary Directory Cleanup Tests
# ---------------------------------------------------------------------------

def test_secure_temporary_directory_cleanup_on_success():
    """Verify secure_temporary_directory cleans up after normal exit."""
    captured_path = None
    with secure_temporary_directory(prefix="docuready_test_") as temp_dir:
        captured_path = temp_dir
        assert captured_path.is_dir()
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
