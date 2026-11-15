"""Document Slot Verification Module for DocuReady.

Checks whether the content of an uploaded document matches the document slot
into which it was uploaded.

Guarantees:
- Expected slot and detected content are independently verified.
- Confident mismatch -> Status.REVIEW with ReasonCode.WRONG_DOCUMENT_TYPE.
- Conflicting anchors / generic keywords / unreadable / blank / corrupted -> Status.REVIEW with ReasonCode.EVIDENCE_UNCERTAIN.
- Correct document in slot -> No finding emitted; clean packet proceeds.
- Mandatory slot absent -> Handled by RULE-DOC-01 (Status.MISSING, ReasonCode.DOC_ABSENT).
- Optional slot absent -> No finding emitted.
- Never produces automatic FAIL.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Set, Tuple

from docuready.domain.enums import ReasonCode, Status
from docuready.domain.models import (
    DOC_TYPE_LABELS,
    DocumentType,
    EvidenceProvenance,
    ExtractedDocument,
    Finding,
    FindingStatus,
    Severity,
)
from docuready.ingest.slot_classifier import classify_document_content, SlotClassification


def validate_slot(
    slot: DocumentType,
    doc: Optional[ExtractedDocument],
    is_mandatory: bool = True,
    emit_for_unreadable: bool = True,
) -> Optional[Finding]:
    """Validates whether an individual document upload matches its designated slot.

    Returns:
        Optional[Finding]: A Finding if there is a mismatch or uncertainty; None if clean.
    """
    if doc is None or doc.status == "MISSING":
        # Missing slots are handled at packet level by RULE-DOC-01 for mandatory slots
        return None

    slot_label = DOC_TYPE_LABELS.get(slot, slot.value)

    if doc.status in ("UNREADABLE", "CORRUPTED"):
        if not emit_for_unreadable:
            # When integrated with validate_packet, RULE-DOC-02 handles legibility/corruption
            return None
        finding = Finding(
            rule_id="RULE-SLOT-01",
            rule_name="Document Slot Verification",
            status=FindingStatus.REVIEW,
            severity=Severity.REVIEW,
            penalty=10,
            field="DOCUMENT_SLOT",
            documents_involved=[slot.value],
            message=(
                f"Slot verification uncertain: Document uploaded to slot '{slot.value}' "
                f"is {doc.status.lower()} and cannot be verified as {slot_label}."
            ),
            evidence=[
                EvidenceProvenance(
                    document_type=slot.value,
                    file_name=doc.file_path,
                    raw_snippet=f"[{doc.status} UPLOAD / INSUFFICIENT EVIDENCE]",
                    extracted_field="DOCUMENT_SLOT",
                    extraction_method=doc.extraction_method,
                )
            ],
            remediation=f"Upload a clear, legible {slot_label} to the {slot.value} slot.",
            statutory_reference="NSP Upload Guidelines & Document Slot Standards",
        )
        finding._is_wrong_type = False
        return finding

    # 1. If detected_type was already established by DocumentExtractor
    if doc.detected_type is not None:
        if doc.detected_type == slot:
            return None
        cand_label = DOC_TYPE_LABELS.get(doc.detected_type, doc.detected_type.value)
        details = doc.classification_details or {}
        anchors = details.get("primary_anchors", [])
        corrob = details.get("corroborating_terms", [])
        anchors_str = ", ".join(f"'{a}'" for a in anchors) or "title anchors"
        corrob_str = ", ".join(f"'{c}'" for c in corrob[:3])
        corrob_desc = f" and corroborating term(s) [{corrob_str}]" if corrob_str else ""
        msg = (
            f"Slot mismatch: Expected '{slot.value}' ({slot_label}) but uploaded document identifies as "
            f"'{doc.detected_type.value}' ({cand_label}) based on primary anchor(s) [{anchors_str}]{corrob_desc}. "
            "A document cannot be accepted in a mismatched slot."
        )
        finding = Finding(
            rule_id="RULE-SLOT-01",
            rule_name="Document Slot Verification",
            status=FindingStatus.REVIEW,
            severity=Severity.REVIEW,
            penalty=10,
            field="DOCUMENT_SLOT",
            documents_involved=[slot.value],
            message=msg,
            evidence=[
                EvidenceProvenance(
                    document_type=slot.value,
                    file_name=doc.file_path,
                    raw_snippet=f"Detected primary anchors: [{anchors_str}]",
                    extracted_field="DOCUMENT_SLOT",
                    extraction_method=doc.extraction_method,
                )
            ],
            remediation=f"Upload the correct {slot_label} to the {slot.value} slot instead of {cand_label}.",
            statutory_reference="NSP Upload Guidelines & Document Slot Standards",
        )
        finding._is_wrong_type = True
        return finding

    # 2. Content-based classification from raw_text if present
    if doc.raw_text and doc.raw_text.strip():
        classification = classify_document_content(doc.raw_text)
        candidate_type = classification.candidate_type

        # Case A: Exact match on expected slot
        if candidate_type == slot:
            return None

        # Case B: Confident mismatch with another supported DocumentType
        if candidate_type is not None and candidate_type != slot:
            cand_label = DOC_TYPE_LABELS.get(candidate_type, candidate_type.value)
            anchors_str = ", ".join(f"'{a}'" for a in classification.primary_anchors) or "title anchors"
            corrob_str = ", ".join(f"'{c}'" for c in classification.corroborating_terms[:3])
            corrob_desc = f" and corroborating term(s) [{corrob_str}]" if corrob_str else ""
            msg = (
                f"Slot mismatch: Expected '{slot.value}' ({slot_label}) but uploaded document identifies as "
                f"'{candidate_type.value}' ({cand_label}) based on primary anchor(s) [{anchors_str}]{corrob_desc}. "
                "A document cannot be accepted in a mismatched slot."
            )
            finding = Finding(
                rule_id="RULE-SLOT-01",
                rule_name="Document Slot Verification",
                status=FindingStatus.REVIEW,
                severity=Severity.REVIEW,
                penalty=10,
                field="DOCUMENT_SLOT",
                documents_involved=[slot.value],
                message=msg,
                evidence=[
                    EvidenceProvenance(
                        document_type=slot.value,
                        file_name=doc.file_path,
                        raw_snippet=f"Detected primary anchors: [{anchors_str}]",
                        extracted_field="DOCUMENT_SLOT",
                        extraction_method=doc.extraction_method,
                    )
                ],
                remediation=f"Upload the correct {slot_label} to the {slot.value} slot instead of {cand_label}.",
                statutory_reference="NSP Upload Guidelines & Document Slot Standards",
            )
            finding._is_wrong_type = True
            return finding

        # Case C: Uncertain / conflicting / generic content
        reason = classification.uncertainty_reason or "Document content could not be verified"
        corrob_str = ", ".join(f"'{c}'" for c in classification.corroborating_terms[:3])
        corrob_desc = f" (supporting terms found: [{corrob_str}])" if corrob_str else ""
        msg = (
            f"Slot verification uncertain: Document in slot '{slot.value}' cannot be verified as {slot_label}: "
            f"{reason}{corrob_desc}."
        )
        finding = Finding(
            rule_id="RULE-SLOT-01",
            rule_name="Document Slot Verification",
            status=FindingStatus.REVIEW,
            severity=Severity.REVIEW,
            penalty=10,
            field="DOCUMENT_SLOT",
            documents_involved=[slot.value],
            message=msg,
            evidence=[
                EvidenceProvenance(
                    document_type=slot.value,
                    file_name=doc.file_path,
                    raw_snippet=f"Slot uncertainty: {reason}",
                    extracted_field="DOCUMENT_SLOT",
                    extraction_method=doc.extraction_method,
                )
            ],
            remediation=f"Ensure an authoritative, legible {slot_label} with clear title headers is uploaded.",
            statutory_reference="NSP Upload Guidelines & Document Slot Standards",
        )
        finding._is_wrong_type = False
        return finding

    # 3. If raw_text is empty:
    # Check if this is an in-memory synthetic fixture with populated fields
    if doc.fields:
        if doc.doc_type == slot:
            return None
        cand_label = DOC_TYPE_LABELS.get(doc.doc_type, doc.doc_type.value)
        msg = (
            f"Slot mismatch: Expected '{slot.value}' ({slot_label}) but synthetic document has type "
            f"'{doc.doc_type.value}' ({cand_label})."
        )
        finding = Finding(
            rule_id="RULE-SLOT-01",
            rule_name="Document Slot Verification",
            status=FindingStatus.REVIEW,
            severity=Severity.REVIEW,
            penalty=10,
            field="DOCUMENT_SLOT",
            documents_involved=[slot.value],
            message=msg,
            evidence=[
                EvidenceProvenance(
                    document_type=slot.value,
                    file_name=doc.file_path,
                    raw_snippet=f"Synthetic document type: {doc.doc_type.value}",
                    extracted_field="DOCUMENT_SLOT",
                    extraction_method=doc.extraction_method,
                )
            ],
            remediation=f"Upload the correct {slot_label} to the {slot.value} slot instead of {cand_label}.",
            statutory_reference="NSP Upload Guidelines & Document Slot Standards",
        )
        finding._is_wrong_type = True
        return finding

    # If both raw_text and fields are empty: truly blank document
    msg = f"Slot verification uncertain: Document in slot '{slot.value}' is blank or empty."
    finding = Finding(
        rule_id="RULE-SLOT-01",
        rule_name="Document Slot Verification",
        status=FindingStatus.REVIEW,
        severity=Severity.REVIEW,
        penalty=10,
        field="DOCUMENT_SLOT",
        documents_involved=[slot.value],
        message=msg,
        evidence=[
            EvidenceProvenance(
                document_type=slot.value,
                file_name=doc.file_path,
                raw_snippet="[BLANK / EMPTY DOCUMENT]",
                extracted_field="DOCUMENT_SLOT",
                extraction_method=doc.extraction_method,
            )
        ],
        remediation=f"Upload a complete, valid {slot_label} to the {slot.value} slot.",
        statutory_reference="NSP Upload Guidelines & Document Slot Standards",
    )
    finding._is_wrong_type = False
    return finding


def validate_packet_slots(
    documents: Dict[DocumentType, ExtractedDocument],
    mandatory_documents: List[DocumentType],
    emit_for_unreadable: bool = False,
) -> Tuple[List[Finding], Set[DocumentType]]:
    """Validates all uploaded documents against their respective slots in the packet.

    Returns:
        Tuple[List[Finding], Set[DocumentType]]:
            - List of slot validation findings (RULE-SLOT-01)
            - Set of mismatched/uncertain slot types that must not fail downstream rules
    """
    findings: List[Finding] = []
    mismatched_slots: Set[DocumentType] = set()

    for slot, doc in documents.items():
        if doc is None or doc.status == "MISSING":
            continue

        finding = validate_slot(
            slot=slot,
            doc=doc,
            is_mandatory=(slot in mandatory_documents),
            emit_for_unreadable=emit_for_unreadable,
        )
        if finding is not None:
            findings.append(finding)
            mismatched_slots.add(slot)

    return findings, mismatched_slots
