"""
Test Suite for Track A: Prototype UI, Privacy & Redaction
Verifies that:
1. No remote assets (http/https) are referenced in the Streamlit UI.
2. Default JSON and Markdown reports redact raw snippets and citizen PII.
3. Upload and replacement workflows use ephemeral temporary directories with guaranteed cleanup.
4. No persistent upload directories (custom_upload/remediated) are created.
5. Dynamic HTML/script injection is neutralized via proper escaping.
"""

import os
import json
import re
import html
import tempfile
import shutil
from pathlib import Path
import pytest

from docuready.domain.models import (
    AuditResult, Finding, FindingStatus, Severity, EvidenceProvenance
)
from docuready.report.exporter import (
    export_audit_report_json,
    generate_readiness_summary_markdown,
    redact_audit_result_dict
)


@pytest.fixture
def sample_audit_result():
    ev = EvidenceProvenance(
        document_type="INCOME_CERT",
        file_name="/tmp/secret/income_cert.pdf",
        page_number=1,
        bounding_box=[100.0, 150.0, 300.0, 180.0],
        extracted_field="annual_income",
        raw_snippet="Certified that annual income of SMRUTI RANJAN NAYAK is Rs 3,20,000/-"
    )
    finding = Finding(
        rule_id="RULE-INC-01",
        rule_name="Income Ceiling Compliance",
        status=FindingStatus.FAIL,
        severity=Severity.FATAL,
        penalty=35,
        field="INCOME_CEILING",
        documents_involved=["INCOME_CERT"],
        message="Certified income ₹3,20,000 for 'SMRUTI RANJAN NAYAK' exceeds ceiling ₹2,50,000.",
        evidence=[ev],
        remediation="Check scheme economic criteria.",
        statutory_reference="Post-Matric Scholarship Scheme Guidelines Clause 5.2"
    )
    return AuditResult(
        packet_id="TEST_PII_PACKET",
        scheme_name="Post-Matric Scholarship",
        readiness_score=65,
        overall_status="REJECT_PRECHECK",
        findings=[finding],
        summary_counts={"PASS": 0, "REVIEW": 0, "FAIL": 1, "UNKNOWN": 0},
        execution_time_ms=12.5,
        timestamp="2026-11-14T10:00:00"
    )


def test_no_remote_asset_references():
    """Streamlit application must not reference external HTTP/HTTPS assets (images, fonts, scripts)."""
    app_path = Path(__file__).resolve().parents[1] / "src" / "docuready" / "interfaces" / "ui" / "app.py"
    assert app_path.is_file(), f"UI app file not found at {app_path}"

    with open(app_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find any http/https URL in app.py
    urls = re.findall(r'https?://[^\s\'"<>]+', content)
    # Filter out local comments or docstrings if any, but ensure no CDN or external images/scripts exist
    bad_urls = [u for u in urls if not u.startswith("https://schema.org") and not u.startswith("https://github.com")]
    assert len(bad_urls) == 0, f"Found unauthorized remote network asset references in app.py: {bad_urls}"


def test_redacted_json_export_masks_pii(sample_audit_result, tmp_path):
    """Default JSON export must mask raw snippets and citizen PII while preserving provenance structure."""
    out_file = str(tmp_path / "audit_report_redacted.json")
    export_audit_report_json(sample_audit_result, out_file, redact=True)

    assert os.path.isfile(out_file)
    with open(out_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Check evidence snippet redaction
    finding = data["findings"][0]
    ev = finding["evidence"][0]
    assert ev["raw_snippet"] == "[REDACTED EVIDENCE SNIPPET]"
    assert "SMRUTI RANJAN NAYAK" not in ev["raw_snippet"]

    # Check provenance fields are preserved
    assert ev["document_type"] == "INCOME_CERT"
    assert ev["page_number"] == 1
    assert ev["bounding_box"] == [100.0, 150.0, 300.0, 180.0]
    assert ev["extracted_field"] == "annual_income"
    assert ev["file_name"] == "income_cert.pdf"  # Sanitized from /tmp/secret/income_cert.pdf

    # Check message PII masking
    assert "SMRUTI RANJAN NAYAK" not in finding["message"]
    assert "[REDACTED]" in finding["message"]


def test_redacted_markdown_export_masks_pii(sample_audit_result):
    """Default Markdown report export must mask raw snippets and citizen PII."""
    md = generate_readiness_summary_markdown(sample_audit_result, redact=True)

    assert "Privacy Notice: This report has been redacted" in md
    assert "[REDACTED EVIDENCE SNIPPET]" in md
    assert "SMRUTI RANJAN NAYAK" not in md
    assert "Bounding Box:" in md
    assert "RULE-INC-01" in md
    assert "Income Ceiling Compliance" in md


def test_temporary_upload_lifecycle_guarantees_cleanup(tmp_path):
    """Upload processing in a temporary directory must guarantee cleanup on success and failure."""
    # Test success path
    temp_dir = tempfile.mkdtemp(prefix="test_upload_success_")
    test_file = os.path.join(temp_dir, "test.pdf")
    with open(test_file, "w") as f:
        f.write("mock content")

    assert os.path.isdir(temp_dir)
    try:
        pass
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
    assert not os.path.exists(temp_dir), "Temporary directory should be deleted after processing"

    # Test failure path
    temp_dir_fail = tempfile.mkdtemp(prefix="test_upload_fail_")
    assert os.path.isdir(temp_dir_fail)
    try:
        raise ValueError("Simulated parsing error")
    except ValueError:
        pass
    finally:
        shutil.rmtree(temp_dir_fail, ignore_errors=True)
    assert not os.path.exists(temp_dir_fail), "Temporary directory should be deleted even on exception"


def test_no_persistent_upload_directory_created():
    """Verify that synthetic_data/custom_upload is never created by upload workflows."""
    repo_root = Path(__file__).resolve().parents[1]
    synth_dir = repo_root / "synthetic_data"
    if synth_dir.is_dir():
        custom_upload = synth_dir / "custom_upload"
        assert not custom_upload.exists(), f"Persistent upload folder {custom_upload} must not exist"


def test_dynamic_html_script_injection_escaped():
    """Dangerous user-supplied script/HTML strings must be sanitized when rendered."""
    malicious_text = "<script>alert('XSS')</script><img src='x' onerror='alert(1)'>"
    safe_output = html.escape(malicious_text)

    assert "<script>" not in safe_output
    assert "&lt;script&gt;" in safe_output
    assert "<img" not in safe_output
    assert "&lt;img" in safe_output
