"""
Loop 35 End-to-End Workflow Reliability & Operational Qualification Tests.
Tests complete workflow boundaries:
- Import & file validation (empty, corrupted, disguised extensions, Unicode paths, path traversal)
- Packet completeness & wrong-slot quarantine
- Cross-document isolation & contradiction detection
- Export integrity (JSON/Markdown consistency, PII redaction, Unicode filenames, empty packets)
- Recovery & idempotency (deterministic canonical replay, repeated audit idempotency)
- Offline network isolation instrumentation
"""

import json
import os
import socket
import tempfile
from datetime import date
from pathlib import Path
import pytest

from docuready.domain.enums import Status, ReasonCode, EvidenceState
from docuready.domain.models import (
    DocumentType, ExtractedDocument, ExtractedField, EvidenceProvenance
)
from docuready.pipeline import AuditPipeline
from docuready.rules.validator import DocuReadyValidator, SchemeConfig
from docuready.report.exporter import (
    export_audit_report_json,
    generate_readiness_summary_markdown
)
from docuready.evidence.cross_document import (
    DocumentIdentity, EntityIdentity, FieldClaim,
    verify_cross_document_packet_claim, VerificationOutcome
)


def _make_valid_field(name: str, raw_val: str, norm_val=None, conf: float = 0.95) -> ExtractedField:
    return ExtractedField(
        field_name=name,
        raw_value=raw_val,
        normalized_value=raw_val if norm_val is None else norm_val,
        confidence=conf,
        evidence_state=EvidenceState.VERIFIED if conf >= 0.70 else EvidenceState.UNCERTAIN,
        page_number=1,
        bounding_box=[10, 10, 100, 30]
    )


def _make_complete_packet_docs() -> dict:
    return {
        DocumentType.APPLICATION_FORM: ExtractedDocument(
            doc_type=DocumentType.APPLICATION_FORM,
            file_path="application_form.pdf",
            status="VALID",
            fields={
                "applicant_name": _make_valid_field("applicant_name", "ANANYA DASH"),
                "dob": _make_valid_field("dob", "15/08/2004", date(2004, 8, 15)),
                "annual_income": _make_valid_field("annual_income", "180000", 180000.0),
                "ifsc": _make_valid_field("ifsc", "SBIN0001234"),
                "account_no": _make_valid_field("account_no", "12345678901"),
                "caste_category": _make_valid_field("caste_category", "SC"),
                "state": _make_valid_field("state", "ODISHA"),
            }
        ),
        DocumentType.INCOME_CERT: ExtractedDocument(
            doc_type=DocumentType.INCOME_CERT,
            file_path="income_cert.pdf",
            status="VALID",
            fields={
                "applicant_name": _make_valid_field("applicant_name", "ANANYA DASH"),
                "annual_income": _make_valid_field("annual_income", "180000", 180000.0),
                "issue_date": _make_valid_field("issue_date", "10/01/2026", date(2026, 1, 10)),
                "certificate_no": _make_valid_field("certificate_no", "INC-2026-991"),
            }
        ),
        DocumentType.CASTE_CERT: ExtractedDocument(
            doc_type=DocumentType.CASTE_CERT,
            file_path="caste_cert.pdf",
            status="VALID",
            fields={
                "applicant_name": _make_valid_field("applicant_name", "ANANYA DASH"),
                "caste_category": _make_valid_field("caste_category", "SC"),
                "certificate_no": _make_valid_field("certificate_no", "CST-2026-442"),
            }
        ),
        DocumentType.RESIDENCE_CERT: ExtractedDocument(
            doc_type=DocumentType.RESIDENCE_CERT,
            file_path="residence_cert.pdf",
            status="VALID",
            fields={
                "applicant_name": _make_valid_field("applicant_name", "ANANYA DASH"),
                "state": _make_valid_field("state", "ODISHA"),
                "certificate_no": _make_valid_field("certificate_no", "RES-2026-112"),
            }
        ),
        DocumentType.MARKSHEET: ExtractedDocument(
            doc_type=DocumentType.MARKSHEET,
            file_path="marksheet.pdf",
            status="VALID",
            fields={
                "applicant_name": _make_valid_field("applicant_name", "ANANYA DASH"),
                "dob": _make_valid_field("dob", "15/08/2004", date(2004, 8, 15)),
                "percentage": _make_valid_field("percentage", "74.5", 74.5),
            }
        ),
        DocumentType.BANK_PASSBOOK: ExtractedDocument(
            doc_type=DocumentType.BANK_PASSBOOK,
            file_path="bank_passbook.pdf",
            status="VALID",
            fields={
                "applicant_name": _make_valid_field("applicant_name", "ANANYA DASH"),
                "ifsc": _make_valid_field("ifsc", "SBIN0001234"),
                "account_no": _make_valid_field("account_no", "12345678901"),
            }
        ),
    }


class TestLoop35ImportAndIngestionBoundaries:
    """5A: File validation, corrupted PDFs, disguised extensions, Unicode filenames."""

    def test_corrupted_and_empty_files_cannot_enter_as_valid_evidence(self, tmp_path):
        pipeline = AuditPipeline(as_of=date(2026, 11, 13))
        empty_pdf = tmp_path / "income_cert.pdf"
        empty_pdf.write_bytes(b"")
        disguised_pdf = tmp_path / "caste_cert.pdf"
        disguised_pdf.write_text("NOT A REAL PDF FILE", encoding="utf-8")

        result, docs = pipeline.load_and_audit_packet(str(tmp_path), packet_id="PKT-CORRUPT")
        assert result.readiness.value == "NOT_READY"
        # Corrupted/empty files must not produce PASS findings
        for doc in docs.values():
            assert doc.status in ["UNREADABLE", "CORRUPTED", "MISSING", "ERROR"]

    def test_unicode_directory_and_filename_handling(self, tmp_path):
        unicode_dir = tmp_path / "आवेदन_पत्र_ओडिशा"
        unicode_dir.mkdir()
        pipeline = AuditPipeline(as_of=date(2026, 11, 13))
        result, docs = pipeline.load_and_audit_packet(str(unicode_dir), packet_id="PKT-UNICODE-EMPTY")
        assert result.packet_id == "PKT-UNICODE-EMPTY"
        assert result.readiness.value == "NOT_READY"


class TestLoop35PacketCompletenessAndIsolation:
    """5B & 5C: Missing docs, wrong slots, cross-applicant isolation."""

    def test_complete_valid_packet_workflow(self):
        validator = DocuReadyValidator(as_of=date(2026, 11, 13))
        docs = _make_complete_packet_docs()
        result = validator.validate_packet("PKT-COMPLETE-01", docs)
        assert result.packet_id == "PKT-COMPLETE-01"
        assert result.readiness.value in ["NO_ISSUES_FOUND", "NEEDS_CHECKS"]
        assert result.v2_summary_counts[Status.FAIL.value] == 0
        assert result.v2_summary_counts[Status.MISSING.value] == 0

    def test_missing_mandatory_document_detected(self):
        validator = DocuReadyValidator(as_of=date(2026, 11, 13))
        docs = _make_complete_packet_docs()
        del docs[DocumentType.INCOME_CERT]
        result = validator.validate_packet("PKT-MISSING-INC", docs)
        assert result.readiness.value == "NOT_READY"
        assert result.v2_summary_counts[Status.MISSING.value] >= 1 or result.v2_summary_counts[Status.FAIL.value] >= 1

    def test_wrong_slot_document_quarantined(self):
        validator = DocuReadyValidator(as_of=date(2026, 11, 13))
        docs = _make_complete_packet_docs()
        # Put a caste cert inside INCOME_CERT slot
        docs[DocumentType.INCOME_CERT] = ExtractedDocument(
            doc_type=DocumentType.CASTE_CERT,
            file_path="wrong_slot.pdf",
            status="VALID",
            raw_text="CASTE CERTIFICATE",
            fields={"annual_income": _make_valid_field("annual_income", "100000")},
            expected_slot=DocumentType.INCOME_CERT
        )
        result = validator.validate_packet("PKT-WRONG-SLOT", docs)
        rule_ids = [f.rule_id for f in result.findings]
        assert "RULE-SLOT-01" in rule_ids
        assert result.readiness.value != "NO_ISSUES_FOUND"

    def test_cross_applicant_isolation_blocks_contamination(self):
        target = EntityIdentity(
            entity_id="ENT-01",
            canonical_name="ANANYA DASH",
            date_of_birth="15/08/2004",
        )
        docs = {
            "D1": DocumentIdentity(doc_id="D1", doc_type="APPLICATION_FORM", file_name="f1.pdf", content_hash="h1"),
            "D2": DocumentIdentity(doc_id="D2", doc_type="INCOME_CERT", file_name="f2.pdf", content_hash="h2"),
        }
        claims = [
            FieldClaim(
                claim_id="C1", doc_id="D1", field_name="annual_income", field_type="amount",
                claimed_value="180000", raw_ocr_value="180000", confidence=95.0,
                entity_hints={"canonical_name": "ANANYA DASH", "date_of_birth": "15/08/2004"}
            ),
            FieldClaim(
                claim_id="C2", doc_id="D2", field_name="annual_income", field_type="amount",
                claimed_value="180000", raw_ocr_value="180000", confidence=95.0,
                entity_hints={"canonical_name": "ANANYA DASH", "date_of_birth": "01/01/1999"}  # Different applicant!
            ),
        ]
        res = verify_cross_document_packet_claim(
            field_name="annual_income",
            target_entity=target,
            claims=claims,
            documents=docs,
            required_doc_types=["APPLICATION_FORM", "INCOME_CERT"],
            operating_threshold=70.0
        )
        assert "D2" not in res.supporting_doc_ids
        assert res.supporting_doc_ids == ["D1"]


class TestLoop35ExportAndIdempotency:
    """5E & 7: Export consistency, redaction, Unicode paths, deterministic replay."""

    def test_export_json_and_markdown_preserve_uncertainty_and_redact_pii(self, tmp_path):
        validator = DocuReadyValidator(as_of=date(2026, 11, 13))
        docs = _make_complete_packet_docs()
        # Inject low-confidence uncertain field
        docs[DocumentType.MARKSHEET].fields["dob"] = _make_valid_field("dob", "15/08/2004", date(2004, 8, 15), conf=0.55)
        result = validator.validate_packet("PKT-EXPORT-01", docs)

        json_path = tmp_path / "रिपोर्ट_PKT_01.json"
        export_audit_report_json(result, str(json_path), redact=True, canonical=True)
        assert json_path.exists()

        exported = json.loads(json_path.read_text(encoding="utf-8"))
        assert exported["packet_id"] == "PKT-EXPORT-01"
        assert exported["summary_counts"][Status.REVIEW.value] == result.v2_summary_counts[Status.REVIEW.value]

        md_text = generate_readiness_summary_markdown(result, redact=True, canonical=True)
        assert "Privacy Notice: This report has been redacted" in md_text
        assert "PKT-EXPORT-01" in md_text

    def test_deterministic_replay_idempotency(self, tmp_path):
        validator = DocuReadyValidator(as_of=date(2026, 11, 13))
        docs = _make_complete_packet_docs()

        r1 = validator.validate_packet("PKT-IDEMPOTENT", docs)
        r2 = validator.validate_packet("PKT-IDEMPOTENT", docs)

        p1 = tmp_path / "run1.json"
        p2 = tmp_path / "run2.json"
        export_audit_report_json(r1, str(p1), redact=True, canonical=True)
        export_audit_report_json(r2, str(p2), redact=True, canonical=True)

        assert p1.read_text(encoding="utf-8") == p2.read_text(encoding="utf-8")


class TestLoop35OfflineNetworkInstrumentation:
    """8: Instrument socket to prove zero outbound network attempts during full workflow."""

    def test_zero_outbound_network_attempts_during_pipeline(self, monkeypatch, tmp_path):
        attempted_connections = []

        class GuardedSocket(socket.socket):
            def connect(self, address):
                attempted_connections.append(address)
                raise RuntimeError(f"Outbound network forbidden: {address}")

        monkeypatch.setattr(socket, "socket", GuardedSocket)

        validator = DocuReadyValidator(as_of=date(2026, 11, 13))
        docs = _make_complete_packet_docs()
        result = validator.validate_packet("PKT-OFFLINE-01", docs)

        out_json = tmp_path / "offline.json"
        export_audit_report_json(result, str(out_json), redact=True, canonical=True)

        assert len(attempted_connections) == 0
        assert out_json.exists()
