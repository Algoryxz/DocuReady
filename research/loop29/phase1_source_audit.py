"""
Phase 1 Source and Evidence Audit for Loop 28.
Verifies and documents implementation details in src/docuready/evidence/cross_document.py
and related modules.
"""

import sys
sys.path.insert(0, ".")
from src.docuready.evidence.cross_document import (
    DocumentIdentity, EntityIdentity, FieldClaim,
    resolve_entity_match, detect_document_independence,
    normalize_claim_value, extract_currency, extract_unit,
    verify_cross_document_packet_claim,
    VerificationOutcome, SourceIndependence
)

findings = []

# Check 1: Father name alone establishing identity
match1, reason1 = resolve_entity_match(
    e1_name="Amit Kumar",
    e2_name="Sunil Kumar",
    e1_hints={"father_name": "Ramesh Kumar"},
    e2_hints={"father_name": "Ramesh Kumar"}
)
findings.append({
    "check": "Father name alone establishing identity",
    "inputs": "Amit Kumar vs Sunil Kumar (same father Ramesh Kumar)",
    "is_match": match1,
    "reason": reason1,
    "status": "PASS" if not match1 else "FAIL"
})

# Check 2: Shared address alone establishing identity
match2, reason2 = resolve_entity_match(
    e1_name="Amit Kumar",
    e2_name="Pooja Sharma",
    e1_hints={"address": "Plot 12, Sahid Nagar, Bhubaneswar"},
    e2_hints={"address": "Plot 12, Sahid Nagar, Bhubaneswar"}
)
findings.append({
    "check": "Shared address alone establishing identity",
    "inputs": "Amit Kumar vs Pooja Sharma (same address)",
    "is_match": match2,
    "reason": reason2,
    "status": "PASS" if not match2 else "FAIL"
})

# Check 3: Conflicting PAN forcing rejection
match3, reason3 = resolve_entity_match(
    e1_name="Rohit Verma",
    e2_name="Rohit Verma",
    e1_hints={"tax_id": "ABCDE1234F"},
    e2_hints={"tax_id": "XYZPR9876K"}
)
findings.append({
    "check": "Conflicting PAN forcing rejection",
    "inputs": "Rohit Verma (ABCDE1234F) vs Rohit Verma (XYZPR9876K)",
    "is_match": match3,
    "reason": reason3,
    "status": "PASS" if not match3 else "FAIL"
})

# Check 4: Identical filenames with different content hashes
doc_a = DocumentIdentity("D1", "FORM", "invoice.pdf", "hash_aaa111", raw_text="Company A Invoice 100")
doc_b = DocumentIdentity("D2", "FORM", "invoice.pdf", "hash_bbb222", raw_text="Company B Invoice 500")
indep4 = detect_document_independence(doc_a, doc_b)
findings.append({
    "check": "Identical generic filename with different content hashes",
    "inputs": "invoice.pdf (hash_aaa) vs invoice.pdf (hash_bbb)",
    "result": indep4.value,
    "status": "WARNING_FALSE_DUPLICATE" if indep4 == SourceIndependence.DUPLICATE else "PASS"
})

# Check 5: High boilerplate similarity (>96%) across different applicants
boilerplate = "STATE SCHOLARSHIP PORTAL GOVERNMENT OF ODISHA APPLICATION FORM FOR HIGHER EDUCATION POST MATRIC SCHOLARSHIP ACADEMIC YEAR 2026-2027 " * 10
text_app1 = boilerplate + " APPLICANT NAME: ROHIT VERMA AADHAAR: 123456789012 SCORE: 85"
text_app2 = boilerplate + " APPLICANT NAME: PRIYA DAS AADHAAR: 987654321098 SCORE: 92"
doc_tmpl1 = DocumentIdentity("D1", "FORM", "app1.pdf", "hash_111", raw_text=text_app1)
doc_tmpl2 = DocumentIdentity("D2", "FORM", "app2.pdf", "hash_222", raw_text=text_app2)
indep5 = detect_document_independence(doc_tmpl1, doc_tmpl2)
findings.append({
    "check": "High template boilerplate similarity (>96%) for different applicants",
    "inputs": "app1 (Rohit) vs app2 (Priya)",
    "result": indep5.value,
    "status": "WARNING_FALSE_DUPLICATE" if indep5 == SourceIndependence.DUPLICATE else "PASS"
})

# Check 6: Unit normalization (1 MT vs 1000 KG)
u1 = normalize_claim_value("1.00 MT", "weight")
u2 = normalize_claim_value("1000.00 KG", "weight")
findings.append({
    "check": "Unit conversion (1.00 MT vs 1000.00 KG)",
    "inputs": "1.00 MT vs 1000.00 KG",
    "val1": u1,
    "val2": u2,
    "status": "EQUAL" if u1 == u2 else "REQUIRES_SEMANTIC_NORMALIZATION"
})

for f in findings:
    print(f"[{f['status']}] {f['check']}: {f.get('reason') or f.get('result') or (f.get('val1') + ' vs ' + f.get('val2'))}")
