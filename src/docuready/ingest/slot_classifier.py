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
        r"\b(?:UNIQUE\s+IDENTIFICATION\s+AUTHORITY|AADHAAR\s+CARD|MERA\s+AADHAAR|UIDAI)\b",
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
        r"\bAADHAAR\s+NUMBER\b",
        r"\bGOVERNMENT\s+OF\s+INDIA\b",
    ],
}

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

    for doc_type, patterns in PRIMARY_ANCHOR_PATTERNS.items():
        found_primary: List[str] = []

        if doc_type == DocumentType.BANK_PASSBOOK:
            # Special protection: bank statements cannot be classified as passbooks
            if not is_bank_statement:
                for pat in patterns:
                    matches = re.findall(pat, t)
                    if matches:
                        # Exclude 'SAVINGS BANK' if 'STATEMENT' is present on the same line
                        if pat == r"\bSAVINGS\s+BANK\b":
                            lines_with_sb = [line for line in t.split("\n") if "SAVINGS BANK" in line]
                            valid_lines = [l for l in lines_with_sb if "STATEMENT" not in l]
                            if valid_lines:
                                found_primary.extend(matches)
                        else:
                            found_primary.extend(matches)

        elif doc_type == DocumentType.AADHAAR:
            # Special protection: check strong identity anchors first
            for pat in patterns:
                matches = re.findall(pat, t)
                if matches:
                    found_primary.extend(matches)
            # If bare AADHAAR appears, verify it is not in bank passbook DBT/seeding context
            if not found_primary and "AADHAAR" in t:
                for line in t.split("\n"):
                    if "AADHAAR" in line:
                        if any(term in line for term in ["SEEDING", "MAPPED", "LINKED", "DBT", "NPCI", "BANK"]):
                            continue
                        found_primary.append("AADHAAR")
                        break

        else:
            for pat in patterns:
                matches = re.findall(pat, t)
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
