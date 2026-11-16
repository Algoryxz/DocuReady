"""Slot classification and anchor verification for DocuReady.

Implements lightweight anchor-keyword sanity checks to verify that an uploaded
document matches the document slot into which it was uploaded.

This is a deterministic anchor check, not an automatic ML classifier.
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set, Any

from docuready.domain.models import DocumentType


@dataclass
class SlotClassification:
    """Detailed result of content-based document slot classification."""

    candidate_type: Optional[DocumentType] = None
    is_confident: bool = False
    is_uncertain: bool = False
    uncertainty_reason: Optional[str] = None
    primary_anchors: List[str] = field(default_factory=list)
    corroborating_terms: List[str] = field(default_factory=list)
    conflicting_types: List[DocumentType] = field(default_factory=list)


# Primary title anchors per document slot
PRIMARY_ANCHOR_PATTERNS: Dict[DocumentType, List[str]] = {
    DocumentType.INCOME_CERT: [
        r"\bINCOME\s+CERTIFICATE\b(?!\s*(?:REFERENCE|REF\b|NO\b|NUMBER))",
    ],
    DocumentType.CASTE_CERT: [
        r"\b(?:CASTE\s+CERTIFICATE|COMMUNITY\s+CERTIFICATE|COMMUNITY\s*/\s*CASTE)\b(?!\s*(?:REFERENCE|REF\b|NO\b|NUMBER))",
    ],
    DocumentType.RESIDENCE_CERT: [
        r"\b(?:RESIDENCE\s+CERTIFICATE|DOMICILE\s+CERTIFICATE|RESIDENT\s*/\s*DOMICILE)\b(?!\s*(?:REFERENCE|REF\b|NO\b|NUMBER))",
    ],
    DocumentType.MARKSHEET: [
        r"\b(?:MARKSHEET|MARKS\s+STATEMENT|HIGH\s+SCHOOL\s+CERTIFICATE|BOARD\s+OF\s+SECONDARY)\b",
    ],
    DocumentType.BANK_PASSBOOK: [
        r"\bPASSBOOK\b",
        r"\bSAVINGS\s+BANK\b",
    ],
    DocumentType.APPLICATION_FORM: [
        r"\b(?:SCHOLARSHIP\s+APPLICATION|COMMON\s+SCHOLARSHIP\s+PORTAL|APPLICATION\s+ACKNOWLEDGEMENT|APPLICATION\s+ACKNOWLEDGMENT)\b",
    ],
    DocumentType.AADHAAR: [
        r"\b(?:UNIQUE\s+IDENTIFICATION\s+AUTHORITY\s+OF\s+INDIA|UNIQUE\s+IDENTIFICATION\s+AUTHORITY|AADHAAR\s+CARD|MERA\s+AADHAAR|UIDAI)\b",
    ],
}

# Corroborating terms per document slot
CORROBORATING_PATTERNS: Dict[DocumentType, List[str]] = {
    DocumentType.INCOME_CERT: [
        r"\bANNUAL\s+(?:FAMILY\s+)?INCOME\b",
        r"\bFAMILY\s+INCOME\b",
        r"\bCERTIFICATE\s+(?:NO|NUMBER)\b",
        r"\bISSUE\s+DATE\b",
        r"\b(?:TAHSILDAR|REVENUE\s+OFFICER|ISSUING\s+AUTHORITY)\b",
    ],
    DocumentType.CASTE_CERT: [
        r"\b(?:CASTE|COMMUNITY|SOCIAL|RECOGNIZED)\s+CATEGORY\b",
        r"\b(?:SC|ST|OBC|SEBC)\b",
        r"\bCERTIFICATE\s+(?:NO|NUMBER)\b",
        r"\b(?:SUB-DIVISIONAL\s+MAGISTRATE|TAHSILDAR|ISSUING\s+AUTHORITY)\b",
    ],
    DocumentType.RESIDENCE_CERT: [
        r"\bPERMANENT\s+RESIDENT\b",
        r"\bRESIDENTIAL\s+ADDRESS\b",
        r"\bDISTRICT\b",
        r"\b(?:TERRITORIAL\s+JURISDICTION|STATE\s+OF)\b",
        r"\bCERTIFICATE\s+(?:NO|NUMBER)\b",
    ],
    DocumentType.MARKSHEET: [
        r"\b(?:EXAMINATION|EXAM)\b",
        r"\bROLL\s+(?:NO|NUMBER)\b",
        r"\b(?:SUBJECT|MARKS\s+OBTAINED|MAX\s+MARKS)\b",
        r"\b(?:TOTAL\s+MARKS|AGGREGATE)\b",
        r"\b(?:PERCENTAGE|GRADE)\b",
    ],
    DocumentType.BANK_PASSBOOK: [
        r"\bACCOUNT\s+HOLDER\b",
        r"\b(?:ACCOUNT\s+NUMBER|A/C\s+NO)\b",
        r"\bIFSC\b",
        r"\bBRANCH\b",
        r"\bBANK\b",
    ],
    DocumentType.APPLICATION_FORM: [
        r"\bAPPLICATION\s+(?:ID|NO|NUMBER)\b",
        r"\bREGISTRATION\s+NUMBER\b",
        r"\bSCHEME\s+NAME\b",
        r"\b(?:APPLICANT\s+DETAILS|APPLICANT\s+DEMOGRAPHICS)\b",
        r"\bACADEMIC\s+SESSION\b",
    ],
    DocumentType.AADHAAR: [
        r"\bUIDAI\b",
        r"\bAADHAAR\s+(?:NUMBER|NO)\b",
        r"\bAADHAAR\b",
        r"\bGOVERNMENT\s+OF\s+INDIA\b",
        r"\bENROLMENT\s+(?:NO|NUMBER)\b",
    ],
}

# Terms indicating instructions, checklists, upload requirements, or attachments
# that must not be mistaken for authoritative document title headers.
INSTRUCTION_EXCLUSION_TERMS = [
    "REQUIRED",
    "REQUIREMENT",
    "REQUIREMENTS",
    "UPLOAD",
    "UPLOADING",
    "UPLOADED",
    "ATTACH",
    "ATTACHED",
    "ATTACHMENT",
    "ATTACHMENTS",
    "ENCLOSE",
    "ENCLOSED",
    "ENCLOSURE",
    "ENCLOSURES",
    "SUBMIT",
    "SUBMISSION",
    "SUBMITTED",
    "MANDATORY",
    "CHECKLIST",
    "COPY OF",
    "COPIES OF",
    "DETAILS OF",
    "PARTICULARS OF",
    "ENCLOSED CERTIFICATE",
    "DOCUMENTS ENCLOSED",
    "DOCUMENTS TO ATTACH",
    "DOCUMENTS TO BE ATTACHED",
    "SUPPORTING DOCUMENTS",
    "ELIGIBILITY",
    "ANNEXURE",
]

BANK_STATEMENT_INDICATORS = [
    "BANK STATEMENT",
    "ACCOUNT STATEMENT",
    "STATEMENT OF ACCOUNT",
    "STATEMENT OF TRANSACTIONS",
    "TRANSACTION HISTORY",
    "TRANSACTION STATEMENT",
    "STATEMENT PERIOD",
    "CLOSING BALANCE",
]


def classify_document_content(text: str) -> SlotClassification:
    """Classifies document text into one of the 7 DocumentTypes using anchor checks.

    Adheres to:
    - Primary anchors establish candidate identity.
    - Multiple conflicting primary anchors -> EVIDENCE_UNCERTAIN.
    - No primary anchor -> EVIDENCE_UNCERTAIN (supporting terms alone are insufficient).
    - Bank statement cannot be treated as a bank passbook.
    - Bare 12-digit numbers or QR codes without identity anchors cannot identify Aadhaar.
    """
    if not text or not text.strip():
        return SlotClassification(
            candidate_type=None,
            is_confident=False,
            is_uncertain=True,
            uncertainty_reason="Document text is empty or blank",
        )

    t = text.upper()

    # Check for explicit bank statement indicators
    is_bank_statement = any(stmt in t for stmt in BANK_STATEMENT_INDICATORS)

    matched_primary: Dict[DocumentType, List[str]] = {}
    matched_corroborating: Dict[DocumentType, List[str]] = {}

    lines = [l.strip() for l in t.splitlines() if l.strip()]

    # Detect whether document contains application form title anchors
    has_app_form_title = any(
        re.search(pat, t) for pat in PRIMARY_ANCHOR_PATTERNS[DocumentType.APPLICATION_FORM]
    )

    for doc_type, patterns in PRIMARY_ANCHOR_PATTERNS.items():
        found_primary: List[str] = []

        if doc_type == DocumentType.BANK_PASSBOOK:
            # Special protection: bank statements cannot be classified as passbooks
            if not is_bank_statement:
                for pat in patterns:
                    for line in lines:
                        if pat == r"\bSAVINGS\s+BANK\b" and "STATEMENT" in line:
                            continue
                        matches = re.findall(pat, line)
                        if matches:
                            found_primary.extend(matches)

        elif doc_type == DocumentType.AADHAAR:
            # Specific identity-document context required (AADHAAR CARD, UIDAI, etc.)
            # Exclude instructional upload references e.g. "Upload Aadhaar Card"
            for pat in patterns:
                for line in lines:
                    if any(term in line for term in INSTRUCTION_EXCLUSION_TERMS):
                        continue
                    matches = re.findall(pat, line)
                    if matches:
                        found_primary.extend(matches)

        elif doc_type in (DocumentType.INCOME_CERT, DocumentType.CASTE_CERT, DocumentType.RESIDENCE_CERT):
            # Certificate primary anchors must be authoritative header titles, not
            # body-text references, checklist items, or upload instructions.
            for pat in patterns:
                for idx, line in enumerate(lines):
                    if any(term in line for term in INSTRUCTION_EXCLUSION_TERMS):
                        continue
                    if re.match(r"^(\d+[\.\)]|\([a-z\d]+\)|[\-\*•])\s+", line):
                        continue
                    if has_app_form_title and idx > 3:
                        # In an application form, subordinate certificate mentions are not titles
                        continue
                    matches = re.findall(pat, line)
                    if matches:
                        found_primary.extend(matches)

        elif doc_type == DocumentType.MARKSHEET:
            for pat in patterns:
                for line in lines:
                    if any(term in line for term in INSTRUCTION_EXCLUSION_TERMS):
                        continue
                    if re.match(r"^(\d+[\.\)]|\([a-z\d]+\)|[\-\*•])\s+", line):
                        continue
                    if has_app_form_title:
                        continue
                    matches = re.findall(pat, line)
                    if matches:
                        found_primary.extend(matches)

        else:
            # Application form
            for pat in patterns:
                for line in lines:
                    matches = re.findall(pat, line)
                    if matches:
                        found_primary.extend(matches)

        if found_primary:
            matched_primary[doc_type] = found_primary

    # Collect corroborating terms
    for doc_type, patterns in CORROBORATING_PATTERNS.items():
        found_corr: List[str] = []
        for pat in patterns:
            matches = re.findall(pat, t)
            if matches:
                found_corr.extend(matches)
        if found_corr:
            matched_corroborating[doc_type] = found_corr

    # Conflicting anchors: multiple different document types matched
    if len(matched_primary) > 1:
        conflicting = list(matched_primary.keys())
        all_anchors = [a for sub in matched_primary.values() for a in sub]
        return SlotClassification(
            candidate_type=None,
            is_confident=False,
            is_uncertain=True,
            uncertainty_reason=f"Conflicting primary anchors detected from multiple types: {', '.join(dt.value for dt in conflicting)}",
            primary_anchors=all_anchors,
            conflicting_types=conflicting,
        )

    # Exactly one document type matched
    if len(matched_primary) == 1:
        cand_type = next(iter(matched_primary.keys()))
        primary = matched_primary[cand_type]
        corrob = matched_corroborating.get(cand_type, [])
        return SlotClassification(
            candidate_type=cand_type,
            is_confident=True,
            is_uncertain=False,
            uncertainty_reason=None,
            primary_anchors=primary,
            corroborating_terms=corrob,
            conflicting_types=[],
        )

    # Zero primary anchors matched
    # Collect any corroborating terms detected across all types
    all_corrob = [c for sub in matched_corroborating.values() for c in sub]

    if is_bank_statement:
        reason = "Document identifies as a bank statement, which cannot be accepted as a bank passbook"
    elif all_corrob:
        reason = (
            f"Corroborating terms ({len(all_corrob)}) present but authoritative primary title anchors "
            "are missing; supporting terms alone cannot establish document identity"
        )
    else:
        reason = "No recognized document title anchors or specific identifiers detected; generic or unreadable content"

    return SlotClassification(
        candidate_type=None,
        is_confident=False,
        is_uncertain=True,
        uncertainty_reason=reason,
        primary_anchors=[],
        corroborating_terms=all_corrob,
        conflicting_types=[],
    )
