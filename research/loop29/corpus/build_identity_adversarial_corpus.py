"""
Builds and evaluates the Phase 5 Identity Resolution Adversarial Suite (20 mandatory cases).
Records decision table and outputs JSON/Markdown artifacts.
"""

import json
import os
import sys

sys.path.insert(0, ".")
from src.docuready.evidence.cross_document import (
    DocumentIdentity, EntityIdentity, FieldClaim,
    resolve_entity_match, detect_document_independence,
    evaluate_semantic_claim_equivalence, VerificationOutcome, SourceIndependence
)

def evaluate_identity_corpus():
    cases = [
        {
            "case_id": "CASE_01_SAME_PERSON_MATCHING_DOB",
            "description": "Same person, same name, matching DOB",
            "e1_name": "Rohit Verma",
            "e2_name": "Rohit Verma",
            "e1_hints": {"date_of_birth": "05/09/2004", "tax_id": "ABCDE1234F"},
            "e2_hints": {"date_of_birth": "05/09/2004", "tax_id": "ABCDE1234F"},
            "expected_decision": "ACCEPT",
        },
        {
            "case_id": "CASE_02_DIFFERENT_PEOPLE_SAME_NAME",
            "description": "Different people, same name, distinct DOBs",
            "e1_name": "Rohit Verma",
            "e2_name": "Rohit Verma",
            "e1_hints": {"date_of_birth": "05/09/2004"},
            "e2_hints": {"date_of_birth": "12/11/1998"},
            "expected_decision": "REJECT",
        },
        {
            "case_id": "CASE_03_SIBLINGS_SHARING_PARENT_ADDRESS",
            "description": "Siblings sharing father name and address, distinct DOBs and names",
            "e1_name": "Amit Kumar Nayak",
            "e2_name": "Anil Kumar Nayak",
            "e1_hints": {"father_name": "Bijay Nayak", "address": "Plot 12, Sahid Nagar, Bhubaneswar", "date_of_birth": "12/04/2001"},
            "e2_hints": {"father_name": "Bijay Nayak", "address": "Plot 12, Sahid Nagar, Bhubaneswar", "date_of_birth": "15/08/2003"},
            "expected_decision": "REJECT",
        },
        {
            "case_id": "CASE_04_PARENT_CHILD_SIMILAR_NAMES",
            "description": "Parent and child with similar names (Ramesh Verma vs Ramesh Verma Jr)",
            "e1_name": "Ramesh Verma",
            "e2_name": "Ramesh Verma Jr",
            "e1_hints": {"date_of_birth": "10/05/1972"},
            "e2_hints": {"date_of_birth": "14/09/2002"},
            "expected_decision": "REJECT",
        },
        {
            "case_id": "CASE_05_DIFFERENT_DOB_SAME_NAME",
            "description": "Different DOB, identical name, without other anchors",
            "e1_name": "Pooja Sharma",
            "e2_name": "Pooja Sharma",
            "e1_hints": {"date_of_birth": "01/01/1995"},
            "e2_hints": {"date_of_birth": "02/02/2000"},
            "expected_decision": "REJECT",
        },
        {
            "case_id": "CASE_06_SAME_ADDRESS_UNRELATED_APPLICANTS",
            "description": "Same rental address, completely unrelated applicants",
            "e1_name": "Suresh Chandra Mohanty",
            "e2_name": "Kavita Agrawal",
            "e1_hints": {"address": "House 45, Sector 4, Rourkela"},
            "e2_hints": {"address": "House 45, Sector 4, Rourkela"},
            "expected_decision": "REJECT",
        },
        {
            "case_id": "CASE_07_SAME_AMOUNT_UNRELATED_APPLICANTS",
            "description": "Same fee payment amount (INR 5500.00), unrelated applicants",
            "e1_name": "Manas Sahoo",
            "e2_name": "Deepak Jena",
            "e1_hints": {"fee_paid": "5500.00"},
            "e2_hints": {"fee_paid": "5500.00"},
            "expected_decision": "REJECT",
        },
        {
            "case_id": "CASE_08_VERMA_VARMA_SPELLING_VARIATION",
            "description": "Verma versus Varma spelling variation with matching DOB anchor",
            "e1_name": "Rohit Verma",
            "e2_name": "Rohit Varma",
            "e1_hints": {"date_of_birth": "05/09/2004"},
            "e2_hints": {"date_of_birth": "05/09/2004"},
            "expected_decision": "ACCEPT",
        },
        {
            "case_id": "CASE_09_PAN_O_0_CONFUSION",
            "description": "PAN O vs 0 confusable at index 4 (BARBOBHUBAN vs BARB0BHUBAN)",
            "e1_name": "Smita Pradhan",
            "e2_name": "Smita Pradhan",
            "e1_hints": {"ifsc_or_pan": "BARB0BHUBAN"},
            "e2_hints": {"ifsc_or_pan": "BARBOBHUBAN"},
            "expected_decision": "REJECT",
        },
        {
            "case_id": "CASE_10_PAN_B_8_CONFUSION",
            "description": "PAN B vs 8 visual confusion in alphanumeric identifier",
            "e1_name": "Alok Mishra",
            "e2_name": "Alok Mishra",
            "e1_hints": {"tax_id": "AZXPR0298B"},
            "e2_hints": {"tax_id": "AZXPR02988"},
            "expected_decision": "REJECT",
        },
        {
            "case_id": "CASE_11_PAN_ONE_CHAR_SUBSTITUTION",
            "description": "PAN 1-char substitution (AZXPR0298B vs AZXPR0298F) across docs",
            "e1_name": "Tapan Sethi",
            "e2_name": "Tapan Sethi",
            "e1_hints": {"tax_id": "AZXPR0298B"},
            "e2_hints": {"tax_id": "AZXPR0298F"},
            "expected_decision": "REJECT",
        },
        {
            "case_id": "CASE_12_PAN_CONFLICT_INDEPENDENT_DOCS",
            "description": "PAN conflict across independent docs (ABCDE1234F vs XYZPR9876K)",
            "e1_name": "Priya Mohapatra",
            "e2_name": "Priya Mohapatra",
            "e1_hints": {"tax_id": "ABCDE1234F"},
            "e2_hints": {"tax_id": "XYZPR9876K"},
            "expected_decision": "REJECT",
        },
        {
            "case_id": "CASE_13_REPEATED_PAN_DUPLICATE_DOCS",
            "description": "Repeated PAN copied into multiple documents (duplicate check)",
            "type": "independence",
            "doc1": DocumentIdentity("D1", "PAN_CARD", "pan.pdf", "hash_same"),
            "doc2": DocumentIdentity("D2", "PAN_CARD", "pan_copy.pdf", "hash_same"),
            "expected_decision": "DUPLICATE",
        },
        {
            "case_id": "CASE_14_DUPLICATE_SCAN_DIFFERENT_FILENAME",
            "description": "Identical content hash under different filenames",
            "type": "independence",
            "doc1": DocumentIdentity("D1", "CERT", "cert.pdf", "hash_999"),
            "doc2": DocumentIdentity("D2", "CERT", "verified_cert_final.pdf", "hash_999"),
            "expected_decision": "DUPLICATE",
        },
        {
            "case_id": "CASE_15_SAME_FILENAME_UNRELATED_DOCS",
            "description": "Same filename ('invoice.pdf') used for distinct documents (different hashes)",
            "type": "independence",
            "doc1": DocumentIdentity("D1", "INVOICE", "invoice.pdf", "hash_alpha", raw_text="Company Alpha 100"),
            "doc2": DocumentIdentity("D2", "INVOICE", "invoice.pdf", "hash_beta", raw_text="Company Beta 900"),
            "expected_decision": "INDEPENDENT",
        },
        {
            "case_id": "CASE_16_SAME_DOC_CHANGED_FORMATTING",
            "description": "Same underlying document with reformatted text",
            "type": "independence",
            "doc1": DocumentIdentity("D1", "PO", "po_v1.pdf", "h1", raw_text="ORDER NO 101 TOTAL 5000 DATED 10/10/2026"),
            "doc2": DocumentIdentity("D2", "PO", "po_v2.pdf", "h1", raw_text="ORDER NO 101 TOTAL 5000 DATED 10/10/2026"),
            "expected_decision": "DUPLICATE",
        },
        {
            "case_id": "CASE_17_MULTILINGUAL_TRANSLITERATION",
            "description": "Transliteration variation (Soumya vs Saumya) with matching DOB",
            "e1_name": "Soumya Ranjan Das",
            "e2_name": "Saumya Ranjan Das",
            "e1_hints": {"date_of_birth": "22/07/2003"},
            "e2_hints": {"date_of_birth": "22/07/2003"},
            "expected_decision": "ACCEPT",
        },
        {
            "case_id": "CASE_18_MISSING_DOB_MISSING_UID",
            "description": "Different names without any DOB or unique identifier",
            "e1_name": "Sunil Patra",
            "e2_name": "Anil Patra",
            "e1_hints": {},
            "e2_hints": {},
            "expected_decision": "REJECT",
        },
        {
            "case_id": "CASE_19_CONFLICTING_FATHER_AND_DOB",
            "description": "Conflicting father name and conflicting DOB despite identical name",
            "e1_name": "Bikash Jena",
            "e2_name": "Bikash Jena",
            "e1_hints": {"father_name": "Niranjan Jena", "date_of_birth": "11/03/1997"},
            "e2_hints": {"father_name": "Gopal Jena", "date_of_birth": "19/08/2001"},
            "expected_decision": "REJECT",
        },
        {
            "case_id": "CASE_20_SHARED_FAMILY_IDENTIFIERS",
            "description": "Two family applicants with shared family ration card, distinct applicant names",
            "e1_name": "Geeta Rani Sahu",
            "e2_name": "Mamata Sahu",
            "e1_hints": {"family_ration_card": "RC-OD-2026-9901"},
            "e2_hints": {"family_ration_card": "RC-OD-2026-9901"},
            "expected_decision": "REJECT",
        },
    ]

    results = []
    passed_cases = 0

    for c in cases:
        c_type = c.get("type", "entity")
        if c_type == "independence":
            res = detect_document_independence(c["doc1"], c["doc2"])
            actual = res.value
            is_pass = (actual == c["expected_decision"])
            reason = f"Independence test: {actual}"
        else:
            is_match, reason = resolve_entity_match(
                e1_name=c["e1_name"],
                e2_name=c["e2_name"],
                e1_hints=c["e1_hints"],
                e2_hints=c["e2_hints"],
            )
            actual = "ACCEPT" if is_match else "REJECT"
            is_pass = (actual == c["expected_decision"])

        if is_pass:
            passed_cases += 1

        results.append({
            "case_id": c["case_id"],
            "description": c["description"],
            "expected": c["expected_decision"],
            "actual": actual,
            "status": "PASS" if is_pass else "FAIL",
            "reason": reason,
        })

    print(f"Adversarial Identity Suite: {passed_cases}/{len(cases)} cases PASSED.")
    for r in results:
        print(f"  [{r['status']}] {r['case_id']}: expected {r['expected']} -> got {r['actual']} ({r['reason']})")

    out_file = os.path.join("research", "loop29", "corpus", "identity_adversarial_results.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({"total_cases": len(cases), "passed_cases": passed_cases, "cases": results}, f, indent=2)
    print(f"Results saved to {out_file}")

if __name__ == "__main__":
    evaluate_identity_corpus()
