"""
Streamlit Applicant-Facing Application for DocuReady
Local-first, deterministic pre-submission document readiness linter for citizen welfare schemes.

Screens:
1. Dashboard: Overall packet readiness score, determination, and summary metrics.
2. Upload Documents: Ingest synthetic demonstration test cases or local test PDFs with temporary-only processing.
3. Document Extraction & Evidence: Inspect extracted fields with page and bounding box provenance.
4. Cross-Document Validation: Bipartite comparison matrix across identity, income, and academic records.
5. Audit Results: Explainable rule findings, evidence citations, and privacy-redacted report export.
6. Document Replacement & Rerun: In-memory document remediation and instantaneous re-audit.
"""

import os
import json
import html
import shutil
import tempfile
from pathlib import Path
import streamlit as st

from docuready.domain.models import (
    DocumentType, DOC_TYPE_LABELS, FindingStatus, Severity
)
from docuready.pipeline import AuditPipeline
from docuready.generator import generate_marksheet, generate_income_certificate
from docuready.report.exporter import (
    export_audit_report_json,
    generate_readiness_summary_markdown,
    redact_audit_result_dict
)


def _find_synthetic_data_dir() -> Path:
    """Locates synthetic_data directory independently of working directory."""
    candidates = [
        Path.cwd() / "synthetic_data",
        Path(__file__).resolve().parents[4] / "synthetic_data",
    ]
    for cand in candidates:
        if cand.is_dir():
            return cand
    return Path.cwd() / "synthetic_data"


_SYNTHETIC_DIR = _find_synthetic_data_dir()


st.set_page_config(
    page_title="DocuReady — Pre-Submission Document Readiness Linter",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for clean governmental/civic-tech styling (fixed, trusted markup only)
st.markdown("""
<style>
    .main-header {
        font-size: 2.0rem;
        font-weight: 700;
        color: #1A365D;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4A5568;
        margin-bottom: 1.2rem;
    }
    .status-badge-ready {
        background-color: #C6F6D5;
        color: #22543D;
        padding: 5px 12px;
        border-radius: 6px;
        font-weight: 700;
        display: inline-block;
    }
    .status-badge-review {
        background-color: #FEFCBF;
        color: #744210;
        padding: 5px 12px;
        border-radius: 6px;
        font-weight: 700;
        display: inline-block;
    }
    .status-badge-action {
        background-color: #FEEBC8;
        color: #7B341E;
        padding: 5px 12px;
        border-radius: 6px;
        font-weight: 700;
        display: inline-block;
    }
    .status-badge-reject {
        background-color: #FED7D7;
        color: #742A2A;
        padding: 5px 12px;
        border-radius: 6px;
        font-weight: 700;
        display: inline-block;
    }
    .finding-card {
        background-color: #F7FAFC;
        border-left: 5px solid #3182CE;
        padding: 14px 18px;
        border-radius: 4px;
        margin-bottom: 14px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .finding-card-fail {
        border-left-color: #E53E3E;
        background-color: #FFF5F5;
    }
    .finding-card-review {
        border-left-color: #D69E2E;
        background-color: #FFFFF0;
    }
    .finding-card-pass {
        border-left-color: #38A169;
        background-color: #F0FFF4;
    }
    .disclaimer-banner {
        background-color: #EBF8FF;
        border: 1px solid #BEE3F8;
        border-radius: 6px;
        padding: 10px 14px;
        margin-bottom: 16px;
        color: #2B6CB0;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)


# Initialize Session State
if "pipeline" not in st.session_state:
    st.session_state.pipeline = AuditPipeline()
if "current_packet_id" not in st.session_state:
    st.session_state.current_packet_id = "PKT_01_CLEAN"
if "audit_result" not in st.session_state or "extracted_docs" not in st.session_state:
    default_dir = _SYNTHETIC_DIR / "pkt_01_clean"
    if default_dir.is_dir():
        res, docs = st.session_state.pipeline.load_and_audit_packet(
            str(default_dir),
            packet_id=st.session_state.current_packet_id
        )
        st.session_state.audit_result = res
        st.session_state.extracted_docs = docs
    else:
        st.session_state.audit_result = None
        st.session_state.extracted_docs = {}


# Navigation Sidebar (No external image requests)
with st.sidebar:
    st.markdown("## 🛡️ DocuReady")
    st.caption("Check your documents before you submit.")
    st.markdown("---")

    screen = st.radio(
        "Navigation",
        [
            "1. Dashboard",
            "2. Upload Documents",
            "3. Document Extraction & Evidence",
            "4. Cross-Document Validation",
            "5. Audit Results",
            "6. Document Replacement & Rerun"
        ],
        index=0
    )

    st.markdown("---")
    st.caption("⚙️ **Current Welfare Scheme:**")
    st.info(
        "**Post-Matric Scholarship (SC/ST/OBC)**\n"
        "- State: Odisha\n"
        "- Income Ceiling: ₹ 2,50,000\n"
        "- Min Academic Cutoff: 50.0%\n"
        "- Cert Validity: 3 Years"
    )

    st.markdown("---")
    st.caption("🔒 **Session Privacy Controls:**")
    if st.button("🧹 Clear Session Data", use_container_width=True):
        st.session_state.audit_result = None
        st.session_state.extracted_docs = {}
        st.session_state.current_packet_id = "CLEARED"
        st.success("Session data cleared from memory.")
        st.rerun()

    st.markdown("---")
    st.caption(
        "⚖️ **Prototype Notice:** DocuReady is an offline pre-submission demographic consistency checker. "
        "It is NOT an official government portal or Aadhaar authentication service. Use with synthetic documents only."
    )


# Prominent Prototype Limitation Notice
st.markdown("""
<div class='disclaimer-banner'>
    <b>PROTOTYPE DEMONSTRATION NOTICE:</b> DocuReady runs client-side to detect cross-document discrepancies before portal submission.
    A successful check does NOT guarantee scheme eligibility or benefit disbursement.
    This prototype processes files locally in temporary directories; real citizen documents should not be used without isolated sandboxing.
</div>
""", unsafe_allow_html=True)


# ==============================================================================
# SCREEN 1: DASHBOARD
# ==============================================================================
if screen == "1. Dashboard":
    st.markdown("<div class='main-header'>DocuReady — Pre-Submission Document Linter</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Eliminating administrative rejections for citizen welfare schemes via deterministic cross-document verification.</div>", unsafe_allow_html=True)

    if not st.session_state.audit_result:
        st.warning("No application packet is currently loaded. Please go to **Screen 2 (Upload Documents)** to select or upload a packet.")
    else:
        res = st.session_state.audit_result

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Scheme Checked", "Post-Matric (SC/ST/OBC)")
        with col2:
            st.metric("Mandatory Documents", "6 Types")
        with col3:
            st.metric("Active Statutory Rules", "11 Deterministic")
        with col4:
            st.metric("Audit Latency", f"{res.execution_time_ms:.1f} ms")

        st.markdown("---")
        st.subheader("Current Loaded Packet Status")

        c_score, c_status, c_counts = st.columns([1, 1.5, 2])
        with c_score:
            st.metric("Readiness Score", f"{res.readiness_score} / 100")
            st.progress(res.readiness_score / 100.0)

        with c_status:
            st.write("**Pre-Check Determination:**")
            if res.overall_status == "READY_TO_SUBMIT":
                st.markdown("<span class='status-badge-ready'>🟢 READY TO SUBMIT</span>", unsafe_allow_html=True)
                st.write("Packet passed all deterministic cross-document consistency checks.")
            elif res.overall_status == "REVIEW_RECOMMENDED":
                st.markdown("<span class='status-badge-review'>🟡 REVIEW RECOMMENDED</span>", unsafe_allow_html=True)
                st.write("Minor variations detected (e.g. initials or ambiguous date format). Human review suggested.")
            elif res.overall_status == "ACTION_REQUIRED":
                st.markdown("<span class='status-badge-action'>🟠 ACTION REQUIRED</span>", unsafe_allow_html=True)
                st.write("Defects detected (DOB mismatch or expired certificate). Submission halted.")
            elif res.overall_status == "REJECT_PRECHECK":
                st.markdown("<span class='status-badge-reject'>🔴 REJECT AT PRE-CHECK</span>", unsafe_allow_html=True)
                st.write("Fatal barrier detected (income ceiling breach or missing mandatory certificate).")
            else:
                st.markdown("<span class='status-badge-reject'>⚪ UNREADABLE DOCUMENT</span>", unsafe_allow_html=True)
                st.write("Scan quality is insufficient for statutory verification.")

        with c_counts:
            st.write("**Rule Results Breakdown:**")
            st.write(f"- ✅ **Passed Checks:** {res.summary_counts.get('PASS', 0)}")
            st.write(f"- ⚠️ **Human Review Items:** {res.summary_counts.get('REVIEW', 0)}")
            st.write(f"- ❌ **Failed Violations:** {res.summary_counts.get('FAIL', 0)}")
            st.write(f"- ❓ **Unreadable / Missing Evidence:** {res.summary_counts.get('UNKNOWN', 0)}")

        st.markdown("---")
        st.subheader("Quick Navigation & Workflow")
        qw1, qw2, qw3 = st.columns(3)
        with qw1:
            st.info("**Step 1: Upload / Select Packet**\nChoose a synthetic test case or upload test PDFs in Screen 2.")
        with qw2:
            st.info("**Step 2: Inspect Extractions & Matrix**\nVerify bounding boxes and relational graph in Screens 3 & 4.")
        with qw3:
            st.info("**Step 3: Remediate & Re-audit**\nReplace defective documents with instant verification in Screen 6.")


# ==============================================================================
# SCREEN 2: UPLOAD DOCUMENTS
# ==============================================================================
elif screen == "2. Upload Documents":
    st.markdown("<div class='main-header'>Upload & Document Ingestion</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Select one of the 8 synthetic demonstration test cases or upload test document PDFs.</div>", unsafe_allow_html=True)

    manifest_path = _SYNTHETIC_DIR / "ground_truth_manifest.json"
    manifest = {}
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

    packets_dict = manifest.get("packets", {})
    packet_options = list(packets_dict.keys())

    st.subheader("1. Load Demonstration Test Packet")
    selected_pid = st.selectbox(
        "Choose Synthetic Test Case:",
        packet_options,
        index=packet_options.index(st.session_state.current_packet_id) if st.session_state.current_packet_id in packet_options else 0
    )

    if st.button("📥 Load & Audit Selected Packet", type="primary"):
        target_folder = packets_dict[selected_pid]["folder"]
        full_path = str(_SYNTHETIC_DIR / target_folder)
        res, docs = st.session_state.pipeline.load_and_audit_packet(full_path, packet_id=selected_pid)
        st.session_state.audit_result = res
        st.session_state.extracted_docs = docs
        st.session_state.current_packet_id = selected_pid
        st.success(f"Loaded and audited '{selected_pid}' successfully in {res.execution_time_ms:.1f} ms!")
        st.rerun()

    if selected_pid in packets_dict:
        meta = packets_dict[selected_pid]
        st.caption(f"**Test Case Description:** {meta['description']}")
        st.caption(f"**Expected Status:** `{meta['expected_status']}` | **Expected Defects:** `{meta['expected_defects_count']}`")

    st.markdown("---")
    st.subheader("2. Upload Custom Document Files (Temporary Processing)")
    st.caption("Uploads are processed strictly inside an isolated temporary directory and deleted immediately after audit.")

    uploaded_files = st.file_uploader(
        "Upload Application Packet (PDF format for all required documents):",
        type=["pdf"],
        accept_multiple_files=True
    )

    if uploaded_files:
        if st.button("🔒 Process & Audit Uploaded Files", type="primary"):
            max_size_bytes = 10 * 1024 * 1024  # 10 MB per file limit
            oversized_files = []
            valid_uploads = []

            for uf in uploaded_files:
                if uf.size > max_size_bytes:
                    oversized_files.append(uf.name)
                else:
                    valid_uploads.append(uf)

            if oversized_files:
                st.error(f"Files exceeded 10MB limit and were rejected: {', '.join(oversized_files)}")

            if valid_uploads:
                temp_dir = tempfile.mkdtemp(prefix="docuready_upload_")
                try:
                    for uf in valid_uploads:
                        safe_name = Path(uf.name).name.replace("..", "").replace("/", "").replace("\\", "")
                        if not safe_name.lower().endswith(".pdf"):
                            safe_name += ".pdf"
                        dest = os.path.join(temp_dir, safe_name)
                        with open(dest, "wb") as f:
                            f.write(uf.read())

                    res, docs = st.session_state.pipeline.load_and_audit_packet(temp_dir, packet_id="CUSTOM_UPLOAD")
                    # Sanitize file paths so temporary filesystem paths are not retained in memory
                    for d in docs.values():
                        d.file_path = os.path.basename(d.file_path)

                    st.session_state.audit_result = res
                    st.session_state.extracted_docs = docs
                    st.session_state.current_packet_id = "CUSTOM_UPLOAD"
                    st.success("Uploaded packet audited successfully! Temporary files removed from disk.")
                    st.rerun()
                finally:
                    # Guaranteed cleanup of all uploaded bytes from disk
                    shutil.rmtree(temp_dir, ignore_errors=True)

    st.markdown("---")
    st.subheader("Current Packet Documents Ingested")
    docs = st.session_state.extracted_docs
    if not docs:
        st.info("No documents currently ingested.")
    else:
        cols = st.columns(3)
        idx = 0
        for dt, d in docs.items():
            with cols[idx % 3]:
                st.markdown(f"**{DOC_TYPE_LABELS.get(dt, dt.value)}**")
                st.write(f"- File: `{os.path.basename(d.file_path)}`")
                st.write(f"- Status: `{d.status}` ({len(d.fields)} extracted fields)")
                idx += 1


# ==============================================================================
# SCREEN 3: DOCUMENT EXTRACTION & EVIDENCE REVIEW
# ==============================================================================
elif screen == "3. Document Extraction & Evidence":
    st.markdown("<div class='main-header'>Document Extraction & Evidence Review</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Inspect fields extracted from PDFs with exact page-level and bounding-box provenance.</div>", unsafe_allow_html=True)

    docs = st.session_state.extracted_docs
    if not docs:
        st.warning("No documents loaded. Please select or upload a packet in Screen 2.")
    else:
        for dt, doc in docs.items():
            label = DOC_TYPE_LABELS.get(dt, dt.value)
            status_emoji = "✅" if doc.status == "VALID" else ("⚠️" if doc.status == "UNREADABLE" else "❌")
            with st.expander(f"{status_emoji} {label} ({doc.status}) — {os.path.basename(doc.file_path)}", expanded=(dt in [DocumentType.INCOME_CERT, DocumentType.MARKSHEET])):
                if doc.status == "UNREADABLE":
                    st.error("Document is flagged as UNREADABLE or Corrupted scan. Text evidence could not be cleanly parsed.")
                elif doc.status == "MISSING":
                    st.error("This mandatory document is MISSING from the application packet.")
                else:
                    st.write(f"**Source Document:** `{os.path.basename(doc.file_path)}` | **Pages:** {doc.page_count}")
                    st.write("**Extracted Fields Table:**")
                    field_data = []
                    for fname, fld in doc.fields.items():
                        state_val = fld.evidence_state.value if hasattr(fld, 'evidence_state') and fld.evidence_state else "VERIFIED"
                        cal_conf = f"{fld.calibrated_confidence * 100:.1f}%" if hasattr(fld, 'calibrated_confidence') and fld.calibrated_confidence else f"{fld.confidence * 100:.0f}%"
                        field_data.append({
                            "Field Name": fname,
                            "Raw Extracted Value": str(fld.raw_value),
                            "Normalized Value": str(fld.normalized_value),
                            "Evidence State": state_val,
                            "Heuristic Confidence": cal_conf,
                            "Syntax Valid": "PASS" if getattr(fld, 'format_valid', True) else "SYNTAX_ERR",
                            "Page #": fld.provenance.page_number if fld.provenance else 1
                        })
                    st.table(field_data)

                    st.markdown("**Extracted Provenance Snippets:**")
                    snippets = [f"• `{f.field_name}`: \"{f.provenance.raw_snippet}\"" for f in doc.fields.values() if f.provenance and f.provenance.raw_snippet]
                    st.code("\n".join(snippets) if snippets else "No snippets available.")


# ==============================================================================
# SCREEN 4: CROSS-DOCUMENT VALIDATION MATRIX
# ==============================================================================
elif screen == "4. Cross-Document Validation":
    st.markdown("<div class='main-header'>Cross-Document Consistency Matrix</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Relational comparison showing cross-document equivalence and discrepancy edges.</div>", unsafe_allow_html=True)

    docs = st.session_state.extracted_docs
    if not docs:
        st.warning("No documents loaded. Please select or upload a packet in Screen 2.")
    else:
        def get_val(dt: DocumentType, fn: str):
            d = docs.get(dt)
            if d and d.status == "VALID":
                f = d.fields.get(fn)
                return str(f.raw_value) if f and f.raw_value is not None else "MISSING"
            return "N/A"

        st.subheader("1. Applicant Name Cross-Comparison")
        name_rows = []
        for dt in [
            DocumentType.APPLICATION_FORM, DocumentType.INCOME_CERT,
            DocumentType.CASTE_CERT, DocumentType.RESIDENCE_CERT,
            DocumentType.MARKSHEET, DocumentType.BANK_PASSBOOK
        ]:
            name_rows.append({
                "Document": DOC_TYPE_LABELS.get(dt, dt.value),
                "Extracted Name": get_val(dt, "applicant_name"),
                "Presence": "Uploaded" if dt in docs and docs[dt].status == "VALID" else "Missing / Incomplete"
            })
        st.table(name_rows)

        st.subheader("2. Date of Birth Cross-Comparison")
        c1, c2 = st.columns(2)
        with c1:
            st.info(f"**Application Form Declared DOB:**\n### {get_val(DocumentType.APPLICATION_FORM, 'dob')}")
        with c2:
            st.info(f"**Marksheet Certified DOB:**\n### {get_val(DocumentType.MARKSHEET, 'dob')}")

        st.subheader("3. Annual Income Cross-Comparison & Statutory Ceiling")
        i1, i2, i3 = st.columns(3)
        with i1:
            st.write("**Application Form Declared:**")
            st.code(get_val(DocumentType.APPLICATION_FORM, "annual_income"))
        with i2:
            st.write("**Income Certificate Certified:**")
            st.code(get_val(DocumentType.INCOME_CERT, "annual_income"))
        with i3:
            st.write("**Statutory Scheme Ceiling:**")
            st.code("₹ 2,50,000 / year")

        st.subheader("4. Bank Account & IFSC Consistency")
        b1, b2 = st.columns(2)
        with b1:
            st.write("**Application Form Account & IFSC:**")
            st.code(f"A/C: {get_val(DocumentType.APPLICATION_FORM, 'account_no')} | IFSC: {get_val(DocumentType.APPLICATION_FORM, 'ifsc')}")
        with b2:
            st.write("**Passbook Account & IFSC:**")
            st.code(f"A/C: {get_val(DocumentType.BANK_PASSBOOK, 'account_no')} | IFSC: {get_val(DocumentType.BANK_PASSBOOK, 'ifsc')}")


# ==============================================================================
# SCREEN 5: AUDIT RESULTS
# ==============================================================================
elif screen == "5. Audit Results":
    st.markdown("<div class='main-header'>Pre-Submission Audit Results</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Deterministic finding classifications with evidence citations and statutory remediation guidance.</div>", unsafe_allow_html=True)

    if not st.session_state.audit_result:
        st.warning("No audit results to display. Please load or audit a packet in Screen 2.")
    else:
        res = st.session_state.audit_result

        # Score Banner
        m1, m2, m3, m4 = st.columns([1.5, 1, 1, 1])
        with m1:
            st.metric("Readiness Score", f"{res.readiness_score} / 100")
            st.progress(res.readiness_score / 100.0)
        with m2:
            st.metric("Passed Checks", res.summary_counts.get("PASS", 0))
        with m3:
            st.metric("Review Items", res.summary_counts.get("REVIEW", 0))
        with m4:
            st.metric("Failed Violations", res.summary_counts.get("FAIL", 0))

        st.markdown("---")
        st.subheader("Audit Findings & Evidence Citations")

        for idx, f in enumerate(res.findings, 1):
            card_class = "finding-card"
            if f.status == FindingStatus.FAIL:
                card_class += " finding-card-fail"
                badge = "<span class='status-badge-reject'>FAIL</span>"
            elif f.status == FindingStatus.REVIEW:
                card_class += " finding-card-review"
                badge = "<span class='status-badge-review'>REVIEW</span>"
            elif f.status == FindingStatus.UNKNOWN:
                card_class += " finding-card-reject"
                badge = "<span class='status-badge-reject'>UNKNOWN</span>"
            else:
                card_class += " finding-card-pass"
                badge = "<span class='status-badge-ready'>PASS</span>"

            penalty_txt = f"<span style='color:#E53E3E; font-weight:bold;'>(-{f.penalty} pts)</span>" if f.penalty > 0 else "<span style='color:#38A169;'>(0 pts)</span>"

            # Safely escape dynamic content to prevent XSS / markup injection
            safe_rule_name = html.escape(str(f.rule_name))
            safe_rule_id = html.escape(str(f.rule_id))
            safe_severity = html.escape(str(f.severity.value))
            safe_docs = html.escape(', '.join(f.documents_involved))
            safe_message = html.escape(str(f.message))
            safe_statutory = html.escape(str(f.statutory_reference))

            st.markdown(f"""
            <div class='{card_class}'>
                <div style='display:flex; justify-content:space-between; align-items:center;'>
                    <h4>{idx}. {safe_rule_name} {penalty_txt}</h4>
                    <div>{badge}</div>
                </div>
                <p><b>Statutory Rule:</b> <code>{safe_rule_id}</code> | <b>Severity:</b> {safe_severity} | <b>Documents:</b> {safe_docs}</p>
                <p><b>Description:</b> {safe_message}</p>
                <p><b>Legal Reference:</b> <i>{safe_statutory}</i></p>
            </div>
            """, unsafe_allow_html=True)

            if f.evidence:
                with st.expander(f"🔍 View Original Evidence for Finding #{idx}", expanded=(f.status != FindingStatus.PASS)):
                    for ev in f.evidence:
                        bbox_str = f", BBox: {ev.bounding_box}" if ev.bounding_box else ""
                        st.info(f"**Document:** `{ev.document_type}` (Page {ev.page_number}{bbox_str})\n\n**Extracted Snippet:** \"{html.escape(str(ev.raw_snippet))}\"")

            if f.status in [FindingStatus.FAIL, FindingStatus.REVIEW, FindingStatus.UNKNOWN]:
                st.warning(f"👉 **Correction Guidance:** {f.remediation}")

            st.write("")

        st.markdown("---")
        st.subheader("Export Audit Report")
        st.caption("Reports are exported in privacy-redacted mode by default (raw extracted snippets and direct citizen PII masked).")

        exp_c1, exp_c2 = st.columns(2)
        with exp_c1:
            redacted_dict = redact_audit_result_dict(res.model_dump())
            json_data = json.dumps(redacted_dict, indent=2)
            st.download_button(
                label="💾 Download Redacted Report (JSON)",
                data=json_data,
                file_name=f"docuready_audit_{res.packet_id}_redacted.json",
                mime="application/json"
            )

        with exp_c2:
            md_report = generate_readiness_summary_markdown(res, redact=True)
            st.download_button(
                label="📄 Download Redacted Summary (Markdown)",
                data=md_report,
                file_name=f"readiness_summary_{res.packet_id}_redacted.md",
                mime="text/markdown"
            )


# ==============================================================================
# SCREEN 6: DOCUMENT REPLACEMENT AND RERUN
# ==============================================================================
elif screen == "6. Document Replacement & Rerun":
    st.markdown("<div class='main-header'>Document Replacement & Instant Re-Audit</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Remediate flawed or conflicting documents in-memory and verify readiness instantaneously.</div>", unsafe_allow_html=True)

    if not st.session_state.audit_result or not st.session_state.extracted_docs:
        st.warning("No active audit packet loaded. Please load or audit a packet in Screen 2.")
    else:
        current_res = st.session_state.audit_result
        st.info(f"**Active Packet:** `{current_res.packet_id}` | **Current Score:** {current_res.readiness_score}/100 | **Status:** `{current_res.overall_status}`")

        st.subheader("1. Select Document to Replace")
        doc_types = list(st.session_state.extracted_docs.keys())
        selected_doc_type = st.selectbox(
            "Choose document to remediate:",
            doc_types,
            format_func=lambda x: f"{DOC_TYPE_LABELS.get(x, x.value)} ({x.value})"
        )

        st.subheader("2. Provide Remediated Document")
        method = st.radio("Remediation Source:", ["Auto-Generate Standard Corrected Version", "Upload Corrected PDF File"])

        if method == "Auto-Generate Standard Corrected Version":
            st.write("Generates a corrected, consistent synthetic PDF matching the applicant's master record.")
            if st.button("Generate & Re-Run Audit", type="primary"):
                temp_dir = tempfile.mkdtemp(prefix="docuready_remed_")
                try:
                    if selected_doc_type == DocumentType.MARKSHEET:
                        replacement_path = os.path.join(temp_dir, "corrected_marksheet.pdf")
                        generate_marksheet(
                            replacement_path,
                            applicant_name="Smruti Ranjan Nayak",
                            father_name="Ramesh Chandra Nayak",
                            dob="14/05/2003",
                            roll_no="2309BA1042",
                            percentage=78.5
                        )
                    elif selected_doc_type == DocumentType.INCOME_CERT:
                        replacement_path = os.path.join(temp_dir, "corrected_income_cert.pdf")
                        generate_income_certificate(
                            replacement_path,
                            applicant_name="Smruti Ranjan Nayak",
                            father_name="Ramesh Chandra Nayak",
                            annual_income="Rs. 1,80,000/-",
                            issue_date="10/01/2025",
                            certificate_no="E-INC/2025/104928"
                        )
                    else:
                        clean_doc_path = _SYNTHETIC_DIR / "pkt_01_clean" / f"{selected_doc_type.value.lower()}.pdf"
                        replacement_path = os.path.join(temp_dir, clean_doc_path.name)
                        shutil.copyfile(str(clean_doc_path), replacement_path)

                    new_res, new_docs = st.session_state.pipeline.replace_document_and_reaudit(
                        st.session_state.extracted_docs,
                        replacement_path,
                        selected_doc_type,
                        packet_id=f"{current_res.packet_id}_REMEDIATED"
                    )

                    # Sanitize paths in memory
                    for d in new_docs.values():
                        d.file_path = os.path.basename(d.file_path)

                    st.session_state.audit_result = new_res
                    st.session_state.extracted_docs = new_docs
                    st.session_state.current_packet_id = f"{current_res.packet_id}_REMEDIATED"
                    st.success(f"Re-audit completed in {new_res.execution_time_ms:.1f} ms! Temporary files purged.")
                    st.rerun()
                finally:
                    shutil.rmtree(temp_dir, ignore_errors=True)

        else:
            new_file = st.file_uploader("Upload replacement PDF:", type=["pdf"])
            if new_file and st.button("Apply Replacement & Re-audit", type="primary"):
                temp_dir = tempfile.mkdtemp(prefix="docuready_remed_")
                try:
                    safe_name = Path(new_file.name).name.replace("..", "").replace("/", "").replace("\\", "")
                    if not safe_name.lower().endswith(".pdf"):
                        safe_name += ".pdf"
                    replacement_path = os.path.join(temp_dir, safe_name)
                    with open(replacement_path, "wb") as f:
                        f.write(new_file.read())

                    new_res, new_docs = st.session_state.pipeline.replace_document_and_reaudit(
                        st.session_state.extracted_docs,
                        replacement_path,
                        selected_doc_type,
                        packet_id=f"{current_res.packet_id}_REMEDIATED"
                    )

                    # Sanitize paths in memory
                    for d in new_docs.values():
                        d.file_path = os.path.basename(d.file_path)

                    st.session_state.audit_result = new_res
                    st.session_state.extracted_docs = new_docs
                    st.session_state.current_packet_id = f"{current_res.packet_id}_REMEDIATED"
                    st.success(f"Re-audit completed in {new_res.execution_time_ms:.1f} ms! Temporary files purged.")
                    st.rerun()
                finally:
                    shutil.rmtree(temp_dir, ignore_errors=True)
