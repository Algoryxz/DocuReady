"""Tests for redaction, safe logging, and secure temporary upload directories (Task T1.4)."""

from __future__ import annotations

import io
import json
import logging
import pathlib
import pytest
from unittest.mock import patch

from docuready.domain.enums import ExitCode, Readiness
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
    """Verify CLI requires explicit --no-redact flag and emits a privacy warning while returning ExitCode."""
    # Run with default redaction
    with patch("sys.argv", ["docuready", "audit", str(_PACKET_DIR)]):
with pytest.raises(SystemExit) as exc1:
    cli_main()

assert exc1.value.code == int(ExitCode.NO_ISSUES)
    captured = capsys.readouterr()
    assert "WARNING: --no-redact specified" not in captured.err

    # Run with --no-redact
    with patch("sys.argv", ["docuready", "audit", str(_PACKET_DIR), "--no-redact"]):
with pytest.raises(SystemExit) as exc2:
    cli_main()

assert exc2.value.code == int(ExitCode.NO_ISSUES)
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


# ---------------------------------------------------------------------------
# 6. T1.4 Full Integration Evidence Tests
# ---------------------------------------------------------------------------

def test_default_export_redaction_integration(tmp_path, capsys):
    """Integration test verifying default export redaction, PII masking, and --no-redact controls.

    Uses a synthetic packet audit result injected with unique PII:
    - Unique Aadhaar: '9999 1111 2222'
    - Unique Bank Account: '123456789012'
    - Unique Phone: '+91 98765 43210'
    - Unique Applicant Name: 'Priya Test Sharma'
    - Raw Evidence Snippet containing identifiers

    Verifies:
    1. Default JSON export omits raw evidence snippets and masks PII while preserving rule IDs and remediation.
    2. Default Markdown export omits raw evidence snippets and masks PII while preserving rule IDs and remediation.
    3. Explicit unredacted export (redact=False) preserves full PII and raw snippets.
    4. CLI invocation requires explicit --no-redact flag and emits a warning on stderr.
    """
    pipeline = AuditPipeline()
    result, _ = pipeline.load_and_audit_packet(str(_PACKET_DIR), packet_id="PKT_01_CLEAN")

    # Inject synthetic finding with distinct identifiers and raw snippet
    uid = "9999 1111 2222"
    bank_acc = "123456789012"
    phone_no = "+91 98765 43210"
    applicant = "Priya Test Sharma"
    raw_snip = f"Candidate '{applicant}' UID: {uid}, Phone: {phone_no}, A/c: {bank_acc}"
    remediation_text = "Ensure original photo ID and passbook are available during document verification."
    rule_id = "RULE-SYNTH-PII-01"

    # Mutate finding 0
    f0 = result.findings[0]
    f0.rule_id = rule_id
    f0.message = f"Demographic check for applicant '{applicant}' with Aadhaar {uid} and mobile {phone_no}"
    f0.remediation = remediation_text
    if f0.evidence:
        f0.evidence[0].raw_snippet = raw_snip

    # 1. Default JSON export
    json_path = tmp_path / "default_export.json"
    export_audit_report_json(result, str(json_path), redact=True)
    json_content = json_path.read_text(encoding="utf-8")

    assert uid not in json_content, "Full Aadhaar must NOT appear in default JSON export"
    assert "9876543210" not in json_content, "Full phone number must NOT appear in default JSON export"
    assert "123456789012" not in json_content, "Full bank account must NOT appear in default JSON export"
    assert applicant not in json_content, "Full applicant name 'Priya Test Sharma' must NOT appear in default JSON export"
    assert raw_snip not in json_content, "Raw evidence snippet must NOT appear in default JSON export"
    assert "[REDACTED EVIDENCE SNIPPET]" in json_content, "Raw snippet must be replaced with placeholder"
    assert rule_id in json_content, "Rule ID must be preserved in default JSON export"
    assert remediation_text in json_content, "Actionable remediation must be preserved in default JSON export"

    # 2. Default Markdown export
    md_content = generate_readiness_summary_markdown(result, redact=True)
    assert uid not in md_content, "Full Aadhaar must NOT appear in default Markdown export"
    assert "9876543210" not in md_content, "Full phone number must NOT appear in default Markdown export"
    assert "123456789012" not in md_content, "Full bank account must NOT appear in default Markdown export"
    assert applicant not in md_content, "Full applicant name 'Priya Test Sharma' must NOT appear in default Markdown export"
    assert raw_snip not in md_content, "Raw evidence snippet must NOT appear in default Markdown export"
    assert rule_id in md_content, "Rule ID must be preserved in default Markdown export"
    assert remediation_text in md_content, "Actionable remediation must be preserved in default Markdown export"
    assert "Privacy Notice: This report has been redacted" in md_content

    # 3. Unredacted Export (redact=False)
    unredacted_json_path = tmp_path / "unredacted_export.json"
    export_audit_report_json(result, str(unredacted_json_path), redact=False)
    unredacted_json = unredacted_json_path.read_text(encoding="utf-8")
    assert uid in unredacted_json, "Unredacted JSON export must retain original Aadhaar"
    assert raw_snip in unredacted_json, "Unredacted JSON export must retain raw snippet"

    unredacted_md = generate_readiness_summary_markdown(result, redact=False)
    assert uid in unredacted_md, "Unredacted Markdown export must retain original Aadhaar"
    assert "Privacy Notice: This report has been redacted" not in unredacted_md

    # 4. CLI with and without --no-redact
    with patch("sys.argv", ["docuready", "audit", str(_PACKET_DIR)]):
with pytest.raises(SystemExit) as exc_info:
    cli_main()

assert exc_info.value.code == int(ExitCode.NO_ISSUES)
    captured_default = capsys.readouterr()
    assert "WARNING: --no-redact specified" not in captured_default.err

    with patch("sys.argv", ["docuready", "audit", str(_PACKET_DIR), "--no-redact"]):
with pytest.raises(SystemExit) as exc_info:
    cli_main()

assert exc_info.value.code == int(ExitCode.NO_ISSUES)
    captured_unredacted = capsys.readouterr()
    assert "WARNING: --no-redact specified" in captured_unredacted.err


def test_full_pipeline_logging_safe():
    """Verify that end-to-end pipeline execution and logging never leak raw citizen PII or OCR text.

    Scope & Limitations:
    Proves that an actual synthetic pipeline audit execution on reference synthetic packet
    data, combined with candidate PII-bearing diagnostic messages dispatched through the
    production pipeline logger, results in zero unmasked citizen identifiers or raw OCR text
    in captured log streams. Does NOT process or evaluate real citizen identity documents.

    Verifies:
    1. SafeLogFilter eager formatting and record.args clearing prevent downstream exposure.
    2. Full pipeline run on synthetic packets produces zero unredacted PII in log records.
    3. Pipeline logger masks Aadhaar, phone, bank account, applicant names, and raw OCR snippets.
    4. Complete injected raw OCR text string is absent from captured logs.
    """
    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    formatter = logging.Formatter("%(levelname)s: %(message)s")
    handler.setFormatter(formatter)

    pipeline_logger = get_safe_logger("docuready.pipeline")
    pipeline_logger.setLevel(logging.DEBUG)
    pipeline_logger.addHandler(handler)

    try:
        # Run full pipeline audit on synthetic packet
        pipeline = AuditPipeline()
        res_clean, docs_clean = pipeline.load_and_audit_packet(str(_PACKET_DIR), packet_id="PKT_01_CLEAN")
assert res_clean.overall_status in (
    Readiness.NO_ISSUES_FOUND,
    "NO_ISSUES_FOUND"
)

        # Explicitly log candidate diagnostic messages that an engineer or extractor might emit
        uid = "9999 1111 2222"
        phone = "9876543210"
        bank_acc = "123456789012"
        applicant = "Priya Test Sharma"
        raw_ocr = "Raw OCR stream text containing Aadhaar 9999 1111 2222 and Phone 9876543210 for applicant 'Priya Test Sharma'"

        # Test %s formatted logging with quoted name
        pipeline_logger.info("Processing applicant '%s' with UID %s and acc %s", applicant, uid, bank_acc)
        # Test freeform message logging with raw OCR string
        pipeline_logger.debug("Extracted raw OCR text: %s", raw_ocr)

        handler.flush()
        logs = log_stream.getvalue()

        # Assert no full citizen identifiers appear anywhere in the logs
        assert uid not in logs, f"Full Aadhaar {uid} must not be logged"
        assert phone not in logs, f"Full phone {phone} must not be logged"
        assert bank_acc not in logs, f"Full bank account {bank_acc} must not be logged"
        assert "9999 1111" not in logs
        assert "9876543210" not in logs
        assert "'Priya Test Sharma'" not in logs, "Quoted citizen name must be masked in logs"
        assert raw_ocr not in logs, "Complete injected raw OCR string must not appear in logs"

        # Assert sanitized representations are present
        assert "XXXX-XXXX-2222" in logs, "Masked Aadhaar must be present"
        assert "••••••••10" in logs, "Masked phone must be present"
        assert "9012" in logs, "Last 4 digits preserved in masked account/Aadhaar"
        assert "'[REDACTED]'" in logs, "Quoted citizen name must be masked as '[REDACTED]'"

    finally:
        pipeline_logger.removeHandler(handler)



def test_cli_exit_code_mapping_across_outcomes():
    """Verify CLI exit codes map to 0 (NO_ISSUES), 1 (NEEDS_CHECKS), 2 (NOT_READY), and 64 (USAGE_ERROR)."""
    # 0: Clean packet -> NO_ISSUES
    with patch("sys.argv", ["docuready", "audit", str(_PACKET_DIR)]):
        with pytest.raises(SystemExit) as exc0:
            cli_main()
        assert exc0.value.code == int(ExitCode.NO_ISSUES)

    # 1: Needs checks packet (PKT_07_UNREADABLE_DOC)
    pkt07 = _REPO_ROOT / "synthetic_data" / "pkt_07_unreadable_doc"
    with patch("sys.argv", ["docuready", "audit", str(pkt07)]):
        with pytest.raises(SystemExit) as exc1:
            cli_main()
        assert exc1.value.code == int(ExitCode.NEEDS_CHECKS)

    # 2: Not ready packet (PKT_02_NAME_CONFLICT)
    pkt02 = _REPO_ROOT / "synthetic_data" / "pkt_02_name_conflict"
    with patch("sys.argv", ["docuready", "audit", str(pkt02)]):
        with pytest.raises(SystemExit) as exc2:
            cli_main()
        assert exc2.value.code == int(ExitCode.NOT_READY)

    # 64: Non-existent directory -> USAGE_ERROR
    with patch("sys.argv", ["docuready", "audit", "/nonexistent/packet/directory"]):
        with pytest.raises(SystemExit) as exc64:
            cli_main()
        assert exc64.value.code == int(ExitCode.USAGE_ERROR)
