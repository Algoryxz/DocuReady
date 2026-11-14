"""
Automated tests for document replacement and instant re-audit workflow.
"""

import os
from pathlib import Path
from docuready.domain.models import DocumentType
from docuready.pipeline import AuditPipeline

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SYNTHETIC_DIR = _REPO_ROOT / "synthetic_data" if (_REPO_ROOT / "synthetic_data").is_dir() else Path.cwd() / "synthetic_data"


def get_doc_path(relative_subpath):
    candidates = [
        _SYNTHETIC_DIR / relative_subpath,
        Path.cwd() / "synthetic_data" / relative_subpath,
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    return str(candidates[0])


def test_document_replacement_workflow():
    pipeline = AuditPipeline()

    # Step 1: Ingest defective packet (DOB mismatch)
    packet_dir = get_doc_path("pkt_03_dob_conflict")
    initial_res, initial_docs = pipeline.load_and_audit_packet(
        packet_dir,
        packet_id="PKT_03_DOB_CONFLICT"
    )
    assert initial_res.overall_status in ["ACTION_REQUIRED", "REJECT_PRECHECK"]
    assert initial_res.readiness_score == 75
    assert any(f.rule_id == "RULE-DOB-01" and f.status == "FAIL" for f in initial_res.findings)

    # Step 2: Remediate by replacing marksheet with corrected marksheet
    corrected_marksheet_path = get_doc_path("pkt_01_clean/marksheet.pdf")
    new_res, new_docs = pipeline.replace_document_and_reaudit(
        initial_docs,
        corrected_marksheet_path,
        DocumentType.MARKSHEET,
        packet_id="PKT_03_REMEDIATED"
    )

    # Step 3: Assert clean resolution
    assert new_res.overall_status == "READY_TO_SUBMIT"
    assert new_res.readiness_score == 100
    assert not any(f.status == "FAIL" for f in new_res.findings)
    assert any(f.rule_id == "RULE-DOB-PASS" and f.status == "PASS" for f in new_res.findings)
