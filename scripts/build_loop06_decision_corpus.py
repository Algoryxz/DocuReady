"""
Loop 06 Decision Corpus Generator
Builds 16 controlled applicant packets in synthetic_data/loop06_decision_corpus/
to stress-test every audit decision engine invariant, scoring rule, status transition,
and conflict resolution path.
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from docuready.generator import (
    generate_application_form,
    generate_bank_passbook,
    generate_caste_certificate,
    generate_income_certificate,
    generate_marksheet,
    generate_residence_certificate,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
CORPUS_DIR = REPO_ROOT / "synthetic_data" / "loop06_decision_corpus"

def clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)

def build_corpus() -> None:
    clean_dir(CORPUS_DIR)

    manifest = {
        "corpus_version": "1.0.0",
        "engineering_loop": "Loop 06 — Audit Decision Engine Calibration & Rule Integrity",
        "total_packets": 16,
        "as_of_reference": "2026-11-16",
        "packets": {}
    }

    # Common valid details
    std_name = "Smruti Nayak"
    std_father = "Rabindranath Nayak"
    std_dob = "14/05/2003"
    std_income = "Rs. 1,80,000/-"
    std_caste = "SEBC"
    std_sub_caste = "GOPALA"
    std_income_no = "E-INC/2025/104928"
    std_caste_no = "CST/2025/88192"
    std_res_no = "RES/2025/99812"
    std_acct = "30987654301"
    std_ifsc = "SBIN0001234"
    std_pct = 72.5
    std_roll = "24OD10492"

    def write_standard_packet(p_dir: Path, **overrides) -> None:
        p_dir.mkdir(parents=True, exist_ok=True)
        # Application Form
        generate_application_form(
            str(p_dir / "application_form.pdf"),
            applicant_name=overrides.get("app_name", std_name),
            father_name=overrides.get("app_father", std_father),
            dob=overrides.get("app_dob", std_dob),
            annual_income=overrides.get("app_income", std_income),
            caste_category=overrides.get("app_caste", std_caste),
            income_cert_no=overrides.get("app_inc_no", std_income_no),
            caste_cert_no=overrides.get("app_cst_no", std_caste_no),
            residence_cert_no=overrides.get("app_res_no", std_res_no),
            account_no=overrides.get("app_acct", std_acct),
            ifsc=overrides.get("app_ifsc", std_ifsc),
        )
        # Income Certificate
        if not overrides.get("skip_income", False):
            generate_income_certificate(
                str(p_dir / "income_cert.pdf"),
                applicant_name=overrides.get("inc_name", std_name),
                father_name=overrides.get("inc_father", std_father),
                annual_income=overrides.get("inc_income", std_income),
                issue_date=overrides.get("inc_issue_date", "15/01/2025"),
                certificate_no=overrides.get("inc_no", std_income_no),
                is_unreadable=overrides.get("inc_unreadable", False),
            )
        # Caste Certificate
        if not overrides.get("skip_caste", False):
            generate_caste_certificate(
                str(p_dir / "caste_cert.pdf"),
                applicant_name=overrides.get("cst_name", std_name),
                father_name=overrides.get("cst_father", std_father),
                caste_category=overrides.get("cst_caste", std_caste),
                sub_caste=overrides.get("cst_sub_caste", std_sub_caste),
                issue_date=overrides.get("cst_issue_date", "10/06/2024"),
                certificate_no=overrides.get("cst_no", std_caste_no),
            )
        # Residence Certificate
        if not overrides.get("skip_residence", False):
            generate_residence_certificate(
                str(p_dir / "residence_cert.pdf"),
                applicant_name=overrides.get("res_name", std_name),
                father_name=overrides.get("res_father", std_father),
                address="AT-KHANDAGIRI, PS-KHANDAGIRI, BHUBANESWAR",
                state=overrides.get("res_state", "ODISHA"),
                issue_date="15/01/2025",
                certificate_no=overrides.get("res_no", std_res_no),
            )
        # Marksheet
        if not overrides.get("skip_marksheet", False):
            generate_marksheet(
                str(p_dir / "marksheet.pdf"),
                applicant_name=overrides.get("mrk_name", std_name),
                father_name=overrides.get("mrk_father", std_father),
                dob=overrides.get("mrk_dob", std_dob),
                roll_no=std_roll,
                percentage=overrides.get("mrk_pct", std_pct),
            )
        # Bank Passbook
        if not overrides.get("skip_bank", False):
            generate_bank_passbook(
                str(p_dir / "bank_passbook.pdf"),
                applicant_name=overrides.get("bnk_name", std_name),
                account_no=overrides.get("bnk_acct", std_acct),
                ifsc=overrides.get("bnk_ifsc", std_ifsc),
            )

    # 1. PKT_01_CLEAN
    p1 = CORPUS_DIR / "PKT_01_CLEAN"
    write_standard_packet(p1)
    manifest["packets"]["PKT_01_CLEAN"] = {
        "description": "Clean upright packet with all 6 valid matching documents",
        "expected_status": "NO_ISSUES_FOUND",
        "expected_score": 100,
        "expected_defects": [],
        "category": "CLEAN"
    }

    # 2. PKT_02_NAME_MISMATCH
    p2 = CORPUS_DIR / "PKT_02_NAME_MISMATCH"
    write_standard_packet(p2, inc_name="Ramesh Patel")
    manifest["packets"]["PKT_02_NAME_MISMATCH"] = {
        "description": "Hard applicant name conflict between Form ('Smruti Nayak') and Income Cert ('Ramesh Patel')",
        "expected_status": "NOT_READY",
        "expected_score": 75,
        "expected_defects": ["RULE-NAME-01"],
        "category": "DEFECTIVE"
    }

    # 3. PKT_03_DOB_MISMATCH
    p3 = CORPUS_DIR / "PKT_03_DOB_MISMATCH"
    write_standard_packet(p3, mrk_dob="20/11/2001")
    manifest["packets"]["PKT_03_DOB_MISMATCH"] = {
        "description": "Hard date of birth mismatch between Form ('14/05/2003') and Marksheet ('20/11/2001')",
        "expected_status": "NOT_READY",
        "expected_score": 75,
        "expected_defects": ["RULE-DOB-01"],
        "category": "DEFECTIVE"
    }

    # 4. PKT_04_INCOME_EXCEEDS_CEILING
    p4 = CORPUS_DIR / "PKT_04_INCOME_EXCEEDS_CEILING"
    write_standard_packet(p4, inc_income="Rs. 3,80,000/-", app_income="Rs. 3,80,000/-")
    manifest["packets"]["PKT_04_INCOME_EXCEEDS_CEILING"] = {
        "description": "Certified family income (₹3,80,000) exceeds scheme statutory ceiling (₹2,50,000)",
        "expected_status": "NOT_READY",
        "expected_score": 65,
        "expected_defects": ["RULE-INC-01"],
        "category": "DEFECTIVE"
    }

    # 5. PKT_05_MISSING_MANDATORY_DOC
    p5 = CORPUS_DIR / "PKT_05_MISSING_MANDATORY_DOC"
    write_standard_packet(p5, skip_income=True)
    manifest["packets"]["PKT_05_MISSING_MANDATORY_DOC"] = {
        "description": "Mandatory Income Certificate is missing from packet",
        "expected_status": "NOT_READY",
        "expected_score": 65,
        "expected_defects": ["RULE-DOC-01"],
        "category": "DEFECTIVE"
    }

    # 6. PKT_06_UNREADABLE_MANDATORY_DOC
    p6 = CORPUS_DIR / "PKT_06_UNREADABLE_MANDATORY_DOC"
    write_standard_packet(p6, inc_unreadable=True)
    manifest["packets"]["PKT_06_UNREADABLE_MANDATORY_DOC"] = {
        "description": "Mandatory Income Certificate is unreadable scan (abstains to REVIEW)",
        "expected_status": "NEEDS_CHECKS",
        "expected_score": 75,
        "expected_defects": ["RULE-DOC-02"],
        "category": "UNCERTAIN"
    }

    # 7. PKT_07_COMPATIBLE_NAME_VARIATION
    p7 = CORPUS_DIR / "PKT_07_COMPATIBLE_NAME_VARIATION"
    write_standard_packet(p7, app_name="Smruti Ranjan Nayak", cst_name="Smruti Nayak")
    manifest["packets"]["PKT_07_COMPATIBLE_NAME_VARIATION"] = {
        "description": "Compatible middle name variation between Form ('Smruti Ranjan Nayak') and Caste ('Smruti Nayak')",
        "expected_status": "NEEDS_CHECKS",
        "expected_score": 75,
        "expected_defects": ["RULE-NAME-02"],
        "category": "UNCERTAIN"
    }

    # 8. PKT_08_EXPIRED_CERTIFICATE
    p8 = CORPUS_DIR / "PKT_08_EXPIRED_CERTIFICATE"
    write_standard_packet(p8, inc_issue_date="10/01/2021")
    manifest["packets"]["PKT_08_EXPIRED_CERTIFICATE"] = {
        "description": "Income Certificate issued on 10/01/2021 exceeds 3-year statutory validity as of Nov 2026",
        "expected_status": "NOT_READY",
        "expected_score": 75,
        "expected_defects": ["RULE-EXP-01"],
        "category": "DEFECTIVE"
    }

    # 9. PKT_09_DOMICILE_MISMATCH
    p9 = CORPUS_DIR / "PKT_09_DOMICILE_MISMATCH"
    write_standard_packet(p9, res_state="BIHAR")
    manifest["packets"]["PKT_09_DOMICILE_MISMATCH"] = {
        "description": "Residence Certificate issued by BIHAR fails statutory ODISHA domicile rule",
        "expected_status": "NOT_READY",
        "expected_score": 75,
        "expected_defects": ["RULE-DOM-01"],
        "category": "DEFECTIVE"
    }

    # 10. PKT_10_INTERACTION_NAME_CONFLICT_AND_MISSING_DOC
    p10 = CORPUS_DIR / "PKT_10_INTERACTION_NAME_CONFLICT_AND_MISSING_DOC"
    write_standard_packet(p10, mrk_name="Priya Sharma", skip_residence=True)
    manifest["packets"]["PKT_10_INTERACTION_NAME_CONFLICT_AND_MISSING_DOC"] = {
        "description": "Interaction: Name conflict on Marksheet (-25) + missing Residence Certificate (-35)",
        "expected_status": "NOT_READY",
        "expected_score": 40,
        "expected_defects": ["RULE-NAME-01", "RULE-DOC-01"],
        "category": "INTERACTION"
    }

    # 11. PKT_11_INTERACTION_DOB_CONFLICT_AND_UNREADABLE_DOC
    p11 = CORPUS_DIR / "PKT_11_INTERACTION_DOB_CONFLICT_AND_UNREADABLE_DOC"
    write_standard_packet(p11, mrk_dob="20/11/2001", inc_unreadable=True)
    manifest["packets"]["PKT_11_INTERACTION_DOB_CONFLICT_AND_UNREADABLE_DOC"] = {
        "description": "Interaction: Hard DOB mismatch (-25) + unreadable Income Certificate (-25)",
        "expected_status": "NOT_READY",
        "expected_score": 50,
        "expected_defects": ["RULE-DOB-01", "RULE-DOC-02"],
        "category": "INTERACTION"
    }

    # 12. PKT_12_SLOT_MISMATCH
    p12 = CORPUS_DIR / "PKT_12_SLOT_MISMATCH"
    write_standard_packet(p12, skip_income=True)
    # Put marksheet into income_cert.pdf slot
    shutil.copyfile(p12 / "marksheet.pdf", p12 / "income_cert.pdf")
    manifest["packets"]["PKT_12_SLOT_MISMATCH"] = {
        "description": "Slot Mismatch: Marksheet uploaded into income_cert.pdf slot",
        "expected_status": "NEEDS_CHECKS",
        "expected_score": 90,
        "expected_defects": ["RULE-SLOT-01"],
        "category": "UNCERTAIN"
    }

    # 13. PKT_13_CATEGORY_EXEMPTION_VERIFIED
    p13 = CORPUS_DIR / "PKT_13_CATEGORY_EXEMPTION_VERIFIED"
    write_standard_packet(p13, mrk_pct=45.0, app_caste="SCHEDULED TRIBE", cst_caste="SCHEDULED TRIBE")
    manifest["packets"]["PKT_13_CATEGORY_EXEMPTION_VERIFIED"] = {
        "description": "ST candidate marks (45%) below standard cutoff (50%) but exempt under Post-Matric Clause 5.2",
        "expected_status": "NO_ISSUES_FOUND",
        "expected_score": 100,
        "expected_defects": [],
        "category": "CLEAN"
    }

    # 14. PKT_14_CATEGORY_EXEMPTION_UNCERTAIN
    p14 = CORPUS_DIR / "PKT_14_CATEGORY_EXEMPTION_UNCERTAIN"
    write_standard_packet(p14, mrk_pct=45.0, app_caste="SCHEDULED TRIBE", skip_caste=True)
    manifest["packets"]["PKT_14_CATEGORY_EXEMPTION_UNCERTAIN"] = {
        "description": "Candidate marks 45%, but Caste Certificate missing so exemption cannot be verified",
        "expected_status": "NOT_READY",
        "expected_score": 65,
        "expected_defects": ["RULE-DOC-01", "RULE-MRK-01"],
        "category": "INTERACTION"
    }

    # 15. PKT_15_DUPLICATE_DOCUMENTS_CLEAN
    p15 = CORPUS_DIR / "PKT_15_DUPLICATE_DOCUMENTS_CLEAN"
    write_standard_packet(p15)
    # Add an additional copy of caste cert as extra document
    shutil.copyfile(p15 / "caste_cert.pdf", p15 / "caste_cert_copy.pdf")
    manifest["packets"]["PKT_15_DUPLICATE_DOCUMENTS_CLEAN"] = {
        "description": "Clean packet with harmless additional duplicate certificate copy",
        "expected_status": "NO_ISSUES_FOUND",
        "expected_score": 100,
        "expected_defects": [],
        "category": "CLEAN"
    }

    # 16. PKT_16_EMPTY_PACKET_FAIL_CLOSED
    p16 = CORPUS_DIR / "PKT_16_EMPTY_PACKET_FAIL_CLOSED"
    p16.mkdir(parents=True, exist_ok=True)
    manifest["packets"]["PKT_16_EMPTY_PACKET_FAIL_CLOSED"] = {
        "description": "Empty packet (zero uploaded documents) fails closed to NOT_READY",
        "expected_status": "NOT_READY",
        "expected_score": 0,
        "expected_defects": ["RULE-DOC-01"],
        "category": "DEFECTIVE"
    }

    # Write manifest
    manifest_path = CORPUS_DIR / "LOOP06_CORPUS_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Generated {len(manifest['packets'])} packets in {CORPUS_DIR}")
    print(f"Manifest written to {manifest_path}")

if __name__ == "__main__":
    build_corpus()
