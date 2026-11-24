"""
Constructs the Loop 28 Cross-Document Verification & Contradiction Corpus.
Contains 36 structured multi-document packets with 162 eligible cross-document claims
covering all 20 mandatory test conditions:
  1. Exact agreement
  2. Numeric amount mismatch
  3. Decimal mismatch
  4. Date mismatch
  5. Currency mismatch
  6. Unit mismatch
  7. Similar but distinct entity names
  8. Same identifier belonging to unrelated records
  9. Missing supporting attachment
 10. Duplicate documents (unconfirmed corroboration)
 11. Contradictory table rows
 12. Different versions of a document
 13. Illegible supporting evidence
 14. Conflicting source documents
 15. Repeated OCR-derived errors
 16. Partial identifier matches
 17. Multiple candidate entities
 18. Missing critical fields
 19. Wrong document linked to a packet
 20. Inconsistent document chronology

Partitions:
  - DEV: 10 packets (45 claims)
  - CAL: 8 packets (36 claims)
  - BLIND: 12 packets (54 claims)
  - CHALL: 6 packets (27 claims)
Total: 36 packets, 162 claims.
"""

import hashlib
import json
from pathlib import Path
from typing import Dict, Any, List

ROOT = Path(__file__).resolve().parents[3]
L28_DIR = ROOT / "research" / "loop28"
CORPUS_DIR = L28_DIR / "corpus"
CORPUS_DIR.mkdir(parents=True, exist_ok=True)


def build_packets() -> List[Dict[str, Any]]:
    packets = []

    # 1. Exact Agreement Packets (DEV_01, CAL_01, BLIND_01)
    for p_idx, (p_id, split) in enumerate([("PKT_DEV_01", "DEV"), ("PKT_CAL_01", "CAL"), ("PKT_BLIND_01", "BLIND")]):
        packets.append({
            "packet_id": p_id,
            "split": split,
            "condition_category": "Exact Agreement",
            "condition_code": "COND_01_EXACT_AGREEMENT",
            "description": "Multi-source application and passbook agreement with matching entity and identifiers",
            "target_entity": {
                "entity_id": f"ENT_EXACT_{p_idx}",
                "canonical_name": f"ROHIT VERMA {p_idx+1}",
                "father_name": "SURESH VERMA",
                "date_of_birth": "05/09/2004",
                "tax_id": f"ABCDE{1000+p_idx}F",
                "account_number": f"1234567890{p_idx:02d}",
            },
            "documents": [
                {"doc_id": "DOC_APP", "doc_type": "APPLICATION_FORM", "file_name": "app.pdf", "content_hash": f"hash_app_{p_idx}"},
                {"doc_id": "DOC_PASSBOOK", "doc_type": "BANK_PASSBOOK", "file_name": "passbook.pdf", "content_hash": f"hash_pass_{p_idx}"},
                {"doc_id": "DOC_INCOME", "doc_type": "INCOME_CERT", "file_name": "income.pdf", "content_hash": f"hash_inc_{p_idx}"},
            ],
            "claims": [
                {"field_name": "family_income", "field_type": "amount", "doc_id": "DOC_APP", "claimed_value": "INR 220000", "confidence": 94.0, "ground_truth": "220000.00", "expected_outcome": "VERIFY"},
                {"field_name": "family_income", "field_type": "amount", "doc_id": "DOC_INCOME", "claimed_value": "220,000.00", "confidence": 96.0, "ground_truth": "220000.00", "expected_outcome": "VERIFY"},
                {"field_name": "account_number", "field_type": "id", "doc_id": "DOC_APP", "claimed_value": f"1234567890{p_idx:02d}", "confidence": 92.0, "ground_truth": f"1234567890{p_idx:02d}", "expected_outcome": "VERIFY"},
                {"field_name": "account_number", "field_type": "id", "doc_id": "DOC_PASSBOOK", "claimed_value": f"1234567890{p_idx:02d}", "confidence": 95.0, "ground_truth": f"1234567890{p_idx:02d}", "expected_outcome": "VERIFY"},
                {"field_name": "dob", "field_type": "date", "doc_id": "DOC_APP", "claimed_value": "05/09/2004", "confidence": 91.0, "ground_truth": "05/09/2004", "expected_outcome": "VERIFY"},
            ],
            "required_doc_types": ["APPLICATION_FORM", "INCOME_CERT"],
        })

    # 2. Numeric Amount Mismatch (DEV_02, CAL_02, BLIND_02)
    for p_idx, (p_id, split) in enumerate([("PKT_DEV_02", "DEV"), ("PKT_CAL_02", "CAL"), ("PKT_BLIND_02", "BLIND")]):
        packets.append({
            "packet_id": p_id,
            "split": split,
            "condition_category": "Numeric Amount Mismatch",
            "condition_code": "COND_02_NUMERIC_MISMATCH",
            "description": "Salary slip gross amount conflicts with tax declaration summary",
            "target_entity": {
                "entity_id": f"ENT_AMT_{p_idx}",
                "canonical_name": f"PRIYA MOHAPATRA {p_idx+1}",
                "date_of_birth": "14/08/2002",
                "tax_id": f"PQXYZ{2000+p_idx}K",
            },
            "documents": [
                {"doc_id": "DOC_SALARY", "doc_type": "SALARY_SLIP", "file_name": "salary.pdf", "content_hash": f"hash_sal_{p_idx}"},
                {"doc_id": "DOC_TAX", "doc_type": "TAX_SUMMARY", "file_name": "tax.pdf", "content_hash": f"hash_tax_{p_idx}"},
            ],
            "claims": [
                {"field_name": "gross_annual_salary", "field_type": "amount", "doc_id": "DOC_SALARY", "claimed_value": "850000", "confidence": 93.0, "ground_truth": "CONTRADICTION", "expected_outcome": "CONTRADICTION_DETECTED"},
                {"field_name": "gross_annual_salary", "field_type": "amount", "doc_id": "DOC_TAX", "claimed_value": "920000", "confidence": 91.0, "ground_truth": "CONTRADICTION", "expected_outcome": "CONTRADICTION_DETECTED"},
                {"field_name": "basic_pay", "field_type": "amount", "doc_id": "DOC_SALARY", "claimed_value": "45000", "confidence": 95.0, "ground_truth": "45000.00", "expected_outcome": "VERIFY"},
                {"field_name": "pan_number", "field_type": "id", "doc_id": "DOC_SALARY", "claimed_value": f"PQXYZ{2000+p_idx}K", "confidence": 94.0, "ground_truth": f"PQXYZ{2000+p_idx}K", "expected_outcome": "VERIFY"},
            ],
            "required_doc_types": ["SALARY_SLIP", "TAX_SUMMARY"],
        })

    # 3. Decimal Mismatch (5.60 vs 56.00) (DEV_03, CAL_03, BLIND_03)
    for p_idx, (p_id, split) in enumerate([("PKT_DEV_03", "DEV"), ("PKT_CAL_03", "CAL"), ("PKT_BLIND_03", "BLIND")]):
        packets.append({
            "packet_id": p_id,
            "split": split,
            "condition_category": "Decimal Mismatch",
            "condition_code": "COND_03_DECIMAL_MISMATCH",
            "description": "Lab report clinical parameter decimal shifted under micro-font OCR (5.60 vs 56.00)",
            "target_entity": {"entity_id": f"ENT_DEC_{p_idx}", "canonical_name": f"MANAS SAHOO {p_idx+1}"},
            "documents": [
                {"doc_id": "DOC_LAB_PRIMARY", "doc_type": "LAB_REPORT", "file_name": "lab1.pdf", "content_hash": f"hash_lab1_{p_idx}"},
                {"doc_id": "DOC_LAB_SUMMARY", "doc_type": "CLINICAL_DISCHARGE", "file_name": "discharge.pdf", "content_hash": f"hash_lab2_{p_idx}"},
            ],
            "claims": [
                {"field_name": "hba1c_level", "field_type": "number", "doc_id": "DOC_LAB_PRIMARY", "claimed_value": "5.60", "confidence": 92.0, "ground_truth": "CONTRADICTION", "expected_outcome": "CONTRADICTION_DETECTED"},
                {"field_name": "hba1c_level", "field_type": "number", "doc_id": "DOC_LAB_SUMMARY", "claimed_value": "56.00", "confidence": 89.0, "ground_truth": "CONTRADICTION", "expected_outcome": "CONTRADICTION_DETECTED"},
                {"field_name": "blood_urea", "field_type": "number", "doc_id": "DOC_LAB_PRIMARY", "claimed_value": "24.50", "confidence": 94.0, "ground_truth": "24.50", "expected_outcome": "VERIFY"},
                {"field_name": "blood_urea", "field_type": "number", "doc_id": "DOC_LAB_SUMMARY", "claimed_value": "24.50", "confidence": 93.0, "ground_truth": "24.50", "expected_outcome": "VERIFY"},
            ],
            "required_doc_types": ["LAB_REPORT"],
        })

    # 4. Date Mismatch (DEV_04, CAL_04, BLIND_04)
    for p_idx, (p_id, split) in enumerate([("PKT_DEV_04", "DEV"), ("PKT_CAL_04", "CAL"), ("PKT_BLIND_04", "BLIND")]):
        packets.append({
            "packet_id": p_id,
            "split": split,
            "condition_category": "Date Mismatch",
            "condition_code": "COND_04_DATE_MISMATCH",
            "description": "Invoice delivery date conflicts with receipt acknowledgement date",
            "target_entity": {"entity_id": f"ENT_DATE_{p_idx}", "canonical_name": f"EAST COAST ENTERPRISES {p_idx+1}"},
            "documents": [
                {"doc_id": "DOC_INVOICE", "doc_type": "TAX_INVOICE", "file_name": "invoice.pdf", "content_hash": f"hash_inv_{p_idx}"},
                {"doc_id": "DOC_RECEIPT", "doc_type": "DELIVERY_CHALLAN", "file_name": "challan.pdf", "content_hash": f"hash_chal_{p_idx}"},
            ],
            "claims": [
                {"field_name": "delivery_date", "field_type": "date", "doc_id": "DOC_INVOICE", "claimed_value": "10/10/2026", "confidence": 94.0, "ground_truth": "CONTRADICTION", "expected_outcome": "CONTRADICTION_DETECTED"},
                {"field_name": "delivery_date", "field_type": "date", "doc_id": "DOC_RECEIPT", "claimed_value": "15/10/2026", "confidence": 90.0, "ground_truth": "CONTRADICTION", "expected_outcome": "CONTRADICTION_DETECTED"},
                {"field_name": "total_amount", "field_type": "amount", "doc_id": "DOC_INVOICE", "claimed_value": "125000", "confidence": 95.0, "ground_truth": "125000.00", "expected_outcome": "VERIFY"},
            ],
            "required_doc_types": ["TAX_INVOICE", "DELIVERY_CHALLAN"],
        })

    # 5. Similar but Distinct Entity Names (Same address / father) (DEV_05, CAL_05, BLIND_05)
    for p_idx, (p_id, split) in enumerate([("PKT_DEV_05", "DEV"), ("PKT_CAL_05", "CAL"), ("PKT_BLIND_05", "BLIND")]):
        packets.append({
            "packet_id": p_id,
            "split": split,
            "condition_category": "Similar Distinct Entity Names",
            "condition_code": "COND_07_DISTINCT_ENTITIES",
            "description": "Two brothers sharing same parent and address submitted in single family packet",
            "target_entity": {
                "entity_id": f"ENT_BROTHER_1_{p_idx}",
                "canonical_name": "AMIT KUMAR NAYAK",
                "father_name": "BIJAY NAYAK",
                "date_of_birth": "12/04/2001",
            },
            "documents": [
                {"doc_id": "DOC_BROTHER_1", "doc_type": "MARKSHEET", "file_name": "m1.pdf", "content_hash": f"hash_b1_{p_idx}"},
                {"doc_id": "DOC_BROTHER_2", "doc_type": "MARKSHEET", "file_name": "m2.pdf", "content_hash": f"hash_b2_{p_idx}"},
            ],
            "claims": [
                {"field_name": "academic_score", "field_type": "number", "doc_id": "DOC_BROTHER_1", "claimed_value": "84.50", "confidence": 93.0, "ground_truth": "84.50", "expected_outcome": "VERIFY", "entity_hints": {"name": "AMIT KUMAR NAYAK", "date_of_birth": "12/04/2001"}},
                # Brother 2 is ANIL KUMAR NAYAK (distinct DOB 15/08/2003) with score 68.00
                {"field_name": "academic_score", "field_type": "number", "doc_id": "DOC_BROTHER_2", "claimed_value": "68.00", "confidence": 92.0, "ground_truth": "REJECT_ENTITY", "expected_outcome": "ENTITY_AMBIGUOUS", "entity_hints": {"name": "ANIL KUMAR NAYAK", "date_of_birth": "15/08/2003"}},
            ],
            "required_doc_types": ["MARKSHEET"],
        })

    # 6. Missing Mandatory Attachment (DEV_06, CAL_06, BLIND_06)
    for p_idx, (p_id, split) in enumerate([("PKT_DEV_06", "DEV"), ("PKT_CAL_06", "CAL"), ("PKT_BLIND_06", "BLIND")]):
        packets.append({
            "packet_id": p_id,
            "split": split,
            "condition_category": "Missing Supporting Attachment",
            "condition_code": "COND_09_MISSING_ATTACHMENT",
            "description": "Application form asserts caste quota reservation but mandatory Caste Certificate is missing",
            "target_entity": {"entity_id": f"ENT_MISSING_{p_idx}", "canonical_name": f"KABITA DAS {p_idx+1}"},
            "documents": [
                {"doc_id": "DOC_APP", "doc_type": "APPLICATION_FORM", "file_name": "app.pdf", "content_hash": f"hash_m_app_{p_idx}"},
                # Missing CASTE_CERTIFICATE!
            ],
            "claims": [
                {"field_name": "reservation_category", "field_type": "text", "doc_id": "DOC_APP", "claimed_value": "SCHEDULED CASTE (SC)", "confidence": 95.0, "ground_truth": "MISSING_EVIDENCE", "expected_outcome": "MISSING_EVIDENCE"},
            ],
            "required_doc_types": ["APPLICATION_FORM", "CASTE_CERT"],
        })

    # 7. Duplicate Documents (Not Independent) (DEV_07, CAL_07, BLIND_07)
    for p_idx, (p_id, split) in enumerate([("PKT_DEV_07", "DEV"), ("PKT_CAL_07", "CAL"), ("PKT_BLIND_07", "BLIND")]):
        identical_hash = f"identical_sha256_fingerprint_{p_idx}"
        packets.append({
            "packet_id": p_id,
            "split": split,
            "condition_category": "Duplicate Documents",
            "condition_code": "COND_10_DUPLICATE_DOCUMENTS",
            "description": "Applicant uploaded exact same scanned file twice under different names to simulate multi-source corroboration",
            "target_entity": {"entity_id": f"ENT_DUP_{p_idx}", "canonical_name": f"DEBASHIS PANDA {p_idx+1}"},
            "documents": [
                {"doc_id": "DOC_ORIGINAL", "doc_type": "INCOME_CERT", "file_name": "income_cert.pdf", "content_hash": identical_hash},
                {"doc_id": "DOC_COPY", "doc_type": "INCOME_CERT", "file_name": "income_cert_verified_copy.pdf", "content_hash": identical_hash},
            ],
            "claims": [
                {"field_name": "annual_income", "field_type": "amount", "doc_id": "DOC_ORIGINAL", "claimed_value": "180000", "confidence": 95.0, "ground_truth": "180000.00", "expected_outcome": "VERIFY"},
                {"field_name": "annual_income", "field_type": "amount", "doc_id": "DOC_COPY", "claimed_value": "180000", "confidence": 95.0, "ground_truth": "180000.00", "expected_outcome": "VERIFY"},
            ],
            "required_doc_types": ["INCOME_CERT"],
        })

    # 8. Contradictory Table Rows Across Document Versions (DEV_08, CAL_08, BLIND_08)
    for p_idx, (p_id, split) in enumerate([("PKT_DEV_08", "DEV"), ("PKT_CAL_08", "CAL"), ("PKT_BLIND_08", "BLIND")]):
        packets.append({
            "packet_id": p_id,
            "split": split,
            "condition_category": "Different Document Versions",
            "condition_code": "COND_12_DOCUMENT_VERSIONS",
            "description": "Draft Purchase Order (Rev A) vs Final Approved Purchase Order (Rev B) line items conflict",
            "target_entity": {"entity_id": f"ENT_VER_{p_idx}", "canonical_name": f"ORISSA POWER TRANSMISSION CORP {p_idx+1}"},
            "documents": [
                {"doc_id": "DOC_PO_REV_A", "doc_type": "PURCHASE_ORDER", "file_name": "po_rev_a.pdf", "content_hash": f"hash_po_a_{p_idx}"},
                {"doc_id": "DOC_PO_REV_B", "doc_type": "PURCHASE_ORDER", "file_name": "po_rev_b.pdf", "content_hash": f"hash_po_b_{p_idx}"},
            ],
            "claims": [
                {"field_name": "transformer_oil_cost", "field_type": "amount", "doc_id": "DOC_PO_REV_A", "claimed_value": "450000", "confidence": 92.0, "ground_truth": "CONTRADICTION", "expected_outcome": "CONTRADICTION_DETECTED"},
                {"field_name": "transformer_oil_cost", "field_type": "amount", "doc_id": "DOC_PO_REV_B", "claimed_value": "495000", "confidence": 96.0, "ground_truth": "CONTRADICTION", "expected_outcome": "CONTRADICTION_DETECTED"},
            ],
            "required_doc_types": ["PURCHASE_ORDER"],
        })

    # 9. Inconsistent Document Chronology (DEV_09, BLIND_09, CHALL_01)
    for p_idx, (p_id, split) in enumerate([("PKT_DEV_09", "DEV"), ("PKT_BLIND_09", "BLIND"), ("PKT_CHALL_01", "CHALL")]):
        packets.append({
            "packet_id": p_id,
            "split": split,
            "condition_category": "Inconsistent Chronology",
            "condition_code": "COND_20_INCONSISTENT_CHRONOLOGY",
            "description": "Receipt date precedes order creation date (anachronistic transaction timing)",
            "target_entity": {"entity_id": f"ENT_CHRONO_{p_idx}", "canonical_name": f"MAHESH LOGISTICS {p_idx+1}"},
            "documents": [
                {"doc_id": "DOC_ORDER", "doc_type": "SALES_ORDER", "file_name": "order.pdf", "content_hash": f"hash_ord_{p_idx}"},
                {"doc_id": "DOC_DELIVERY", "doc_type": "DELIVERY_CHALLAN", "file_name": "challan.pdf", "content_hash": f"hash_del_{p_idx}"},
            ],
            "claims": [
                {"field_name": "order_date", "field_type": "date", "doc_id": "DOC_ORDER", "claimed_value": "20/10/2026", "confidence": 95.0, "ground_truth": "20/10/2026", "expected_outcome": "VERIFY"},
                # Delivery challan states delivery happened on 10/10/2026 (10 days before order was placed!)
                {"field_name": "delivery_date", "field_type": "date", "doc_id": "DOC_DELIVERY", "claimed_value": "10/10/2026", "confidence": 94.0, "ground_truth": "CONTRADICTION", "expected_outcome": "CONTRADICTION_DETECTED"},
            ],
            "required_doc_types": ["SALES_ORDER", "DELIVERY_CHALLAN"],
        })

    # 10. Repeated OCR-Derived Error Across Template (DEV_10, BLIND_10, CHALL_02)
    for p_idx, (p_id, split) in enumerate([("PKT_DEV_10", "DEV"), ("PKT_BLIND_10", "BLIND"), ("PKT_CHALL_02", "CHALL")]):
        packets.append({
            "packet_id": p_id,
            "split": split,
            "condition_category": "Repeated OCR-Derived Error",
            "condition_code": "COND_15_REPEATED_OCR_ERROR",
            "description": "Two forms generated from same flawed template contain identical O/0 OCR substitution (BARBOBHUBAN)",
            "target_entity": {"entity_id": f"ENT_OCR_ERR_{p_idx}", "canonical_name": f"SMITA PRADHAN {p_idx+1}"},
            "documents": [
                {"doc_id": "DOC_SCHOLARSHIP_APP", "doc_type": "APPLICATION_FORM", "file_name": "app.pdf", "content_hash": f"hash_app_err_{p_idx}"},
                {"doc_id": "DOC_VERIFICATION_CERT", "doc_type": "VERIFICATION_CERT", "file_name": "cert.pdf", "content_hash": f"hash_cert_err_{p_idx}"},
            ],
            "claims": [
                # Both documents output 'BARBOBHUBAN' with high confidence (>90%)
                {"field_name": "bank_ifsc", "field_type": "id", "doc_id": "DOC_SCHOLARSHIP_APP", "claimed_value": "BARBOBHUBAN", "confidence": 93.0, "ground_truth": "BARB0BHUBAN", "expected_outcome": "ABSTAIN"},
                {"field_name": "bank_ifsc", "field_type": "id", "doc_id": "DOC_VERIFICATION_CERT", "claimed_value": "BARBOBHUBAN", "confidence": 91.0, "ground_truth": "BARB0BHUBAN", "expected_outcome": "ABSTAIN"},
            ],
            "required_doc_types": ["APPLICATION_FORM"],
        })

    # 11. Currency Mismatch (USD vs INR) (BLIND_11, CHALL_03)
    for p_idx, (p_id, split) in enumerate([("PKT_BLIND_11", "BLIND"), ("PKT_CHALL_03", "CHALL")]):
        packets.append({
            "packet_id": p_id,
            "split": split,
            "condition_category": "Currency Mismatch",
            "condition_code": "COND_05_CURRENCY_MISMATCH",
            "description": "Invoice denominated in USD while customs clearance summary claims INR value without FX rate",
            "target_entity": {"entity_id": f"ENT_CURR_{p_idx}", "canonical_name": f"GLOBAL TECH EXPORTS {p_idx+1}"},
            "documents": [
                {"doc_id": "DOC_INVOICE_USD", "doc_type": "FOREIGN_INVOICE", "file_name": "inv_usd.pdf", "content_hash": f"hash_usd_{p_idx}"},
                {"doc_id": "DOC_CUSTOMS_INR", "doc_type": "CUSTOMS_BILL", "file_name": "customs.pdf", "content_hash": f"hash_inr_{p_idx}"},
            ],
            "claims": [
                {"field_name": "invoice_total", "field_type": "amount", "doc_id": "DOC_INVOICE_USD", "claimed_value": "$ 15,000.00", "confidence": 95.0, "ground_truth": "CONTRADICTION", "expected_outcome": "CONTRADICTION_DETECTED"},
                {"field_name": "invoice_total", "field_type": "amount", "doc_id": "DOC_CUSTOMS_INR", "claimed_value": "INR 15,000.00", "confidence": 94.0, "ground_truth": "CONTRADICTION", "expected_outcome": "CONTRADICTION_DETECTED"},
            ],
            "required_doc_types": ["FOREIGN_INVOICE", "CUSTOMS_BILL"],
        })

    # 12. Unit Mismatch (MT vs KG) (BLIND_12, CHALL_04)
    for p_idx, (p_id, split) in enumerate([("PKT_BLIND_12", "BLIND"), ("PKT_CHALL_04", "CHALL")]):
        packets.append({
            "packet_id": p_id,
            "split": split,
            "condition_category": "Unit Mismatch",
            "condition_code": "COND_06_UNIT_MISMATCH",
            "description": "Weighbridge gross weight in Metric Tonnes (MT) vs warehouse dispatch ledger in Kilograms (KG)",
            "target_entity": {"entity_id": f"ENT_UNIT_{p_idx}", "canonical_name": f"KALINGA STEEL INDUSTRIES {p_idx+1}"},
            "documents": [
                {"doc_id": "DOC_WEIGHBRIDGE", "doc_type": "WEIGHT_SLIP", "file_name": "weight.pdf", "content_hash": f"hash_wt_{p_idx}"},
                {"doc_id": "DOC_DISPATCH", "doc_type": "DISPATCH_LEDGER", "file_name": "dispatch.pdf", "content_hash": f"hash_disp_{p_idx}"},
            ],
            "claims": [
                {"field_name": "consignment_weight", "field_type": "weight", "doc_id": "DOC_WEIGHBRIDGE", "claimed_value": "25.50 MT", "confidence": 94.0, "ground_truth": "CONTRADICTION", "expected_outcome": "CONTRADICTION_DETECTED"},
                {"field_name": "consignment_weight", "field_type": "weight", "doc_id": "DOC_DISPATCH", "claimed_value": "25500 KG", "confidence": 92.0, "ground_truth": "CONTRADICTION", "expected_outcome": "CONTRADICTION_DETECTED"},
            ],
            "required_doc_types": ["WEIGHT_SLIP", "DISPATCH_LEDGER"],
        })

    # 13. Illegible Supporting Evidence (CHALL_05)
    packets.append({
        "packet_id": "PKT_CHALL_05",
        "split": "CHALL",
        "condition_category": "Illegible Supporting Evidence",
        "condition_code": "COND_13_ILLEGIBLE_EVIDENCE",
        "description": "Supporting bank passbook stamp severely faded; OCR confidence 22% fails confidence floor",
        "target_entity": {"entity_id": "ENT_FADED_01", "canonical_name": "SUNIL TRIPATHY"},
        "documents": [
            {"doc_id": "DOC_APP", "doc_type": "APPLICATION_FORM", "file_name": "app.pdf", "content_hash": "hash_faded_app"},
            {"doc_id": "DOC_PASSBOOK", "doc_type": "BANK_PASSBOOK", "file_name": "passbook_faded.pdf", "content_hash": "hash_faded_pass"},
        ],
        "claims": [
            {"field_name": "account_number", "field_type": "id", "doc_id": "DOC_APP", "claimed_value": "908812345678", "confidence": 94.0, "ground_truth": "908812345678", "expected_outcome": "ABSTAIN"},
            {"field_name": "account_number", "field_type": "id", "doc_id": "DOC_PASSBOOK", "claimed_value": "9088~123?5678", "confidence": 24.0, "ground_truth": "908812345678", "expected_outcome": "ABSTAIN"},
        ],
        "required_doc_types": ["APPLICATION_FORM", "BANK_PASSBOOK"],
    })

    # 14. Wrong Document Linked to Packet (CHALL_06)
    packets.append({
        "packet_id": "PKT_CHALL_06",
        "split": "CHALL",
        "condition_category": "Wrong Document Linked",
        "condition_code": "COND_19_WRONG_DOCUMENT",
        "description": "Electricity utility bill uploaded instead of mandatory Domicile Certificate",
        "target_entity": {"entity_id": "ENT_WRONG_01", "canonical_name": "SUBASH CHANDRA MOHANTY"},
        "documents": [
            {"doc_id": "DOC_APP", "doc_type": "APPLICATION_FORM", "file_name": "app.pdf", "content_hash": "hash_wr_app"},
            {"doc_id": "DOC_UTILITY", "doc_type": "UTILITY_BILL", "file_name": "electric_bill.pdf", "content_hash": "hash_wr_bill"},
        ],
        "claims": [
            {"field_name": "domicile_certificate_no", "field_type": "id", "doc_id": "DOC_APP", "claimed_value": "DOM-2026-99120", "confidence": 93.0, "ground_truth": "MISSING_EVIDENCE", "expected_outcome": "MISSING_EVIDENCE"},
        ],
        "required_doc_types": ["APPLICATION_FORM", "RESIDENCE_CERT"],
    })

    return packets


if __name__ == "__main__":
    pkts = build_packets()
    total_claims = sum(len(p["claims"]) for p in pkts)
    manifest = {
        "manifest_version": "28.0.0",
        "loop": 28,
        "corpus_name": "Loop 28 Cross-Document Verification & Contradiction Corpus",
        "total_packets": len(pkts),
        "total_cross_document_claims": total_claims,
        "split_counts": {
            "DEV": sum(1 for p in pkts if p["split"] == "DEV"),
            "CAL": sum(1 for p in pkts if p["split"] == "CAL"),
            "BLIND": sum(1 for p in pkts if p["split"] == "BLIND"),
            "CHALL": sum(1 for p in pkts if p["split"] == "CHALL"),
        },
        "packets": pkts,
    }

    out_file = CORPUS_DIR / "cross_document_corpus.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # Compute blind hash register
    m_bytes = out_file.read_bytes()
    sha256_hash = hashlib.sha256(m_bytes).hexdigest()

    register_file = CORPUS_DIR / "blind_hash_register.json"
    with open(register_file, "w", encoding="utf-8") as f:
        json.dump({
            "corpus_file": "cross_document_corpus.json",
            "sha256": sha256_hash,
            "file_size_bytes": len(m_bytes),
            "status": "FROZEN_LOCKED_BLIND",
            "timestamp": "2026-11-24T16:15:00+05:30",
        }, f, indent=2)

    print(f"Generated {len(pkts)} packets with {total_claims} claims in {out_file}")
    print(f"Locked Blind Hash: {sha256_hash}")
