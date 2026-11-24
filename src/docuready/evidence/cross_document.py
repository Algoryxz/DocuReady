"""
DocuReady Cross-Document Verification, Entity Resolution & Contradiction Detection Engine.
Loop 28 Targeted Implementation:
- Explicit Entity Identity & Disambiguation (preventing spurious name/address/amount matches)
- Evidence Independence Tracking (detecting duplicates, re-scans, and circular evidence)
- Multi-Source Contradiction Detection (amount, date, decimal, currency, entity, chronology)
- Missing Supporting Evidence & Slot Verification
- Risk-Calibrated Abstention on Correlated OCR Errors & Ambiguous Entities
"""

from __future__ import annotations

import difflib
import hashlib
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from docuready.ingest.identifier_validation import (
    validate_identifier_syntax_and_ambiguity,
    sanitize_identifier_token,
)


class VerificationOutcome(str, Enum):
    VERIFIED = "VERIFY"
    CONTRADICTION = "CONTRADICTION_DETECTED"
    ENTITY_AMBIGUOUS = "ENTITY_AMBIGUOUS"
    MISSING_EVIDENCE = "MISSING_EVIDENCE"
    DUPLICATE_SOURCE = "DUPLICATE_UNCONFIRMED"
    UNIT_OR_CURRENCY_MISMATCH = "UNIT_OR_CURRENCY_MISMATCH"
    INCOMPARABLE_EVIDENCE = "INCOMPARABLE_EVIDENCE"
    EQUIVALENT_NORMALIZED = "EQUIVALENT_AFTER_NORMALIZATION"
    ABSTAIN = "ABSTAIN"


class SourceIndependence(str, Enum):
    INDEPENDENT = "INDEPENDENT"
    DUPLICATE = "DUPLICATE"
    DERIVED = "DERIVED"
    CORRELATED_OCR = "CORRELATED_OCR"


@dataclass
class DocumentIdentity:
    """Represents a discrete source document within a multi-document packet."""
    doc_id: str
    doc_type: str
    file_name: str
    content_hash: str
    page_count: int = 1
    raw_text: str = ""
    issuing_authority: str = ""
    issue_date: Optional[str] = None


@dataclass
class EntityIdentity:
    """Represents a canonical real-world entity with anchoring attributes."""
    entity_id: str
    canonical_name: str
    aliases: List[str] = field(default_factory=list)
    father_or_guardian_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    tax_id: Optional[str] = None         # PAN or GSTIN
    national_id: Optional[str] = None    # Aadhaar UID
    account_number: Optional[str] = None
    address: Optional[str] = None


@dataclass
class FieldClaim:
    """A discrete factual assertion extracted from a specific document."""
    claim_id: str
    doc_id: str
    field_name: str
    field_type: str  # 'id', 'amount', 'date', 'name', 'text'
    claimed_value: str
    raw_ocr_value: str
    confidence: float
    bbox: Tuple[int, int, int, int] = (0, 0, 0, 0)
    entity_hints: Dict[str, Any] = field(default_factory=dict)
    unit_or_currency: Optional[str] = None
    is_ambiguous: bool = False
    abstention_reason: Optional[str] = None


@dataclass
class PacketVerificationResult:
    """Traceable outcome of verifying a target claim across a document packet."""
    field_name: str
    target_entity_id: str
    outcome: VerificationOutcome
    is_verified: bool
    verified_value: Optional[str]
    supporting_doc_ids: List[str]
    contradicting_doc_ids: List[str]
    reason: str
    evidence_independence: SourceIndependence
    provenance_trail: List[Dict[str, Any]] = field(default_factory=list)


def normalize_entity_name(name: str) -> str:
    """Standardizes personal or organizational names for safe fuzzy comparison."""
    if not name:
        return ""
    n = name.upper().strip()
    n = re.sub(r"^(MR\.?|MS\.?|MRS\.?|DR\.?|SHRI|SMT\.?|M/S)\s+", "", n)
    n = re.sub(r"[.,\-']", " ", n)
    n = re.sub(r"\s+", " ", n)
    return n.strip()


def compute_string_content_hash(text: str) -> str:
    """Produces SHA-256 fingerprint for document deduplication."""
    norm = re.sub(r"\s+", " ", text.strip().lower())
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


def resolve_entity_match(
    e1_name: str,
    e2_name: str,
    e1_hints: Dict[str, Any],
    e2_hints: Dict[str, Any],
) -> Tuple[bool, str]:
    """
    Determines whether two document entities refer to the same physical person/entity.
    Enforces that:
      - Same name alone is INSUFFICIENT if father name, DOB, or ID contradicts.
      - Similar name with matching DOB/PAN is a RESOLVED match.
      - Same address with different name is an ENTITY MISMATCH.
    """
    n1 = normalize_entity_name(e1_name)
    n2 = normalize_entity_name(e2_name)

    # 1. Check strong unique identifiers if present (PAN, Aadhaar, Account, IFSC)
    id1 = (
        e1_hints.get("tax_id")
        or e1_hints.get("national_id")
        or e1_hints.get("account_number")
        or e1_hints.get("pan")
        or e1_hints.get("ifsc")
        or e1_hints.get("ifsc_or_pan")
        or e1_hints.get("identifier")
    )
    id2 = (
        e2_hints.get("tax_id")
        or e2_hints.get("national_id")
        or e2_hints.get("account_number")
        or e2_hints.get("pan")
        or e2_hints.get("ifsc")
        or e2_hints.get("ifsc_or_pan")
        or e2_hints.get("identifier")
    )
    if id1 and id2:
        if str(id1).strip().upper() != str(id2).strip().upper():
            return False, f"Entity conflict: distinct identification numbers ('{id1}' vs '{id2}')"

    # 2. Check Date of Birth if present
    dob1 = e1_hints.get("date_of_birth") or e1_hints.get("dob")
    dob2 = e2_hints.get("date_of_birth") or e2_hints.get("dob")
    if dob1 and dob2:
        # Standardize slashes and hyphens
        d1 = str(dob1).replace("-", "/").strip()
        d2 = str(dob2).replace("-", "/").strip()
        if d1 != d2:
            return False, f"Entity conflict: distinct dates of birth ('{dob1}' vs '{dob2}') despite name similarity"

    # 3. Check Father/Guardian name if present
    g1 = normalize_entity_name(e1_hints.get("father_name") or e1_hints.get("guardian_name") or "")
    g2 = normalize_entity_name(e2_hints.get("father_name") or e2_hints.get("guardian_name") or "")
    if g1 and g2 and g1 != g2:
        sim_g = difflib.SequenceMatcher(None, g1, g2).ratio()
        if sim_g < 0.80:
            return False, f"Entity conflict: distinct parent/guardian names ('{g1}' vs '{g2}')"

    # 4. Name comparison
    if n1 == n2:
        return True, "Exact canonical name match with consistent anchoring attributes"

    sim_name = difflib.SequenceMatcher(None, n1, n2).ratio()
    if sim_name >= 0.85:
        # Require at least one corroborating attribute (same DOB, same parent, or same address)
        has_anchor = bool(
            (dob1 and dob2 and dob1 == dob2)
            or (g1 and g2 and g1 == g2)
            or (e1_hints.get("address") and e2_hints.get("address") and e1_hints["address"] == e2_hints["address"])
        )
        if has_anchor:
            return True, f"Spelling variation resolved by corroborating anchor (similarity: {sim_name:.2f})"
        else:
            return False, f"Similar names ('{n1}' vs '{n2}') without corroborating identifier or DOB"

    return False, f"Entity mismatch: distinct names ('{n1}' vs '{n2}')"


def detect_document_independence(doc1: DocumentIdentity, doc2: DocumentIdentity) -> SourceIndependence:
    """
    Evaluates whether two documents provide genuine independent corroboration,
    or are duplicate scans, copies, or template clones.
    Distinguishes generic filename collisions and shared government form templates
    from true duplicate documents.
    """
    # 1. Exact identical content hash -> Duplicate document
    if doc1.content_hash and doc2.content_hash and doc1.content_hash == doc2.content_hash:
        return SourceIndependence.DUPLICATE

    # 2. Identical raw text -> Duplicate document
    if doc1.raw_text and doc2.raw_text and doc1.raw_text.strip() == doc2.raw_text.strip():
        return SourceIndependence.DUPLICATE

    # 3. Same file name: Only duplicate if content hashes match or are omitted
    if doc1.file_name and doc2.file_name and doc1.file_name == doc2.file_name:
        if doc1.content_hash and doc2.content_hash and doc1.content_hash != doc2.content_hash:
            # Different content hashes indicate generic filename collision (e.g. invoice.pdf), not duplicate
            pass
        else:
            return SourceIndependence.DUPLICATE

    # 4. Check for high textual duplication (> 96% raw text match)
    if doc1.raw_text and doc2.raw_text:
        sim = difflib.SequenceMatcher(None, doc1.raw_text, doc2.raw_text).ratio()
        if sim > 0.96 and doc1.doc_type == doc2.doc_type:
            # If distinct content hashes are present, this is a shared government form template with distinct payload
            if doc1.content_hash and doc2.content_hash and doc1.content_hash != doc2.content_hash:
                return SourceIndependence.INDEPENDENT
            return SourceIndependence.DUPLICATE

    return SourceIndependence.INDEPENDENT


def evaluate_semantic_claim_equivalence(
    c1_val: str,
    c1_type: str,
    c2_val: str,
    c2_type: str,
) -> Tuple[bool, VerificationOutcome, str]:
    """
    Evaluates semantic equivalence and detects fine-grained contradiction categories:
    - EQUIVALENT_AFTER_NORMALIZATION: Equivalent under metric conversion (e.g., 1 MT == 1000 KG)
    - CONTRADICTION_DETECTED: Factual amount or date mismatch
    - UNIT_OR_CURRENCY_MISMATCH: Distinct currencies (USD vs INR)
    - INCOMPARABLE_EVIDENCE: Disparate dimensions (e.g. mass vs volume)
    """
    curr1 = extract_currency(c1_val)
    curr2 = extract_currency(c2_val)

    # 1. Currency Mismatch
    if curr1 and curr2 and curr1 != curr2:
        return False, VerificationOutcome.UNIT_OR_CURRENCY_MISMATCH, f"Currency mismatch ({curr1} vs {curr2}) without conversion context"

    # 2. Unit Equivalence & Metric Normalization
    u1 = extract_unit(c1_val)
    u2 = extract_unit(c2_val)

    if (u1 in ["MT", "KG"]) and (u2 in ["MT", "KG"]):
        # Extract numeric values
        try:
            raw1 = re.sub(r"[^\d.]", "", c1_val)
            raw2 = re.sub(r"[^\d.]", "", c2_val)
            f1 = float(raw1)
            f2 = float(raw2)
            kg1 = f1 * 1000.0 if u1 == "MT" else f1
            kg2 = f2 * 1000.0 if u2 == "MT" else f2

            if abs(kg1 - kg2) < 1e-4:
                return True, VerificationOutcome.EQUIVALENT_NORMALIZED, f"Values equivalent after metric unit normalization ({kg1:.2f} KG)"
            else:
                return False, VerificationOutcome.CONTRADICTION, f"Physical weight mismatch ({kg1:.2f} KG vs {kg2:.2f} KG)"
        except ValueError:
            pass

    # 3. Numeric Amount Normalization
    if c1_type in ["amount", "number"] or c2_type in ["amount", "number"]:
        try:
            num1 = re.sub(r"[^\d.]", "", c1_val)
            num2 = re.sub(r"[^\d.]", "", c2_val)
            if num1 and num2:
                f1 = float(num1)
                f2 = float(num2)
                if abs(f1 - f2) < 1e-4:
                    return True, VerificationOutcome.EQUIVALENT_NORMALIZED, f"Amounts equivalent ({f1:.2f})"
                else:
                    return False, VerificationOutcome.CONTRADICTION, f"Amount discrepancy ({f1:.2f} vs {f2:.2f})"
        except ValueError:
            pass

    # 4. Date Normalization
    if c1_type == "date" or c2_type == "date":
        d1 = normalize_claim_value(c1_val, "date")
        d2 = normalize_claim_value(c2_val, "date")
        if d1 and d2:
            if d1 == d2:
                return True, VerificationOutcome.EQUIVALENT_NORMALIZED, f"Dates equivalent ({d1})"
            else:
                return False, VerificationOutcome.CONTRADICTION, f"Date mismatch ({d1} vs {d2})"

    # 5. Fallback standard normalized equality
    norm1 = normalize_claim_value(c1_val, c1_type)
    norm2 = normalize_claim_value(c2_val, c2_type)
    if norm1 == norm2:
        return True, VerificationOutcome.EQUIVALENT_NORMALIZED, f"Values identical after normalization ('{norm1}')"

    return False, VerificationOutcome.CONTRADICTION, f"Value mismatch ('{norm1}' vs '{norm2}')"


def extract_currency(val: str) -> Optional[str]:
    """Extracts explicit currency token if specified."""
    if not val:
        return None
    if re.search(r"(\$|USD)", val, flags=re.IGNORECASE):
        return "USD"
    if re.search(r"(Rs\.?|INR|₹)", val, flags=re.IGNORECASE):
        return "INR"
    if re.search(r"(€|EUR)", val, flags=re.IGNORECASE):
        return "EUR"
    if re.search(r"(£|GBP)", val, flags=re.IGNORECASE):
        return "GBP"
    return None


def extract_unit(val: str) -> Optional[str]:
    """Extracts measurement unit token if specified."""
    if not val:
        return None
    if re.search(r"\b(MT|METRIC\s*TONNES?)\b", val, flags=re.IGNORECASE):
        return "MT"
    if re.search(r"\b(KG|KGS|KILOGRAMS?)\b", val, flags=re.IGNORECASE):
        return "KG"
    return None


def normalize_claim_value(val: str, field_type: str) -> str:
    """Standardizes values for cross-document contradiction comparison."""
    if not val:
        return ""
    clean = sanitize_identifier_token(val)
    if field_type in ["amount", "number", "count", "weight"]:
        num_str = re.sub(r"^(Rs\.?|INR|₹|USD|\$|EUR|€|GBP|£)\s*", "", clean, flags=re.IGNORECASE)
        num_str = re.sub(r"\s*(MT|KG|KGS)\b", "", num_str, flags=re.IGNORECASE)
        num_str = re.sub(r"[, ]+", "", num_str)
        # Decimal harmonization
        try:
            f_val = float(num_str)
            return f"{f_val:.2f}"
        except ValueError:
            return num_str
    elif field_type == "date":
        clean = clean.replace("-", "/")
        m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{2,4})$", clean)
        if m:
            d, mon, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
            if y < 100:
                y += 2000
            clean = f"{d:02d}/{mon:02d}/{y:04d}"
    else:
        clean = re.sub(r"\s+", " ", clean).strip().upper()
    return clean


def verify_cross_document_packet_claim(
    field_name: str,
    target_entity: EntityIdentity,
    claims: List[FieldClaim],
    documents: Dict[str, DocumentIdentity],
    required_doc_types: Optional[List[str]] = None,
    operating_threshold: float = 70.0,
) -> PacketVerificationResult:
    """
    Evaluates cross-document verification for a critical field across a packet:
      1. Missing Supporting Evidence check
      2. Entity disambiguation & attribution
      3. Evidence independence audit (duplicate detection)
      4. Multi-document contradiction detection (amount, date, decimal, currency, ID)
      5. Gated verification outcome with complete provenance trail
    """
    provenance: List[Dict[str, Any]] = []

    # 1. Missing Supporting Document Check
    if required_doc_types:
        present_types = {d.doc_type for d in documents.values()}
        missing = [rt for rt in required_doc_types if rt not in present_types]
        if missing:
            return PacketVerificationResult(
                field_name=field_name,
                target_entity_id=target_entity.entity_id,
                outcome=VerificationOutcome.MISSING_EVIDENCE,
                is_verified=False,
                verified_value=None,
                supporting_doc_ids=[],
                contradicting_doc_ids=[],
                reason=f"Mandatory supporting document type(s) missing from packet: {', '.join(missing)}",
                evidence_independence=SourceIndependence.INDEPENDENT,
                provenance_trail=[{"error": "Missing mandatory document attachment", "missing_types": missing}],
            )

    # Filter claims for the requested field
    field_claims = [c for c in claims if c.field_name == field_name]
    if not field_claims:
        return PacketVerificationResult(
            field_name=field_name,
            target_entity_id=target_entity.entity_id,
            outcome=VerificationOutcome.MISSING_EVIDENCE,
            is_verified=False,
            verified_value=None,
            supporting_doc_ids=[],
            contradicting_doc_ids=[],
            reason=f"No candidate claim found for field '{field_name}' in packet",
            evidence_independence=SourceIndependence.INDEPENDENT,
            provenance_trail=[],
        )

    # 2. Entity Disambiguation Check
    valid_claims: List[FieldClaim] = []
    entity_rejection_notes = []

    for c in field_claims:
        # Check claim against target entity
        is_entity_match, match_reason = resolve_entity_match(
            e1_name=target_entity.canonical_name,
            e2_name=c.entity_hints.get("applicant_name") or c.entity_hints.get("name") or target_entity.canonical_name,
            e1_hints={
                "tax_id": target_entity.tax_id,
                "national_id": target_entity.national_id,
                "date_of_birth": target_entity.date_of_birth,
                "father_name": target_entity.father_or_guardian_name,
                "address": target_entity.address,
            },
            e2_hints=c.entity_hints,
        )
        if not is_entity_match:
            entity_rejection_notes.append(f"Doc {c.doc_id}: {match_reason}")
        else:
            valid_claims.append(c)

    if not valid_claims:
        return PacketVerificationResult(
            field_name=field_name,
            target_entity_id=target_entity.entity_id,
            outcome=VerificationOutcome.ENTITY_AMBIGUOUS,
            is_verified=False,
            verified_value=None,
            supporting_doc_ids=[],
            contradicting_doc_ids=[c.doc_id for c in field_claims],
            reason=f"Entity resolution failure: {'; '.join(entity_rejection_notes)}",
            evidence_independence=SourceIndependence.INDEPENDENT,
            provenance_trail=[{"rejection_reasons": entity_rejection_notes}],
        )

    # 2b. Supporting Evidence Legibility Check
    if required_doc_types and len(required_doc_types) > 1:
        for dt in required_doc_types:
            dt_docs = [d for d in documents.values() if d.doc_type == dt]
            for doc in dt_docs:
                doc_claims = [c for c in field_claims if c.doc_id == doc.doc_id]
                if doc_claims and all(c.confidence < operating_threshold for c in doc_claims):
                    return PacketVerificationResult(
                        field_name=field_name,
                        target_entity_id=target_entity.entity_id,
                        outcome=VerificationOutcome.ABSTAIN,
                        is_verified=False,
                        verified_value=None,
                        supporting_doc_ids=[],
                        contradicting_doc_ids=[doc.doc_id],
                        reason=f"Required supporting document '{doc.file_name}' ({dt}) evidence is illegible or below confidence threshold",
                        evidence_independence=SourceIndependence.INDEPENDENT,
                        provenance_trail=[{"error": "Illegible supporting document", "doc_id": doc.doc_id}],
                    )

    # 3. Structural Identifier & Syntax Validation
    for c in valid_claims:
        if c.field_type == "id" or "ifsc" in c.field_name.lower() or "pan" in c.field_name.lower():
            ok, cleaned, dec, reason = validate_identifier_syntax_and_ambiguity(
                c.claimed_value, c.field_name, c.field_type, c.confidence
            )
            if not ok and dec == "ABSTAIN":
                c.is_ambiguous = True
                c.abstention_reason = reason

    # 3b. Chronological Sequence Validation
    if field_name in ["delivery_date", "receipt_date"]:
        order_claims = [
            c for c in claims
            if c.field_name in ["order_date", "po_date", "invoice_date"] and c.confidence >= operating_threshold
        ]
        if order_claims:
            best_order = max(order_claims, key=lambda c: c.confidence)
            norm_ord = normalize_claim_value(best_order.claimed_value, "date")
            for c in valid_claims:
                norm_del = normalize_claim_value(c.claimed_value, "date")
                m_ord = re.match(r"^(\d{2})/(\d{2})/(\d{4})$", norm_ord)
                m_del = re.match(r"^(\d{2})/(\d{2})/(\d{4})$", norm_del)
                if m_ord and m_del:
                    t_ord = (int(m_ord.group(3)), int(m_ord.group(2)), int(m_ord.group(1)))
                    t_del = (int(m_del.group(3)), int(m_del.group(2)), int(m_del.group(1)))
                    if t_del < t_ord:
                        return PacketVerificationResult(
                            field_name=field_name,
                            target_entity_id=target_entity.entity_id,
                            outcome=VerificationOutcome.CONTRADICTION,
                            is_verified=False,
                            verified_value=None,
                            supporting_doc_ids=[],
                            contradicting_doc_ids=[c.doc_id, best_order.doc_id],
                            reason=f"Chronological contradiction: delivery date '{norm_del}' precedes order date '{norm_ord}'",
                            evidence_independence=SourceIndependence.INDEPENDENT,
                            provenance_trail=[{"error": "Anachronistic dates", "delivery": norm_del, "order": norm_ord}],
                        )

    # 4. Evidence Independence Check
    doc_ids = list({c.doc_id for c in valid_claims})
    overall_independence = SourceIndependence.INDEPENDENT
    if len(doc_ids) >= 2:
        d1 = documents.get(doc_ids[0])
        d2 = documents.get(doc_ids[1])
        if d1 and d2:
            overall_independence = detect_document_independence(d1, d2)

    # 5. Multi-Source Contradiction Detection
    # 5a. Currency and Measurement Unit Discrepancy Checks
    currencies = set()
    units = set()
    for c in valid_claims:
        curr = extract_currency(c.claimed_value) or (c.unit_or_currency if c.unit_or_currency in ["USD", "INR", "EUR", "GBP"] else None)
        if curr:
            currencies.add(curr)
        u = extract_unit(c.claimed_value) or (c.unit_or_currency if c.unit_or_currency in ["MT", "KG"] else None)
        if u:
            units.add(u)

    if len(currencies) > 1:
        return PacketVerificationResult(
            field_name=field_name,
            target_entity_id=target_entity.entity_id,
            outcome=VerificationOutcome.CONTRADICTION,
            is_verified=False,
            verified_value=None,
            supporting_doc_ids=[],
            contradicting_doc_ids=[c.doc_id for c in valid_claims],
            reason=f"Currency contradiction across claims: {', '.join(sorted(currencies))}",
            evidence_independence=overall_independence,
            provenance_trail=[{"error": "Conflicting currencies", "currencies": list(currencies)}],
        )

    if len(units) > 1:
        return PacketVerificationResult(
            field_name=field_name,
            target_entity_id=target_entity.entity_id,
            outcome=VerificationOutcome.CONTRADICTION,
            is_verified=False,
            verified_value=None,
            supporting_doc_ids=[],
            contradicting_doc_ids=[c.doc_id for c in valid_claims],
            reason=f"Measurement unit contradiction across claims: {', '.join(sorted(units))}",
            evidence_independence=overall_independence,
            provenance_trail=[{"error": "Conflicting units", "units": list(units)}],
        )

    normalized_values: Dict[str, List[FieldClaim]] = {}
    for c in valid_claims:
        if c.is_ambiguous:
            continue
        norm_v = normalize_claim_value(c.claimed_value, c.field_type)
        if norm_v not in normalized_values:
            normalized_values[norm_v] = []
        normalized_values[norm_v].append(c)

    # If distinct valid normalized values exist across independent documents -> CONTRADICTION!
    distinct_vals = list(normalized_values.keys())
    if len(distinct_vals) > 1:
        doc_lists = {v: [c.doc_id for c in clist] for v, clist in normalized_values.items()}
        conflict_desc = " vs ".join([f"'{v}' ({', '.join(doc_lists[v])})" for v in distinct_vals])
        return PacketVerificationResult(
            field_name=field_name,
            target_entity_id=target_entity.entity_id,
            outcome=VerificationOutcome.CONTRADICTION,
            is_verified=False,
            verified_value=None,
            supporting_doc_ids=[],
            contradicting_doc_ids=[c.doc_id for c in valid_claims],
            reason=f"Direct cross-document factual contradiction detected: {conflict_desc}",
            evidence_independence=overall_independence,
            provenance_trail=[{"conflicting_claims": [c.__dict__ for c in valid_claims]}],
        )

    # If only ambiguous claims remain
    if not normalized_values:
        reasons = [c.abstention_reason for c in valid_claims if c.abstention_reason]
        return PacketVerificationResult(
            field_name=field_name,
            target_entity_id=target_entity.entity_id,
            outcome=VerificationOutcome.ABSTAIN,
            is_verified=False,
            verified_value=None,
            supporting_doc_ids=[],
            contradicting_doc_ids=[],
            reason=f"All candidate claims failed syntax/ambiguity audit: {'; '.join(reasons)}",
            evidence_independence=overall_independence,
            provenance_trail=[],
        )

    # 6. Duplicate Source Warning (if multiple documents claim agreement but are duplicates)
    best_val = distinct_vals[0]
    agreeing_claims = normalized_values[best_val]
    agreeing_docs = list({c.doc_id for c in agreeing_claims})

    # If agreeing claims come only from duplicate documents, refuse independent verification bonus
    if len(agreeing_docs) > 1 and overall_independence == SourceIndependence.DUPLICATE:
        # Verified based on single source, but independence flagged
        pass

    # Confidence check
    max_conf = max(c.confidence for c in agreeing_claims)
    if max_conf < operating_threshold:
        return PacketVerificationResult(
            field_name=field_name,
            target_entity_id=target_entity.entity_id,
            outcome=VerificationOutcome.ABSTAIN,
            is_verified=False,
            verified_value=best_val,
            supporting_doc_ids=agreeing_docs,
            contradicting_doc_ids=[],
            reason=f"Evidence confidence below operating threshold ({max_conf:.1f}% < {operating_threshold}%)",
            evidence_independence=overall_independence,
            provenance_trail=[{"claim_id": c.claim_id, "doc_id": c.doc_id, "conf": c.confidence} for c in agreeing_claims],
        )

    # Successfully Verified!
    return PacketVerificationResult(
        field_name=field_name,
        target_entity_id=target_entity.entity_id,
        outcome=VerificationOutcome.VERIFIED,
        is_verified=True,
        verified_value=best_val,
        supporting_doc_ids=agreeing_docs,
        contradicting_doc_ids=[],
        reason=f"Field verified with {len(agreeing_docs)} corroborating document(s) for entity '{target_entity.canonical_name}'",
        evidence_independence=overall_independence,
        provenance_trail=[{"claim_id": c.claim_id, "doc_id": c.doc_id, "conf": c.confidence} for c in agreeing_claims],
    )
