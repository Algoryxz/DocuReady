"""Closed primitive execution engine for DocuReady scheme packs (ARCHITECTURE_V2 §7).

Implements the 9 approved closed primitives deterministically in pure Python:
1. require_document
2. field_present
3. match_across
4. within_validity
5. numeric_cap
6. numeric_consistency
7. age_on
8. enum_in
9. legible

Strict architectural invariants:
- Zero dynamic code execution (strictly no eval, exec, importlib, or compilation).
- Fully deterministic: all dates evaluate against an explicitly injected `as_of` clock.
- Complete evidence provenance and match grade preservation.
- Weakest-evidence propagation: uncertain evidence never hardcodes to VERIFIED.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

from docuready.domain.enums import (
    EvidenceState,
    MatchGrade,
    Raw,
    normalize_evidence_state,
)
from docuready.domain.models import (
    DocumentType,
    EvidenceProvenance,
    ExtractedDocument,
    ExtractedField,
)
from docuready.normalize.normalizer import (
    compare_amounts,
    compare_dates,
    compare_identifiers,
    compare_names,
    parse_and_normalize_date,
    validate_ifsc_code,
)
from docuready.outcome.resolver import weakest_evidence

ALLOWED_COMPARATORS: frozenset[str] = frozenset(
    {"<=", ">=", "<", ">", "==", "!=", "lte", "gte", "eq", "lt", "gt"}
)


@dataclass(frozen=True)
class PrimitiveResult:
    """Raw deterministic evaluation result produced by a closed primitive."""

    raw: Raw
    match_grade: Optional[MatchGrade] = None
    evidence_state: Optional[EvidenceState] = None
    evidence: List[EvidenceProvenance] = field(default_factory=list)
    field_name: Optional[str] = None
    documents_involved: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    message: Optional[str] = None


@dataclass(frozen=True)
class ExecutionContext:
    """Execution context injected into primitive evaluations."""

    as_of: date
    scheme_name: str = "generic.demo"
    mismatched_slots: Set[DocumentType] = field(default_factory=set)


def resolve_doc_type(name: str) -> Optional[DocumentType]:
    """Resolve a slot/document string name into a canonical DocumentType."""
    if not isinstance(name, str):
        return None
    normalized = name.strip().upper().replace("-", "_").replace(" ", "_")
    alias_map = {
        "APPLICATION_FORM": DocumentType.APPLICATION_FORM,
        "APPLICATION": DocumentType.APPLICATION_FORM,
        "FORM": DocumentType.APPLICATION_FORM,
        "INCOME_CERT": DocumentType.INCOME_CERT,
        "INCOME_CERTIFICATE": DocumentType.INCOME_CERT,
        "INCOME": DocumentType.INCOME_CERT,
        "CASTE_CERT": DocumentType.CASTE_CERT,
        "CASTE_CERTIFICATE": DocumentType.CASTE_CERT,
        "CASTE": DocumentType.CASTE_CERT,
        "RESIDENCE_CERT": DocumentType.RESIDENCE_CERT,
        "RESIDENCE_CERTIFICATE": DocumentType.RESIDENCE_CERT,
        "RESIDENCE": DocumentType.RESIDENCE_CERT,
        "MARKSHEET": DocumentType.MARKSHEET,
        "MARK_SHEET": DocumentType.MARKSHEET,
        "BANK_PASSBOOK": DocumentType.BANK_PASSBOOK,
        "PASSBOOK": DocumentType.BANK_PASSBOOK,
        "BANK": DocumentType.BANK_PASSBOOK,
        "AADHAAR_CARD": DocumentType.AADHAAR,
        "AADHAAR": DocumentType.AADHAAR,
    }
    if normalized in alias_map:
        return alias_map[normalized]
    try:
        return DocumentType(normalized)
    except ValueError:
        return None


def get_document(
    documents: Dict[Any, ExtractedDocument],
    doc_name: str,
    mismatched_slots: Optional[Set[DocumentType]] = None,
) -> Optional[ExtractedDocument]:
    """Retrieve an extracted document from the packet dictionary.

    Fails closed if the document is in mismatched_slots to prevent corrupt
    or mismatched extractions from leaking into downstream rules.
    """
    dt = resolve_doc_type(doc_name)
    if mismatched_slots and dt in mismatched_slots:
        return None

    if dt is not None and dt in documents:
        return documents[dt]
    # Check string keys directly
    for k, doc in documents.items():
        k_str = k.value if hasattr(k, "value") else str(k)
        if k_str.upper() == doc_name.upper():
            return doc
        if dt is not None and k_str.upper() == dt.value.upper():
            return doc
    return None


def get_field_from_doc(
    doc: Optional[ExtractedDocument], field_name: str
) -> Optional[ExtractedField]:
    """Retrieve an extracted field from a document by field name (case-insensitive)."""
    if not doc or not doc.fields:
        return None
    if field_name in doc.fields:
        return doc.fields[field_name]
    fname_norm = field_name.strip().lower()
    for k, f in doc.fields.items():
        if k.strip().lower() == fname_norm:
            return f
    return None


def parse_field_spec(
    spec: str, default_docs: Optional[List[str]] = None
) -> Tuple[Optional[str], str]:
    """Parse a field specification into (doc_name, field_name)."""
    if "." in spec:
        doc_part, f_part = spec.split(".", 1)
        return doc_part.strip(), f_part.strip()
    doc_part = default_docs[0] if default_docs and len(default_docs) > 0 else None
    return doc_part, spec.strip()


def get_field_evidence_state(f: ExtractedField) -> EvidenceState:
    """Extract canonical evidence state from field, treating is_uncertain as UNCERTAIN."""
    if getattr(f, "is_uncertain", False):
        return EvidenceState.UNCERTAIN
    return normalize_evidence_state(getattr(f, "evidence_state", None))


# ---------------------------------------------------------------------------
# 1. require_document
# ---------------------------------------------------------------------------
def eval_require_document(
    documents: Dict[Any, ExtractedDocument],
    inputs: Dict[str, Any],
    params: Dict[str, Any],
    context: ExecutionContext,
) -> PrimitiveResult:
    """Evaluate mandatory document slot presence and integrity."""
    slot = inputs.get("slot") or inputs.get("field")
    slots = inputs.get("slots") or inputs.get("docs") or ([slot] if slot else [])
    min_pages = int(params.get("min_pages", 1))

    if not slots:
        return PrimitiveResult(
            raw=Raw.INDETERMINATE,
            message="No document slot specified for require_document",
        )

    for slot_name in slots:
        doc = get_document(documents, slot_name, context.mismatched_slots)
        dt = resolve_doc_type(slot_name)
        doc_label = dt.value if dt else slot_name

        if doc is None or doc.status == "MISSING":
            return PrimitiveResult(
                raw=Raw.DOC_ABSENT,
                documents_involved=[doc_label],
                message=f"Mandatory document '{doc_label}' is missing from the application packet.",
            )

        if doc.status in ("UNREADABLE", "CORRUPTED"):
            ev = []
            if doc.file_path:
                ev.append(
                    EvidenceProvenance(
                        document_type=doc_label,
                        file_name=doc.file_path,
                        raw_snippet="[UNREADABLE SCAN / INSUFFICIENT EVIDENCE]",
                    )
                )
            return PrimitiveResult(
                raw=Raw.INDETERMINATE,
                evidence_state=EvidenceState.UNCERTAIN,
                documents_involved=[doc_label],
                evidence=ev,
                message=f"Document '{doc_label}' is unreadable or corrupted. Clear evidence cannot be extracted.",
            )

        if doc.page_count < min_pages:
            return PrimitiveResult(
                raw=Raw.VIOLATED,
                evidence_state=EvidenceState.VERIFIED,
                documents_involved=[doc_label],
                message=f"Document '{doc_label}' has {doc.page_count} pages, which is less than required {min_pages}.",
            )

    return PrimitiveResult(
        raw=Raw.SATISFIED,
        evidence_state=EvidenceState.VERIFIED,
        documents_involved=[
            (resolve_doc_type(s).value if resolve_doc_type(s) else s) for s in slots
        ],
        message="Mandatory document completeness satisfied.",
    )


# ---------------------------------------------------------------------------
# 2. field_present
# ---------------------------------------------------------------------------
def eval_field_present(
    documents: Dict[Any, ExtractedDocument],
    inputs: Dict[str, Any],
    params: Dict[str, Any],
    context: ExecutionContext,
) -> PrimitiveResult:
    """Evaluate presence and non-emptiness of extracted field(s) with fail-closed abstention."""
    field_name = inputs.get("field", "")
    docs = inputs.get("docs") or inputs.get("slots") or []

    if not docs:
        docs = [d.doc_type.value for d in documents.values() if hasattr(d, "doc_type")]

    unavailable_docs: List[str] = []
    missing_field_docs: List[str] = []
    found_evidences: List[EvidenceProvenance] = []
    found_states: List[EvidenceState] = []
    doc_labels: List[str] = []

    for doc_name in docs:
        doc = get_document(documents, doc_name, context.mismatched_slots)
        dt = resolve_doc_type(doc_name)
        doc_label = dt.value if dt else doc_name
        doc_labels.append(doc_label)

        if doc is None or doc.status != "VALID":
            unavailable_docs.append(doc_label)
            continue

        f = get_field_from_doc(doc, field_name)
        if not f or not f.raw_value or not f.raw_value.strip():
            missing_field_docs.append(doc_label)
        else:
            found_states.append(get_field_evidence_state(f))
            if f.provenance:
                found_evidences.append(f.provenance)

    incomplete_docs = unavailable_docs + missing_field_docs
    if incomplete_docs:
        if unavailable_docs and missing_field_docs:
            msg = (
                f"Mandatory field '{field_name}' cannot be assessed: unavailable source(s) "
                f"{', '.join(unavailable_docs)} and unextracted or empty field in {', '.join(missing_field_docs)}."
            )
        elif unavailable_docs:
            msg = (
                f"Source document(s) {', '.join(unavailable_docs)} unavailable or not VALID; "
                f"mandatory field '{field_name}' cannot be assessed."
            )
        else:
            msg = (
                f"Mandatory field '{field_name}' could not be extracted or is empty "
                f"in {', '.join(missing_field_docs)}."
            )
        return PrimitiveResult(
            raw=Raw.INDETERMINATE,
            field_name=field_name.upper(),
            documents_involved=incomplete_docs,
            evidence=found_evidences,
            evidence_state=EvidenceState.UNCERTAIN,
            message=msg,
        )

    if not found_states:
        return PrimitiveResult(
            raw=Raw.INDETERMINATE,
            field_name=field_name.upper(),
            documents_involved=doc_labels,
            evidence=[],
            evidence_state=EvidenceState.UNCERTAIN,
            message=f"No valid source evidence available to assess mandatory field '{field_name}'.",
        )

    weakest = weakest_evidence(found_states)

    return PrimitiveResult(
        raw=Raw.SATISFIED,
        field_name=field_name.upper(),
        documents_involved=doc_labels,
        evidence=found_evidences,
        evidence_state=weakest,
        message=f"Field '{field_name}' was extracted from the supplied document(s).",
    )


# ---------------------------------------------------------------------------
# 3. match_across
# ---------------------------------------------------------------------------
def eval_match_across(
    documents: Dict[Any, ExtractedDocument],
    inputs: Dict[str, Any],
    params: Dict[str, Any],
    context: ExecutionContext,
) -> PrimitiveResult:
    """Evaluate cross-document consistency across all fields with weakest-evidence propagation."""
    grade_type = str(params.get("grade", "text")).lower().strip()
    raw_fields = inputs.get("fields") or []
    single_field = inputs.get("field")
    input_docs = inputs.get("docs") or []

    collected_fields: List[Tuple[str, ExtractedField]] = []

    if raw_fields:
        for fspec in raw_fields:
            doc_name, f_name = parse_field_spec(fspec, input_docs)
            if not doc_name:
                continue
            doc = get_document(documents, doc_name, context.mismatched_slots)
            if doc and doc.status == "VALID":
                f = get_field_from_doc(doc, f_name)
                if f and f.raw_value:
                    dt = resolve_doc_type(doc_name)
                    collected_fields.append((dt.value if dt else doc_name, f))
    elif single_field:
        for doc_name in input_docs:
            doc = get_document(documents, doc_name, context.mismatched_slots)
            if doc and doc.status == "VALID":
                f = get_field_from_doc(doc, single_field)
                if f and f.raw_value:
                    dt = resolve_doc_type(doc_name)
                    collected_fields.append((dt.value if dt else doc_name, f))

    # Single-field validation mode (e.g. Bank IFSC code validation)
    if len(collected_fields) == 1 and grade_type == "id":
        doc_label, f_obj = collected_fields[0]
        ev = [
            f_obj.provenance
            or EvidenceProvenance(
                document_type=doc_label,
                file_name="",
                extracted_field=f_obj.field_name,
                raw_snippet=f_obj.raw_value,
            )
        ]
        ev_state = get_field_evidence_state(f_obj)
        if f_obj.field_name.lower() in ("ifsc", "ifsc_code"):
            if not validate_ifsc_code(f_obj.raw_value):
                return PrimitiveResult(
                    raw=Raw.VIOLATED,
                    match_grade=MatchGrade.CONFLICT,
                    evidence_state=ev_state,
                    field_name="IFSC_FORMAT",
                    documents_involved=[doc_label],
                    evidence=ev,
                    message=f"Bank IFSC code '{f_obj.raw_value}' violates standard RBI format (4 letters, 0, 6 alphanumeric).",
                )
            return PrimitiveResult(
                raw=Raw.SATISFIED,
                match_grade=MatchGrade.EXACT if ev_state is EvidenceState.VERIFIED else MatchGrade.AMBIGUOUS,
                evidence_state=ev_state,
                field_name="IFSC_FORMAT",
                documents_involved=[doc_label],
                evidence=ev,
                message=f"Bank IFSC code '{f_obj.raw_value}' is valid per RBI standard.",
            )

    if len(collected_fields) < 2:
        return PrimitiveResult(
            raw=Raw.INDETERMINATE,
            match_grade=MatchGrade.AMBIGUOUS,
            evidence_state=EvidenceState.UNCERTAIN,
            message="Insufficient extracted fields for cross-document comparison.",
        )

    all_ev_states = [get_field_evidence_state(f) for _, f in collected_fields]
    weakest = weakest_evidence(all_ev_states)
    is_any_unc = any(s is EvidenceState.UNCERTAIN for s in all_ev_states)

    primary_doc, primary_f = collected_fields[0]
    all_ev = [
        (
            f.provenance
            or EvidenceProvenance(
                document_type=dt_name,
                file_name="",
                extracted_field=f.field_name,
                raw_snippet=f.raw_value,
            )
        )
        for dt_name, f in collected_fields
    ]
    docs_involved = [dt_name for dt_name, _ in collected_fields]

    # Mode A: Applicant Name Matching across all documents
    if grade_type == "name":
        overall_grade = MatchGrade.EXACT
        for dt2, f2 in collected_fields[1:]:
            cmp = compare_names(primary_f.raw_value, f2.raw_value)
            c_grade = cmp.get("grade")
            if c_grade == MatchGrade.COMPATIBLE and overall_grade == MatchGrade.EXACT:
                overall_grade = MatchGrade.COMPATIBLE

            pair_unc = primary_f.is_uncertain or f2.is_uncertain
            ev_pair = [
                primary_f.provenance
                or EvidenceProvenance(
                    document_type=primary_doc,
                    file_name="",
                    raw_snippet=primary_f.raw_value,
                ),
                f2.provenance
                or EvidenceProvenance(
                    document_type=dt2, file_name="", raw_snippet=f2.raw_value
                ),
            ]

            if cmp["status"] == "FAIL":
                if pair_unc or is_any_unc:
                    return PrimitiveResult(
                        raw=Raw.INDETERMINATE,
                        match_grade=MatchGrade.AMBIGUOUS,
                        evidence_state=EvidenceState.UNCERTAIN,
                        field_name="APPLICANT_NAME_UNCERTAIN",
                        documents_involved=[primary_doc, dt2],
                        evidence=ev_pair,
                        message=f"Apparent name discrepancy between {primary_doc} ('{primary_f.raw_value}') and {dt2} ('{f2.raw_value}'), but extraction has low confidence. Human review required.",
                    )
                return PrimitiveResult(
                    raw=Raw.VIOLATED,
                    match_grade=cmp.get("grade", MatchGrade.CONFLICT),
                    evidence_state=EvidenceState.VERIFIED,
                    field_name="APPLICANT_NAME",
                    documents_involved=[primary_doc, dt2],
                    evidence=ev_pair,
                    message=f"Conflicting applicant names between {primary_doc} ('{primary_f.raw_value}') and {dt2} ('{f2.raw_value}').",
                )
            if cmp["status"] == "REVIEW":
                return PrimitiveResult(
                    raw=Raw.VIOLATED if c_grade is MatchGrade.COMPATIBLE else Raw.INDETERMINATE,
                    match_grade=c_grade or MatchGrade.COMPATIBLE,
                    evidence_state=EvidenceState.UNCERTAIN if pair_unc else EvidenceState.VERIFIED,
                    field_name="APPLICANT_NAME_VARIATION",
                    documents_involved=[primary_doc, dt2],
                    evidence=ev_pair,
                    message=f"Name variation detected between {primary_doc} ('{primary_f.raw_value}') and {dt2} ('{f2.raw_value}'): {cmp.get('notes', '')}.",
                )

        # All names matched: propagate uncertainty if any field was uncertain
        if is_any_unc:
            return PrimitiveResult(
                raw=Raw.SATISFIED,
                match_grade=MatchGrade.AMBIGUOUS,
                evidence_state=EvidenceState.UNCERTAIN,
                field_name="APPLICANT_NAME",
                documents_involved=docs_involved,
                evidence=all_ev[:2],
                message="Applicant names appear consistent, but extraction evidence is uncertain.",
            )

        msg = (
            "Applicant name matches consistently across all verified documents."
            if overall_grade == MatchGrade.EXACT
            else "Applicant name has compatible variation (e.g. token reordering) across verified documents."
        )
        return PrimitiveResult(
            raw=Raw.SATISFIED,
            match_grade=overall_grade,
            evidence_state=weakest,
            field_name="APPLICANT_NAME",
            documents_involved=docs_involved,
            evidence=all_ev[:2],
            message=msg,
        )

    # Mode B: Date Matching across all documents
    if grade_type == "date":
        for dt2, f2 in collected_fields[1:]:
            cmp_dob = compare_dates(primary_f.raw_value, f2.raw_value)
            d1, st1, _ = parse_and_normalize_date(primary_f.raw_value)
            d2, st2, _ = parse_and_normalize_date(f2.raw_value)
            ev_pair = [
                primary_f.provenance or EvidenceProvenance(document_type=primary_doc, file_name="", extracted_field=primary_f.field_name, raw_snippet=primary_f.raw_value),
                f2.provenance or EvidenceProvenance(document_type=dt2, file_name="", extracted_field=f2.field_name, raw_snippet=f2.raw_value),
            ]

            if st1 == "INVALID_FORMAT" or st2 == "INVALID_FORMAT":
                return PrimitiveResult(
                    raw=Raw.VIOLATED,
                    match_grade=MatchGrade.CONFLICT,
                    evidence_state=weakest,
                    field_name="DOB_FORMAT",
                    documents_involved=[primary_doc, dt2],
                    evidence=ev_pair,
                    message=f"Malformed Date of Birth format: {primary_doc} ('{primary_f.raw_value}') or {dt2} ('{f2.raw_value}').",
                )
            if cmp_dob.get("grade") == MatchGrade.AMBIGUOUS:
                return PrimitiveResult(
                    raw=Raw.INDETERMINATE,
                    match_grade=MatchGrade.AMBIGUOUS,
                    evidence_state=EvidenceState.UNCERTAIN,
                    field_name="DOB_AMBIGUITY",
                    documents_involved=[primary_doc, dt2],
                    evidence=ev_pair,
                    message=f"Ambiguous date representation detected ('{primary_f.raw_value}' vs '{f2.raw_value}'). Could represent DD/MM/YYYY or MM/DD/YYYY.",
                )
            if cmp_dob.get("grade") == MatchGrade.CONFLICT:
                if primary_f.is_uncertain or f2.is_uncertain or is_any_unc:
                    return PrimitiveResult(
                        raw=Raw.INDETERMINATE,
                        match_grade=MatchGrade.AMBIGUOUS,
                        evidence_state=EvidenceState.UNCERTAIN,
                        field_name="DATE_OF_BIRTH_UNCERTAIN",
                        documents_involved=[primary_doc, dt2],
                        evidence=ev_pair,
                        message=f"Potential Date of Birth discrepancy between {primary_doc} ({d1}) and {dt2} ({d2}), but extraction has low OCR confidence. Human verification required.",
                    )
                return PrimitiveResult(
                    raw=Raw.VIOLATED,
                    match_grade=MatchGrade.CONFLICT,
                    evidence_state=EvidenceState.VERIFIED,
                    field_name="DATE_OF_BIRTH",
                    documents_involved=[primary_doc, dt2],
                    evidence=ev_pair,
                    message=f"Date of Birth contradiction: {primary_doc} ({d1}) vs {dt2} ({d2}).",
                )

        if is_any_unc:
            return PrimitiveResult(
                raw=Raw.SATISFIED,
                match_grade=MatchGrade.AMBIGUOUS,
                evidence_state=EvidenceState.UNCERTAIN,
                field_name="DATE_OF_BIRTH",
                documents_involved=docs_involved,
                evidence=all_ev[:2],
                message="Date of Birth appears to match, but extraction evidence is uncertain.",
            )

        d_final, _, _ = parse_and_normalize_date(primary_f.raw_value)
        return PrimitiveResult(
            raw=Raw.SATISFIED,
            match_grade=MatchGrade.EXACT,
            evidence_state=weakest,
            field_name="DATE_OF_BIRTH",
            documents_involved=docs_involved,
            evidence=all_ev[:2],
            message=f"Date of Birth matches consistently ({d_final}).",
        )

    # Mode C: Identifier Matching across all documents
    if grade_type == "id":
        for dt2, f2 in collected_fields[1:]:
            ev_pair = [
                primary_f.provenance or EvidenceProvenance(document_type=primary_doc, file_name="", extracted_field=primary_f.field_name, raw_snippet=primary_f.raw_value),
                f2.provenance or EvidenceProvenance(document_type=dt2, file_name="", extracted_field=f2.field_name, raw_snippet=f2.raw_value),
            ]
            cmp_id = compare_identifiers(
                primary_f.raw_value,
                f2.raw_value,
                is_uncertain=(primary_f.is_uncertain or f2.is_uncertain or is_any_unc),
            )
            if cmp_id.get("grade") == MatchGrade.CONFLICT:
                if primary_f.is_uncertain or f2.is_uncertain or is_any_unc:
                    return PrimitiveResult(
                        raw=Raw.INDETERMINATE,
                        match_grade=MatchGrade.AMBIGUOUS,
                        evidence_state=EvidenceState.UNCERTAIN,
                        field_name="IDENTIFIER_MISMATCH",
                        documents_involved=[primary_doc, dt2],
                        evidence=ev_pair,
                        message=f"Reference number comparison ambiguous between {primary_doc} ('{primary_f.raw_value}') and {dt2} ('{f2.raw_value}'): extraction uncertain.",
                    )
                return PrimitiveResult(
                    raw=Raw.VIOLATED,
                    match_grade=MatchGrade.CONFLICT,
                    evidence_state=EvidenceState.VERIFIED,
                    field_name="IDENTIFIER_MISMATCH",
                    documents_involved=[primary_doc, dt2],
                    evidence=ev_pair,
                    message=f"Reference number discrepancy between {primary_doc} ('{primary_f.raw_value}') and {dt2} ('{f2.raw_value}').",
                )
            if cmp_id.get("grade") == MatchGrade.AMBIGUOUS:
                if primary_f.raw_value.strip() != f2.raw_value.strip():
                    return PrimitiveResult(
                        raw=Raw.INDETERMINATE,
                        match_grade=MatchGrade.AMBIGUOUS,
                        evidence_state=EvidenceState.UNCERTAIN,
                        field_name="IDENTIFIER_MISMATCH",
                        documents_involved=[primary_doc, dt2],
                        evidence=ev_pair,
                        message=f"Reference number comparison ambiguous between {primary_doc} ('{primary_f.raw_value}') and {dt2} ('{f2.raw_value}'): {cmp_id.get('notes', 'Extraction uncertain')}.",
                    )

        if is_any_unc:
            return PrimitiveResult(
                raw=Raw.SATISFIED,
                match_grade=MatchGrade.AMBIGUOUS,
                evidence_state=EvidenceState.UNCERTAIN,
                field_name="IDENTIFIER_MATCH",
                documents_involved=docs_involved,
                evidence=all_ev[:2],
                message="Identifiers appear to match, but extraction evidence is uncertain.",
            )

        return PrimitiveResult(
            raw=Raw.SATISFIED,
            match_grade=MatchGrade.EXACT,
            evidence_state=weakest,
            field_name="IDENTIFIER_MATCH",
            documents_involved=docs_involved,
            evidence=all_ev[:2],
            message=f"Certificate reference number matches across verified documents.",
        )

    # Mode D: Plain Text Matching across all documents
    t_primary = " ".join(primary_f.raw_value.strip().lower().split())
    for dt2, f2 in collected_fields[1:]:
        t2 = " ".join(f2.raw_value.strip().lower().split())
        ev_pair = [
            primary_f.provenance or EvidenceProvenance(document_type=primary_doc, file_name="", extracted_field=primary_f.field_name, raw_snippet=primary_f.raw_value),
            f2.provenance or EvidenceProvenance(document_type=dt2, file_name="", extracted_field=f2.field_name, raw_snippet=f2.raw_value),
        ]
        if t_primary != t2:
            return PrimitiveResult(
                raw=Raw.VIOLATED,
                match_grade=MatchGrade.CONFLICT,
                evidence_state=weakest,
                documents_involved=[primary_doc, dt2],
                evidence=ev_pair,
                message=f"Field values differ: '{primary_f.raw_value}' vs '{f2.raw_value}'.",
            )

    if is_any_unc:
        return PrimitiveResult(
            raw=Raw.SATISFIED,
            match_grade=MatchGrade.AMBIGUOUS,
            evidence_state=EvidenceState.UNCERTAIN,
            documents_involved=docs_involved,
            evidence=all_ev[:2],
            message="Field values match, but extraction evidence is uncertain.",
        )

    return PrimitiveResult(
        raw=Raw.SATISFIED,
        match_grade=MatchGrade.EXACT,
        evidence_state=weakest,
        documents_involved=docs_involved,
        evidence=all_ev[:2],
        message=f"Field values match across all verified documents.",
    )


# ---------------------------------------------------------------------------
# 4. within_validity
# ---------------------------------------------------------------------------
def eval_within_validity(
    documents: Dict[Any, ExtractedDocument],
    inputs: Dict[str, Any],
    params: Dict[str, Any],
    context: ExecutionContext,
) -> PrimitiveResult:
    """Evaluate certificate issue date age against validity duration with weakest-evidence propagation."""
    field_name = inputs.get("field", "issue_date")
    docs = inputs.get("docs") or ["INCOME_CERT"]

    doc_name = docs[0]
    doc = get_document(documents, doc_name, context.mismatched_slots)
    dt = resolve_doc_type(doc_name)
    doc_label = dt.value if dt else doc_name

    if doc is None or doc.status != "VALID":
        return PrimitiveResult(
            raw=Raw.INDETERMINATE,
            evidence_state=EvidenceState.UNCERTAIN,
            documents_involved=[doc_label],
            message=f"Document '{doc_label}' missing or unextracted for validity check.",
        )

    f = get_field_from_doc(doc, field_name)
    if not f or not f.raw_value:
        return PrimitiveResult(
            raw=Raw.INDETERMINATE,
            evidence_state=EvidenceState.UNCERTAIN,
            documents_involved=[doc_label],
            message=f"Issue date field '{field_name}' not found on {doc_label}.",
        )

    ev_state = get_field_evidence_state(f)
    ev = [
        f.provenance
        or EvidenceProvenance(
            document_type=doc_label,
            file_name=doc.file_path,
            extracted_field=field_name,
            raw_snippet=f.raw_value,
        )
    ]
    p_date, st_date, _ = parse_and_normalize_date(f.raw_value)
    if not p_date:
        return PrimitiveResult(
            raw=Raw.INDETERMINATE,
            evidence_state=EvidenceState.UNCERTAIN,
            field_name="CERT_DATE_PARSE",
            documents_involved=[doc_label],
            evidence=ev,
            message=f"Issue date '{f.raw_value}' on {doc_label} is unreadable or malformed.",
        )

    age_days = (context.as_of - p_date).days
    age_years = age_days / 365.25
    age_months = age_days / (365.25 / 12.0)

    val_years = params.get("validity_years")
    val_months = params.get("validity_months")
    val_days = params.get("validity_days")

    if val_years is not None:
        max_years = float(val_years)
        if age_years > max_years:
            return PrimitiveResult(
                raw=Raw.VIOLATED,
                evidence_state=ev_state,
                field_name="CERTIFICATE_EXPIRY",
                documents_involved=[doc_label],
                evidence=ev,
                message=f"Income Certificate expired: issued on {p_date} ({age_years:.1f} years ago; maximum validity is {int(max_years) if max_years.is_integer() else max_years} years).",
            )
        return PrimitiveResult(
            raw=Raw.SATISFIED,
            evidence_state=ev_state,
            field_name="CERTIFICATE_VALIDITY",
            documents_involved=[doc_label],
            evidence=ev,
            message=f"Income Certificate is valid (issued {p_date}, age {age_years:.1f} years <= {int(max_years) if max_years.is_integer() else max_years} years).",
        )

    if val_months is not None:
        max_months = float(val_months)
        if age_months > max_months:
            return PrimitiveResult(
                raw=Raw.VIOLATED,
                evidence_state=ev_state,
                field_name="CERTIFICATE_EXPIRY",
                documents_involved=[doc_label],
                evidence=ev,
                message=f"Certificate expired: {age_months:.1f} months old exceeds maximum {max_months} months.",
            )
        return PrimitiveResult(
            raw=Raw.SATISFIED,
            evidence_state=ev_state,
            field_name="CERTIFICATE_VALIDITY",
            documents_involved=[doc_label],
            evidence=ev,
            message=f"Certificate is valid ({age_months:.1f} months old <= {max_months} months).",
        )

    if val_days is not None:
        max_days = int(val_days)
        if age_days > max_days:
            return PrimitiveResult(
                raw=Raw.VIOLATED,
                evidence_state=ev_state,
                field_name="CERTIFICATE_EXPIRY",
                documents_involved=[doc_label],
                evidence=ev,
                message=f"Certificate expired: {age_days} days old exceeds maximum {max_days} days.",
            )
        return PrimitiveResult(
            raw=Raw.SATISFIED,
            evidence_state=ev_state,
            field_name="CERTIFICATE_VALIDITY",
            documents_involved=[doc_label],
            evidence=ev,
            message=f"Certificate is valid ({age_days} days old <= {max_days} days).",
        )

    return PrimitiveResult(
        raw=Raw.INDETERMINATE,
        evidence_state=EvidenceState.UNCERTAIN,
        message="No validity duration (validity_years/months/days) specified in params.",
    )


# ---------------------------------------------------------------------------
# 5. numeric_cap
# ---------------------------------------------------------------------------
def eval_numeric_cap(
    documents: Dict[Any, ExtractedDocument],
    inputs: Dict[str, Any],
    params: Dict[str, Any],
    context: ExecutionContext,
) -> PrimitiveResult:
    """Evaluate numeric field against statutory ceiling or cutoff with weakest-evidence propagation."""
    field_name = inputs.get("field", "")
    docs = inputs.get("docs") or []
    cap = float(params.get("cap", 0.0))
    comparator = str(params.get("comparator", "<=")).strip()

    if comparator not in ALLOWED_COMPARATORS:
        raise ValueError(
            f"Invalid numeric_cap comparator '{comparator}'. Allowed: {sorted(ALLOWED_COMPARATORS)}"
        )

    if not docs:
        docs = [d.doc_type.value for d in documents.values() if hasattr(d, "doc_type")]

    doc_name = docs[0]
    doc = get_document(documents, doc_name, context.mismatched_slots)
    dt = resolve_doc_type(doc_name)
    doc_label = dt.value if dt else doc_name

    if doc is None or doc.status != "VALID":
        return PrimitiveResult(
            raw=Raw.INDETERMINATE,
            evidence_state=EvidenceState.UNCERTAIN,
            documents_involved=[doc_label],
            message=f"Document '{doc_label}' missing or unextracted for numeric cap check.",
        )

    f = get_field_from_doc(doc, field_name)
    if not f:
        return PrimitiveResult(
            raw=Raw.INDETERMINATE,
            evidence_state=EvidenceState.UNCERTAIN,
            documents_involved=[doc_label],
            message=f"Field '{field_name}' not found on {doc_label}.",
        )

    ev_state = get_field_evidence_state(f)
    ev = [
        f.provenance
        or EvidenceProvenance(
            document_type=doc_label,
            file_name=doc.file_path,
            extracted_field=field_name,
            raw_snippet=f.raw_value,
        )
    ]
    num_val = f.normalized_value
    if num_val is None:
        try:
            num_val = float(str(f.raw_value).replace(",", "").strip())
        except (ValueError, TypeError):
            num_val = None

    if num_val is None:
        return PrimitiveResult(
            raw=Raw.INDETERMINATE,
            evidence_state=EvidenceState.UNCERTAIN,
            field_name="INCOME_VALUE" if "income" in field_name.lower() else "NUMERIC_VALUE",
            documents_involved=[doc_label],
            evidence=ev,
            message=f"Could not parse valid numerical value from '{f.raw_value}' on {doc_label}.",
        )

    num_val = float(num_val)

    if comparator in ("<=", "lte", "<", "lt"):
        is_breach = num_val > cap if comparator in ("<=", "lte") else num_val >= cap
        if is_breach:
            if ev_state is EvidenceState.UNCERTAIN:
                return PrimitiveResult(
                    raw=Raw.VIOLATED,
                    evidence_state=EvidenceState.UNCERTAIN,
                    field_name="INCOME_CEILING_UNCERTAIN" if "income" in field_name.lower() else "CEILING_UNCERTAIN",
                    documents_involved=[doc_label],
                    evidence=ev,
                    message=f"Certified annual income appears to be ₹{num_val:,.0f} (above ceiling ₹{cap:,.0f}), but extraction has low OCR confidence. Verify certificate manually.",
                )
            return PrimitiveResult(
                raw=Raw.VIOLATED,
                evidence_state=ev_state,
                field_name="INCOME_CEILING" if "income" in field_name.lower() else "NUMERIC_CEILING",
                documents_involved=[doc_label],
                evidence=ev,
                message=f"Certified annual income ₹{num_val:,.0f} exceeds scheme ceiling ₹{cap:,.0f}.",
            )
        # Satisified (within ceiling): propagate ev_state (NEVER hardcoded VERIFIED)
        return PrimitiveResult(
            raw=Raw.SATISFIED,
            evidence_state=ev_state,
            field_name="INCOME_CEILING" if "income" in field_name.lower() else "NUMERIC_CEILING",
            documents_involved=[doc_label],
            evidence=ev,
            message=f"Certified annual income ₹{num_val:,.0f} is within statutory ceiling (₹{cap:,.0f}).",
        )

    if comparator in (">=", "gte", ">", "gt"):
        is_breach = num_val < cap if comparator in (">=", "gte") else num_val <= cap
        if is_breach:
            if ev_state is EvidenceState.UNCERTAIN:
                return PrimitiveResult(
                    raw=Raw.VIOLATED,
                    evidence_state=EvidenceState.UNCERTAIN,
                    field_name="MERIT_PERCENTAGE",
                    documents_involved=[doc_label],
                    evidence=ev,
                    message=f"Aggregate marks ({num_val}%) appears below cutoff ({cap}%), but extraction has low OCR confidence.",
                )
            return PrimitiveResult(
                raw=Raw.VIOLATED,
                evidence_state=ev_state,
                field_name="MERIT_PERCENTAGE",
                documents_involved=[doc_label],
                evidence=ev,
                message=f"Aggregate marks ({num_val}%) is below minimum scheme cutoff ({cap}%).",
            )
        # Satisfied (above cutoff): propagate ev_state (NEVER hardcoded VERIFIED)
        return PrimitiveResult(
            raw=Raw.SATISFIED,
            evidence_state=ev_state,
            field_name="MERIT_PERCENTAGE",
            documents_involved=[doc_label],
            evidence=ev,
            message=f"Aggregate marks ({num_val}%) satisfies the minimum cutoff ({cap}%).",
        )

    return PrimitiveResult(
        raw=Raw.INDETERMINATE,
        evidence_state=EvidenceState.UNCERTAIN,
        message=f"Unsupported comparator '{comparator}' for numeric_cap",
    )


# ---------------------------------------------------------------------------
# 6. numeric_consistency
# ---------------------------------------------------------------------------
def eval_numeric_consistency(
    documents: Dict[Any, ExtractedDocument],
    inputs: Dict[str, Any],
    params: Dict[str, Any],
    context: ExecutionContext,
) -> PrimitiveResult:
    """Evaluate numeric consistency across all configured fields with weakest-evidence propagation."""
    raw_fields = inputs.get("fields") or []
    tolerance = float(params.get("tolerance", 0.0))
    tolerance_pct = params.get("tolerance_pct")
    tol_pct = float(tolerance_pct) if tolerance_pct is not None else 0.0

    collected: List[Tuple[str, ExtractedField, float]] = []

    for fspec in raw_fields:
        doc_name, f_name = parse_field_spec(fspec)
        if not doc_name:
            continue
        doc = get_document(documents, doc_name, context.mismatched_slots)
        if doc and doc.status == "VALID":
            f = get_field_from_doc(doc, f_name)
            if f and f.raw_value:
                val = f.normalized_value
                if val is None:
                    try:
                        val = float(str(f.raw_value).replace(",", "").strip())
                    except (ValueError, TypeError):
                        val = None
                if val is not None:
                    dt = resolve_doc_type(doc_name)
                    collected.append((dt.value if dt else doc_name, f, float(val)))

    if len(collected) < 2:
        return PrimitiveResult(
            raw=Raw.INDETERMINATE,
            evidence_state=EvidenceState.UNCERTAIN,
            message="Insufficient numeric fields extracted for consistency check.",
        )

    field_states = [get_field_evidence_state(f) for _, f, _ in collected]
    weakest = weakest_evidence(field_states)
    is_any_unc = any(s is EvidenceState.UNCERTAIN for s in field_states)

    all_ev = [
        f.provenance
        or EvidenceProvenance(
            document_type=doc_name,
            file_name="",
            extracted_field=f.field_name,
            raw_snippet=f.raw_value,
        )
        for doc_name, f, _ in collected
    ]
    docs_involved = [doc_name for doc_name, _, _ in collected]

    # Compare all pairs
    primary_doc, primary_f, primary_val = collected[0]
    for doc2, f2, val2 in collected[1:]:
        ev_both = [all_ev[0], f2.provenance or EvidenceProvenance(document_type=doc2, file_name="", extracted_field=f2.field_name, raw_snippet=f2.raw_value)]
        diff = abs(primary_val - val2)
        max_allowed = max(tolerance, (primary_val * tol_pct / 100.0) if tol_pct > 0 else 0.0)

        if diff > max(1.0, max_allowed):
            if is_any_unc or primary_f.is_uncertain or f2.is_uncertain:
                return PrimitiveResult(
                    raw=Raw.VIOLATED,
                    match_grade=MatchGrade.AMBIGUOUS,
                    evidence_state=EvidenceState.UNCERTAIN,
                    field_name="INCOME_MISMATCH_UNCERTAIN",
                    documents_involved=[primary_doc, doc2],
                    evidence=ev_both,
                    message=f"Income variance detected: Certified ₹{primary_val:,.0f} vs Declared ₹{val2:,.0f}, but extraction has low OCR confidence. Verify figures visually.",
                )
            return PrimitiveResult(
                raw=Raw.VIOLATED,
                match_grade=MatchGrade.CONFLICT,
                evidence_state=EvidenceState.VERIFIED,
                field_name="INCOME_MISMATCH",
                documents_involved=[primary_doc, doc2],
                evidence=ev_both,
                message=f"Income mismatch: Certified ₹{primary_val:,.0f} vs Declared on form ₹{val2:,.0f}.",
            )

    if is_any_unc:
        return PrimitiveResult(
            raw=Raw.SATISFIED,
            match_grade=MatchGrade.AMBIGUOUS,
            evidence_state=EvidenceState.UNCERTAIN,
            field_name="INCOME_MATCH",
            documents_involved=docs_involved,
            evidence=all_ev[:2],
            message=f"Declared income (₹{primary_val:,.0f}) appears to match, but extraction evidence is uncertain.",
        )

    return PrimitiveResult(
        raw=Raw.SATISFIED,
        match_grade=MatchGrade.EXACT,
        evidence_state=weakest,
        field_name="INCOME_MATCH",
        documents_involved=docs_involved,
        evidence=all_ev[:2],
        message=f"Declared income (₹{primary_val:,.0f}) matches certified income exactly.",
    )


# ---------------------------------------------------------------------------
# 7. age_on
# ---------------------------------------------------------------------------
def eval_age_on(
    documents: Dict[Any, ExtractedDocument],
    inputs: Dict[str, Any],
    params: Dict[str, Any],
    context: ExecutionContext,
) -> PrimitiveResult:
    """Evaluate applicant age as of reference date with weakest-evidence propagation."""
    dob_field = inputs.get("dob_field") or inputs.get("field") or "dob"
    docs = inputs.get("docs") or ["APPLICATION_FORM"]
    ref_date_raw = params.get("reference_date")
    ref_date = context.as_of

    if ref_date_raw is not None:
        if isinstance(ref_date_raw, date):
            ref_date = ref_date_raw
        elif isinstance(ref_date_raw, str):
            try:
                ref_date = date.fromisoformat(ref_date_raw)
            except ValueError:
                pass

    min_age = params.get("min_age")
    max_age = params.get("max_age")

    doc_name = docs[0]
    doc = get_document(documents, doc_name, context.mismatched_slots)
    dt = resolve_doc_type(doc_name)
    doc_label = dt.value if dt else doc_name

    if doc is None or doc.status != "VALID":
        return PrimitiveResult(
            raw=Raw.INDETERMINATE,
            evidence_state=EvidenceState.UNCERTAIN,
            documents_involved=[doc_label],
            message=f"Document '{doc_label}' missing or unextracted for age check.",
        )

    f = get_field_from_doc(doc, dob_field)
    if not f or not f.raw_value:
        return PrimitiveResult(
            raw=Raw.INDETERMINATE,
            evidence_state=EvidenceState.UNCERTAIN,
            documents_involved=[doc_label],
            message=f"DOB field '{dob_field}' not found on {doc_label}.",
        )

    ev_state = get_field_evidence_state(f)
    ev = [
        f.provenance
        or EvidenceProvenance(
            document_type=doc_label,
            file_name=doc.file_path,
            extracted_field=dob_field,
            raw_snippet=f.raw_value,
        )
    ]
    p_dob, st_dob, _ = parse_and_normalize_date(f.raw_value)
    if not p_dob:
        return PrimitiveResult(
            raw=Raw.INDETERMINATE,
            evidence_state=EvidenceState.UNCERTAIN,
            field_name="DOB_PARSE",
            documents_involved=[doc_label],
            evidence=ev,
            message=f"DOB '{f.raw_value}' on {doc_label} cannot be parsed.",
        )

    # Age calculation
    age = (
        ref_date.year
        - p_dob.year
        - int((ref_date.month, ref_date.day) < (p_dob.month, p_dob.day))
    )

    if min_age is not None and age < int(min_age):
        return PrimitiveResult(
            raw=Raw.VIOLATED,
            evidence_state=ev_state,
            field_name="AGE_ELIGIBILITY",
            documents_involved=[doc_label],
            evidence=ev,
            message=f"Applicant age ({age} years as of {ref_date}) is below statutory minimum {min_age} years.",
        )

    if max_age is not None and age > int(max_age):
        return PrimitiveResult(
            raw=Raw.VIOLATED,
            evidence_state=ev_state,
            field_name="AGE_ELIGIBILITY",
            documents_involved=[doc_label],
            evidence=ev,
            message=f"Applicant age ({age} years as of {ref_date}) exceeds statutory maximum {max_age} years.",
        )

    return PrimitiveResult(
        raw=Raw.SATISFIED,
        evidence_state=ev_state,
        field_name="AGE_ELIGIBILITY",
        documents_involved=[doc_label],
        evidence=ev,
        message=f"Applicant age ({age} years as of {ref_date}) satisfies age eligibility criteria.",
    )


# ---------------------------------------------------------------------------
# 8. enum_in
# ---------------------------------------------------------------------------
def eval_enum_in(
    documents: Dict[Any, ExtractedDocument],
    inputs: Dict[str, Any],
    params: Dict[str, Any],
    context: ExecutionContext,
) -> PrimitiveResult:
    """Evaluate categorical field against an approved enumeration with weakest-evidence propagation."""
    field_name = inputs.get("field", "")
    docs = inputs.get("docs") or []
    allowed = params.get("allowed") or params.get("values") or []

    if isinstance(allowed, (str, int, float)):
        allowed = [str(allowed)]
    allowed_set = {str(item).strip().upper() for item in allowed}

    if not docs:
        docs = [d.doc_type.value for d in documents.values() if hasattr(d, "doc_type")]

    doc_name = docs[0]
    doc = get_document(documents, doc_name, context.mismatched_slots)
    dt = resolve_doc_type(doc_name)
    doc_label = dt.value if dt else doc_name

    if doc is None or doc.status != "VALID":
        return PrimitiveResult(
            raw=Raw.INDETERMINATE,
            evidence_state=EvidenceState.UNCERTAIN,
            documents_involved=[doc_label],
            message=f"Document '{doc_label}' missing or unextracted for categorical check.",
        )

    f = get_field_from_doc(doc, field_name)
    if not f or not f.raw_value:
        return PrimitiveResult(
            raw=Raw.INDETERMINATE,
            evidence_state=EvidenceState.UNCERTAIN,
            documents_involved=[doc_label],
            message=f"Field '{field_name}' not found on {doc_label}.",
        )

    ev_state = get_field_evidence_state(f)
    ev = [
        f.provenance
        or EvidenceProvenance(
            document_type=doc_label,
            file_name=doc.file_path,
            extracted_field=field_name,
            raw_snippet=f.raw_value,
        )
    ]
    raw_val = f.raw_value.strip().upper()

    if raw_val not in allowed_set:
        return PrimitiveResult(
            raw=Raw.VIOLATED,
            evidence_state=ev_state,
            field_name="DOMICILE_STATE" if "state" in field_name.lower() else field_name.upper(),
            documents_involved=[doc_label],
            evidence=ev,
            message=f"Applicant domicile state '{raw_val}' does not match required scheme state '{next(iter(allowed_set), '')}'.",
        )

    return PrimitiveResult(
        raw=Raw.SATISFIED,
        evidence_state=ev_state,
        field_name="DOMICILE_STATE" if "state" in field_name.lower() else field_name.upper(),
        documents_involved=[doc_label],
        evidence=ev,
        message=f"Applicant residence state '{raw_val}' matches scheme requirements.",
    )


# ---------------------------------------------------------------------------
# 9. legible
# ---------------------------------------------------------------------------
def eval_legible(
    documents: Dict[Any, ExtractedDocument],
    inputs: Dict[str, Any],
    params: Dict[str, Any],
    context: ExecutionContext,
) -> PrimitiveResult:
    """Evaluate document scan legibility and extraction confidence."""
    slot = inputs.get("slot") or inputs.get("field")
    slots = inputs.get("slots") or inputs.get("docs") or ([slot] if slot else [])
    min_confidence = float(params.get("min_confidence", 0.60))

    if not slots:
        slots = [d.doc_type.value for d in documents.values() if hasattr(d, "doc_type")]

    for slot_name in slots:
        doc = get_document(documents, slot_name, context.mismatched_slots)
        dt = resolve_doc_type(slot_name)
        doc_label = dt.value if dt else slot_name

        if doc is None:
            continue

        if doc.status in ("UNREADABLE", "CORRUPTED"):
            ev = [
                EvidenceProvenance(
                    document_type=doc_label,
                    file_name=doc.file_path,
                    raw_snippet="[UNREADABLE SCAN / INSUFFICIENT EVIDENCE]",
                )
            ]
            return PrimitiveResult(
                raw=Raw.INDETERMINATE,
                evidence_state=EvidenceState.UNCERTAIN,
                field_name="SCAN_QUALITY",
                documents_involved=[doc_label],
                evidence=ev,
                message=f"Document '{doc_label}' is unreadable or corrupted. Clear evidence cannot be extracted.",
            )

        if doc.mean_ocr_confidence is not None and doc.mean_ocr_confidence < min_confidence:
            ev = [
                EvidenceProvenance(
                    document_type=doc_label,
                    file_name=doc.file_path,
                    raw_snippet=f"[LOW OCR CONFIDENCE: {doc.mean_ocr_confidence:.2f}]",
                )
            ]
            return PrimitiveResult(
                raw=Raw.INDETERMINATE,
                evidence_state=EvidenceState.UNCERTAIN,
                field_name="SCAN_QUALITY",
                documents_involved=[doc_label],
                evidence=ev,
                message=f"Document '{doc_label}' scan quality ({doc.mean_ocr_confidence:.2f}) is below confidence threshold ({min_confidence:.2f}).",
            )

    return PrimitiveResult(
        raw=Raw.SATISFIED,
        evidence_state=EvidenceState.VERIFIED,
        field_name="SCAN_QUALITY",
        message="Document legibility and scan quality verified.",
    )


# ---------------------------------------------------------------------------
# CLOSED PRIMITIVE REGISTRY
# ---------------------------------------------------------------------------
PRIMITIVE_REGISTRY: Dict[
    str,
    Callable[
        [Dict[Any, ExtractedDocument], Dict[str, Any], Dict[str, Any], ExecutionContext],
        PrimitiveResult,
    ],
] = {
    "require_document": eval_require_document,
    "field_present": eval_field_present,
    "match_across": eval_match_across,
    "within_validity": eval_within_validity,
    "numeric_cap": eval_numeric_cap,
    "numeric_consistency": eval_numeric_consistency,
    "age_on": eval_age_on,
    "enum_in": eval_enum_in,
    "legible": eval_legible,
}
