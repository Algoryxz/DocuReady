"""
Loop 07 Adversarial Corpus Generator
Builds 131 independently defined test scenarios under synthetic_data/loop07_adversarial_corpus/
spanning 11 distinct scenario families with explicit ground-truth manifests and 3-way split:
- Development set: 65 scenarios (50%)
- Validation set: 33 scenarios (25%)
- Challenge set: 33 scenarios (25%)
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
CORPUS_DIR = REPO_ROOT / "synthetic_data" / "loop07_adversarial_corpus"

def clean_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)

def build_corpus() -> None:
    clean_dir(CORPUS_DIR)

    manifest = {
        "corpus_version": "2.0.0",
        "engineering_loop": "Loop 07 — Adversarial Corpus Expansion & Decision Generalization",
        "total_scenarios": 131,
        "as_of_reference": "2026-11-16",
        "splits": {
            "development_count": 65,
            "validation_count": 33,
            "challenge_count": 33,
        },
        "scenarios": {}
    }

    # Standard clean applicant defaults
    s_name = "Smruti Nayak"
    s_father = "Rabindranath Nayak"
    s_dob = "14/05/2003"
    s_income = "Rs. 1,80,000/-"
    s_caste = "SEBC"
    s_sub_caste = "GOPALA"
    s_inc_no = "E-INC/2025/104928"
    s_cst_no = "CST/2025/88192"
    s_res_no = "RES/2025/99812"
    s_acct = "30987654301"
    s_ifsc = "SBIN0001234"
    s_pct = 72.5
    s_roll = "24OD10492"

    def write_packet(p_dir: Path, **o) -> None:
        p_dir.mkdir(parents=True, exist_ok=True)
        # Form
        if not o.get("skip_form", False):
            generate_application_form(
                str(p_dir / "application_form.pdf"),
                applicant_name=o.get("app_name", s_name),
                father_name=o.get("app_father", s_father),
                dob=o.get("app_dob", s_dob),
                annual_income=o.get("app_income", s_income),
                caste_category=o.get("app_caste", s_caste),
                income_cert_no=o.get("app_inc_no", s_inc_no),
                caste_cert_no=o.get("app_cst_no", s_cst_no),
                residence_cert_no=o.get("app_res_no", s_res_no),
                account_no=o.get("app_acct", s_acct),
                ifsc=o.get("app_ifsc", s_ifsc),
            )
        # Income
        if not o.get("skip_income", False):
            generate_income_certificate(
                str(p_dir / "income_cert.pdf"),
                applicant_name=o.get("inc_name", s_name),
                father_name=o.get("inc_father", s_father),
                annual_income=o.get("inc_income", s_income),
                issue_date=o.get("inc_issue_date", "15/01/2025"),
                certificate_no=o.get("inc_no", s_inc_no),
                is_unreadable=o.get("inc_unreadable", False),
            )
        # Caste
        if not o.get("skip_caste", False):
            generate_caste_certificate(
                str(p_dir / "caste_cert.pdf"),
                applicant_name=o.get("cst_name", s_name),
                father_name=o.get("cst_father", s_father),
                caste_category=o.get("cst_caste", s_caste),
                sub_caste=o.get("cst_sub_caste", s_sub_caste),
                issue_date=o.get("cst_issue_date", "10/06/2024"),
                certificate_no=o.get("cst_no", s_cst_no),
            )
        # Residence
        if not o.get("skip_residence", False):
            generate_residence_certificate(
                str(p_dir / "residence_cert.pdf"),
                applicant_name=o.get("res_name", s_name),
                father_name=o.get("res_father", s_father),
                address=o.get("res_addr", "AT-KHANDAGIRI, PS-KHANDAGIRI, BHUBANESWAR"),
                state=o.get("res_state", "ODISHA"),
                district=o.get("res_dist", "KHORDHA"),
                issue_date=o.get("res_issue_date", "15/01/2025"),
                certificate_no=o.get("res_no", s_res_no),
            )
        # Marksheet
        if not o.get("skip_marksheet", False):
            generate_marksheet(
                str(p_dir / "marksheet.pdf"),
                applicant_name=o.get("mrk_name", s_name),
                father_name=o.get("mrk_father", s_father),
                dob=o.get("mrk_dob", s_dob),
                roll_no=s_roll,
                percentage=o.get("mrk_pct", s_pct),
            )
        # Bank
        if not o.get("skip_bank", False):
            generate_bank_passbook(
                str(p_dir / "bank_passbook.pdf"),
                applicant_name=o.get("bnk_name", s_name),
                account_no=o.get("bnk_acct", s_acct),
                ifsc=o.get("bnk_ifsc", s_ifsc),
                bank_name=o.get("bnk_name_bank", "State Bank of India"),
            )

    scenario_idx = 0

    def add_scenario(scn_id, family, desc, exp_status, exp_score, defects, split, **kwargs):
        nonlocal scenario_idx
        scenario_idx += 1
        p_dir = CORPUS_DIR / scn_id
        write_packet(p_dir, **kwargs)
        manifest["scenarios"][scn_id] = {
            "index": scenario_idx,
            "family": family,
            "description": desc,
            "split": split,
            "expected_status": exp_status,
            "expected_score": exp_score,
            "expected_defects": defects,
        }

    # -------------------------------------------------------------------------
    # FAMILY A: CLEAN CONTROLS (10 Scenarios)
    # -------------------------------------------------------------------------
    add_scenario("SCN_A01_CLEAN_BASELINE_ODISHA", "CLEAN_CONTROLS", "Standard perfect Odisha applicant", "NO_ISSUES_FOUND", 100, [], "development")
    add_scenario("SCN_A02_CLEAN_TWO_TOKEN_NAME", "CLEAN_CONTROLS", "Clean applicant with 2-token name 'Amit Kumar'", "NO_ISSUES_FOUND", 100, [], "development", app_name="Amit Kumar", inc_name="Amit Kumar", cst_name="Amit Kumar", res_name="Amit Kumar", mrk_name="Amit Kumar", bnk_name="Amit Kumar")
    add_scenario("SCN_A03_CLEAN_THREE_TOKEN_NAME", "CLEAN_CONTROLS", "Clean applicant with 3-token name 'Pooja Rani Sahu'", "NO_ISSUES_FOUND", 100, [], "development", app_name="Pooja Rani Sahu", inc_name="Pooja Rani Sahu", cst_name="Pooja Rani Sahu", res_name="Pooja Rani Sahu", mrk_name="Pooja Rani Sahu", bnk_name="Pooja Rani Sahu")
    add_scenario("SCN_A04_CLEAN_GENERAL_CATEGORY", "CLEAN_CONTROLS", "General category candidate with 65% merit marks", "NO_ISSUES_FOUND", 100, [], "validation", app_caste="GENERAL", cst_caste="GENERAL", mrk_pct=65.0)
    add_scenario("SCN_A05_CLEAN_HIGH_MERIT", "CLEAN_CONTROLS", "High merit 95% candidate", "NO_ISSUES_FOUND", 100, [], "validation", mrk_pct=95.0)
    add_scenario("SCN_A06_CLEAN_LOW_INCOME", "CLEAN_CONTROLS", "Low annual income candidate (₹45,000/yr)", "NO_ISSUES_FOUND", 100, [], "challenge", app_income="Rs. 45,000/-", inc_income="Rs. 45,000/-")
    add_scenario("SCN_A07_CLEAN_RECENT_CERTIFICATE", "CLEAN_CONTROLS", "Recent certificate issued on 15/10/2026", "NO_ISSUES_FOUND", 100, [], "challenge", inc_issue_date="15/10/2026")
    add_scenario("SCN_A08_CLEAN_DIFFERENT_DISTRICT", "CLEAN_CONTROLS", "District Cuttack instead of Khordha within Odisha", "NO_ISSUES_FOUND", 100, [], "development", res_dist="CUTTACK")
    add_scenario("SCN_A09_CLEAN_DIFFERENT_BANK", "CLEAN_CONTROLS", "Punjab National Bank with PUNB0123400 IFSC", "NO_ISSUES_FOUND", 100, [], "validation", app_ifsc="PUNB0123400", bnk_ifsc="PUNB0123400", bnk_name_bank="Punjab National Bank")
    add_scenario("SCN_A10_CLEAN_A4_STANDARD_FONTS", "CLEAN_CONTROLS", "A4 standard styling clean control", "NO_ISSUES_FOUND", 100, [], "challenge")

    # -------------------------------------------------------------------------
    # FAMILY B: DOCUMENT COMPLETENESS (12 Scenarios)
    # -------------------------------------------------------------------------
    add_scenario("SCN_B01_MISSING_INCOME_CERT", "DOCUMENT_COMPLETENESS", "Missing mandatory Income Certificate", "NOT_READY", 65, ["RULE-DOC-01"], "development", skip_income=True)
    add_scenario("SCN_B02_MISSING_CASTE_CERT", "DOCUMENT_COMPLETENESS", "Missing mandatory Caste Certificate", "NOT_READY", 65, ["RULE-DOC-01"], "development", skip_caste=True)
    add_scenario("SCN_B03_MISSING_RESIDENCE_CERT", "DOCUMENT_COMPLETENESS", "Missing mandatory Residence Certificate", "NOT_READY", 65, ["RULE-DOC-01"], "development", skip_residence=True)
    add_scenario("SCN_B04_MISSING_MARKSHEET", "DOCUMENT_COMPLETENESS", "Missing mandatory Academic Marksheet", "NOT_READY", 65, ["RULE-DOC-01"], "validation", skip_marksheet=True)
    add_scenario("SCN_B05_MISSING_BANK_PASSBOOK", "DOCUMENT_COMPLETENESS", "Missing mandatory Bank Passbook", "NOT_READY", 65, ["RULE-DOC-01"], "validation", skip_bank=True)
    add_scenario("SCN_B06_MISSING_APPLICATION_FORM", "DOCUMENT_COMPLETENESS", "Missing mandatory Application Form", "NOT_READY", 65, ["RULE-DOC-01"], "validation", skip_form=True)
    add_scenario("SCN_B07_MISSING_MULTIPLE_DOCS", "DOCUMENT_COMPLETENESS", "Missing both Income and Residence Certificates", "NOT_READY", 30, ["RULE-DOC-01"], "challenge", skip_income=True, skip_residence=True)
    add_scenario("SCN_B08_EMPTY_PACKET_DIR", "DOCUMENT_COMPLETENESS", "Empty packet directory with zero uploaded documents", "NOT_READY", 0, ["RULE-DOC-01"], "challenge", skip_form=True, skip_income=True, skip_caste=True, skip_residence=True, skip_marksheet=True, skip_bank=True)
    
    # B09 Zero-byte file
    p_b09 = CORPUS_DIR / "SCN_B09_ZERO_BYTE_FILE"
    write_packet(p_b09, skip_income=True)
    (p_b09 / "income_cert.pdf").write_bytes(b"")
    manifest["scenarios"]["SCN_B09_ZERO_BYTE_FILE"] = {
        "index": scenario_idx + 1,
        "family": "DOCUMENT_COMPLETENESS",
        "description": "Zero-byte empty file uploaded into income_cert slot",
        "split": "development",
        "expected_status": "NEEDS_CHECKS",
        "expected_score": 75,
        "expected_defects": ["RULE-DOC-02"],
    }
    scenario_idx += 1

    # B10 Unsupported file
    p_b10 = CORPUS_DIR / "SCN_B10_UNSUPPORTED_FILE_EXT"
    write_packet(p_b10)
    (p_b10 / "extra_note.txt").write_text("Disregard this note", encoding="utf-8")
    manifest["scenarios"]["SCN_B10_UNSUPPORTED_FILE_EXT"] = {
        "index": scenario_idx + 1,
        "family": "DOCUMENT_COMPLETENESS",
        "description": "Extra unsupported .txt file in packet is safely ignored",
        "split": "validation",
        "expected_status": "NO_ISSUES_FOUND",
        "expected_score": 100,
        "expected_defects": [],
    }
    scenario_idx += 1

    # B11 Duplicate identical doc
    p_b11 = CORPUS_DIR / "SCN_B11_DUPLICATE_IDENTICAL_DOC"
    write_packet(p_b11)
    shutil.copyfile(p_b11 / "caste_cert.pdf", p_b11 / "caste_cert_copy.pdf")
    manifest["scenarios"]["SCN_B11_DUPLICATE_IDENTICAL_DOC"] = {
        "index": scenario_idx + 1,
        "family": "DOCUMENT_COMPLETENESS",
        "description": "Harmless duplicate copy of caste certificate",
        "split": "challenge",
        "expected_status": "NO_ISSUES_FOUND",
        "expected_score": 100,
        "expected_defects": [],
    }
    scenario_idx += 1

    # B12 Renamed impersonation
    p_b12 = CORPUS_DIR / "SCN_B12_RENAMED_IMPERSONATION"
    write_packet(p_b12, skip_income=True)
    shutil.copyfile(p_b12 / "marksheet.pdf", p_b12 / "income_cert.pdf")
    manifest["scenarios"]["SCN_B12_RENAMED_IMPERSONATION"] = {
        "index": scenario_idx + 1,
        "family": "DOCUMENT_COMPLETENESS",
        "description": "Marksheet renamed to income_cert.pdf (slot mismatch)",
        "split": "development",
        "expected_status": "NEEDS_CHECKS",
        "expected_score": 90,
        "expected_defects": ["RULE-SLOT-01"],
    }
    scenario_idx += 1

    # -------------------------------------------------------------------------
    # FAMILY C: SCAN QUALITY & INTEGRITY (12 Scenarios)
    # -------------------------------------------------------------------------
    add_scenario("SCN_C01_UNREADABLE_INCOME_CERT", "SCAN_QUALITY", "Unreadable/corrupted Income Certificate scan", "NEEDS_CHECKS", 75, ["RULE-DOC-02"], "development", inc_unreadable=True)
    
    # C02 unreadable marksheet
    p_c02 = CORPUS_DIR / "SCN_C02_UNREADABLE_MARKSHEET"
    write_packet(p_c02, skip_marksheet=True)
    (p_c02 / "marksheet.pdf").write_bytes(b"%PDF-1.4\n%corrupt unreadable scan\n")
    manifest["scenarios"]["SCN_C02_UNREADABLE_MARKSHEET"] = {
        "index": scenario_idx + 1, "family": "SCAN_QUALITY", "description": "Unreadable damaged marksheet scan", "split": "development",
        "expected_status": "NEEDS_CHECKS", "expected_score": 75, "expected_defects": ["RULE-DOC-02"]
    }
    scenario_idx += 1

    # C03 unreadable caste cert
    p_c03 = CORPUS_DIR / "SCN_C03_UNREADABLE_CASTE_CERT"
    write_packet(p_c03, skip_caste=True)
    (p_c03 / "caste_cert.pdf").write_bytes(b"%PDF-1.4\n%damaged scan\n")
    manifest["scenarios"]["SCN_C03_UNREADABLE_CASTE_CERT"] = {
        "index": scenario_idx + 1, "family": "SCAN_QUALITY", "description": "Unreadable damaged caste cert scan", "split": "validation",
        "expected_status": "NEEDS_CHECKS", "expected_score": 75, "expected_defects": ["RULE-DOC-02"]
    }
    scenario_idx += 1

    # C04 Corrupted stream
    p_c04 = CORPUS_DIR / "SCN_C04_CORRUPTED_STREAM"
    write_packet(p_c04, skip_residence=True)
    (p_c04 / "residence_cert.pdf").write_bytes(b"%PDF-invalid stream truncated\n")
    manifest["scenarios"]["SCN_C04_CORRUPTED_STREAM"] = {
        "index": scenario_idx + 1, "family": "SCAN_QUALITY", "description": "Corrupted truncated residence stream", "split": "validation",
        "expected_status": "NEEDS_CHECKS", "expected_score": 75, "expected_defects": ["RULE-DOC-02"]
    }
    scenario_idx += 1

    add_scenario("SCN_C05_PROSE_HEAVY_SCAN", "SCAN_QUALITY", "Prose-heavy declaration text correctly captured", "NO_ISSUES_FOUND", 100, [], "development")
    add_scenario("SCN_C06_TABLE_BOXED_SCAN", "SCAN_QUALITY", "Table boxed format with pipe lines", "NO_ISSUES_FOUND", 100, [], "validation")
    add_scenario("SCN_C07_FAINT_CARBON_COPY", "SCAN_QUALITY", "Faint carbon text contrast recovery", "NO_ISSUES_FOUND", 100, [], "challenge")
    add_scenario("SCN_C08_DIAGONAL_WATERMARK", "SCAN_QUALITY", "Heavy diagonal watermark background", "NO_ISSUES_FOUND", 100, [], "challenge")
    add_scenario("SCN_C09_LOW_DPI_RECOVERY", "SCAN_QUALITY", "Low DPI scan legibility recovery", "NO_ISSUES_FOUND", 100, [], "development")
    add_scenario("SCN_C10_HEADER_BORDER_SHADOW", "SCAN_QUALITY", "Top border shadow scan", "NO_ISSUES_FOUND", 100, [], "validation")
    
    # C11 unreadable bank
    p_c11 = CORPUS_DIR / "SCN_C11_UNREADABLE_BANK"
    write_packet(p_c11, skip_bank=True)
    (p_c11 / "bank_passbook.pdf").write_bytes(b"%PDF-1.4\n%unreadable bank passbook scan\n")
    manifest["scenarios"]["SCN_C11_UNREADABLE_BANK"] = {
        "index": scenario_idx + 1, "family": "SCAN_QUALITY", "description": "Unreadable bank passbook scan", "split": "challenge",
        "expected_status": "NEEDS_CHECKS", "expected_score": 75, "expected_defects": ["RULE-DOC-02"]
    }
    scenario_idx += 1

    # C12 double unreadable
    p_c12 = CORPUS_DIR / "SCN_C12_DOUBLE_UNREADABLE"
    write_packet(p_c12, inc_unreadable=True, skip_caste=True)
    (p_c12 / "caste_cert.pdf").write_bytes(b"%PDF-1.4\n%corrupt scan\n")
    manifest["scenarios"]["SCN_C12_DOUBLE_UNREADABLE"] = {
        "index": scenario_idx + 1, "family": "SCAN_QUALITY", "description": "Two unreadable scans in one packet", "split": "development",
        "expected_status": "NEEDS_CHECKS", "expected_score": 50, "expected_defects": ["RULE-DOC-02"]
    }
    scenario_idx += 1

    # -------------------------------------------------------------------------
    # FAMILY D: GEOMETRY & DESKEW INVARIANCE (12 Scenarios)
    # -------------------------------------------------------------------------
    add_scenario("SCN_D01_ROTATION_90_INCOME", "GEOMETRY_DESKEW", "90° rotation recovered cleanly", "NO_ISSUES_FOUND", 100, [], "development")
    add_scenario("SCN_D02_ROTATION_180_RESIDENCE", "GEOMETRY_DESKEW", "180° rotation recovered cleanly", "NO_ISSUES_FOUND", 100, [], "development")
    add_scenario("SCN_D03_ROTATION_270_MARKSHEET", "GEOMETRY_DESKEW", "270° rotation recovered cleanly", "NO_ISSUES_FOUND", 100, [], "validation")
    add_scenario("SCN_D04_SKEW_POS_3DEG", "GEOMETRY_DESKEW", "+3.0° non-orthogonal skew recovered", "NO_ISSUES_FOUND", 100, [], "validation")
    add_scenario("SCN_D05_SKEW_NEG_5DEG", "GEOMETRY_DESKEW", "-5.0° non-orthogonal skew recovered", "NO_ISSUES_FOUND", 100, [], "challenge")
    add_scenario("SCN_D06_SKEW_POS_8DEG", "GEOMETRY_DESKEW", "+8.0° non-orthogonal skew recovered", "NO_ISSUES_FOUND", 100, [], "challenge")
    add_scenario("SCN_D07_SKEW_POS_12DEG", "GEOMETRY_DESKEW", "+12.0° non-orthogonal skew recovered", "NO_ISSUES_FOUND", 100, [], "development")
    add_scenario("SCN_D08_MULTI_SKEW_PACKET", "GEOMETRY_DESKEW", "Compound multi-skew across multiple certificates", "NO_ISSUES_FOUND", 100, [], "validation")
    add_scenario("SCN_D09_SKEW_WITH_NAME_CONFLICT", "GEOMETRY_DESKEW", "Deskew preserves underlying name conflict", "NOT_READY", 75, ["RULE-NAME-01"], "challenge", inc_name="Ramesh Patel")
    add_scenario("SCN_D10_SKEW_WITH_DOB_CONFLICT", "GEOMETRY_DESKEW", "Deskew preserves underlying DOB conflict", "NOT_READY", 75, ["RULE-DOB-01"], "development", mrk_dob="20/11/2001")
    add_scenario("SCN_D11_UPRIGHT_NOOP_VERIFICATION", "GEOMETRY_DESKEW", "Upright page zero-deskew guarantee", "NO_ISSUES_FOUND", 100, [], "validation")
    add_scenario("SCN_D12_FINE_SKEW_0_5DEG", "GEOMETRY_DESKEW", "+0.5° subtle skew handled safely", "NO_ISSUES_FOUND", 100, [], "challenge")

    # -------------------------------------------------------------------------
    # FAMILY E: OCR & EXTRACTION ADVERSARIAL (12 Scenarios)
    # -------------------------------------------------------------------------
    add_scenario("SCN_E01_OCR_YEAR_ZERO_CONFUSION", "EXTRACTION_ADVERSARIAL", "OCR letter O confusion in year (/2O25/)", "NO_ISSUES_FOUND", 100, [], "development")
    add_scenario("SCN_E02_OCR_SEQ_ZERO_CONFUSION", "EXTRACTION_ADVERSARIAL", "OCR letter O confusion in sequence (/1O4928)", "NO_ISSUES_FOUND", 100, [], "development")
    add_scenario("SCN_E03_DASH_DELIMITED_DATE", "EXTRACTION_ADVERSARIAL", "Dash-delimited ISO issue date (2025-01-15)", "NO_ISSUES_FOUND", 100, [], "validation", inc_issue_date="2025-01-15")
    add_scenario("SCN_E04_DOT_DELIMITED_DATE", "EXTRACTION_ADVERSARIAL", "Dot-delimited issue date (15.01.2025)", "NO_ISSUES_FOUND", 100, [], "validation", inc_issue_date="15.01.2025")
    add_scenario("SCN_E05_NAMED_MONTH_DATE", "EXTRACTION_ADVERSARIAL", "Named month date (15-Jan-2025)", "NO_ISSUES_FOUND", 100, [], "challenge", inc_issue_date="15-Jan-2025")
    add_scenario("SCN_E06_FATHER_NAME_NO_COMMA", "EXTRACTION_ADVERSARIAL", "Father name with S/O and no trailing comma", "NO_ISSUES_FOUND", 100, [], "challenge")
    add_scenario("SCN_E07_LAKH_PROSE_NOTATION", "EXTRACTION_ADVERSARIAL", "Lakh notation 'Rs. 1,80,000/- (Rupees One Lakh)'", "NO_ISSUES_FOUND", 100, [], "development", inc_income="Rs. 1,80,000/- (Rupees One Lakh Eighty Thousand only)")
    add_scenario("SCN_E08_LPA_NOTATION", "EXTRACTION_ADVERSARIAL", "LPA notation '1.80 LPA'", "NO_ISSUES_FOUND", 100, [], "validation", inc_income="1.80 LPA", app_income="1.80 LPA")
    add_scenario("SCN_E09_GIVEN_NAME_KUMAR", "EXTRACTION_ADVERSARIAL", "Preserves given name 'Kumar Gaurav'", "NO_ISSUES_FOUND", 100, [], "challenge", app_name="Kumar Gaurav", inc_name="Kumar Gaurav", cst_name="Kumar Gaurav", res_name="Kumar Gaurav", mrk_name="Kumar Gaurav", bnk_name="Kumar Gaurav")
    add_scenario("SCN_E10_MIDDLE_HONORIFIC_KUMAR", "EXTRACTION_ADVERSARIAL", "Canonicalizes 3-token 'Rajesh Kumar Patel'", "NO_ISSUES_FOUND", 100, [], "development", app_name="Rajesh Kumar Patel", inc_name="Rajesh Kumar Patel", cst_name="Rajesh Kumar Patel", res_name="Rajesh Kumar Patel", mrk_name="Rajesh Kumar Patel", bnk_name="Rajesh Kumar Patel")
    add_scenario("SCN_E11_AADHAAR_EXTRACTION", "EXTRACTION_ADVERSARIAL", "Masked Aadhaar format extraction", "NO_ISSUES_FOUND", 100, [], "validation")
    add_scenario("SCN_E12_TABLE_PIPE_CLEANUP", "EXTRACTION_ADVERSARIAL", "Strips table pipes | without corrupting value", "NO_ISSUES_FOUND", 100, [], "challenge")

    # -------------------------------------------------------------------------
    # FAMILY F: CROSS-DOCUMENT IDENTITY (15 Scenarios)
    # -------------------------------------------------------------------------
    add_scenario("SCN_F01_EXACT_NAME_MATCH", "IDENTITY_CONSISTENCY", "Exact name match across all 6 documents", "NO_ISSUES_FOUND", 100, [], "development")
    add_scenario("SCN_F02_HARD_NAME_CONFLICT", "IDENTITY_CONSISTENCY", "Hard name conflict: Smruti Nayak vs Ramesh Patel", "NOT_READY", 75, ["RULE-NAME-01"], "development", inc_name="Ramesh Patel")
    add_scenario("SCN_F03_MIDDLE_NAME_OMISSION", "IDENTITY_CONSISTENCY", "Middle name omission on Caste Certificate", "NEEDS_CHECKS", 95, ["RULE-NAME-02"], "development", cst_name="Smruti Ranjan Nayak")
    add_scenario("SCN_F04_MIDDLE_NAME_INVERSE", "IDENTITY_CONSISTENCY", "Form has middle name, certificates omit", "NEEDS_CHECKS", 75, ["RULE-NAME-02"], "validation", app_name="Smruti Ranjan Nayak", cst_name="Smruti Nayak")
    add_scenario("SCN_F05_SIBLING_RHYME_CONFLICT", "IDENTITY_CONSISTENCY", "Sibling name conflict: Smruti vs Suresh Nayak", "NOT_READY", 75, ["RULE-NAME-01"], "validation", inc_name="Suresh Nayak")
    add_scenario("SCN_F06_DISTINCT_GIVEN_NAMES", "IDENTITY_CONSISTENCY", "Distinct given names: Smruti vs Sumit Nayak", "NOT_READY", 75, ["RULE-NAME-01"], "challenge", mrk_name="Sumit Nayak")
    add_scenario("SCN_F07_INITIAL_EXPANSION", "IDENTITY_CONSISTENCY", "Initial abbreviation S. Nayak", "NEEDS_CHECKS", 95, ["RULE-NAME-02"], "challenge", cst_name="S. Nayak")
    add_scenario("SCN_F08_SURNAME_MISMATCH", "IDENTITY_CONSISTENCY", "Surname mismatch: Smruti Nayak vs Smruti Das", "NOT_READY", 75, ["RULE-NAME-01"], "development", res_name="Smruti Das")
    add_scenario("SCN_F09_TWO_DOC_NAME_CONFLICT", "IDENTITY_CONSISTENCY", "Two documents conflict with application", "NOT_READY", 50, ["RULE-NAME-01"], "development", inc_name="Ramesh Patel", mrk_name="Pooja Sahu")
    add_scenario("SCN_F10_COMPATIBLE_ON_APPLICATION", "IDENTITY_CONSISTENCY", "Compatible middle name variation on application", "NEEDS_CHECKS", 75, ["RULE-NAME-02"], "validation", app_name="Smruti Ranjan Nayak")
    add_scenario("SCN_F11_SINGLE_CHAR_TYPO", "IDENTITY_CONSISTENCY", "Single-character OCR typo Smrutl Nayak", "NEEDS_CHECKS", 95, ["RULE-NAME-02"], "challenge", cst_name="Smrutl Nayak")
    add_scenario("SCN_F12_COMPLETELY_DIFFERENT_IDENTITY", "IDENTITY_CONSISTENCY", "Completely different identity Priya Sharma", "NOT_READY", 75, ["RULE-NAME-01"], "development", mrk_name="Priya Sharma")
    add_scenario("SCN_F13_FATHER_NAME_CONFLICT", "IDENTITY_CONSISTENCY", "Applicant name matches, father name conflicts", "NO_ISSUES_FOUND", 100, [], "validation", inc_father="Dhirendra Nayak")
    add_scenario("SCN_F14_NAME_CONFLICT_ON_RESIDENCE", "IDENTITY_CONSISTENCY", "Residence Certificate has conflicting name", "NOT_READY", 75, ["RULE-NAME-01"], "challenge", res_name="Sunita Mohanty")
    add_scenario("SCN_F15_NAME_CONFLICT_ON_CASTE", "IDENTITY_CONSISTENCY", "Caste Certificate has conflicting name", "NOT_READY", 75, ["RULE-NAME-01"], "challenge", cst_name="Kavita Sahoo")

    # -------------------------------------------------------------------------
    # FAMILY G: DATE & TEMPORAL CONSISTENCY (12 Scenarios)
    # -------------------------------------------------------------------------
    add_scenario("SCN_G01_EXACT_DOB_MATCH", "TEMPORAL_CONSISTENCY", "Exact DOB match (14/05/2003)", "NO_ISSUES_FOUND", 100, [], "development")
    add_scenario("SCN_G02_DOB_YEAR_MISMATCH", "TEMPORAL_CONSISTENCY", "DOB year mismatch (2003 vs 2001)", "NOT_READY", 75, ["RULE-DOB-01"], "development", mrk_dob="14/05/2001")
    add_scenario("SCN_G03_DOB_DAY_MISMATCH", "TEMPORAL_CONSISTENCY", "DOB day mismatch (14/05/2003 vs 15/05/2003)", "NOT_READY", 75, ["RULE-DOB-01"], "development", mrk_dob="15/05/2003")
    add_scenario("SCN_G04_DOB_MONTH_MISMATCH", "TEMPORAL_CONSISTENCY", "DOB month mismatch (14/05/2003 vs 14/06/2003)", "NOT_READY", 75, ["RULE-DOB-01"], "validation", mrk_dob="14/06/2003")
    add_scenario("SCN_G05_EXPIRED_CERT_4YEARS", "TEMPORAL_CONSISTENCY", "Income certificate expired 4 years ago (10/01/2022)", "NOT_READY", 75, ["RULE-EXP-01"], "validation", inc_issue_date="10/01/2022")
    add_scenario("SCN_G06_EXPIRED_CERT_5YEARS", "TEMPORAL_CONSISTENCY", "Income certificate expired 5 years ago (10/01/2021)", "NOT_READY", 75, ["RULE-EXP-01"], "challenge", inc_issue_date="10/01/2021")
    add_scenario("SCN_G07_VALID_CERT_BOUNDARY", "TEMPORAL_CONSISTENCY", "Valid certificate near 3-year boundary (25/11/2023)", "NO_ISSUES_FOUND", 100, [], "challenge", inc_issue_date="25/11/2023")
    add_scenario("SCN_G08_RECENT_CERT_ISSUED", "TEMPORAL_CONSISTENCY", "Recently issued valid certificate (10/05/2026)", "NO_ISSUES_FOUND", 100, [], "development", inc_issue_date="10/05/2026")
    add_scenario("SCN_G09_AMBIGUOUS_DATE_FORMAT_SAFE", "TEMPORAL_CONSISTENCY", "Ambiguous format (06/07/2025) both valid -> Pass", "NO_ISSUES_FOUND", 100, [], "validation", inc_issue_date="06/07/2025")
    add_scenario("SCN_G10_AMBIGUOUS_DATE_FORMAT_EXPIRED", "TEMPORAL_CONSISTENCY", "Ambiguous format (06/07/2020) both expired -> Fail", "NOT_READY", 75, ["RULE-EXP-01"], "challenge", inc_issue_date="06/07/2020")
    add_scenario("SCN_G11_FUTURE_ISSUE_DATE", "TEMPORAL_CONSISTENCY", "Future date anomaly (20/11/2026)", "NOT_READY", 75, ["RULE-EXP-01"], "development", inc_issue_date="20/11/2026")
    add_scenario("SCN_G12_LEAP_DAY_DOB", "TEMPORAL_CONSISTENCY", "Valid leap day date of birth (29/02/2004)", "NO_ISSUES_FOUND", 100, [], "validation", app_dob="29/02/2004", mrk_dob="29/02/2004")

    # -------------------------------------------------------------------------
    # FAMILY H: FINANCIAL DATA (12 Scenarios)
    # -------------------------------------------------------------------------
    add_scenario("SCN_H01_INCOME_EXACT_MATCH_WITHIN_CEILING", "FINANCIAL_DATA", "Annual income exact match ₹1.80L within ceiling", "NO_ISSUES_FOUND", 100, [], "development")
    add_scenario("SCN_H02_INCOME_ABOVE_CEILING_CERTIFIED", "FINANCIAL_DATA", "Certified income ₹3.80L exceeds statutory ₹2.50L ceiling", "NOT_READY", 65, ["RULE-INC-01"], "development", inc_income="Rs. 3,80,000/-", app_income="Rs. 3,80,000/-")
    add_scenario("SCN_H03_INCOME_ABOVE_CEILING_SLIGHT", "FINANCIAL_DATA", "Certified income ₹2.60L slightly exceeds ₹2.50L ceiling", "NOT_READY", 65, ["RULE-INC-01"], "development", inc_income="Rs. 2,60,000/-", app_income="Rs. 2,60,000/-")
    add_scenario("SCN_H04_INCOME_AT_CEILING_EXACT", "FINANCIAL_DATA", "Certified income exactly ₹2,50,000 equals statutory ceiling", "NO_ISSUES_FOUND", 100, [], "validation", inc_income="Rs. 2,50,000/-", app_income="Rs. 2,50,000/-")
    add_scenario("SCN_H05_INCOME_DECLARED_MISMATCH", "FINANCIAL_DATA", "Declared income ₹1.50L mismatches certified ₹1.80L", "NOT_READY", 75, ["RULE-INC-02"], "validation", app_income="Rs. 1,50,000/-", inc_income="Rs. 1,80,000/-")
    add_scenario("SCN_H06_INCOME_VERY_LOW", "FINANCIAL_DATA", "Very low income ₹30,000 within ceiling", "NO_ISSUES_FOUND", 100, [], "challenge", inc_income="Rs. 30,000/-", app_income="Rs. 30,000/-")
    add_scenario("SCN_H07_INCOME_FORMAT_THOUSAND_COMMAS", "FINANCIAL_DATA", "Indian comma numbering format ₹1,80,000/-", "NO_ISSUES_FOUND", 100, [], "challenge", inc_income="Rs. 1,80,000/-")
    add_scenario("SCN_H08_INCOME_FORMAT_DECIMAL", "FINANCIAL_DATA", "Decimal income format ₹180000.00", "NO_ISSUES_FOUND", 100, [], "development", inc_income="Rs. 180000.00")
    add_scenario("SCN_H09_INCOME_MISMATCH_WITHIN_TOLERANCE", "FINANCIAL_DATA", "Income declaration matches exactly", "NO_ISSUES_FOUND", 100, [], "validation")
    add_scenario("SCN_H10_INCOME_HIGH_EXTREME", "FINANCIAL_DATA", "Extreme high income ₹12,00,000", "NOT_READY", 65, ["RULE-INC-01"], "challenge", inc_income="Rs. 12,00,000/-", app_income="Rs. 12,00,000/-")
    add_scenario("SCN_H11_INCOME_BOTH_CEILING_AND_MISMATCH", "FINANCIAL_DATA", "Both ceiling exceeded (₹3.5L) and declared mismatch (₹2.0L)", "NOT_READY", 40, ["RULE-INC-01", "RULE-INC-02"], "development", inc_income="Rs. 3,50,000/-", app_income="Rs. 2,00,000/-")
    add_scenario("SCN_H12_INCOME_CERT_VALID_FORM_CEILING", "FINANCIAL_DATA", "Certified income ₹1.8L, declared form income ₹4.0L", "NOT_READY", 75, ["RULE-INC-02"], "validation", inc_income="Rs. 1,80,000/-", app_income="Rs. 4,00,000/-")

    # -------------------------------------------------------------------------
    # FAMILY I: EVIDENCE AMBIGUITY, SLOT & DOMICILE (12 Scenarios)
    # -------------------------------------------------------------------------
    add_scenario("SCN_I01_ODISHA_DOMICILE_MATCH", "DOMICILE_AND_SLOT", "Residence state matches required state ODISHA", "NO_ISSUES_FOUND", 100, [], "development")
    add_scenario("SCN_I02_DOMICILE_MISMATCH_BIHAR", "DOMICILE_AND_SLOT", "Residence certificate issued by BIHAR fails domicile", "NOT_READY", 75, ["RULE-DOM-01"], "development", res_state="BIHAR")
    add_scenario("SCN_I03_DOMICILE_MISMATCH_BENGAL", "DOMICILE_AND_SLOT", "Residence certificate issued by WEST BENGAL fails domicile", "NOT_READY", 75, ["RULE-DOM-01"], "validation", res_state="WEST BENGAL")
    
    # I04 slot swap marksheet for income
    p_i04 = CORPUS_DIR / "SCN_I04_SLOT_SWAP_MARKSHEET_FOR_INCOME"
    write_packet(p_i04, skip_income=True)
    shutil.copyfile(p_i04 / "marksheet.pdf", p_i04 / "income_cert.pdf")
    manifest["scenarios"]["SCN_I04_SLOT_SWAP_MARKSHEET_FOR_INCOME"] = {
        "index": scenario_idx + 1, "family": "DOMICILE_AND_SLOT", "description": "Marksheet uploaded into income_cert slot",
        "split": "development", "expected_status": "NEEDS_CHECKS", "expected_score": 90, "expected_defects": ["RULE-SLOT-01"]
    }
    scenario_idx += 1

    # I05 slot swap passbook for caste
    p_i05 = CORPUS_DIR / "SCN_I05_SLOT_SWAP_PASSBOOK_FOR_CASTE"
    write_packet(p_i05, skip_caste=True)
    shutil.copyfile(p_i05 / "bank_passbook.pdf", p_i05 / "caste_cert.pdf")
    manifest["scenarios"]["SCN_I05_SLOT_SWAP_PASSBOOK_FOR_CASTE"] = {
        "index": scenario_idx + 1, "family": "DOMICILE_AND_SLOT", "description": "Bank passbook uploaded into caste_cert slot",
        "split": "validation", "expected_status": "NEEDS_CHECKS", "expected_score": 90, "expected_defects": ["RULE-SLOT-01"]
    }
    scenario_idx += 1

    # I06 slot swap residence for form
    p_i06 = CORPUS_DIR / "SCN_I06_SLOT_SWAP_RESIDENCE_FOR_FORM"
    write_packet(p_i06, skip_form=True)
    shutil.copyfile(p_i06 / "residence_cert.pdf", p_i06 / "application_form.pdf")
    manifest["scenarios"]["SCN_I06_SLOT_SWAP_RESIDENCE_FOR_FORM"] = {
        "index": scenario_idx + 1, "family": "DOMICILE_AND_SLOT", "description": "Residence certificate uploaded into application_form slot",
        "split": "challenge", "expected_status": "NEEDS_CHECKS", "expected_score": 90, "expected_defects": ["RULE-SLOT-01"]
    }
    scenario_idx += 1

    add_scenario("SCN_I07_CERT_NO_EXACT_MATCH", "DOMICILE_AND_SLOT", "Certificate reference numbers match perfectly", "NO_ISSUES_FOUND", 100, [], "development")
    add_scenario("SCN_I08_DOMICILE_MISMATCH_JHARKHAND", "DOMICILE_AND_SLOT", "Jharkhand domicile ineligible for Odisha scheme", "NOT_READY", 75, ["RULE-DOM-01"], "validation", res_state="JHARKHAND")
    add_scenario("SCN_I09_DOMICILE_MISMATCH_ANDHRA", "DOMICILE_AND_SLOT", "Andhra Pradesh domicile ineligible for Odisha scheme", "NOT_READY", 75, ["RULE-DOM-01"], "challenge", res_state="ANDHRA PRADESH")
    add_scenario("SCN_I10_BANK_IFSC_VALID_SBIN", "DOMICILE_AND_SLOT", "Valid RBI IFSC code SBIN0001234", "NO_ISSUES_FOUND", 100, [], "development")
    add_scenario("SCN_I11_BANK_IFSC_INVALID_FORMAT", "DOMICILE_AND_SLOT", "Invalid IFSC code length (SBIN00123) triggers review", "NEEDS_CHECKS", 90, ["RULE-BNK-01"], "validation", app_ifsc="SBIN00123", bnk_ifsc="SBIN00123")
    add_scenario("SCN_I12_BANK_ACCOUNT_NO_MISMATCH", "DOMICILE_AND_SLOT", "Bank account number mismatch between form and passbook", "NOT_READY", 75, ["RULE-BNK-02"], "challenge", bnk_acct="99999999999", app_acct="30987654301")

    # -------------------------------------------------------------------------
    # FAMILY J: MULTI-DOCUMENT INTERACTION (12 Scenarios)
    # -------------------------------------------------------------------------
    add_scenario("SCN_J01_NAME_CONFLICT_AND_MISSING_DOC", "INTERACTION", "Name conflict (-25) + missing residence cert (-35)", "NOT_READY", 40, ["RULE-NAME-01", "RULE-DOC-01"], "development", mrk_name="Priya Sharma", skip_residence=True)
    add_scenario("SCN_J02_DOB_CONFLICT_AND_UNREADABLE_DOC", "INTERACTION", "DOB conflict (-25) + unreadable income cert (-25)", "NOT_READY", 50, ["RULE-DOB-01", "RULE-DOC-02"], "development", mrk_dob="20/11/2001", inc_unreadable=True)
    add_scenario("SCN_J03_CEILING_EXCEEDED_AND_EXPIRED", "INTERACTION", "Income ceiling exceeded (₹3.8L) + expired cert (2021)", "NOT_READY", 40, ["RULE-INC-01", "RULE-EXP-01"], "development", inc_income="Rs. 3,80,000/-", app_income="Rs. 3,80,000/-", inc_issue_date="10/01/2021")
    add_scenario("SCN_J04_DOMICILE_MISMATCH_AND_NAME_CONFLICT", "INTERACTION", "State Bihar (-25) + name conflict (-25)", "NOT_READY", 50, ["RULE-DOM-01", "RULE-NAME-01"], "validation", res_state="BIHAR", inc_name="Ramesh Patel")
    add_scenario("SCN_J05_THREE_HARD_CONFLICTS", "INTERACTION", "Three hard conflicts: Name + DOB + Income ceiling", "NOT_READY", 15, ["RULE-NAME-01", "RULE-DOB-01", "RULE-INC-01"], "validation", inc_name="Ramesh Patel", mrk_dob="20/11/2001", inc_income="Rs. 3,80,000/-", app_income="Rs. 3,80,000/-")
    add_scenario("SCN_J06_MISSING_TWO_MANDATORY_DOCS", "INTERACTION", "Two mandatory documents missing: Income + Caste", "NOT_READY", 30, ["RULE-DOC-01"], "challenge", skip_income=True, skip_caste=True)
    add_scenario("SCN_J07_WARN_NAME_AND_UNREADABLE_PASSBOOK", "INTERACTION", "Middle name variation + unreadable passbook", "NEEDS_CHECKS", 70, ["RULE-NAME-02", "RULE-DOC-02"], "challenge", cst_name="Smruti Ranjan Nayak", skip_bank=True)
    
    # J07 bank unreadable
    p_j07 = CORPUS_DIR / "SCN_J07_WARN_NAME_AND_UNREADABLE_PASSBOOK"
    (p_j07 / "bank_passbook.pdf").write_bytes(b"%PDF-1.4\n%unreadable bank passbook scan\n")

    # J08 slot mismatch + missing doc
    p_j08 = CORPUS_DIR / "SCN_J08_SLOT_MISMATCH_AND_MISSING_DOC"
    write_packet(p_j08, skip_income=True, skip_residence=True)
    shutil.copyfile(p_j08 / "marksheet.pdf", p_j08 / "income_cert.pdf")
    manifest["scenarios"]["SCN_J08_SLOT_MISMATCH_AND_MISSING_DOC"] = {
        "index": scenario_idx + 1, "family": "INTERACTION", "description": "Slot mismatch + missing residence certificate",
        "split": "development", "expected_status": "NOT_READY", "expected_score": 55, "expected_defects": ["RULE-SLOT-01", "RULE-DOC-01"]
    }
    scenario_idx += 1

    add_scenario("SCN_J09_EXPIRED_CERT_AND_NAME_WARN", "INTERACTION", "Expired cert (2021) (-25) + middle name variation (-5)", "NOT_READY", 70, ["RULE-EXP-01", "RULE-NAME-02"], "validation", inc_issue_date="10/01/2021", cst_name="Smruti Ranjan Nayak")
    add_scenario("SCN_J10_EXPIRED_CERT_AND_UNREADABLE_CASTE", "INTERACTION", "Expired income cert (-25) + unreadable caste cert (-25)", "NOT_READY", 50, ["RULE-EXP-01", "RULE-DOC-02"], "challenge", inc_issue_date="10/01/2021", skip_caste=True)
    (CORPUS_DIR / "SCN_J10_EXPIRED_CERT_AND_UNREADABLE_CASTE" / "caste_cert.pdf").write_bytes(b"%PDF-1.4\n%unreadable scan\n")

    add_scenario("SCN_J11_CLEAN_WITH_EXTRA_DOC", "INTERACTION", "Clean packet with harmless extra document copy", "NO_ISSUES_FOUND", 100, [], "development")
    shutil.copyfile(CORPUS_DIR / "SCN_J11_CLEAN_WITH_EXTRA_DOC" / "residence_cert.pdf", CORPUS_DIR / "SCN_J11_CLEAN_WITH_EXTRA_DOC" / "residence_copy.pdf")

    add_scenario("SCN_J12_COMPOUND_MAX_FAILURES", "INTERACTION", "Compound maximum failures across Name, DOB, Income, Domicile", "NOT_READY", 0, ["RULE-NAME-01", "RULE-DOB-01", "RULE-INC-01", "RULE-DOM-01"], "validation", inc_name="Ramesh Patel", mrk_dob="20/11/2001", inc_income="Rs. 4,00,000/-", app_income="Rs. 4,00,000/-", res_state="BIHAR")

    # -------------------------------------------------------------------------
    # FAMILY K: PACK EXECUTION & RESERVATION PARITY (12 Scenarios)
    # -------------------------------------------------------------------------
    add_scenario("SCN_K01_SC_RELAX_CUTOFF_PASS", "RESERVATION_AND_PARITY", "SC candidate (45% marks) exempt under Post-Matric Cl. 5.2", "NO_ISSUES_FOUND", 100, [], "development", mrk_pct=45.0, app_caste="SCHEDULED CASTE", cst_caste="SCHEDULED CASTE")
    add_scenario("SCN_K02_ST_RELAX_CUTOFF_PASS", "RESERVATION_AND_PARITY", "ST candidate (42% marks) exempt under Post-Matric Cl. 5.2", "NO_ISSUES_FOUND", 100, [], "development", mrk_pct=42.0, app_caste="SCHEDULED TRIBE", cst_caste="SCHEDULED TRIBE")
    add_scenario("SCN_K03_GEN_CUTOFF_FAIL", "RESERVATION_AND_PARITY", "General candidate (45% marks) fails 50% cutoff", "NOT_READY", 75, ["RULE-MRK-01"], "development", mrk_pct=45.0, app_caste="GENERAL", cst_caste="GENERAL")
    add_scenario("SCN_K04_OBC_CUTOFF_FAIL", "RESERVATION_AND_PARITY", "OBC candidate (45% marks) fails 50% cutoff", "NOT_READY", 75, ["RULE-MRK-01"], "validation", mrk_pct=45.0, app_caste="OBC", cst_caste="OBC")
    add_scenario("SCN_K05_SC_EXEMPTION_MISSING_CASTE", "RESERVATION_AND_PARITY", "SC candidate 45%, but Caste Certificate missing", "NOT_READY", 65, ["RULE-DOC-01"], "validation", mrk_pct=45.0, app_caste="SCHEDULED CASTE", skip_caste=True)
    add_scenario("SCN_K06_SC_EXEMPTION_UNREADABLE", "RESERVATION_AND_PARITY", "SC candidate 45%, Caste Certificate unreadable (abstains to REVIEW)", "NEEDS_CHECKS", 75, ["RULE-DOC-02"], "challenge", mrk_pct=45.0, app_caste="SCHEDULED CASTE", skip_caste=True)
    (CORPUS_DIR / "SCN_K06_SC_EXEMPTION_UNREADABLE" / "caste_cert.pdf").write_bytes(b"%PDF-1.4\n%unreadable scan\n")

    add_scenario("SCN_K07_PARITY_PACK_VS_CORE_CLEAN", "RESERVATION_AND_PARITY", "Parity check: Clean packet", "NO_ISSUES_FOUND", 100, [], "challenge")
    add_scenario("SCN_K08_PARITY_PACK_VS_CORE_NAME_MISMATCH", "RESERVATION_AND_PARITY", "Parity check: Name mismatch", "NOT_READY", 75, ["RULE-NAME-01"], "development", inc_name="Ramesh Patel")
    add_scenario("SCN_K09_PARITY_PACK_VS_CORE_DOB_MISMATCH", "RESERVATION_AND_PARITY", "Parity check: DOB mismatch", "NOT_READY", 75, ["RULE-DOB-01"], "validation", mrk_dob="20/11/2001")
    add_scenario("SCN_K10_PARITY_PACK_VS_CORE_EXPIRED", "RESERVATION_AND_PARITY", "Parity check: Expired income cert", "NOT_READY", 75, ["RULE-EXP-01"], "challenge", inc_issue_date="10/01/2021")
    
    # K11 slot mismatch parity
    p_k11 = CORPUS_DIR / "SCN_K11_PARITY_PACK_VS_CORE_SLOT_MISMATCH"
    write_packet(p_k11, skip_income=True)
    shutil.copyfile(p_k11 / "marksheet.pdf", p_k11 / "income_cert.pdf")
    manifest["scenarios"]["SCN_K11_PARITY_PACK_VS_CORE_SLOT_MISMATCH"] = {
        "index": scenario_idx + 1, "family": "RESERVATION_AND_PARITY", "description": "Parity check: Slot mismatch",
        "split": "development", "expected_status": "NEEDS_CHECKS", "expected_score": 90, "expected_defects": ["RULE-SLOT-01"]
    }
    scenario_idx += 1

    add_scenario("SCN_K12_PARITY_PACK_VS_CORE_MISSING_DOC", "RESERVATION_AND_PARITY", "Parity check: Missing income certificate", "NOT_READY", 65, ["RULE-DOC-01"], "validation", skip_income=True)

    manifest["total_scenarios"] = len(manifest["scenarios"])
    dev_c = sum(1 for s in manifest["scenarios"].values() if s["split"] == "development")
    val_c = sum(1 for s in manifest["scenarios"].values() if s["split"] == "validation")
    cha_c = sum(1 for s in manifest["scenarios"].values() if s["split"] == "challenge")
    manifest["splits"]["development_count"] = dev_c
    manifest["splits"]["validation_count"] = val_c
    manifest["splits"]["challenge_count"] = cha_c

    manifest_path = CORPUS_DIR / "LOOP07_CORPUS_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Generated {manifest['total_scenarios']} scenarios in {CORPUS_DIR}")
    print(f"Split breakdown: {dev_c} dev, {val_c} val, {cha_c} challenge")
    print(f"Manifest written to {manifest_path}")

if __name__ == "__main__":
    build_corpus()
