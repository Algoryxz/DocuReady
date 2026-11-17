"""Tests for Scheme Pack Execution Engine (Task T3.2).

Validates:
1. Pack lifecycle enforcement (rejecting draft unless allow_draft=True).
2. Parameter resolution ($income_ceiling, $income_tolerance, etc.).
3. Structural missing-document handling across all 6 required slots individually.
4. Unreadable/corrupted document handling.
5. Tri-state category exemption evaluation (verified SC/ST, verified GENERAL, missing/unreadable/uncertain, misleading substrings).
6. Slot mismatch containment (mismatched slots cannot produce downstream PASS).
7. Injected clock conflict detection and unverified source disclosure.
"""

from datetime import date
from pathlib import Path
import pytest

from docuready.domain.enums import MatchGrade, Readiness, ReasonCode, Status
from docuready.domain.models import (
    DocumentType,
    EvidenceProvenance,
    ExtractedDocument,
    ExtractedField,
)
from docuready.rules.engine import PackExecutionEngine
from docuready.rules.loader import PackLoadError, load_pack
from docuready.rules.schema import CitationReference, RemediationMetadata, RuleDefinition

_REPO_ROOT = Path(__file__).resolve().parent.parent


def _make_field(doc_type: str, field_name: str, raw_val: str, norm_val=None, is_uncertain: bool = False):
    return ExtractedField(
        field_name=field_name,
        raw_value=raw_val,
        normalized_value=norm_val if norm_val is not None else raw_val,
        is_uncertain=is_uncertain,
        provenance=EvidenceProvenance(
            document_type=doc_type,
            file_name=f"{doc_type.lower()}.pdf",
            extracted_field=field_name,
            raw_snippet=raw_val,
        ),
    )


def _make_clean_packet():
    return {
        DocumentType.APPLICATION_FORM: ExtractedDocument(
            doc_type=DocumentType.APPLICATION_FORM,
            file_path="application_form.pdf",
            status="VALID",
            fields={
                "applicant_name": _make_field("APPLICATION_FORM", "applicant_name", "Aarav Sharma"),
                "annual_income": _make_field("APPLICATION_FORM", "annual_income", "180000", 180000.0),
                "caste_category": _make_field("APPLICATION_FORM", "caste_category", "GENERAL"),
                "dob": _make_field("APPLICATION_FORM", "dob", "15/08/2005"),
                "income_cert_no": _make_field("APPLICATION_FORM", "income_cert_no", "INC-2025-00123"),
                "caste_cert_no": _make_field("APPLICATION_FORM", "caste_cert_no", "CST-2025-00456"),
                "ifsc": _make_field("APPLICATION_FORM", "ifsc", "SBIN0001234"),
                "account_no": _make_field("APPLICATION_FORM", "account_no", "123456789012"),
            },
        ),
        DocumentType.INCOME_CERT: ExtractedDocument(
            doc_type=DocumentType.INCOME_CERT,
            file_path="income_cert.pdf",
            status="VALID",
            fields={
                "applicant_name": _make_field("INCOME_CERT", "applicant_name", "Aarav Sharma"),
                "annual_income": _make_field("INCOME_CERT", "annual_income", "180000", 180000.0),
                "issue_date": _make_field("INCOME_CERT", "issue_date", "15/01/2025"),
                "certificate_no": _make_field("INCOME_CERT", "certificate_no", "INC-2025-00123"),
            },
        ),
        DocumentType.CASTE_CERT: ExtractedDocument(
            doc_type=DocumentType.CASTE_CERT,
            file_path="caste_cert.pdf",
            status="VALID",
            fields={
                "applicant_name": _make_field("CASTE_CERT", "applicant_name", "Aarav Sharma"),
                "caste_category": _make_field("CASTE_CERT", "caste_category", "GENERAL"),
                "certificate_no": _make_field("CASTE_CERT", "certificate_no", "CST-2025-00456"),
            },
        ),
        DocumentType.RESIDENCE_CERT: ExtractedDocument(
            doc_type=DocumentType.RESIDENCE_CERT,
            file_path="residence_cert.pdf",
            status="VALID",
            fields={
                "applicant_name": _make_field("RESIDENCE_CERT", "applicant_name", "Aarav Sharma"),
                "state": _make_field("RESIDENCE_CERT", "state", "ODISHA"),
                "certificate_no": _make_field("RESIDENCE_CERT", "certificate_no", "RES-2025-00789"),
            },
        ),
        DocumentType.MARKSHEET: ExtractedDocument(
            doc_type=DocumentType.MARKSHEET,
            file_path="marksheet.pdf",
            status="VALID",
            fields={
                "applicant_name": _make_field("MARKSHEET", "applicant_name", "Aarav Sharma"),
                "dob": _make_field("MARKSHEET", "dob", "15/08/2005"),
                "percentage": _make_field("MARKSHEET", "percentage", "78.5", 78.5),
            },
        ),
        DocumentType.BANK_PASSBOOK: ExtractedDocument(
            doc_type=DocumentType.BANK_PASSBOOK,
            file_path="bank_passbook.pdf",
            status="VALID",
            fields={
                "applicant_name": _make_field("BANK_PASSBOOK", "applicant_name", "Aarav Sharma"),
                "account_no": _make_field("BANK_PASSBOOK", "account_no", "123456789012"),
                "ifsc": _make_field("BANK_PASSBOOK", "ifsc", "SBIN0001234"),
            },
        ),
    }


# ---------------------------------------------------------------------------
# 1. Lifecycle and Draft Rejection Contract
# ---------------------------------------------------------------------------
def test_engine_lifecycle_rejects_draft_by_default():
    pack_dir = _REPO_ROOT / "packs" / "generic.demo"
    # generic.demo has status 'draft'. Engine must reject by default when allow_draft=False
    with pytest.raises((ValueError, PackLoadError)) as exc:
        PackExecutionEngine(pack_dir, allow_draft=False)
    assert "draft" in str(exc.value)
    assert "allow_draft" in str(exc.value) or "allow-draft" in str(exc.value)


def test_engine_lifecycle_permits_draft_when_explicit():
    pack_dir = _REPO_ROOT / "packs" / "generic.demo"
    engine = PackExecutionEngine(pack_dir, allow_draft=True)
    assert engine.pack.pack_id == "generic.demo"


def test_engine_lifecycle_rejects_invalid_source_reference(tmp_path: Path):
    pack_dir = tmp_path / "bad_source_pack"
    pack_dir.mkdir(parents=True)
    sources_yaml = """
pack_id: bad_source_pack
version: "1.0.0"
sources:
  - id: "SRC-REAL-01"
    title: "Test"
    issuing_body: "Test Body"
    url: "https://example.invalid"
    retrieved_on: "2026-11-15"
    status: "unverified"
    reviewed_by: "Test"
    clause: "1.0"
    supports_rule: false
"""
    pack_yaml = """
pack_id: bad_source_pack
version: "1.0.0"
status: draft
doc_slots:
  app:
    ocr_langs: [eng]
rules:
  - id: RULE-01
    primitive: field_present
    inputs: { field: "name", docs: ["app"] }
    max_severity: FAIL
    citation:
      source: SRC-NONEXISTENT
      clause: "1.0"
    remediation:
      authority: "Test"
      steps: ["Test"]
"""
    (pack_dir / "sources.yaml").write_text(sources_yaml.strip(), encoding="utf-8")
    (pack_dir / "pack.yaml").write_text(pack_yaml.strip(), encoding="utf-8")
    with pytest.raises(PackLoadError) as exc:
        PackExecutionEngine(pack_dir, allow_draft=True)
    assert "SRC-NONEXISTENT" in str(exc.value)


def test_engine_lifecycle_rejects_invalid_primitive_config(tmp_path: Path):
    pack_dir = tmp_path / "bad_prim_pack"
    pack_dir.mkdir(parents=True)
    sources_yaml = """
pack_id: bad_prim_pack
version: "1.0.0"
sources:
  - id: "SRC-01"
    title: "Test"
    issuing_body: "Test Body"
    url: "https://example.invalid"
    retrieved_on: "2026-11-15"
    status: "unverified"
    reviewed_by: "Test"
    clause: "1.0"
    supports_rule: false
"""
    pack_yaml = """
pack_id: bad_prim_pack
version: "1.0.0"
status: draft
doc_slots:
  app:
    ocr_langs: [eng]
rules:
  - id: RULE-01
    primitive: unknown_primitive_name
    inputs: { field: "name", docs: ["app"] }
    max_severity: FAIL
    citation:
      source: SRC-01
      clause: "1.0"
    remediation:
      authority: "Test"
      steps: ["Test"]
"""
    (pack_dir / "sources.yaml").write_text(sources_yaml.strip(), encoding="utf-8")
    (pack_dir / "pack.yaml").write_text(pack_yaml.strip(), encoding="utf-8")
    with pytest.raises(PackLoadError) as exc:
        PackExecutionEngine(pack_dir, allow_draft=True)
    assert "unknown_primitive_name" in str(exc.value)


# ---------------------------------------------------------------------------
# 2. Clean Packet Execution & Unverified Citation Disclosures
# ---------------------------------------------------------------------------
def test_engine_clean_packet():
    pack_dir = _REPO_ROOT / "packs" / "generic.demo"
    engine = PackExecutionEngine(pack_dir, allow_draft=True)

    packet = _make_clean_packet()
    res = engine.validate_packet("CLEAN_001", packet, as_of=date(2026, 11, 15))

    assert res.readiness is Readiness.NO_ISSUES_FOUND
    assert res.readiness_score == 100

    # Unverified citation metadata must retain [source pending verification]
    unverified_finding = next(f for f in res.findings if f.rule_id == "RULE-DOM-01")
    assert "[source pending verification]" in unverified_finding.statutory_reference


# ---------------------------------------------------------------------------
# 3. Structural Missing Document Handling Across All 6 Slots Individually
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "slot_to_remove",
    [
        DocumentType.APPLICATION_FORM,
        DocumentType.INCOME_CERT,
        DocumentType.CASTE_CERT,
        DocumentType.RESIDENCE_CERT,
        DocumentType.MARKSHEET,
        DocumentType.BANK_PASSBOOK,
    ],
)
def test_engine_individual_missing_required_document(slot_to_remove: DocumentType):
    pack_dir = _REPO_ROOT / "packs" / "generic.demo"
    engine = PackExecutionEngine(pack_dir, allow_draft=True)

    packet = _make_clean_packet()
    del packet[slot_to_remove]

    res = engine.validate_packet(f"MISSING_{slot_to_remove.value}", packet, as_of=date(2026, 11, 15))

    assert res.readiness is Readiness.NOT_READY
    assert res.v2_summary_counts[Status.MISSING.value] >= 1

    missing_finding = next(
        f for f in res.findings
        if f.rule_id == "RULE-DOC-01" and slot_to_remove.value in f.documents_involved
    )
    assert missing_finding.resolved_status is Status.MISSING
    assert missing_finding.reason_code == ReasonCode.DOC_ABSENT.value


# ---------------------------------------------------------------------------
# 4. Unreadable and Corrupted Document Handling Across All 6 Slots
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "slot_to_corrupt",
    [
        DocumentType.APPLICATION_FORM,
        DocumentType.INCOME_CERT,
        DocumentType.CASTE_CERT,
        DocumentType.RESIDENCE_CERT,
        DocumentType.MARKSHEET,
        DocumentType.BANK_PASSBOOK,
    ],
)
def test_engine_individual_unreadable_required_document(slot_to_corrupt: DocumentType):
    pack_dir = _REPO_ROOT / "packs" / "generic.demo"
    engine = PackExecutionEngine(pack_dir, allow_draft=True)

    packet = _make_clean_packet()
    packet[slot_to_corrupt] = ExtractedDocument(
        doc_type=slot_to_corrupt,
        file_path=f"{slot_to_corrupt.value.lower()}.pdf",
        status="UNREADABLE",
    )

    res = engine.validate_packet(f"UNREADABLE_{slot_to_corrupt.value}", packet, as_of=date(2026, 11, 15))
    assert res.readiness is not Readiness.NO_ISSUES_FOUND
    assert res.readiness is Readiness.NEEDS_CHECKS

    unreadable_finding = next(
        f for f in res.findings
        if f.rule_id == "RULE-DOC-02" and slot_to_corrupt.value in f.documents_involved
    )
    assert unreadable_finding.resolved_status is Status.REVIEW
    assert unreadable_finding.reason_code == ReasonCode.INSUFFICIENT_DATA.value


# ---------------------------------------------------------------------------
# 5. Tri-State Category Exemption Evaluation
# ---------------------------------------------------------------------------
def test_engine_exemption_verified_sc():
    pack_dir = _REPO_ROOT / "packs" / "generic.demo"
    engine = PackExecutionEngine(pack_dir, allow_draft=True)

    packet = _make_clean_packet()
    # Below cutoff (45.0% < 50.0%) but verified SC
    packet[DocumentType.MARKSHEET].fields["percentage"] = _make_field("MARKSHEET", "percentage", "45.0", 45.0)
    packet[DocumentType.APPLICATION_FORM].fields["caste_category"] = _make_field("APPLICATION_FORM", "caste_category", "SCHEDULED CASTE (SC)")

    res = engine.validate_packet("EXEMPT_SC", packet, as_of=date(2026, 11, 15))
    mrk_finding = next(f for f in res.findings if f.rule_id == "RULE-MRK-01")
    assert mrk_finding.resolved_status is Status.NOT_APPLICABLE
    assert "EXEMPT" in mrk_finding.reason_code


def test_engine_exemption_verified_st():
    pack_dir = _REPO_ROOT / "packs" / "generic.demo"
    engine = PackExecutionEngine(pack_dir, allow_draft=True)

    packet = _make_clean_packet()
    packet[DocumentType.MARKSHEET].fields["percentage"] = _make_field("MARKSHEET", "percentage", "45.0", 45.0)
    packet[DocumentType.APPLICATION_FORM].fields["caste_category"] = _make_field("APPLICATION_FORM", "caste_category", "ST")

    res = engine.validate_packet("EXEMPT_ST", packet, as_of=date(2026, 11, 15))
    mrk_finding = next(f for f in res.findings if f.rule_id == "RULE-MRK-01")
    assert mrk_finding.resolved_status is Status.NOT_APPLICABLE


def test_engine_exemption_verified_general_fails_cutoff():
    pack_dir = _REPO_ROOT / "packs" / "generic.demo"
    engine = PackExecutionEngine(pack_dir, allow_draft=True)

    packet = _make_clean_packet()
    packet[DocumentType.MARKSHEET].fields["percentage"] = _make_field("MARKSHEET", "percentage", "45.0", 45.0)
    packet[DocumentType.APPLICATION_FORM].fields["caste_category"] = _make_field("APPLICATION_FORM", "caste_category", "GENERAL")

    res = engine.validate_packet("NOT_EXEMPT_GEN", packet, as_of=date(2026, 11, 15))
    mrk_finding = next(f for f in res.findings if f.rule_id == "RULE-MRK-01")
    assert mrk_finding.resolved_status is Status.FAIL


def test_engine_exemption_uncertain_or_missing_abstains_to_review():
    pack_dir = _REPO_ROOT / "packs" / "generic.demo"
    engine = PackExecutionEngine(pack_dir, allow_draft=True)

    packet = _make_clean_packet()
    packet[DocumentType.MARKSHEET].fields["percentage"] = _make_field("MARKSHEET", "percentage", "45.0", 45.0)

    # 1. Uncertain SC extraction
    packet[DocumentType.APPLICATION_FORM].fields["caste_category"] = _make_field(
        "APPLICATION_FORM", "caste_category", "SC", is_uncertain=True
    )
    packet[DocumentType.CASTE_CERT].fields.pop("caste_category", None)
    res_unc = engine.validate_packet("EXEMPT_UNC", packet, as_of=date(2026, 11, 15))
    mrk_unc = next(f for f in res_unc.findings if f.rule_id == "RULE-MRK-01")
    assert mrk_unc.resolved_status is Status.REVIEW
    assert mrk_unc.reason_code in (ReasonCode.EVIDENCE_UNCERTAIN.value, ReasonCode.INSUFFICIENT_DATA.value)

    # 2. Missing caste_category field across all candidate documents
    packet[DocumentType.APPLICATION_FORM].fields.pop("caste_category", None)
    packet[DocumentType.CASTE_CERT].fields.pop("caste_category", None)
    res_miss = engine.validate_packet("EXEMPT_MISSING", packet, as_of=date(2026, 11, 15))
    mrk_miss = next(f for f in res_miss.findings if f.rule_id == "RULE-MRK-01")
    assert mrk_miss.resolved_status is Status.REVIEW
    assert mrk_miss.reason_code in (ReasonCode.EVIDENCE_UNCERTAIN.value, ReasonCode.INSUFFICIENT_DATA.value)


def test_engine_exemption_misleading_substring_not_matched():
    pack_dir = _REPO_ROOT / "packs" / "generic.demo"
    engine = PackExecutionEngine(pack_dir, allow_draft=True)

    packet = _make_clean_packet()
    packet[DocumentType.MARKSHEET].fields["percentage"] = _make_field("MARKSHEET", "percentage", "45.0", 45.0)

    # Misleading word containing 'SC' (e.g. SCHOLARSHIP, DISCIPLINE)
    packet[DocumentType.APPLICATION_FORM].fields["caste_category"] = _make_field(
        "APPLICATION_FORM", "caste_category", "SCHOLARSHIP HOLDER / GENERAL"
    )
    res = engine.validate_packet("MISLEADING_SC", packet, as_of=date(2026, 11, 15))
    mrk = next(f for f in res.findings if f.rule_id == "RULE-MRK-01")
    # Must NOT match SC; ordinary rule applies and fails cutoff
    assert mrk.resolved_status is Status.FAIL


def test_engine_exemption_missing_or_unreadable_app_form_abstains_to_review():
    pack_dir = _REPO_ROOT / "packs" / "generic.demo"
    engine = PackExecutionEngine(pack_dir, allow_draft=True)

    # A: Missing application form -> exemption evidence is unavailable, abstains to REVIEW
    packet_no_app = _make_clean_packet()
    packet_no_app[DocumentType.MARKSHEET].fields["percentage"] = _make_field("MARKSHEET", "percentage", "45.0", 45.0)
    del packet_no_app[DocumentType.APPLICATION_FORM]
    packet_no_app[DocumentType.CASTE_CERT].fields.pop("caste_category", None)

    res_no_app = engine.validate_packet("EXEMPT_NO_APP", packet_no_app, as_of=date(2026, 11, 15))
    mrk_no_app = next(f for f in res_no_app.findings if f.rule_id == "RULE-MRK-01")
    assert mrk_no_app.resolved_status is Status.REVIEW

    # B: Unreadable application form -> exemption evidence uncertain, abstains to REVIEW
    packet_unread_app = _make_clean_packet()
    packet_unread_app[DocumentType.MARKSHEET].fields["percentage"] = _make_field("MARKSHEET", "percentage", "45.0", 45.0)
    packet_unread_app[DocumentType.APPLICATION_FORM] = ExtractedDocument(
        doc_type=DocumentType.APPLICATION_FORM,
        file_path="app_form.pdf",
        status="UNREADABLE",
    )
    packet_unread_app[DocumentType.CASTE_CERT].fields.pop("caste_category", None)

    res_unread = engine.validate_packet("EXEMPT_UNREAD_APP", packet_unread_app, as_of=date(2026, 11, 15))
    mrk_unread = next(f for f in res_unread.findings if f.rule_id == "RULE-MRK-01")
    assert mrk_unread.resolved_status is Status.REVIEW


def test_engine_exemption_misc_token_does_not_exempt():
    pack_dir = _REPO_ROOT / "packs" / "generic.demo"
    engine = PackExecutionEngine(pack_dir, allow_draft=True)

    packet = _make_clean_packet()
    packet[DocumentType.MARKSHEET].fields["percentage"] = _make_field("MARKSHEET", "percentage", "45.0", 45.0)
    # Token containing 'SC' inside 'MISC' must NOT match '\bSC\b'
    packet[DocumentType.APPLICATION_FORM].fields["caste_category"] = _make_field(
        "APPLICATION_FORM", "caste_category", "MISC / GENERAL"
    )
    packet[DocumentType.CASTE_CERT].fields.pop("caste_category", None)

    res = engine.validate_packet("COLLISION_MISC", packet, as_of=date(2026, 11, 15))
    mrk = next(f for f in res.findings if f.rule_id == "RULE-MRK-01")
    # Ordinary academic cutoff applied after verified non-exemption
    assert mrk.resolved_status is Status.FAIL


# ---------------------------------------------------------------------------
# 6. Slot Mismatch Containment
# ---------------------------------------------------------------------------
def test_engine_slot_mismatch_prevents_downstream_pass():
    pack_dir = _REPO_ROOT / "packs" / "generic.demo"
    engine = PackExecutionEngine(pack_dir, allow_draft=True)

    packet = _make_clean_packet()
    # Put Caste Certificate into Income Certificate slot
    packet[DocumentType.INCOME_CERT] = ExtractedDocument(
        doc_type=DocumentType.INCOME_CERT,
        file_path="caste_cert_in_income_slot.pdf",
        status="VALID",
        detected_type=DocumentType.CASTE_CERT,
        fields={
            "applicant_name": _make_field("INCOME_CERT", "applicant_name", "Aarav Sharma"),
            "annual_income": _make_field("INCOME_CERT", "annual_income", "180000", 180000.0),
        },
    )

    res = engine.validate_packet("SLOT_MISMATCH", packet, as_of=date(2026, 11, 15))
    assert res.readiness is Readiness.NOT_READY

    # Slot finding emitted
    slot_finding = next((f for f in res.findings if f.rule_id == "RULE-SLOT-01"), None)
    assert slot_finding is not None
    assert slot_finding.reason_code == ReasonCode.WRONG_DOCUMENT_TYPE.value

    # Income rules dependent on mismatched slot cannot produce PASS
    inc_findings = [f for f in res.findings if f.rule_id in ("RULE-INC-01", "RULE-INC-02", "RULE-EXP-01")]
    for f in inc_findings:
        assert f.resolved_status is not Status.PASS


# ---------------------------------------------------------------------------
# 7. Injected Clock Invariance & Conflict Rejection
# ---------------------------------------------------------------------------
def test_engine_conflicting_clock_rejected():
    pack_dir = _REPO_ROOT / "packs" / "generic.demo"
    engine = PackExecutionEngine(pack_dir, allow_draft=True)

    packet = _make_clean_packet()
    with pytest.raises(ValueError) as exc:
        engine.validate_packet("CLOCK_CONFLICT", packet, as_of=date(2026, 11, 15), audit_date=date(2026, 11, 16))
    assert "Conflicting as_of" in str(exc.value)
