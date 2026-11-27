"""Unit tests for the 9 closed primitives (ARCHITECTURE_V2 §7).

Verifies that every primitive in the closed registry:
1. Executes deterministically in pure Python without dynamic code execution.
2. Accurately evaluates evidence states, match grades, and raw outcomes.
3. Correctly handles boundary conditions, uncertain extractions, multi-field sets, and injected clocks.
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
# 2. field_present with weakest-evidence propagation
# ---------------------------------------------------------------------------
def test_field_present(ctx):
    # Verified field
    doc = _make_doc(
        DocumentType.APPLICATION_FORM,
        fields={"applicant_name": _make_field("APPLICATION_FORM", "applicant_name", "Aarav Sharma")},
    )
    docs = {DocumentType.APPLICATION_FORM: doc}

    res_ok = eval_field_present(docs, {"field": "applicant_name", "docs": ["application_form"]}, {}, ctx)
    assert res_ok.raw is Raw.SATISFIED
    assert res_ok.evidence_state is EvidenceState.VERIFIED

    # Present but uncertain field -> evidence_state MUST propagate UNCERTAIN
    doc_unc = _make_doc(
        DocumentType.APPLICATION_FORM,
        fields={"applicant_name": _make_field("APPLICATION_FORM", "applicant_name", "Aarav Sharma", is_uncertain=True)},
    )
    res_unc = eval_field_present({DocumentType.APPLICATION_FORM: doc_unc}, {"field": "applicant_name", "docs": ["application_form"]}, {}, ctx)
    assert res_unc.raw is Raw.SATISFIED
    assert res_unc.evidence_state is EvidenceState.UNCERTAIN

    # Missing field on VALID doc -> INDETERMINATE / UNCERTAIN (never VIOLATED/VERIFIED)
    res_missing = eval_field_present(docs, {"field": "dob", "docs": ["application_form"]}, {}, ctx)
    assert res_missing.raw is Raw.INDETERMINATE
    assert res_missing.evidence_state is EvidenceState.UNCERTAIN
    assert "DOB" in res_missing.field_name
    assert res_missing.documents_involved == ["APPLICATION_FORM"]
    assert "could not be extracted" in res_missing.message.lower()


def test_field_present_unavailable_and_mixed_sources(ctx):
    from docuready.domain.enums import ReasonCode, Status
    from docuready.outcome.resolver import resolve_outcome

    # 1. Absent source
    res_absent = eval_field_present({}, {"field": "applicant_name", "docs": ["aadhaar_card"]}, {}, ctx)
    assert res_absent.raw is Raw.INDETERMINATE
    assert res_absent.evidence_state is EvidenceState.UNCERTAIN
    assert res_absent.documents_involved == ["AADHAAR"]
    assert "unavailable" in res_absent.message.lower()
    assert res_absent.evidence == []
    out_absent = resolve_outcome(res_absent.raw, res_absent.evidence_state)
    assert out_absent.status is Status.REVIEW
    assert out_absent.reason_code == ReasonCode.INSUFFICIENT_DATA.value

    # 2. Explicit MISSING, UNREADABLE, CORRUPTED sources
    for bad_status in ("MISSING", "UNREADABLE", "CORRUPTED"):
        bad_doc = _make_doc(DocumentType.AADHAAR, status=bad_status, fields={})
        res_bad = eval_field_present(
            {DocumentType.AADHAAR: bad_doc}, {"field": "applicant_name", "docs": ["aadhaar_card"]}, {}, ctx
        )
        assert res_bad.raw is Raw.INDETERMINATE
        assert res_bad.evidence_state is EvidenceState.UNCERTAIN
        assert res_bad.documents_involved == ["AADHAAR"]
        out_bad = resolve_outcome(res_bad.raw, res_bad.evidence_state)
        assert out_bad.status is Status.REVIEW
        assert out_bad.reason_code == ReasonCode.INSUFFICIENT_DATA.value

    # 3. Slot mismatch (via ExecutionContext.mismatched_slots)
    valid_doc = _make_doc(
        DocumentType.AADHAAR,
        fields={"applicant_name": _make_field("AADHAAR", "applicant_name", "Pravasini Sahoo")},
    )
    mismatch_ctx = ExecutionContext(as_of=ctx.as_of, mismatched_slots={DocumentType.AADHAAR})
    res_mismatch = eval_field_present(
        {DocumentType.AADHAAR: valid_doc}, {"field": "applicant_name", "docs": ["aadhaar_card"]}, {}, mismatch_ctx
    )
    assert res_mismatch.raw is Raw.INDETERMINATE
    assert res_mismatch.evidence_state is EvidenceState.UNCERTAIN
    assert res_mismatch.documents_involved == ["AADHAAR"]

    # 4. Empty and whitespace-only field values on VALID doc
    for blank in ("", "   "):
        blank_doc = _make_doc(
            DocumentType.APPLICATION_FORM,
            fields={"applicant_name": _make_field("APPLICATION_FORM", "applicant_name", blank)},
        )
        res_blank = eval_field_present(
            {DocumentType.APPLICATION_FORM: blank_doc},
            {"field": "applicant_name", "docs": ["application_form"]},
            {},
            ctx,
        )
        assert res_blank.raw is Raw.INDETERMINATE
        assert res_blank.evidence_state is EvidenceState.UNCERTAIN
        assert res_blank.documents_involved == ["APPLICATION_FORM"]
        assert "present" not in res_blank.message.lower()

    # 5. Non-empty PROVISIONAL value -> SATISFIED / PROVISIONAL -> REVIEW / CANNOT_CONFIRM
    prov_field = ExtractedField(
        field_name="applicant_name",
        raw_value="Aarav Sharma",
        normalized_value="Aarav Sharma",
        evidence_state=EvidenceState.PROVISIONAL,
        provenance=EvidenceProvenance(
            document_type="APPLICATION_FORM",
            file_name="app.pdf",
            extracted_field="applicant_name",
            raw_snippet="Aarav Sharma",
        ),
    )
    res_prov = eval_field_present(
        {DocumentType.APPLICATION_FORM: _make_doc(DocumentType.APPLICATION_FORM, fields={"applicant_name": prov_field})},
        {"field": "applicant_name", "docs": ["application_form"]},
        {},
        ctx,
    )
    assert res_prov.raw is Raw.SATISFIED
    assert res_prov.evidence_state is EvidenceState.PROVISIONAL
    out_prov = resolve_outcome(res_prov.raw, res_prov.evidence_state)
    assert out_prov.status is Status.REVIEW
    assert out_prov.reason_code == ReasonCode.CANNOT_CONFIRM.value

    # 6. Mixed: one VALID doc missing field + another source absent -> INDETERMINATE (never VIOLATED/PASS)
    mixed_docs = {
        DocumentType.APPLICATION_FORM: _make_doc(DocumentType.APPLICATION_FORM, fields={}),
    }
    res_mixed = eval_field_present(
        mixed_docs,
        {"field": "applicant_name", "docs": ["application_form", "income_certificate"]},
        {},
        ctx,
    )
    assert res_mixed.raw is Raw.INDETERMINATE
    assert res_mixed.evidence_state is EvidenceState.UNCERTAIN
    assert set(res_mixed.documents_involved) == {"INCOME_CERT", "APPLICATION_FORM"}
    out_mixed = resolve_outcome(res_mixed.raw, res_mixed.evidence_state)
    assert out_mixed.status is Status.REVIEW
    assert out_mixed.reason_code == ReasonCode.INSUFFICIENT_DATA.value

    # 7. Mixed provenance: one VALID doc with extracted field + genuine provenance, another source absent
    mixed_prov_docs = {
        DocumentType.APPLICATION_FORM: _make_doc(
            DocumentType.APPLICATION_FORM,
            fields={"applicant_name": _make_field("APPLICATION_FORM", "applicant_name", "Aarav Sharma")},
        ),
    }
    res_mixed_prov = eval_field_present(
        mixed_prov_docs,
        {"field": "applicant_name", "docs": ["application_form", "income_certificate"]},
        {},
        ctx,
    )
    assert res_mixed_prov.raw is Raw.INDETERMINATE
    assert res_mixed_prov.evidence_state is EvidenceState.UNCERTAIN
    assert res_mixed_prov.documents_involved == ["INCOME_CERT"]
    assert len(res_mixed_prov.evidence) == 1
    assert res_mixed_prov.evidence[0].document_type == "APPLICATION_FORM"
    assert res_mixed_prov.evidence[0].extracted_field == "applicant_name"
    out_mixed_prov = resolve_outcome(res_mixed_prov.raw, res_mixed_prov.evidence_state)
    assert out_mixed_prov.status is Status.REVIEW
    assert out_mixed_prov.reason_code == ReasonCode.INSUFFICIENT_DATA.value


def test_field_present_fail_closed_matrix(ctx):
    """Verify all 8 fail-closed cases for eval_field_present."""
    # 1. Source absent from packet
    res_absent = eval_field_present({}, {"field": "applicant_name", "docs": ["aadhaar_card"]}, {}, ctx)
    assert res_absent.raw is Raw.INDETERMINATE
    assert res_absent.evidence_state is EvidenceState.UNCERTAIN
    assert "AADHAAR" in res_absent.documents_involved

    # 2. Explicit document status: MISSING
    doc_missing = ExtractedDocument(
        doc_type=DocumentType.AADHAAR,
        file_path="",
        status="MISSING",
        page_count=0,
        fields={},
    )
    res_doc_missing = eval_field_present({DocumentType.AADHAAR: doc_missing}, {"field": "applicant_name", "docs": ["aadhaar_card"]}, {}, ctx)
    assert res_doc_missing.raw is Raw.INDETERMINATE
    assert res_doc_missing.evidence_state is EvidenceState.UNCERTAIN

    # 3. UNREADABLE and CORRUPTED source documents
    for bad_status in ("UNREADABLE", "CORRUPTED"):
        doc_bad = ExtractedDocument(
            doc_type=DocumentType.AADHAAR,
            file_path="bad.pdf",
            status=bad_status,
            page_count=1,
            fields={},
        )
        res_bad = eval_field_present({DocumentType.AADHAAR: doc_bad}, {"field": "applicant_name", "docs": ["aadhaar_card"]}, {}, ctx)
        assert res_bad.raw is Raw.INDETERMINATE
        assert res_bad.evidence_state is EvidenceState.UNCERTAIN

    # 4. VALID document with empty or whitespace-only field
    for blank in ("", "   \t\n "):
        doc_blank = _make_doc(
            DocumentType.AADHAAR,
            fields={"applicant_name": _make_field("AADHAAR", "applicant_name", blank)},
        )
        res_blank = eval_field_present({DocumentType.AADHAAR: doc_blank}, {"field": "applicant_name", "docs": ["aadhaar_card"]}, {}, ctx)
        assert res_blank.raw is Raw.INDETERMINATE
        assert res_blank.evidence_state is EvidenceState.UNCERTAIN

    # 5. VALID document with provisional field -> SATISFIED / PROVISIONAL
    doc_prov = _make_doc(
        DocumentType.AADHAAR,
        fields={"applicant_name": _make_field("AADHAAR", "applicant_name", "Aarav Sharma", evidence_state=EvidenceState.PROVISIONAL)},
    )
    res_prov = eval_field_present({DocumentType.AADHAAR: doc_prov}, {"field": "applicant_name", "docs": ["aadhaar_card"]}, {}, ctx)
    assert res_prov.raw is Raw.SATISFIED
    assert res_prov.evidence_state is EvidenceState.PROVISIONAL

    # 6. Multi-source case: one valid with field, one absent -> INDETERMINATE / UNCERTAIN
    doc_ok = _make_doc(
        DocumentType.APPLICATION_FORM,
        fields={"applicant_name": _make_field("APPLICATION_FORM", "applicant_name", "Aarav Sharma")},
    )
    res_multi = eval_field_present(
        {DocumentType.APPLICATION_FORM: doc_ok},
        {"field": "applicant_name", "docs": ["application_form", "aadhaar_card"]},
        {},
        ctx,
    )
    assert res_multi.raw is Raw.INDETERMINATE
    assert res_multi.evidence_state is EvidenceState.UNCERTAIN
    assert "AADHAAR" in res_multi.documents_involved


# ---------------------------------------------------------------------------
# 3. match_across with weakest-evidence and multi-field propagation
# ---------------------------------------------------------------------------
def test_match_across_name_exact_and_uncertain(ctx):
    # Exact match across 3 documents
    docs_3 = {
        DocumentType.APPLICATION_FORM: _make_doc(
            DocumentType.APPLICATION_FORM,
            fields={"applicant_name": _make_field("APPLICATION_FORM", "applicant_name", "Aarav Sharma")},
        ),
        DocumentType.INCOME_CERT: _make_doc(
            DocumentType.INCOME_CERT,
            fields={"applicant_name": _make_field("INCOME_CERT", "applicant_name", "Aarav Sharma")},
        ),
        DocumentType.MARKSHEET: _make_doc(
            DocumentType.MARKSHEET,
            fields={"applicant_name": _make_field("MARKSHEET", "applicant_name", "Aarav Sharma")},
        ),
    }
    res_3 = eval_match_across(
        docs_3,
        {"fields": ["application_form.applicant_name", "income_cert.applicant_name", "marksheet.applicant_name"]},
        {"grade": "name"},
        ctx,
    )
    assert res_3.raw is Raw.SATISFIED
    assert res_3.match_grade is MatchGrade.EXACT
    assert res_3.evidence_state is EvidenceState.VERIFIED

    # Matching names with uncertain OCR -> match_grade MUST be AMBIGUOUS and evidence_state UNCERTAIN
    docs_unc = {
        DocumentType.APPLICATION_FORM: _make_doc(
            DocumentType.APPLICATION_FORM,
            fields={"applicant_name": _make_field("APPLICATION_FORM", "applicant_name", "Aarav Sharma", is_uncertain=True)},
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
    assert res_unc.raw is Raw.SATISFIED
    assert res_unc.match_grade is MatchGrade.AMBIGUOUS
    assert res_unc.evidence_state is EvidenceState.UNCERTAIN

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


def test_match_across_date_exact_and_uncertain(ctx):
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
    assert res_dob.evidence_state is EvidenceState.VERIFIED

    # Matching dates with uncertain OCR -> match_grade MUST be AMBIGUOUS and evidence_state UNCERTAIN
    docs_dob_unc = {
        DocumentType.APPLICATION_FORM: _make_doc(
            DocumentType.APPLICATION_FORM,
            fields={"dob": _make_field("APPLICATION_FORM", "dob", "15/08/2005", is_uncertain=True)},
        ),
        DocumentType.MARKSHEET: _make_doc(
            DocumentType.MARKSHEET,
            fields={"dob": _make_field("MARKSHEET", "dob", "15/08/2005")},
        ),
    }
    res_dob_unc = eval_match_across(
        docs_dob_unc,
        {"fields": ["application_form.dob", "marksheet.dob"]},
        {"grade": "date"},
        ctx,
    )
    assert res_dob_unc.raw is Raw.SATISFIED
    assert res_dob_unc.match_grade is MatchGrade.AMBIGUOUS
    assert res_dob_unc.evidence_state is EvidenceState.UNCERTAIN

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


def test_match_across_id_exact_and_uncertain(ctx):
    # Single field valid IFSC
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

    # Cross-document account matching with verified evidence
    docs_acc = {
        DocumentType.BANK_PASSBOOK: _make_doc(
            DocumentType.BANK_PASSBOOK,
            fields={"account_no": _make_field("BANK_PASSBOOK", "account_no", "123456789012")},
        ),
        DocumentType.APPLICATION_FORM: _make_doc(
            DocumentType.APPLICATION_FORM,
            fields={"account_no": _make_field("APPLICATION_FORM", "account_no", "123456789012")},
        ),
    }
    res_acc = eval_match_across(
        docs_acc,
        {"fields": ["bank_passbook.account_no", "application_form.account_no"]},
        {"grade": "id"},
        ctx,
    )
    assert res_acc.raw is Raw.SATISFIED
    assert res_acc.match_grade is MatchGrade.EXACT
    assert res_acc.evidence_state is EvidenceState.VERIFIED

    # Matching identifiers with uncertain OCR -> match_grade MUST be AMBIGUOUS and evidence_state UNCERTAIN
    docs_acc_unc = {
        DocumentType.BANK_PASSBOOK: _make_doc(
            DocumentType.BANK_PASSBOOK,
            fields={"account_no": _make_field("BANK_PASSBOOK", "account_no", "123456789012", is_uncertain=True)},
        ),
        DocumentType.APPLICATION_FORM: _make_doc(
            DocumentType.APPLICATION_FORM,
            fields={"account_no": _make_field("APPLICATION_FORM", "account_no", "123456789012")},
        ),
    }
    res_acc_unc = eval_match_across(
        docs_acc_unc,
        {"fields": ["bank_passbook.account_no", "application_form.account_no"]},
        {"grade": "id"},
        ctx,
    )
    assert res_acc_unc.raw is Raw.SATISFIED
    assert res_acc_unc.match_grade is MatchGrade.AMBIGUOUS
    assert res_acc_unc.evidence_state is EvidenceState.UNCERTAIN


# ---------------------------------------------------------------------------
# 4. within_validity with validity_months and weakest-evidence
# ---------------------------------------------------------------------------
def test_within_validity_with_months_and_uncertain(ctx):
    # Valid with validity_years (issued 2025-01-15, as_of 2026-11-15 -> ~1.8 years <= 3 years)
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
    assert res_val.evidence_state is EvidenceState.VERIFIED

    # Valid with validity_months (issued 2026-06-15, as_of 2026-11-15 -> 5 months <= 6 months)
    docs_months = {
        DocumentType.INCOME_CERT: _make_doc(
            DocumentType.INCOME_CERT,
            fields={"issue_date": _make_field("INCOME_CERT", "issue_date", "15/06/2026")},
        )
    }
    res_months = eval_within_validity(
        docs_months,
        {"field": "issue_date", "docs": ["income_certificate"]},
        {"validity_months": 6},
        ctx,
    )
    assert res_months.raw is Raw.SATISFIED

    # Expired with validity_months (issued 2026-01-15, as_of 2026-11-15 -> 10 months > 6 months)
    res_months_exp = eval_within_validity(
        docs_valid,
        {"field": "issue_date", "docs": ["income_certificate"]},
        {"validity_months": 6},
        ctx,
    )
    assert res_months_exp.raw is Raw.VIOLATED

    # Uncertain issue date -> evidence_state MUST be UNCERTAIN
    docs_unc = {
        DocumentType.INCOME_CERT: _make_doc(
            DocumentType.INCOME_CERT,
            fields={"issue_date": _make_field("INCOME_CERT", "issue_date", "15/01/2025", is_uncertain=True)},
        )
    }
    res_unc = eval_within_validity(
        docs_unc,
        {"field": "issue_date", "docs": ["income_certificate"]},
        {"validity_years": 3},
        ctx,
    )
    assert res_unc.raw is Raw.SATISFIED
    assert res_unc.evidence_state is EvidenceState.UNCERTAIN


# ---------------------------------------------------------------------------
# 5. numeric_cap with closed comparator set and weakest-evidence
# ---------------------------------------------------------------------------
def test_numeric_cap_closed_comparator_and_uncertain(ctx):
    # Comparator validation
    docs = {
        DocumentType.INCOME_CERT: _make_doc(
            DocumentType.INCOME_CERT,
            fields={"annual_income": _make_field("INCOME_CERT", "annual_income", "180000", 180000.0)},
        )
    }
    with pytest.raises(ValueError) as exc:
        eval_numeric_cap(
            docs,
            {"field": "annual_income", "docs": ["income_certificate"]},
            {"cap": 250000.0, "comparator": "unsupported_comparator"},
            ctx,
        )
    assert "Invalid numeric_cap comparator" in str(exc.value)

    # Uncertain but numerically compliant income -> evidence_state MUST propagate UNCERTAIN
    docs_unc_inc = {
        DocumentType.INCOME_CERT: _make_doc(
            DocumentType.INCOME_CERT,
            fields={"annual_income": _make_field("INCOME_CERT", "annual_income", "180000", 180000.0, is_uncertain=True)},
        )
    }
    res_unc_inc = eval_numeric_cap(
        docs_unc_inc,
        {"field": "annual_income", "docs": ["income_certificate"]},
        {"cap": 250000.0, "comparator": "<="},
        ctx,
    )
    assert res_unc_inc.raw is Raw.SATISFIED
    assert res_unc_inc.evidence_state is EvidenceState.UNCERTAIN

    # Uncertain but above-cutoff academic percentage -> evidence_state MUST propagate UNCERTAIN
    docs_unc_mrk = {
        DocumentType.MARKSHEET: _make_doc(
            DocumentType.MARKSHEET,
            fields={"percentage": _make_field("MARKSHEET", "percentage", "78.5", 78.5, is_uncertain=True)},
        )
    }
    res_unc_mrk = eval_numeric_cap(
        docs_unc_mrk,
        {"field": "percentage", "docs": ["marksheet"]},
        {"cap": 50.0, "comparator": ">="},
        ctx,
    )
    assert res_unc_mrk.raw is Raw.SATISFIED
    assert res_unc_mrk.evidence_state is EvidenceState.UNCERTAIN


# ---------------------------------------------------------------------------
# 6. numeric_consistency with multi-field and weakest-evidence
# ---------------------------------------------------------------------------
def test_numeric_consistency_multi_field_and_uncertain(ctx):
    # Matching declared and certified income with uncertain OCR -> MUST be AMBIGUOUS and UNCERTAIN
    docs_unc = {
        DocumentType.INCOME_CERT: _make_doc(
            DocumentType.INCOME_CERT,
            fields={"annual_income": _make_field("INCOME_CERT", "annual_income", "180000", 180000.0, is_uncertain=True)},
        ),
        DocumentType.APPLICATION_FORM: _make_doc(
            DocumentType.APPLICATION_FORM,
            fields={"annual_income": _make_field("APPLICATION_FORM", "annual_income", "180000", 180000.0)},
        ),
    }
    res_unc = eval_numeric_consistency(
        docs_unc,
        {"fields": ["income_certificate.annual_income", "application_form.annual_income"]},
        {"tolerance": 0.0},
        ctx,
    )
    assert res_unc.raw is Raw.SATISFIED
    assert res_unc.match_grade is MatchGrade.AMBIGUOUS
    assert res_unc.evidence_state is EvidenceState.UNCERTAIN

    # Multi-field comparison across 3 documents
    docs_3 = {
        DocumentType.INCOME_CERT: _make_doc(
            DocumentType.INCOME_CERT,
            fields={"annual_income": _make_field("INCOME_CERT", "annual_income", "180000", 180000.0)},
        ),
        DocumentType.APPLICATION_FORM: _make_doc(
            DocumentType.APPLICATION_FORM,
            fields={"annual_income": _make_field("APPLICATION_FORM", "annual_income", "180000", 180000.0)},
        ),
        DocumentType.MARKSHEET: _make_doc(
            DocumentType.MARKSHEET,
            fields={"annual_income": _make_field("MARKSHEET", "annual_income", "180000", 180000.0)},
        ),
    }
    res_3 = eval_numeric_consistency(
        docs_3,
        {"fields": ["income_certificate.annual_income", "application_form.annual_income", "marksheet.annual_income"]},
        {"tolerance": 0.0},
        ctx,
    )
    assert res_3.raw is Raw.SATISFIED
    assert res_3.match_grade is MatchGrade.EXACT
    assert res_3.evidence_state is EvidenceState.VERIFIED


# ---------------------------------------------------------------------------
# 7. age_on
# ---------------------------------------------------------------------------
def test_age_on(ctx):
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


# ---------------------------------------------------------------------------
# 10. Comprehensive Evidence Uncertainty Cases (Task T3.2.1)
# ---------------------------------------------------------------------------
def test_match_across_compatible_and_text_with_uncertainty(ctx):
    # Compatible name match with uncertain extraction
    docs_compat_unc = {
        DocumentType.APPLICATION_FORM: _make_doc(
            DocumentType.APPLICATION_FORM,
            fields={"applicant_name": _make_field("APPLICATION_FORM", "applicant_name", "Sharma Aarav", is_uncertain=True)},
        ),
        DocumentType.INCOME_CERT: _make_doc(
            DocumentType.INCOME_CERT,
            fields={"applicant_name": _make_field("INCOME_CERT", "applicant_name", "Aarav Sharma")},
        ),
    }
    res_compat_unc = eval_match_across(
        docs_compat_unc,
        {"fields": ["application_form.applicant_name", "income_cert.applicant_name"]},
        {"grade": "name"},
        ctx,
    )
    assert res_compat_unc.raw is Raw.SATISFIED
    assert res_compat_unc.match_grade is MatchGrade.AMBIGUOUS
    assert res_compat_unc.evidence_state is EvidenceState.UNCERTAIN

    # Text match with verified vs uncertain extraction
    docs_text = {
        DocumentType.RESIDENCE_CERT: _make_doc(
            DocumentType.RESIDENCE_CERT,
            fields={"state": _make_field("RESIDENCE_CERT", "state", "ODISHA")},
        ),
        DocumentType.APPLICATION_FORM: _make_doc(
            DocumentType.APPLICATION_FORM,
            fields={"state": _make_field("APPLICATION_FORM", "state", "ODISHA")},
        ),
    }
    res_text = eval_match_across(
        docs_text,
        {"fields": ["residence_cert.state", "application_form.state"]},
        {"grade": "text"},
        ctx,
    )
    assert res_text.raw is Raw.SATISFIED
    assert res_text.match_grade is MatchGrade.EXACT
    assert res_text.evidence_state is EvidenceState.VERIFIED

    # Text match with uncertain extraction
    docs_text_unc = {
        DocumentType.RESIDENCE_CERT: _make_doc(
            DocumentType.RESIDENCE_CERT,
            fields={"state": _make_field("RESIDENCE_CERT", "state", "ODISHA", is_uncertain=True)},
        ),
        DocumentType.APPLICATION_FORM: _make_doc(
            DocumentType.APPLICATION_FORM,
            fields={"state": _make_field("APPLICATION_FORM", "state", "ODISHA")},
        ),
    }
    res_text_unc = eval_match_across(
        docs_text_unc,
        {"fields": ["residence_cert.state", "application_form.state"]},
        {"grade": "text"},
        ctx,
    )
    assert res_text_unc.raw is Raw.SATISFIED
    assert res_text_unc.match_grade is MatchGrade.AMBIGUOUS
    assert res_text_unc.evidence_state is EvidenceState.UNCERTAIN


def test_numeric_cap_below_at_above_with_uncertainty(ctx):
    # 1. Below cap with uncertain extraction
    docs_below = {
        DocumentType.INCOME_CERT: _make_doc(
            DocumentType.INCOME_CERT,
            fields={"annual_income": _make_field("INCOME_CERT", "annual_income", "180000", 180000.0, is_uncertain=True)},
        )
    }
    res_below = eval_numeric_cap(
        docs_below,
        {"field": "annual_income", "docs": ["income_certificate"]},
        {"cap": 250000.0, "comparator": "<="},
        ctx,
    )
    assert res_below.raw is Raw.SATISFIED
    assert res_below.evidence_state is EvidenceState.UNCERTAIN

    # 2. At cap with uncertain extraction
    docs_at = {
        DocumentType.INCOME_CERT: _make_doc(
            DocumentType.INCOME_CERT,
            fields={"annual_income": _make_field("INCOME_CERT", "annual_income", "250000", 250000.0, is_uncertain=True)},
        )
    }
    res_at = eval_numeric_cap(
        docs_at,
        {"field": "annual_income", "docs": ["income_certificate"]},
        {"cap": 250000.0, "comparator": "<="},
        ctx,
    )
    assert res_at.raw is Raw.SATISFIED
    assert res_at.evidence_state is EvidenceState.UNCERTAIN

    # 3. Above cap with uncertain extraction
    docs_above = {
        DocumentType.INCOME_CERT: _make_doc(
            DocumentType.INCOME_CERT,
            fields={"annual_income": _make_field("INCOME_CERT", "annual_income", "300000", 300000.0, is_uncertain=True)},
        )
    }
    res_above = eval_numeric_cap(
        docs_above,
        {"field": "annual_income", "docs": ["income_certificate"]},
        {"cap": 250000.0, "comparator": "<="},
        ctx,
    )
    assert res_above.raw is Raw.VIOLATED
    assert res_above.evidence_state is EvidenceState.UNCERTAIN


def test_numeric_consistency_one_or_both_uncertain(ctx):
    # One value uncertain
    docs_one_unc = {
        DocumentType.INCOME_CERT: _make_doc(
            DocumentType.INCOME_CERT,
            fields={"annual_income": _make_field("INCOME_CERT", "annual_income", "180000", 180000.0, is_uncertain=True)},
        ),
        DocumentType.APPLICATION_FORM: _make_doc(
            DocumentType.APPLICATION_FORM,
            fields={"annual_income": _make_field("APPLICATION_FORM", "annual_income", "180000", 180000.0)},
        ),
    }
    res_one = eval_numeric_consistency(
        docs_one_unc,
        {"fields": ["income_cert.annual_income", "application_form.annual_income"]},
        {"tolerance": 0.0},
        ctx,
    )
    assert res_one.raw is Raw.SATISFIED
    assert res_one.evidence_state is EvidenceState.UNCERTAIN

    # Both values uncertain
    docs_both_unc = {
        DocumentType.INCOME_CERT: _make_doc(
            DocumentType.INCOME_CERT,
            fields={"annual_income": _make_field("INCOME_CERT", "annual_income", "180000", 180000.0, is_uncertain=True)},
        ),
        DocumentType.APPLICATION_FORM: _make_doc(
            DocumentType.APPLICATION_FORM,
            fields={"annual_income": _make_field("APPLICATION_FORM", "annual_income", "180000", 180000.0, is_uncertain=True)},
        ),
    }
    res_both = eval_numeric_consistency(
        docs_both_unc,
        {"fields": ["income_cert.annual_income", "application_form.annual_income"]},
        {"tolerance": 0.0},
        ctx,
    )
    assert res_both.raw is Raw.SATISFIED
    assert res_both.evidence_state is EvidenceState.UNCERTAIN


def test_enum_in_and_age_on_with_uncertainty(ctx):
    # Enum match with uncertain extraction
    docs_enum_unc = {
        DocumentType.RESIDENCE_CERT: _make_doc(
            DocumentType.RESIDENCE_CERT,
            fields={"state": _make_field("RESIDENCE_CERT", "state", "ODISHA", is_uncertain=True)},
        )
    }
    res_enum_unc = eval_enum_in(
        docs_enum_unc,
        {"field": "state", "docs": ["residence_certificate"]},
        {"values": ["ODISHA"]},
        ctx,
    )
    assert res_enum_unc.raw is Raw.SATISFIED
    assert res_enum_unc.evidence_state is EvidenceState.UNCERTAIN

    # Age on with uncertain DOB extraction
    docs_age_unc = {
        DocumentType.APPLICATION_FORM: _make_doc(
            DocumentType.APPLICATION_FORM,
            fields={"dob": _make_field("APPLICATION_FORM", "dob", "15/08/2005", is_uncertain=True)},
        )
    }
    res_age_unc = eval_age_on(
        docs_age_unc,
        {"field": "dob", "docs": ["application_form"]},
        {"min_age": 18, "max_age": 30},
        ctx,
    )
    assert res_age_unc.raw is Raw.SATISFIED
    assert res_age_unc.evidence_state is EvidenceState.UNCERTAIN


def test_both_uncertainty_representations_consistent(ctx):
    """Test both is_uncertain=True and evidence_state=EvidenceState.UNCERTAIN representations."""
    # 1. Model field with is_uncertain=True
    field_flag = _make_field("INCOME_CERT", "annual_income", "180000", 180000.0, is_uncertain=True)
    assert field_flag.evidence_state is EvidenceState.UNCERTAIN or field_flag.is_uncertain

    # 2. Model field with explicit evidence_state=EvidenceState.UNCERTAIN
    field_enum = _make_field("INCOME_CERT", "annual_income", "180000", 180000.0, is_uncertain=False)
    field_enum.evidence_state = EvidenceState.UNCERTAIN

    docs_flag = {DocumentType.INCOME_CERT: _make_doc(DocumentType.INCOME_CERT, fields={"annual_income": field_flag})}
    docs_enum = {DocumentType.INCOME_CERT: _make_doc(DocumentType.INCOME_CERT, fields={"annual_income": field_enum})}

    res_flag = eval_numeric_cap(docs_flag, {"field": "annual_income", "docs": ["income_certificate"]}, {"cap": 250000.0, "comparator": "<="}, ctx)
    res_enum = eval_numeric_cap(docs_enum, {"field": "annual_income", "docs": ["income_certificate"]}, {"cap": 250000.0, "comparator": "<="}, ctx)

    assert res_flag.raw == res_enum.raw == Raw.SATISFIED
    assert res_flag.evidence_state == res_enum.evidence_state == EvidenceState.UNCERTAIN
