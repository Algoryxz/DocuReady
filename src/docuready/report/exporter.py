"""
Privacy-Conscious Audit Report Exporter for DocuReady
Exports audit results and evidence citations to structured JSON and formatted Markdown summaries.
Ensures citizen privacy by masking raw evidence snippets and PII values by default.
"""

import json
import re
import os
from typing import Dict, Any, List
from docuready.domain.models import AuditResult, FindingStatus


def _sanitize_message(message: str) -> str:
    """Masks extracted literal values (names, numbers, quotes) in finding descriptions."""
    def replace_quote(match):
        val = match.group(1)
        # Keep document types intact
        if val in ["APPLICATION_FORM", "INCOME_CERT", "CASTE_CERT", "RESIDENCE_CERT", "MARKSHEET", "BANK_PASSBOOK", "AADHAAR"]:
            return f"'{val}'"
        return "'[REDACTED]'"

    sanitized = re.sub(r"'([^']+)'", replace_quote, message)
    # Mask currency amounts: e.g. ₹2,80,000 or ₹ 250,000
    sanitized = re.sub(r"₹\s*[\d,]+(?:\.\d+)?", "₹[REDACTED]", sanitized)
    return sanitized


def redact_audit_result_dict(result_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Produces a privacy-redacted copy of an AuditResult dictionary."""
    redacted = json.loads(json.dumps(result_dict))

    for f in redacted.get("findings", []):
        if "message" in f and f["message"]:
            f["message"] = _sanitize_message(f["message"])

        for ev in f.get("evidence", []):
            if "raw_snippet" in ev and ev["raw_snippet"]:
                ev["raw_snippet"] = "[REDACTED EVIDENCE SNIPPET]"
            if "file_name" in ev and ev["file_name"]:
                ev["file_name"] = os.path.basename(ev["file_name"])

    return redacted


def export_audit_report_json(result: AuditResult, output_path: str, redact: bool = True) -> str:
    """
    Exports AuditResult object into formatted JSON report.
    By default (redact=True), masks raw document snippets and extracted citizen PII.
    """
    data = result.model_dump()
    if redact:
        data = redact_audit_result_dict(data)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return output_path


def generate_readiness_summary_markdown(result: AuditResult, redact: bool = True) -> str:
    """
    Generates a professional markdown Pre-Submission Readiness Certificate / Audit Report.
    By default (redact=True), masks raw document snippets and citizen PII.
    """
    status_emojis = {
        "READY_TO_SUBMIT": "🟢 READY TO SUBMIT",
        "REVIEW_RECOMMENDED": "🟡 REVIEW RECOMMENDED",
        "ACTION_REQUIRED": "🟠 ACTION REQUIRED (SUBMISSION HALTED)",
        "REJECT_PRECHECK": "🔴 REJECTED AT PRE-CHECK",
        "UNREADABLE_PACKET": "⚪ UNREADABLE DOCUMENT PACKET"
    }
    status_label = status_emojis.get(result.overall_status, result.overall_status)

    md = []
    md.append("# DOCUREADY PRE-SUBMISSION READINESS REPORT")
    if redact:
        md.append("> *Privacy Notice: This report has been redacted to mask extracted personal snippets and citizen identifiers.*  \n")
    md.append(f"**Packet ID:** `{result.packet_id}`  ")
    md.append(f"**Target Scheme:** {result.scheme_name}  ")
    md.append(f"**Audit Timestamp:** {result.timestamp}  ")
    md.append(f"**Execution Latency:** {result.execution_time_ms:.1f} ms  ")
    md.append(f"**Overall Readiness Score:** **{result.readiness_score} / 100**  ")
    md.append(f"**Determination:** **{status_label}**  \n")
    md.append("---")
    md.append("## Executive Summary")
    md.append(f"- **Passed Checks:** {result.summary_counts.get(FindingStatus.PASS.value, 0)}")
    md.append(f"- **Review Advisory Items:** {result.summary_counts.get(FindingStatus.REVIEW.value, 0)}")
    md.append(f"- **Failed Statutory Rules:** {result.summary_counts.get(FindingStatus.FAIL.value, 0)}")
    md.append(f"- **Unreadable / Missing Evidence:** {result.summary_counts.get(FindingStatus.UNKNOWN.value, 0)}\n")

    md.append("---")
    md.append("## Detailed Evidence-Linked Findings\n")

    for idx, f in enumerate(result.findings, 1):
        status_badge = f"[{f.status.value}]"
        penalty_str = f"(-{f.penalty} pts)" if f.penalty > 0 else "(0 pts)"
        msg = _sanitize_message(f.message) if redact else f.message

        md.append(f"### {idx}. {status_badge} {f.rule_name} {penalty_str}")
        md.append(f"- **Rule ID:** `{f.rule_id}`")
        md.append(f"- **Severity Tier:** `{f.severity.value}`")
        md.append(f"- **Documents Involved:** {', '.join(f.documents_involved)}")
        md.append(f"- **Description:** {msg}")
        md.append(f"- **Statutory Source:** *{f.statutory_reference}*")

        if f.evidence:
            md.append("- **Source Provenance & Evidence:**")
            for ev in f.evidence:
                loc = f"Page {ev.page_number}"
                if ev.bounding_box:
                    loc += f" (Bounding Box: {ev.bounding_box})"
                snippet_txt = "[REDACTED EVIDENCE SNIPPET]" if redact else f'"{ev.raw_snippet}"'
                field_info = f" [Field: `{ev.extracted_field}`]" if ev.extracted_field else ""
                md.append(f"  - `{ev.document_type}`: {snippet_txt} [{loc}]{field_info}")

        md.append(f"- **Actionable Remediation Guidance:**  \n  👉 **{f.remediation}**\n")

    md.append("---")
    md.append("### Legal Notice & System Boundaries")
    md.append(
        "> **Note:** DocuReady is an offline pre-submission demographic consistency and document readiness linter. "
        "It is NOT an official government portal, legal authority, or Aadhaar authentication service. "
        "A successful pre-check does not guarantee scheme eligibility, acceptance, or benefit disbursement. "
        "Final eligibility and benefit disbursement remain strictly under the jurisdiction of official scheme authorities."
    )

    return "\n".join(md)
