"""
Audit Report Exporter for DocuReady MVP
Exports audit results and evidence citations to structured JSON and formatted Markdown/Text summaries.
"""

import json
from typing import Dict, Any
from docuready.domain.models import AuditResult, FindingStatus


def export_audit_report_json(result: AuditResult, output_path: str) -> str:
    """Exports AuditResult object into formatted JSON report."""
    data = result.model_dump()
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return output_path


def generate_readiness_summary_markdown(result: AuditResult) -> str:
    """Generates a professional markdown Pre-Submission Readiness Certificate / Audit Report."""
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
    md.append(f"**Packet ID:** `{result.packet_id}`  ")
    md.append(f"**Target Scheme:** {result.scheme_name}  ")
    md.append(f"**Audit Timestamp:** {result.timestamp}  ")
    md.append(f"**Execution Latency:** {result.execution_time_ms} ms  ")
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
        md.append(f"### {idx}. {status_badge} {f.rule_name} {penalty_str}")
        md.append(f"- **Rule ID:** `{f.rule_id}`")
        md.append(f"- **Severity Tier:** `{f.severity.value}`")
        md.append(f"- **Documents Involved:** {', '.join(f.documents_involved)}")
        md.append(f"- **Description:** {f.message}")
        md.append(f"- **Statutory Source:** *{f.statutory_reference}*")

        if f.evidence:
            md.append("- **Source Provenance & Evidence:**")
            for ev in f.evidence:
                loc = f"Page {ev.page_number}"
                if ev.bounding_box:
                    loc += f" (Bounding Box: {ev.bounding_box})"
                md.append(f"  - `{ev.document_type}`: \"{ev.raw_snippet}\" [{loc}]")

        md.append(f"- **Actionable Remediation Guidance:**  \n  👉 **{f.remediation}**\n")

    md.append("---")
    md.append("### Legal Notice & System Boundaries")
    md.append(
        "> **Note:** DocuReady is a pre-submission demographic consistency and document readiness linter. "
        "It does NOT claim Aadhaar biometrics authenticity, bank balance verification, or official government sanction. "
        "Final eligibility and benefit disbursement remain strictly under the jurisdiction of official scheme authorities."
    )

    return "\n".join(md)
