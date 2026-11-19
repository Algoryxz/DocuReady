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
    source_lines: List[str] = field(default_factory=list)


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
    "DOCUMENTS TO",
    "SUPPORTING DOCUMENTS",
    "DETAILS",
    "PARTICULARS",
    "INFORMATION",
    "HOLDER",
    "HOLDERS",
    "NUMBER",
    "NO.",
    "NO:",
    "REF",
    "REFERENCE",
    "STATUS",
    "LINKED",
    "SEEDED",
    "SEEDING",
    "MAPPED",
    "ELIGIBILITY",
    "ANNEXURE",
    "SECTION",
    "CLAUSE",
]

# Terms indicating prose, statutory purpose statements, or submission justifications
# that must not be mistaken for authoritative document title headers.
PROSE_NARRATIVE_TERMS = [
    "ISSUED FOR",
    "SUBMITTED FOR",
    "SUBMITTED WITH",
    "SUBMITTED ALONG",
    "ALONG WITH",
    "IN CONNECTION WITH",
    "PURPOSES",
    "PURPOSE OF",
    "APPLYING FOR",
    "BONAFIDE",
    "CERTIFY THAT",
    "HEREBY",
    "THIS IS TO",
    "CERTIFIED THAT",
]

# Terms indicating narrative sentences, finite verb predicates, or descriptive clauses
# that establish a line is running prose/body text rather than an authoritative document title header.
VERB_PREDICATE_TERMS = [
    "HAS",
    "HAVE",
    "HAD",
    "IS",
    "ARE",
    "WAS",
    "WERE",
    "BEEN",
    "BEING",
    "BE",
    "REVIEWED",
    "MENTIONED",
    "DISCUSSED",
    "SUBMITTED",
    "SUBMITS",
    "PROVIDES",
    "PROVIDED",
    "RECEIVED",
    "STATING",
    "STATED",
    "CERTIFIES",
    "CAN",
    "COULD",
    "WILL",
    "WOULD",
    "SHALL",
    "SHOULD",
    "MAY",
    "MIGHT",
    "MUST",
]

NARRATIVE_ADVERBIALS = [
    "EARLIER",
    "PREVIOUSLY",
    "ALREADY",
    "LATER",
    "RECENTLY",
]

NARRATIVE_PHRASES = [
    "BY THE COMMITTEE",
    "BY THE APPLICANT",
    "BY THE STUDENT",
    "FROM THE DISTRICT",
    "IN THE DISCUSSION",
    "FOR THE COMMITTEE",
    "ELIGIBILITY DISCUSSION",
    "COMMITTEE REVIEW",
]

NARRATIVE_SUBJECT_PATTERNS = [
    r"^(?:THE|A|AN|THIS|THAT)\s+(?:APPLICANT|STUDENT|CANDIDATE|COMMITTEE|BOARD|COUNCIL|OFFICER|DISCUSSION|MEETING|RECORD)\b",
    r"^(?:THE|A|AN)\s+[A-Z\s]+\s+(?:IS|ARE|WAS|WERE|HAS|HAD)\b",
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


def is_authoritative_title_line(line: str, doc_type: DocumentType) -> bool:
    """Evaluates whether a text line is an authoritative document title header.

    Rejects:
    - Empty or whitespace lines
    - Running prose / narrative sentences (ending with sentence terminal punctuation: '.', '?', '!')
    - Lines starting with narrative subjects ('The applicant...', 'A caste certificate is...')
    - Lines containing finite verbs/predicates ('has', 'was reviewed', 'is mentioned', 'submitted')
    - Lines containing narrative sentence adverbials ('earlier', 'previously', etc.)
    - Lines containing narrative prepositional/discussion phrases ('in the eligibility discussion', etc.)
    - Lines containing instructional or checklist terms (UPLOAD, ATTACH, REQUIRED, etc.)
    - Lines containing narrative or prose justification terms (ISSUED FOR, SUBMITTED ALONG, etc.)
    - Numbered or bulleted list items (e.g. '1. ', '(a) ', '- ')
    - Form field labels / key-value lines (ending with ':' or having short prefix before ':')
    - Bank statement lines for BANK_PASSBOOK
    """
    line_clean = line.strip().upper()
    if not line_clean:
        return False

    # Terminal sentence punctuation indicates running prose, not a title header
    if line_clean.endswith((".", "?", "!")):
        return False

    # Narrative subject starters (e.g. "The applicant has...", "A caste certificate is...")
    if any(re.search(pat, line_clean) for pat in NARRATIVE_SUBJECT_PATTERNS):
        return False

    # Narrative verbs/predicates forming a sentence
    words = set(re.findall(r"\b[A-Z]+\b", line_clean))
    if any(verb in words for verb in VERB_PREDICATE_TERMS):
        return False

    if any(adv in words for adv in NARRATIVE_ADVERBIALS):
        return False

    if any(phrase in line_clean for phrase in NARRATIVE_PHRASES):
        return False

    if any(ex in line_clean for ex in INSTRUCTION_EXCLUSION_TERMS):
        return False

    if any(p in line_clean for p in PROSE_NARRATIVE_TERMS):
        return False

    if re.match(r"^(\d+[\.\)]|\([a-z\d]+\)|[\-\*•])\s+", line_clean):
        return False

    if line_clean.endswith(":"):
        return False
    if ":" in line_clean:
        parts = line_clean.split(":", 1)
        if len(parts[0].split()) <= 4:
            return False

    if doc_type == DocumentType.BANK_PASSBOOK:
        if "STATEMENT" in line_clean:
            return False

    return True


def classify_document_content(text: str) -> SlotClassification:
    """Classifies document text into one of the 7 DocumentTypes using anchor checks.

    Adheres to:
    - Primary anchors establish candidate identity when found on authoritative title lines.
    - Multiple conflicting primary anchors -> EVIDENCE_UNCERTAIN.
    - No primary anchor -> EVIDENCE_UNCERTAIN (supporting terms alone are insufficient).
    - Bank statement cannot be treated as a bank passbook.
    - Bare numbers, field labels, or instructions cannot establish document identity.
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
    matched_source_lines: Dict[DocumentType, List[str]] = {}
    matched_corroborating: Dict[DocumentType, List[str]] = {}

    lines = [l.strip() for l in t.splitlines() if l.strip()]

    for doc_type, patterns in PRIMARY_ANCHOR_PATTERNS.items():
        if doc_type == DocumentType.BANK_PASSBOOK and is_bank_statement:
            continue

        found_primary: List[str] = []
        found_lines: List[str] = []

        for pat in patterns:
            for line in lines:
                if not is_authoritative_title_line(line, doc_type):
                    continue
                matches = re.findall(pat, line)
                if matches:
                    found_primary.extend(matches)
                    for m in matches:
                        if m not in found_lines:
                            found_lines.append(m)

        if found_primary:
            matched_primary[doc_type] = found_primary
            matched_source_lines[doc_type] = found_lines

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
        all_source_lines = [l for sub in matched_source_lines.values() for l in sub]
        return SlotClassification(
            candidate_type=None,
            is_confident=False,
            is_uncertain=True,
            uncertainty_reason=f"Conflicting primary anchors detected from multiple types: {', '.join(dt.value for dt in conflicting)}",
            primary_anchors=all_anchors,
            corroborating_terms=[],
            conflicting_types=conflicting,
            source_lines=all_source_lines,
        )

    # Exactly one document type matched
    if len(matched_primary) == 1:
        cand_type = next(iter(matched_primary.keys()))
        primary = matched_primary[cand_type]
        corrob = matched_corroborating.get(cand_type, [])
        source_lines = matched_source_lines.get(cand_type, [])
        return SlotClassification(
            candidate_type=cand_type,
            is_confident=True,
            is_uncertain=False,
            uncertainty_reason=None,
            primary_anchors=primary,
            corroborating_terms=corrob,
            conflicting_types=[],
            source_lines=source_lines,
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
        source_lines=[],
    )
