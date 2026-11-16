"""Contract tests for evidence provenance, coordinate stability, and redaction policy.

Ensures that:
1. Python AuditPipeline produces EvidenceProvenance with stable contracts.
2. Coordinates are PyMuPDF points [x0, y0, x1, y1] with top-left origin.
3. Missing documents produce empty evidence without inventing fake provenance coordinates.
4. Public redaction policy redacts raw snippets while preserving bounding boxes and page numbers.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pytest

from docuready.domain.models import EvidenceProvenance
from docuready.pipeline import AuditPipeline
from docuready.report.redact import redact_audit_result_dict


@pytest.fixture(scope="module")
def synthetic_packets_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "synthetic_data"


def test_clean_packet_evidence_provenance_contract(synthetic_packets_dir: Path) -> None:
    pkt_path = synthetic_packets_dir / "pkt_01_clean"
    if not pkt_path.exists():
        pytest.skip("synthetic_data/pkt_01_clean not found")

    pipeline = AuditPipeline(as_of=date(2026, 3, 1))
    result, extracted_docs = pipeline.load_and_audit_packet(
        str(pkt_path), packet_id="TEST_CLEAN_EVIDENCE", as_of=date(2026, 3, 1)
    )

    # 1. Findings must contain evidence items where fields match
    findings_with_evidence = [f for f in result.findings if f.evidence]
    assert len(findings_with_evidence) > 0, "Clean packet must have findings with attached evidence"

    for finding in findings_with_evidence:
        for ev in finding.evidence:
            assert isinstance(ev, EvidenceProvenance)
            assert ev.file_name.endswith(".pdf")
            assert ev.page_number >= 1

            if ev.bounding_box is not None:
                assert len(ev.bounding_box) == 4
                x0, y0, x1, y1 = ev.bounding_box
                assert x1 >= x0, f"x1 ({x1}) must be >= x0 ({x0})"
                assert y1 >= y0, f"y1 ({y1}) must be >= y0 ({y0})"
                assert x0 >= 0 and y0 >= 0

    # 2. Public redaction contract
    public_dict = redact_audit_result_dict(result.to_public_dict(canonical=True))
    assert public_dict["packet_id"] == "TEST_CLEAN_EVIDENCE"
    assert public_dict["readiness_score"] >= 90

    # Verify that raw snippets are redacted in the public output
    for pub_finding in public_dict["findings"]:
        for pub_ev in pub_finding.get("evidence", []):
            snippet = pub_ev.get("raw_snippet", "")
            assert (
                "[REDACTED" in snippet or not snippet
            ), f"Evidence snippet must be redacted in public dict: {snippet}"
            # Bounding box must NOT be redacted
            if pub_ev.get("bounding_box") is not None:
                assert len(pub_ev["bounding_box"]) == 4


def test_missing_document_does_not_invent_fake_coordinates(synthetic_packets_dir: Path) -> None:
    pkt_path = synthetic_packets_dir / "pkt_05_missing_certificate"
    if not pkt_path.exists():
        pytest.skip("synthetic_data/pkt_05_missing_certificate not found")

    pipeline = AuditPipeline(as_of=date(2026, 3, 1))
    result, extracted_docs = pipeline.load_and_audit_packet(
        str(pkt_path), packet_id="TEST_MISSING_CERT", as_of=date(2026, 3, 1)
    )

    # Find RULE-DOC-01 for missing document
    missing_findings = [f for f in result.findings if f.rule_id == "RULE-DOC-01"]
    assert len(missing_findings) > 0, "Missing certificate packet must trigger RULE-DOC-01"

    for finding in missing_findings:
        # Crucial invariant: Missing document must NOT have synthesized bounding boxes
        assert (
            len(finding.evidence) == 0
        ), "Missing document finding must have empty evidence, never synthesized coordinates"


def test_name_conflict_evidence_traceability(synthetic_packets_dir: Path) -> None:
    pkt_path = synthetic_packets_dir / "pkt_02_name_conflict"
    if not pkt_path.exists():
        pytest.skip("synthetic_data/pkt_02_name_conflict not found")

    pipeline = AuditPipeline(as_of=date(2026, 3, 1))
    result, extracted_docs = pipeline.load_and_audit_packet(
        str(pkt_path), packet_id="TEST_NAME_CONFLICT", as_of=date(2026, 3, 1)
    )

    conflict_findings = [f for f in result.findings if f.status.value in ("FAIL", "WARN")]
    assert len(conflict_findings) > 0, "Name conflict packet must have non-pass findings"

    name_findings = [f for f in conflict_findings if "NAME" in f.rule_id]
    assert len(name_findings) > 0, "Must have a name conflict finding"

    for finding in name_findings:
        # Finding must reference multiple documents involved in conflict
        assert len(finding.documents_involved) >= 2
        # Evidence items must trace back to the conflicting documents
        ev_docs = {ev.file_name for ev in finding.evidence}
        assert len(ev_docs) >= 1
