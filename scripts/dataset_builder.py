"""
Demonstration Dataset Builder for DocuReady MVP
Generates 8 synthetic test packets with real PDF files and compiles ground_truth_manifest.json.
All applicant data is 100% synthetic.
"""

import os
import json
from typing import Dict, Any

from src.generator import (
    generate_income_certificate, generate_caste_certificate,
    generate_residence_certificate, generate_marksheet,
    generate_bank_passbook, generate_application_form
)


def build_demonstration_dataset(base_dir: str) -> Dict[str, Any]:
    """Generates all 8 synthetic test cases and writes ground_truth_manifest.json."""
    os.makedirs(base_dir, exist_ok=True)
    manifest = {
        "dataset_name": "DocuReady Synthetic Multi-Document Evaluation Dataset",
        "version": "1.0.0",
        "date_created": "2026-11-13",
        "description": "Completely synthetic multi-document applicant packets covering 8 standard defect patterns.",
        "packets": {}
    }

    # ---------------- 1. CLEAN PACKET ----------------
    p1_dir = os.path.join(base_dir, "pkt_01_clean")
    os.makedirs(p1_dir, exist_ok=True)
    generate_income_certificate(
        os.path.join(p1_dir, "income_cert.pdf"),
        applicant_name="Smruti Ranjan Nayak",
        father_name="Ramesh Chandra Nayak",
        annual_income="Rs. 1,80,000/-",
        issue_date="10/01/2025",
        certificate_no="E-INC/2025/104928"
    )
    generate_caste_certificate(
        os.path.join(p1_dir, "caste_cert.pdf"),
        applicant_name="Smruti Ranjan Nayak",
        father_name="Ramesh Chandra Nayak",
        caste_category="SEBC",
        sub_caste="Chasa",
        issue_date="12/03/2024",
        certificate_no="CST/2025/88192"
    )
    generate_residence_certificate(
        os.path.join(p1_dir, "residence_cert.pdf"),
        applicant_name="Smruti Ranjan Nayak",
        father_name="Ramesh Chandra Nayak",
        address="Plot 104, Saheed Nagar, Bhubaneswar",
        state="ODISHA",
        issue_date="15/01/2025",
        certificate_no="RES/2025/99812"
    )
    generate_marksheet(
        os.path.join(p1_dir, "marksheet.pdf"),
        applicant_name="Smruti Ranjan Nayak",
        father_name="Ramesh Chandra Nayak",
        dob="14/05/2003",
        roll_no="2309BA1042",
        percentage=78.5
    )
    generate_bank_passbook(
        os.path.join(p1_dir, "bank_passbook.pdf"),
        applicant_name="Smruti Ranjan Nayak",
        account_no="30987654301",
        ifsc="SBIN0001234"
    )
    generate_application_form(
        os.path.join(p1_dir, "application_form.pdf"),
        applicant_name="Smruti Ranjan Nayak",
        father_name="Ramesh Chandra Nayak",
        dob="14/05/2003",
        annual_income="Rs. 1,80,000/-",
        caste_category="SEBC",
        income_cert_no="E-INC/2025/104928",
        caste_cert_no="CST/2025/88192",
        residence_cert_no="RES/2025/99812",
        account_no="30987654301",
        ifsc="SBIN0001234"
    )
    manifest["packets"]["PKT_01_CLEAN"] = {
        "packet_id": "PKT_01_CLEAN",
        "description": "Standard fully consistent applicant packet. All 6 documents match exactly.",
        "folder": "pkt_01_clean",
        "expected_status": "READY_TO_SUBMIT",
        "expected_score_min": 95,
        "expected_defects_count": 0,
        "expected_failure_rules": []
    }

    # ---------------- 2. CONFLICTING APPLICANT NAMES ----------------
    p2_dir = os.path.join(base_dir, "pkt_02_name_conflict")
    os.makedirs(p2_dir, exist_ok=True)
    generate_income_certificate(
        os.path.join(p2_dir, "income_cert.pdf"),
        applicant_name="Smruti Ranjan Nayak",
        father_name="Ramesh Chandra Nayak",
        annual_income="Rs. 1,80,000/-",
        issue_date="10/01/2025",
        certificate_no="E-INC/2025/104928"
    )
    generate_caste_certificate(
        os.path.join(p2_dir, "caste_cert.pdf"),
        applicant_name="Smruti Ranjan Nayak",
        father_name="Ramesh Chandra Nayak",
        caste_category="SEBC",
        sub_caste="Chasa",
        issue_date="12/03/2024",
        certificate_no="CST/2025/88192"
    )
    generate_residence_certificate(
        os.path.join(p2_dir, "residence_cert.pdf"),
        applicant_name="Smruti Ranjan Nayak",
        father_name="Ramesh Chandra Nayak",
        address="Plot 104, Saheed Nagar, Bhubaneswar",
        state="ODISHA",
        issue_date="15/01/2025",
        certificate_no="RES/2025/99812"
    )
    # Defect: Marksheet has completely different person's name
    generate_marksheet(
        os.path.join(p2_dir, "marksheet.pdf"),
        applicant_name="Rajesh Kumar Patel",
        father_name="Ramesh Chandra Nayak",
        dob="14/05/2003",
        roll_no="2309BA1042",
        percentage=78.5
    )
    generate_bank_passbook(
        os.path.join(p2_dir, "bank_passbook.pdf"),
        applicant_name="Smruti Ranjan Nayak",
        account_no="30987654301",
        ifsc="SBIN0001234"
    )
    generate_application_form(
        os.path.join(p2_dir, "application_form.pdf"),
        applicant_name="Smruti Ranjan Nayak",
        father_name="Ramesh Chandra Nayak",
        dob="14/05/2003",
        annual_income="Rs. 1,80,000/-",
        caste_category="SEBC",
        income_cert_no="E-INC/2025/104928",
        caste_cert_no="CST/2025/88192",
        residence_cert_no="RES/2025/99812",
        account_no="30987654301",
        ifsc="SBIN0001234"
    )
    manifest["packets"]["PKT_02_NAME_CONFLICT"] = {
        "packet_id": "PKT_02_NAME_CONFLICT",
        "description": "Marksheet belongs to Rajesh Kumar Patel instead of applicant Smruti Ranjan Nayak.",
        "folder": "pkt_02_name_conflict",
        "expected_status": "ACTION_REQUIRED",
        "expected_score_min": 0,
        "expected_defects_count": 1,
        "expected_failure_rules": ["RULE-NAME-01"]
    }

    # ---------------- 3. CONFLICTING DATES OF BIRTH ----------------
    p3_dir = os.path.join(base_dir, "pkt_03_dob_conflict")
    os.makedirs(p3_dir, exist_ok=True)
    generate_income_certificate(
        os.path.join(p3_dir, "income_cert.pdf"),
        applicant_name="Smruti Ranjan Nayak",
        father_name="Ramesh Chandra Nayak",
        annual_income="Rs. 1,80,000/-",
        issue_date="10/01/2025",
        certificate_no="E-INC/2025/104928"
    )
    generate_caste_certificate(
        os.path.join(p3_dir, "caste_cert.pdf"),
        applicant_name="Smruti Ranjan Nayak",
        father_name="Ramesh Chandra Nayak",
        caste_category="SEBC",
        sub_caste="Chasa",
        issue_date="12/03/2024",
        certificate_no="CST/2025/88192"
    )
    generate_residence_certificate(
        os.path.join(p3_dir, "residence_cert.pdf"),
        applicant_name="Smruti Ranjan Nayak",
        father_name="Ramesh Chandra Nayak",
        address="Plot 104, Saheed Nagar, Bhubaneswar",
        state="ODISHA",
        issue_date="15/01/2025",
        certificate_no="RES/2025/99812"
    )
    # Defect: Marksheet has 14/05/2005 vs Form 14/05/2003
    generate_marksheet(
        os.path.join(p3_dir, "marksheet.pdf"),
        applicant_name="Smruti Ranjan Nayak",
        father_name="Ramesh Chandra Nayak",
        dob="14/05/2005",
        roll_no="2309BA1042",
        percentage=78.5
    )
    generate_bank_passbook(
        os.path.join(p3_dir, "bank_passbook.pdf"),
        applicant_name="Smruti Ranjan Nayak",
        account_no="30987654301",
        ifsc="SBIN0001234"
    )
    generate_application_form(
        os.path.join(p3_dir, "application_form.pdf"),
        applicant_name="Smruti Ranjan Nayak",
        father_name="Ramesh Chandra Nayak",
        dob="14/05/2003",
        annual_income="Rs. 1,80,000/-",
        caste_category="SEBC",
        income_cert_no="E-INC/2025/104928",
        caste_cert_no="CST/2025/88192",
        residence_cert_no="RES/2025/99812",
        account_no="30987654301",
        ifsc="SBIN0001234"
    )
    manifest["packets"]["PKT_03_DOB_CONFLICT"] = {
        "packet_id": "PKT_03_DOB_CONFLICT",
        "description": "Date of Birth mismatch: Application form declares 14/05/2003 but Marksheet states 14/05/2005.",
        "folder": "pkt_03_dob_conflict",
        "expected_status": "ACTION_REQUIRED",
        "expected_score_min": 0,
        "expected_defects_count": 1,
        "expected_failure_rules": ["RULE-DOB-01"]
    }

    # ---------------- 4. CONFLICTING INCOME VALUES & CEILING BREACH ----------------
    p4_dir = os.path.join(base_dir, "pkt_04_income_conflict")
    os.makedirs(p4_dir, exist_ok=True)
    # Defect: Certified income is Rs. 3,20,000/- (exceeds 2.5L ceiling & conflicts with declared 1.8L)
    generate_income_certificate(
        os.path.join(p4_dir, "income_cert.pdf"),
        applicant_name="Smruti Ranjan Nayak",
        father_name="Ramesh Chandra Nayak",
        annual_income="Rs. 3,20,000/-",
        issue_date="10/01/2025",
        certificate_no="E-INC/2025/104928"
    )
    generate_caste_certificate(
        os.path.join(p4_dir, "caste_cert.pdf"),
        applicant_name="Smruti Ranjan Nayak",
        father_name="Ramesh Chandra Nayak",
        caste_category="SEBC",
        sub_caste="Chasa",
        issue_date="12/03/2024",
        certificate_no="CST/2025/88192"
    )
    generate_residence_certificate(
        os.path.join(p4_dir, "residence_cert.pdf"),
        applicant_name="Smruti Ranjan Nayak",
        father_name="Ramesh Chandra Nayak",
        address="Plot 104, Saheed Nagar, Bhubaneswar",
        state="ODISHA",
        issue_date="15/01/2025",
        certificate_no="RES/2025/99812"
    )
    generate_marksheet(
        os.path.join(p4_dir, "marksheet.pdf"),
        applicant_name="Smruti Ranjan Nayak",
        father_name="Ramesh Chandra Nayak",
        dob="14/05/2003",
        roll_no="2309BA1042",
        percentage=78.5
    )
    generate_bank_passbook(
        os.path.join(p4_dir, "bank_passbook.pdf"),
        applicant_name="Smruti Ranjan Nayak",
        account_no="30987654301",
        ifsc="SBIN0001234"
    )
    generate_application_form(
        os.path.join(p4_dir, "application_form.pdf"),
        applicant_name="Smruti Ranjan Nayak",
        father_name="Ramesh Chandra Nayak",
        dob="14/05/2003",
        annual_income="Rs. 1,80,000/-",
        caste_category="SEBC",
        income_cert_no="E-INC/2025/104928",
        caste_cert_no="CST/2025/88192",
        residence_cert_no="RES/2025/99812",
        account_no="30987654301",
        ifsc="SBIN0001234"
    )
    manifest["packets"]["PKT_04_INCOME_CONFLICT"] = {
        "packet_id": "PKT_04_INCOME_CONFLICT",
        "description": "Income Certificate states Rs. 3,20,000/- (exceeding statutory 2.5L ceiling and conflicting with declared 1.8L).",
        "folder": "pkt_04_income_conflict",
        "expected_status": "REJECT_PRECHECK",
        "expected_score_min": 0,
        "expected_defects_count": 2,
        "expected_failure_rules": ["RULE-INC-01", "RULE-INC-02"]
    }

    # ---------------- 5. MISSING CERTIFICATE ----------------
    p5_dir = os.path.join(base_dir, "pkt_05_missing_certificate")
    os.makedirs(p5_dir, exist_ok=True)
    generate_income_certificate(
        os.path.join(p5_dir, "income_cert.pdf"),
        applicant_name="Smruti Ranjan Nayak",
        father_name="Ramesh Chandra Nayak",
        annual_income="Rs. 1,80,000/-",
        issue_date="10/01/2025",
        certificate_no="E-INC/2025/104928"
    )
    # Defect: caste_cert.pdf is omitted entirely!
    generate_residence_certificate(
        os.path.join(p5_dir, "residence_cert.pdf"),
        applicant_name="Smruti Ranjan Nayak",
        father_name="Ramesh Chandra Nayak",
        address="Plot 104, Saheed Nagar, Bhubaneswar",
        state="ODISHA",
        issue_date="15/01/2025",
        certificate_no="RES/2025/99812"
    )
    generate_marksheet(
        os.path.join(p5_dir, "marksheet.pdf"),
        applicant_name="Smruti Ranjan Nayak",
        father_name="Ramesh Chandra Nayak",
        dob="14/05/2003",
        roll_no="2309BA1042",
        percentage=78.5
    )
    generate_bank_passbook(
        os.path.join(p5_dir, "bank_passbook.pdf"),
        applicant_name="Smruti Ranjan Nayak",
        account_no="30987654301",
        ifsc="SBIN0001234"
    )
    generate_application_form(
        os.path.join(p5_dir, "application_form.pdf"),
        applicant_name="Smruti Ranjan Nayak",
        father_name="Ramesh Chandra Nayak",
        dob="14/05/2003",
        annual_income="Rs. 1,80,000/-",
        caste_category="SEBC",
        income_cert_no="E-INC/2025/104928",
        caste_cert_no="CST/2025/88192",
        residence_cert_no="RES/2025/99812",
        account_no="30987654301",
        ifsc="SBIN0001234"
    )
    manifest["packets"]["PKT_05_MISSING_CERTIFICATE"] = {
        "packet_id": "PKT_05_MISSING_CERTIFICATE",
        "description": "Mandatory Caste Certificate is absent from the packet.",
        "folder": "pkt_05_missing_certificate",
        "expected_status": "REJECT_PRECHECK",
        "expected_score_min": 0,
        "expected_defects_count": 1,
        "expected_failure_rules": ["RULE-DOC-01"]
    }

    # ---------------- 6. MULTIPLE SIMULTANEOUS DEFECTS ----------------
    p6_dir = os.path.join(base_dir, "pkt_06_multiple_defects")
    os.makedirs(p6_dir, exist_ok=True)
    # Defect A: Expired income cert (issued 10/01/2020, >3 years old)
    generate_income_certificate(
        os.path.join(p6_dir, "income_cert.pdf"),
        applicant_name="Smruti Ranjan Nayak",
        father_name="Ramesh Chandra Nayak",
        annual_income="Rs. 1,80,000/-",
        issue_date="10/01/2020",
        certificate_no="E-INC/2020/004928"
    )
    generate_caste_certificate(
        os.path.join(p6_dir, "caste_cert.pdf"),
        applicant_name="Smruti Ranjan Nayak",
        father_name="Ramesh Chandra Nayak",
        caste_category="SEBC",
        sub_caste="Chasa",
        issue_date="12/03/2024",
        certificate_no="CST/2025/88192"
    )
    generate_residence_certificate(
        os.path.join(p6_dir, "residence_cert.pdf"),
        applicant_name="Smruti Ranjan Nayak",
        father_name="Ramesh Chandra Nayak",
        address="Plot 104, Saheed Nagar, Bhubaneswar",
        state="ODISHA",
        issue_date="15/01/2025",
        certificate_no="RES/2025/99812"
    )
    # Defect B: DOB mismatch (2006 vs 2003) and Marks below cutoff (41.0% < 50.0%)
    generate_marksheet(
        os.path.join(p6_dir, "marksheet.pdf"),
        applicant_name="Smruti Ranjan Nayak",
        father_name="Ramesh Chandra Nayak",
        dob="14/05/2006",
        roll_no="2309BA1042",
        percentage=41.0
    )
    # Defect C: Bank Passbook name belongs to different individual ("Sanjay Panda")
    generate_bank_passbook(
        os.path.join(p6_dir, "bank_passbook.pdf"),
        applicant_name="Sanjay Panda",
        account_no="30987654301",
        ifsc="SBIN0001234"
    )
    generate_application_form(
        os.path.join(p6_dir, "application_form.pdf"),
        applicant_name="Smruti Ranjan Nayak",
        father_name="Ramesh Chandra Nayak",
        dob="14/05/2003",
        annual_income="Rs. 1,80,000/-",
        caste_category="SEBC",
        income_cert_no="E-INC/2020/004928",
        caste_cert_no="CST/2025/88192",
        residence_cert_no="RES/2025/99812",
        account_no="30987654301",
        ifsc="SBIN0001234"
    )
    manifest["packets"]["PKT_06_MULTIPLE_DEFECTS"] = {
        "packet_id": "PKT_06_MULTIPLE_DEFECTS",
        "description": "Multiple defects: Expired income certificate, academic marks below cutoff, DOB mismatch, passbook name discrepancy.",
        "folder": "pkt_06_multiple_defects",
        "expected_status": "ACTION_REQUIRED",
        "expected_score_min": 0,
        "expected_defects_count": 4,
        "expected_failure_rules": ["RULE-EXP-01", "RULE-MRK-01", "RULE-DOB-01", "RULE-NAME-01"]
    }

    # ---------------- 7. UNREADABLE DOCUMENT ----------------
    p7_dir = os.path.join(base_dir, "pkt_07_unreadable_doc")
    os.makedirs(p7_dir, exist_ok=True)
    # Defect: Income Certificate is unreadable/corrupted scan
    generate_income_certificate(
        os.path.join(p7_dir, "income_cert.pdf"),
        applicant_name="Smruti Ranjan Nayak",
        father_name="Ramesh Chandra Nayak",
        annual_income="Rs. 1,80,000/-",
        issue_date="10/01/2025",
        certificate_no="E-INC/2025/104928",
        is_unreadable=True
    )
    generate_caste_certificate(
        os.path.join(p7_dir, "caste_cert.pdf"),
        applicant_name="Smruti Ranjan Nayak",
        father_name="Ramesh Chandra Nayak",
        caste_category="SEBC",
        sub_caste="Chasa",
        issue_date="12/03/2024",
        certificate_no="CST/2025/88192"
    )
    generate_residence_certificate(
        os.path.join(p7_dir, "residence_cert.pdf"),
        applicant_name="Smruti Ranjan Nayak",
        father_name="Ramesh Chandra Nayak",
        address="Plot 104, Saheed Nagar, Bhubaneswar",
        state="ODISHA",
        issue_date="15/01/2025",
        certificate_no="RES/2025/99812"
    )
    generate_marksheet(
        os.path.join(p7_dir, "marksheet.pdf"),
        applicant_name="Smruti Ranjan Nayak",
        father_name="Ramesh Chandra Nayak",
        dob="14/05/2003",
        roll_no="2309BA1042",
        percentage=78.5
    )
    generate_bank_passbook(
        os.path.join(p7_dir, "bank_passbook.pdf"),
        applicant_name="Smruti Ranjan Nayak",
        account_no="30987654301",
        ifsc="SBIN0001234"
    )
    generate_application_form(
        os.path.join(p7_dir, "application_form.pdf"),
        applicant_name="Smruti Ranjan Nayak",
        father_name="Ramesh Chandra Nayak",
        dob="14/05/2003",
        annual_income="Rs. 1,80,000/-",
        caste_category="SEBC",
        income_cert_no="E-INC/2025/104928",
        caste_cert_no="CST/2025/88192",
        residence_cert_no="RES/2025/99812",
        account_no="30987654301",
        ifsc="SBIN0001234"
    )
    manifest["packets"]["PKT_07_UNREADABLE_DOC"] = {
        "packet_id": "PKT_07_UNREADABLE_DOC",
        "description": "Income Certificate has illegible scan / corrupt text quality.",
        "folder": "pkt_07_unreadable_doc",
        "expected_status": "UNREADABLE_PACKET",
        "expected_score_min": 0,
        "expected_defects_count": 1,
        "expected_failure_rules": ["RULE-DOC-02"]
    }

    # ---------------- 8. AMBIGUOUS EVIDENCE ----------------
    p8_dir = os.path.join(base_dir, "pkt_08_ambiguous_evidence")
    os.makedirs(p8_dir, exist_ok=True)
    generate_income_certificate(
        os.path.join(p8_dir, "income_cert.pdf"),
        applicant_name="Smruti Ranjan Nayak",
        father_name="Ramesh Chandra Nayak",
        annual_income="Rs. 1,80,000/-",
        issue_date="10/01/2025",
        certificate_no="E-INC/2025/104928"
    )
    generate_caste_certificate(
        os.path.join(p8_dir, "caste_cert.pdf"),
        applicant_name="Smruti Ranjan Nayak",
        father_name="Ramesh Chandra Nayak",
        caste_category="SEBC",
        sub_caste="Chasa",
        issue_date="12/03/2024",
        certificate_no="CST/2025/88192"
    )
    generate_residence_certificate(
        os.path.join(p8_dir, "residence_cert.pdf"),
        applicant_name="Smruti Ranjan Nayak",
        father_name="Ramesh Chandra Nayak",
        address="Plot 104, Saheed Nagar, Bhubaneswar",
        state="ODISHA",
        issue_date="15/01/2025",
        certificate_no="RES/2025/99812"
    )
    # Ambiguity 1: DOB written as 05/04/2003 vs 04/05/2003 (both <= 12)
    generate_marksheet(
        os.path.join(p8_dir, "marksheet.pdf"),
        applicant_name="Smruti Ranjan Nayak",
        father_name="Ramesh Chandra Nayak",
        dob="05/04/2003",
        roll_no="2309BA1042",
        percentage=78.5
    )
    # Ambiguity 2: Initials variation "S R Nayak" on passbook vs "Smruti Ranjan Nayak"
    generate_bank_passbook(
        os.path.join(p8_dir, "bank_passbook.pdf"),
        applicant_name="S R Nayak",
        account_no="30987654301",
        ifsc="SBIN0001234"
    )
    generate_application_form(
        os.path.join(p8_dir, "application_form.pdf"),
        applicant_name="Smruti Ranjan Nayak",
        father_name="Ramesh Chandra Nayak",
        dob="04/05/2003",
        annual_income="Rs. 1,80,000/-",
        caste_category="SEBC",
        income_cert_no="E-INC/2025/104928",
        caste_cert_no="CST/2025/88192",
        residence_cert_no="RES/2025/99812",
        account_no="30987654301",
        ifsc="SBIN0001234"
    )
    manifest["packets"]["PKT_08_AMBIGUOUS_EVIDENCE"] = {
        "packet_id": "PKT_08_AMBIGUOUS_EVIDENCE",
        "description": "Date format ambiguity (04/05/2003 vs 05/04/2003) and Name initial variation ('S R Nayak' vs 'Smruti Ranjan Nayak').",
        "folder": "pkt_08_ambiguous_evidence",
        "expected_status": "REVIEW_RECOMMENDED",
        "expected_score_min": 75,
        "expected_defects_count": 2,
        "expected_failure_rules": ["RULE-DOB-02", "RULE-NAME-02"]
    }

    manifest_path = os.path.join(os.path.dirname(base_dir), "ground_truth_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return manifest


if __name__ == "__main__":
    import sys
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "docuready-mvp/synthetic_data"
    m = build_demonstration_dataset(out_dir)
    print(f"Generated {len(m['packets'])} test packets in '{out_dir}'.")
