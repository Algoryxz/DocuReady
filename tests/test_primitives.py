"""Unit tests for the 9 closed primitives (ARCHITECTURE_V2 §7).

Verifies that every primitive in the closed registry:
1. Executes deterministically in pure Python without dynamic code execution.
2. Accurately evaluates evidence states, match grades, and raw outcomes.
3. Correctly handles boundary conditions, uncertain extractions, and injected clocks.
"""

from datetime import date
from typing import Dict
import pytest

from docuready.domain.enums import EvidenceState, ExtractionMethod, MatchGrade, Raw
from docuready.domain.models import (
    DocumentType,
    EvidenceProvenance,
    ExtractedDocument,
    ExtractedField,
)
from docuready.rules.primitives import (
    PRIMITIVE_REGISTRY,
    ExecutionContext,
    eval_age_on,
    eval_enum_in,
    eval_field_present,
    eval_legible,
    eval_match_across,
    eval_numeric_cap,
    eval_numeric_consistency,
    eval_require_document,
    eval_within_validity,
)


def _make_field(
    doc_type: str,
    field_name: str,
    raw_val: str,
    norm_val=None,
    is_uncertain: bool = False,
    evidence_state: EvidenceState = EvidenceState.VERIFIED,
) -> ExtractedField:
    return ExtractedField(
        field_name=field_name,
        raw_value=raw_val,
        normalized_value=norm_val if norm_val is not None else raw_val,
        is_uncertain=is_uncertain,
        evidence_state=evidence_state,
        provenance=EvidenceProvenance(
            document_type=doc_type,
            file_name=f"{doc_type.lower()}.pdf",
            extracted_field=field_name,
            raw_snippet=raw_val,
        ),
    )


def _make_doc(
    doc_type: DocumentType,
    status: str = "VALID",
    fields: Dict[str, ExtractedField] = None,
    page_count: int = 1,
    mean_ocr_confidence: float = 0.95,
) -> ExtractedDocument:
    return ExtractedDocument(
        doc_type=doc_type,
        file_path=f"{doc_type.value.lower()}.pdf",
        status=status,
        fields=fields or {},
        page_count=page_count,
        mean_ocr_confidence=mean_ocr_confidence,
    )


@pytest.fixture
def ctx() -> ExecutionContext:
    return ExecutionContext(as_of=date(2026, 11, 15))


# ---------------------------------------------------------------------------
# Registry Invariants
# ---------------------------------------------------------------------------
def test_primitive_registry_completeness():
    expected = {
        "require_document",
        "field_present",
        "match_across",
        "within_validity",
        "numeric_cap",
        "numeric_consistency",
        "age_on",
        "enum_in",
        "legible",
    }
    assert set(PRIMITIVE_REGISTRY.keys()) == expected
    for name, fn in PRIMITIVE_REGISTRY.items():
        assert callable(fn), f"Registry entry {name} must be callable"


# ---------------------------------------------------------------------------
# 1. require_document
# ---------------------------------------------------------------------------
def test_require_document(ctx):
    # Satisfied
    docs = {
        DocumentType.INCOME_CERT: _make_doc(DocumentType.INCOME_CERT, status="VALID", page_count=2)
    }
    res = eval_require_document(docs, {"slot": "income_certificate"}, {"min_pages": 1}, ctx)
    assert res.raw is Raw.SATISFIED
    assert res.evidence_state is EvidenceState.VERIFIED

    # Missing
    res_miss = eval_require_document({}, {"slot": "income_certificate"}, {}, ctx)
    assert res_miss.raw is Raw.DOC_ABSENT

    # Unreadable
    docs_unreadable = {
        DocumentType.INCOME_CERT: _make_doc(DocumentType.INCOME_CERT, status="UNREADABLE")
    }
    res_unreadable = eval_require_document(docs_unreadable, {"slot": "income_certificate"}, {}, ctx)
    assert res_unreadable.raw is Raw.INDETERMINATE
    assert res_unreadable.evidence_state is EvidenceState.UNCERTAIN

    # Insufficient pages
    res_pages = eval_require_document(docs, {"slot": "income_certificate"}, {"min_pages": 3}, ctx)
    assert res_pages.raw is Raw.VIOLATED


# ---------------------------------------------------------------------------
# 2. field_present
# ---------------------------------------------------------------------------
def test_field_present(ctx):
    doc = _make_doc(
        DocumentType.APPLICATION_FORM,
        fields={"applicant_name": _make_field("APPLICATION_FORM", "applicant_name", "Aarav Sharma")},
    )
    docs = {DocumentType.APPLICATION_FORM: doc}

    res_ok = eval_field_present(docs, {"field": "applicant_name", "docs": ["application_form"]}, {}, ctx)
    assert res_ok.raw is Raw.SATISFIED

    res_missing = eval_field_present(docs, {"field": "dob", "docs": ["application_form"]}, {}, ctx)
    assert res_missing.raw is Raw.VIOLATED
    assert "DOB" in res_missing.field_name


# ---------------------------------------------------------------------------
# 3. match_across
# ---------------------------------------------------------------------------
def test_match_across_name(ctx):
    # Exact match
    docs_exact = {
        DocumentType.APPLICATION_FORM: _make_doc(
            DocumentType.APPLICATION_FORM,
            fields={"applicant_name": _make_field("APPLICATION_FORM", "applicant_name", "Aarav Sharma")},
        ),
        DocumentType.INCOME_CERT: _make_doc(
            DocumentType.INCOME_CERT,
            fields={"applicant_name": _make_field("INCOME_CERT", "applicant_name", "Aarav Sharma")},
        ),
    }
    res_exact = eval_match_across(
        docs_exact,
        {"fields": ["application_form.applicant_name", "income_cert.applicant_name"]},
        {"grade": "name"},
        ctx,
    )
    assert res_exact.raw is Raw.SATISFIED
    assert res_exact.match_grade is MatchGrade.EXACT

    # Compatible match (token reordering)
    docs_compat = {
        DocumentType.APPLICATION_FORM: _make_doc(
            DocumentType.APPLICATION_FORM,
            fields={"applicant_name": _make_field("APPLICATION_FORM", "applicant_name", "Sharma Aarav")},
        ),
        DocumentType.INCOME_CERT: _make_doc(
            DocumentType.INCOME_CERT,
            fields={"applicant_name": _make_field("INCOME_CERT", "applicant_name", "Aarav Sharma")},
        ),
    }
    res_compat = eval_match_across(
        docs_compat,
        {"fields": ["application_form.applicant_name", "income_cert.applicant_name"]},
        {"grade": "name"},
        ctx,
    )
    assert res_compat.raw is Raw.SATISFIED
    assert res_compat.match_grade is MatchGrade.COMPATIBLE

    # Conflicting match
    docs_conflict = {
        DocumentType.APPLICATION_FORM: _make_doc(
            DocumentType.APPLICATION_FORM,
            fields={"applicant_name": _make_field("APPLICATION_FORM", "applicant_name", "Rohan Verma")},
        ),
        DocumentType.INCOME_CERT: _make_doc(
            DocumentType.INCOME_CERT,
            fields={"applicant_name": _make_field("INCOME_CERT", "applicant_name", "Aarav Sharma")},
        ),
    }
    res_conflict = eval_match_across(
        docs_conflict,
        {"fields": ["application_form.applicant_name", "income_cert.applicant_name"]},
        {"grade": "name"},
        ctx,
    )
    assert res_conflict.raw is Raw.VIOLATED
    assert res_conflict.match_grade is MatchGrade.CONFLICT

    # Uncertain OCR
    docs_unc = {
        DocumentType.APPLICATION_FORM: _make_doc(
            DocumentType.APPLICATION_FORM,
            fields={"applicant_name": _make_field("APPLICATION_FORM", "applicant_name", "Rohan Verma", is_uncertain=True)},
        ),
        DocumentType.INCOME_CERT: _make_doc(
            DocumentType.INCOME_CERT,
            fields={"applicant_name": _make_field("INCOME_CERT", "applicant_name", "Aarav Sharma")},
        ),
    }
    res_unc = eval_match_across(
        docs_unc,
        {"fields": ["application_form.applicant_name", "income_cert.applicant_name"]},
        {"grade": "name"},
        ctx,
    )
    assert res_unc.raw is Raw.INDETERMINATE
    assert res_unc.match_grade is MatchGrade.AMBIGUOUS


def test_match_across_date(ctx):
    # Exact match
    docs_dob = {
        DocumentType.APPLICATION_FORM: _make_doc(
            DocumentType.APPLICATION_FORM,
            fields={"dob": _make_field("APPLICATION_FORM", "dob", "15/08/2005")},
        ),
        DocumentType.MARKSHEET: _make_doc(
            DocumentType.MARKSHEET,
            fields={"dob": _make_field("MARKSHEET", "dob", "15/08/2005")},
        ),
    }
    res_dob = eval_match_across(
        docs_dob,
        {"fields": ["application_form.dob", "marksheet.dob"]},
        {"grade": "date"},
        ctx,
    )
    assert res_dob.raw is Raw.SATISFIED
    assert res_dob.match_grade is MatchGrade.EXACT

    # Ambiguous date representation (e.g. 05/06/2005 vs 06/05/2005)
    docs_amb = {
        DocumentType.APPLICATION_FORM: _make_doc(
            DocumentType.APPLICATION_FORM,
            fields={"dob": _make_field("APPLICATION_FORM", "dob", "05/06/2005")},
        ),
        DocumentType.MARKSHEET: _make_doc(
            DocumentType.MARKSHEET,
            fields={"dob": _make_field("MARKSHEET", "dob", "06/05/2005")},
        ),
    }
    res_amb = eval_match_across(
        docs_amb,
        {"fields": ["application_form.dob", "marksheet.dob"]},
        {"grade": "date"},
        ctx,
    )
    assert res_amb.raw is Raw.INDETERMINATE
    assert res_amb.match_grade is MatchGrade.AMBIGUOUS


def test_match_across_id(ctx):
    # Valid IFSC code (single field evaluation)
    docs_ifsc = {
        DocumentType.BANK_PASSBOOK: _make_doc(
            DocumentType.BANK_PASSBOOK,
            fields={"ifsc": _make_field("BANK_PASSBOOK", "ifsc", "SBIN0001234")},
        )
    }
    res_ifsc = eval_match_across(
        docs_ifsc,
        {"field": "ifsc", "docs": ["bank_passbook"]},
        {"grade": "id"},
        ctx,
    )
    assert res_ifsc.raw is Raw.SATISFIED
    assert res_ifsc.match_grade is MatchGrade.EXACT

    # Invalid IFSC
    docs_ifsc_bad = {
        DocumentType.BANK_PASSBOOK: _make_doc(
            DocumentType.BANK_PASSBOOK,
            fields={"ifsc": _make_field("BANK_PASSBOOK", "ifsc", "INVALID_IFSC")},
        )
    }
    res_bad = eval_match_across(
        docs_ifsc_bad,
        {"field": "ifsc", "docs": ["bank_passbook"]},
        {"grade": "id"},
        ctx,
    )
    assert res_bad.raw is Raw.VIOLATED
    assert res_bad.match_grade is MatchGrade.CONFLICT


# ---------------------------------------------------------------------------
# 4. within_validity
# ---------------------------------------------------------------------------
def test_within_validity(ctx):
    # Valid (issued 2025-01-15, as_of 2026-11-15 -> ~1.8 years <= 3 years)
    docs_valid = {
        DocumentType.INCOME_CERT: _make_doc(
            DocumentType.INCOME_CERT,
            fields={"issue_date": _make_field("INCOME_CERT", "issue_date", "15/01/2025")},
        )
    }
    res_val = eval_within_validity(
        docs_valid,
        {"field": "issue_date", "docs": ["income_certificate"]},
        {"validity_years": 3},
        ctx,
    )
    assert res_val.raw is Raw.SATISFIED

    # Expired (issued 2020-01-15, as_of 2026-11-15 -> > 6 years)
    docs_exp = {
        DocumentType.INCOME_CERT: _make_doc(
            DocumentType.INCOME_CERT,
            fields={"issue_date": _make_field("INCOME_CERT", "issue_date", "15/01/2020")},
        )
    }
    res_exp = eval_within_validity(
        docs_exp,
        {"field": "issue_date", "docs": ["income_certificate"]},
        {"validity_years": 3},
        ctx,
    )
    assert res_exp.raw is Raw.VIOLATED


# ---------------------------------------------------------------------------
# 5. numeric_cap
# ---------------------------------------------------------------------------
def test_numeric_cap(ctx):
    # Ceiling pass (180,000 <= 250,000)
    docs_pass = {
        DocumentType.INCOME_CERT: _make_doc(
            DocumentType.INCOME_CERT,
            fields={"annual_income": _make_field("INCOME_CERT", "annual_income", "180000", 180000.0)},
        )
    }
    res_pass = eval_numeric_cap(
        docs_pass,
        {"field": "annual_income", "docs": ["income_certificate"]},
        {"cap": 250000.0, "comparator": "<="},
        ctx,
    )
    assert res_pass.raw is Raw.SATISFIED

    # Ceiling breach (300,000 > 250,000)
    docs_breach = {
        DocumentType.INCOME_CERT: _make_doc(
            DocumentType.INCOME_CERT,
            fields={"annual_income": _make_field("INCOME_CERT", "annual_income", "300000", 300000.0)},
        )
    }
    res_breach = eval_numeric_cap(
        docs_breach,
        {"field": "annual_income", "docs": ["income_certificate"]},
        {"cap": 250000.0, "comparator": "<="},
        ctx,
    )
    assert res_breach.raw is Raw.VIOLATED

    # Mark cutoff pass (78.5 >= 50.0)
    docs_mrk = {
        DocumentType.MARKSHEET: _make_doc(
            DocumentType.MARKSHEET,
            fields={"percentage": _make_field("MARKSHEET", "percentage", "78.5", 78.5)},
        )
    }
    res_mrk = eval_numeric_cap(
        docs_mrk,
        {"field": "percentage", "docs": ["marksheet"]},
        {"cap": 50.0, "comparator": ">="},
        ctx,
    )
    assert res_mrk.raw is Raw.SATISFIED


# ---------------------------------------------------------------------------
# 6. numeric_consistency
# ---------------------------------------------------------------------------
def test_numeric_consistency(ctx):
    # Exact match
    docs_match = {
        DocumentType.INCOME_CERT: _make_doc(
            DocumentType.INCOME_CERT,
            fields={"annual_income": _make_field("INCOME_CERT", "annual_income", "180000", 180000.0)},
        ),
        DocumentType.APPLICATION_FORM: _make_doc(
            DocumentType.APPLICATION_FORM,
            fields={"annual_income": _make_field("APPLICATION_FORM", "annual_income", "180000", 180000.0)},
        ),
    }
    res_match = eval_numeric_consistency(
        docs_match,
        {"fields": ["income_certificate.annual_income", "application_form.annual_income"]},
        {"tolerance": 0.0},
        ctx,
    )
    assert res_match.raw is Raw.SATISFIED
    assert res_match.match_grade is MatchGrade.EXACT

    # Mismatch
    docs_diff = {
        DocumentType.INCOME_CERT: _make_doc(
            DocumentType.INCOME_CERT,
            fields={"annual_income": _make_field("INCOME_CERT", "annual_income", "200000", 200000.0)},
        ),
        DocumentType.APPLICATION_FORM: _make_doc(
            DocumentType.APPLICATION_FORM,
            fields={"annual_income": _make_field("APPLICATION_FORM", "annual_income", "180000", 180000.0)},
        ),
    }
    res_diff = eval_numeric_consistency(
        docs_diff,
        {"fields": ["income_certificate.annual_income", "application_form.annual_income"]},
        {"tolerance": 0.0},
        ctx,
    )
    assert res_diff.raw is Raw.VIOLATED
    assert res_diff.match_grade is MatchGrade.CONFLICT


# ---------------------------------------------------------------------------
# 7. age_on
# ---------------------------------------------------------------------------
def test_age_on(ctx):
    # DOB 2005-08-15 as of 2026-11-15 -> 21 years old
    docs_age = {
        DocumentType.APPLICATION_FORM: _make_doc(
            DocumentType.APPLICATION_FORM,
            fields={"dob": _make_field("APPLICATION_FORM", "dob", "15/08/2005")},
        )
    }
    res_age = eval_age_on(
        docs_age,
        {"field": "dob", "docs": ["application_form"]},
        {"min_age": 18, "max_age": 30},
        ctx,
    )
    assert res_age.raw is Raw.SATISFIED

    # Underage check (min_age 25)
    res_under = eval_age_on(
        docs_age,
        {"field": "dob", "docs": ["application_form"]},
        {"min_age": 25},
        ctx,
    )
    assert res_under.raw is Raw.VIOLATED


# ---------------------------------------------------------------------------
# 8. enum_in
# ---------------------------------------------------------------------------
def test_enum_in(ctx):
    # Domicile state match
    docs_dom = {
        DocumentType.RESIDENCE_CERT: _make_doc(
            DocumentType.RESIDENCE_CERT,
            fields={"state": _make_field("RESIDENCE_CERT", "state", "ODISHA")},
        )
    }
    res_dom = eval_enum_in(
        docs_dom,
        {"field": "state", "docs": ["residence_certificate"]},
        {"values": ["ODISHA"]},
        ctx,
    )
    assert res_dom.raw is Raw.SATISFIED

    # Mismatch
    docs_other = {
        DocumentType.RESIDENCE_CERT: _make_doc(
            DocumentType.RESIDENCE_CERT,
            fields={"state": _make_field("RESIDENCE_CERT", "state", "MAHARASHTRA")},
        )
    }
    res_other = eval_enum_in(
        docs_other,
        {"field": "state", "docs": ["residence_certificate"]},
        {"values": ["ODISHA"]},
        ctx,
    )
    assert res_other.raw is Raw.VIOLATED


# ---------------------------------------------------------------------------
# 9. legible
# ---------------------------------------------------------------------------
def test_legible(ctx):
    docs_clean = {
        DocumentType.INCOME_CERT: _make_doc(DocumentType.INCOME_CERT, status="VALID", mean_ocr_confidence=0.92)
    }
    res_clean = eval_legible(docs_clean, {"slot": "income_certificate"}, {"min_confidence": 0.60}, ctx)
    assert res_clean.raw is Raw.SATISFIED

    docs_corrupt = {
        DocumentType.INCOME_CERT: _make_doc(DocumentType.INCOME_CERT, status="CORRUPTED")
    }
    res_corrupt = eval_legible(docs_corrupt, {"slot": "income_certificate"}, {}, ctx)
    assert res_corrupt.raw is Raw.INDETERMINATE
    assert res_corrupt.evidence_state is EvidenceState.UNCERTAIN
