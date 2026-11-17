"""Tests for Scheme Pack Execution Engine (Task T3.2).

Validates:
1. Loading and executing generic.demo pack using closed primitives.
2. Parameter resolution ($income_ceiling, $income_tolerance, etc.).
3. Equivalence against canonical baseline test packets.
4. Correct evaluation of exempt_when clauses (SC/ST marks relaxation).
5. Clean rejection of unregistered primitives.
"""

from datetime import date
from pathlib import Path
import pytest

from docuready.domain.enums import MatchGrade, Readiness, Status
from docuready.domain.models import (
    DocumentType,
    EvidenceProvenance,
    ExtractedDocument,
    ExtractedField,
)
from docuready.rules.engine import PackExecutionEngine
from docuready.rules.loader import load_pack
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


def test_engine_clean_packet():
    pack_dir = _REPO_ROOT / "packs" / "generic.demo"
    engine = PackExecutionEngine(pack_dir, allow_draft=True)

    packet = _make_clean_packet()
    res = engine.validate_packet("CLEAN_001", packet, as_of=date(2026, 11, 15))

    assert res.readiness is Readiness.NO_ISSUES_FOUND
    assert res.readiness_score == 100
    assert len(res.findings) == len(engine.pack.rules)

    # Every canonical rule must pass
    statuses = [f.resolved_status for f in res.findings]
    assert all(s in (Status.PASS, Status.NOT_APPLICABLE) for s in statuses)


def test_engine_income_ceiling_breach():
    pack_dir = _REPO_ROOT / "packs" / "generic.demo"
    engine = PackExecutionEngine(pack_dir, allow_draft=True)

    packet = _make_clean_packet()
    # Modify income to exceed ceiling (300,000 > 250,000)
    packet[DocumentType.INCOME_CERT].fields["annual_income"] = _make_field(
        "INCOME_CERT", "annual_income", "300000", 300000.0
    )
    packet[DocumentType.APPLICATION_FORM].fields["annual_income"] = _make_field(
        "APPLICATION_FORM", "annual_income", "300000", 300000.0
    )

    res = engine.validate_packet("BREACH_001", packet, as_of=date(2026, 11, 15))

    assert res.readiness is Readiness.NOT_READY
    inc_finding = next(f for f in res.findings if f.rule_id == "RULE-INC-01")
    assert inc_finding.resolved_status is Status.FAIL


def test_engine_exempt_when_sc_st():
    pack_dir = _REPO_ROOT / "packs" / "generic.demo"
    engine = PackExecutionEngine(pack_dir, allow_draft=True)

    packet = _make_clean_packet()
    # Marksheet percentage is 45.0% (< 50.0% cutoff)
    packet[DocumentType.MARKSHEET].fields["percentage"] = _make_field(
        "MARKSHEET", "percentage", "45.0", 45.0
    )
    # Set caste category to SC
    packet[DocumentType.APPLICATION_FORM].fields["caste_category"] = _make_field(
        "APPLICATION_FORM", "caste_category", "SCHEDULED CASTE (SC)"
    )

    res = engine.validate_packet("EXEMPT_001", packet, as_of=date(2026, 11, 15))

    mrk_finding = next(f for f in res.findings if f.rule_id == "RULE-MRK-01")
    # Category exemption renders as NOT_APPLICABLE
    assert mrk_finding.resolved_status is Status.NOT_APPLICABLE
    assert "EXEMPT" in mrk_finding.reason_code


def test_engine_unregistered_primitive_rejected():
    pack_dir = _REPO_ROOT / "packs" / "generic.demo"
    pack, sources = load_pack(pack_dir)

    # Inject an invalid rule with unknown primitive
    invalid_rule = RuleDefinition(
        id="RULE-INVALID",
        primitive="completely_unknown_primitive",
        inputs={},
        params={},
        max_severity="FAIL",
        citation=CitationReference(source="SRC-DOC-01"),
        remediation=RemediationMetadata(authority="Test"),
    )
    pack.rules.append(invalid_rule)

    engine = PackExecutionEngine(pack, sources)
    with pytest.raises(ValueError) as exc:
        engine.validate_packet("TEST_001", _make_clean_packet(), as_of=date(2026, 11, 15))
    assert "Unknown or unregistered primitive" in str(exc.value)
