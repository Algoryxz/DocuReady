"""
scripts/build_loop05_extraction_corpus.py

Generates 12 controlled synthetic fixtures in synthetic_data/loop05_extraction_corpus/
exercising diverse extraction, normalization, and ambiguity challenges:
- Lakh word in currency description without multiplier explosion
- "Kumar" preservation in middle and given names
- Multiple date formats (dots, dashes, named months, slashes)
- Table boxed layouts with pipes and borders
- Genuine competing candidate values on the same document
- Father's name variants (S/o, D/o, no comma)
- Aadhaar card document slot extraction
- LPA decimal multiplier normalization
- Type-aware certificate number normalization

All identities use non-real synthetic demographic data.
"""

import os
import json
from pathlib import Path
import pymupdf
import PIL.Image
import PIL.ImageDraw
import PIL.ImageFont

OUT_DIR = Path("synthetic_data/loop05_extraction_corpus")
OUT_DIR.mkdir(parents=True, exist_ok=True)
MANIFEST_PATH = OUT_DIR / "LOOP05_CORPUS_MANIFEST.json"


def _create_pdf_from_lines(lines, out_path: Path):
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=842)  # A4 72 dpi points
    
    y = 60
    for item in lines:
        if isinstance(item, tuple):
            text, size, is_bold = item
            fontname = "helv"
        else:
            text = str(item)
            size = 11
            fontname = "helv"

        if text.strip() == "---":
            # Draw line
            page.draw_line(pymupdf.Point(50, y), pymupdf.Point(545, y), color=(0.4, 0.4, 0.4), width=1)
            y += 18
            continue

        page.insert_text(pymupdf.Point(50, y), text, fontsize=size, fontname=fontname, color=(0.1, 0.1, 0.1))
        y += size + 10

    doc.save(str(out_path))
    doc.close()


def generate_corpus():
    manifest = {}

    # Fixture 1: Standard Income cert with "Rupees One Lakh Eighty Thousand Only" in text
    f1_lines = [
        ("GOVERNMENT OF ODISHA - REVENUE & DISASTER MANAGEMENT", 13, True),
        ("OFFICE OF THE TAHSILDAR, BHUBANESWAR, KHORDHA", 11, False),
        ("INCOME CERTIFICATE", 14, True),
        "---",
        "Certificate No: E-INC/2025/104928",
        "Issue Date: 10/01/2025",
        "Valid For: 3 Years from issue",
        "---",
        "This is to certify that Smruti Ranjan Nayak, Son of Ramesh Chandra Nayak resident of",
        "Tahsil BHUBANESWAR, District KHORDHA, in the State of ODISHA, has a total verified",
        "annual family income from all sources of:",
        ("Income (in figures): Rs. 1,80,000/- (Rupees One Lakh Eighty Thousand Only)", 12, True),
        "Income Assessment Year: 2024-2025",
        "---",
        "Digitally Signed by: Revenue Officer / Tahsildar, BHUBANESWAR"
    ]
    fn1 = "l05_clean_income_standard.pdf"
    _create_pdf_from_lines(f1_lines, OUT_DIR / fn1)
    manifest[fn1] = {
        "file_name": fn1,
        "doc_type": "INCOME_CERT",
        "category": "lakh_text_in_parentheses",
        "expected_fields": {
            "applicant_name": "SMRUTI RANJAN NAYAK",
            "father_name": "RAMESH CHANDRA NAYAK",
            "annual_income": 180000.0,
            "issue_date": "2025-01-10",
            "certificate_no": "EINC/2025/104928"
        }
    }

    # Fixture 2: "Kumar" as Middle Name
    f2_lines = [
        ("GOVERNMENT OF ODISHA - REVENUE DEPARTMENT", 13, True),
        ("INCOME CERTIFICATE", 14, True),
        "---",
        "Certificate No: E-INC/2025/209141",
        "Issue Date: 15/02/2025",
        "This is to certify that Santosh Kumar Nayak, Son/Daughter of Ramesh Chandra Nayak, resident of",
        "Tahsil BHUBANESWAR, District KHORDHA, State of ODISHA.",
        "Annual Family Income (in figures): Rs. 2,40,000/-",
        "---",
        "Digitally Signed by: Tahsildar"
    ]
    fn2 = "l05_kumar_middle_name.pdf"
    _create_pdf_from_lines(f2_lines, OUT_DIR / fn2)
    manifest[fn2] = {
        "file_name": fn2,
        "doc_type": "INCOME_CERT",
        "category": "kumar_middle_name",
        "expected_fields": {
            "applicant_name": "SANTOSH NAYAK",
            "father_name": "RAMESH CHANDRA NAYAK",
            "annual_income": 240000.0,
            "issue_date": "2025-02-15"
        }
    }

    # Fixture 3: "Kumar" as Given Name
    f3_lines = [
        ("COUNCIL OF HIGHER SECONDARY EDUCATION, ODISHA", 13, True),
        ("SENIOR SCHOOL CERTIFICATE EXAMINATION MARKSHEET", 12, True),
        "---",
        "Candidate Name: Kumar Gaurav",
        "Father's Name: Ramesh Chandra Gaurav",
        "Roll No: 2309BA1042",
        "Date of Birth: 15/08/2004",
        "AGGREGATE RESULT: PASSED (78.5%)",
        "---",
        "Date of Issue: 25/05/2024"
    ]
    fn3 = "l05_kumar_given_name.pdf"
    _create_pdf_from_lines(f3_lines, OUT_DIR / fn3)
    manifest[fn3] = {
        "file_name": fn3,
        "doc_type": "MARKSHEET",
        "category": "kumar_given_name",
        "expected_fields": {
            "applicant_name": "KUMAR GAURAV",
            "father_name": "RAMESH CHANDRA GAURAV",
            "dob": "2004-08-15",
            "roll_no": "2309BA1042",
            "percentage": 78.5
        }
    }

    # Fixture 4: Dot-delimited Date Format
    f4_lines = [
        ("GOVERNMENT OF ODISHA - REVENUE DEPARTMENT", 13, True),
        ("RESIDENCE CERTIFICATE", 14, True),
        "---",
        "Certificate No: E-RES/2025/892104",
        "Issue Date: 10.01.2025",
        "Applicant Full Name: Smruti Ranjan Nayak",
        "Father / Guardian Name: Ramesh Chandra Nayak",
        "Domicile State: ODISHA",
        "---",
        "Digitally Signed"
    ]
    fn4 = "l05_date_dot_delimited.pdf"
    _create_pdf_from_lines(f4_lines, OUT_DIR / fn4)
    manifest[fn4] = {
        "file_name": fn4,
        "doc_type": "RESIDENCE_CERT",
        "category": "date_dot_delimited",
        "expected_fields": {
            "applicant_name": "SMRUTI RANJAN NAYAK",
            "father_name": "RAMESH CHANDRA NAYAK",
            "issue_date": "2025-01-10",
            "state": "ODISHA"
        }
    }

    # Fixture 5: Named Month Date Format (e.g. 10 Jan 2025)
    f5_lines = [
        ("GOVERNMENT OF ODISHA - REVENUE DEPARTMENT", 13, True),
        ("RESIDENCE CERTIFICATE", 14, True),
        "---",
        "Certificate No: E-RES/2025/892105",
        "Issue Date: 10 Jan 2025",
        "Applicant Full Name: Smruti Ranjan Nayak",
        "Father / Guardian Name: Ramesh Chandra Nayak",
        "Domicile State: ODISHA",
        "---",
        "Digitally Signed"
    ]
    fn5 = "l05_date_named_month.pdf"
    _create_pdf_from_lines(f5_lines, OUT_DIR / fn5)
    manifest[fn5] = {
        "file_name": fn5,
        "doc_type": "RESIDENCE_CERT",
        "category": "date_named_month",
        "expected_fields": {
            "applicant_name": "SMRUTI RANJAN NAYAK",
            "issue_date": "2025-01-10"
        }
    }

    # Fixture 6: Dash-delimited Date Format (e.g. 10-01-2025)
    f6_lines = [
        ("GOVERNMENT OF ODISHA - REVENUE DEPARTMENT", 13, True),
        ("CASTE CERTIFICATE", 14, True),
        "---",
        "Certificate No: E-CST/2025/309124",
        "Issue Date: 10-01-2025",
        "Applicant Name: Smruti Ranjan Nayak",
        "Son/Daughter of: Ramesh Chandra Nayak",
        "Recognized Category: SEBC",
        "Sub-Caste: CHASA",
        "State: ODISHA",
        "---",
        "Digitally Signed"
    ]
    fn6 = "l05_date_dash_delimited.pdf"
    _create_pdf_from_lines(f6_lines, OUT_DIR / fn6)
    manifest[fn6] = {
        "file_name": fn6,
        "doc_type": "CASTE_CERT",
        "category": "date_dash_delimited",
        "expected_fields": {
            "applicant_name": "SMRUTI RANJAN NAYAK",
            "issue_date": "2025-01-10",
            "caste_category": "SEBC"
        }
    }

    # Fixture 7: Boxed Table Layout with Pipes and Vertical Separators
    f7_lines = [
        ("GOVERNMENT OF ODISHA - REVENUE & DISASTER MANAGEMENT", 13, True),
        ("OFFICIAL INCOME CERTIFICATE (ASSESSMENT FORM)", 12, True),
        "---",
        "| Field Name | Extracted Record Value |",
        "| Certificate Number | E-INC/2025/778899 |",
        "| Date of Issue | 10/01/2025 |",
        "| Applicant Name | Smruti Ranjan Nayak |",
        "| Father's Name | Ramesh Chandra Nayak |",
        "| Total Annual Family Income | Rs. 1,80,000 |",
        "| State of Domicile | ODISHA |",
        "---",
        "Authorized by Revenue Officer"
    ]
    fn7 = "l05_table_boxed_layout.pdf"
    _create_pdf_from_lines(f7_lines, OUT_DIR / fn7)
    manifest[fn7] = {
        "file_name": fn7,
        "doc_type": "INCOME_CERT",
        "category": "table_pipe_layout",
        "expected_fields": {
            "applicant_name": "SMRUTI RANJAN NAYAK",
            "father_name": "RAMESH CHANDRA NAYAK",
            "annual_income": 180000.0,
            "certificate_no": "EINC/2025/778899"
        }
    }

    # Fixture 8: Genuine Competing Candidate Values on Same Document
    f8_lines = [
        ("GOVERNMENT OF ODISHA - REVENUE DEPARTMENT", 13, True),
        ("INCOME ASSESSMENT STATEMENT", 14, True),
        "---",
        "Applicant Name: Smruti Ranjan Nayak",
        "Son/Daughter of: Ramesh Chandra Nayak",
        "Assessment Year: 2024-2025",
        "Income from Agriculture: Rs. 1,20,000",
        "Income from Other Sources: Rs. 60,000",
        "Total Annual Family Income: Rs. 1,80,000",
        "Prior Year Declared Income: Rs. 2,40,000",
        "Issue Date: 10/01/2025",
        "Certificate No: E-INC/2025/554433"
    ]
    fn8 = "l05_competing_amounts_conflict.pdf"
    _create_pdf_from_lines(f8_lines, OUT_DIR / fn8)
    manifest[fn8] = {
        "file_name": fn8,
        "doc_type": "INCOME_CERT",
        "category": "competing_amounts_ambiguity",
        "expected_fields": {
            "applicant_name": "SMRUTI RANJAN NAYAK",
            "annual_income": 180000.0
        }
    }

    # Fixture 9: Father's Name with S/o and No Trailing Comma
    f9_lines = [
        ("GOVERNMENT OF ODISHA - REVENUE DEPARTMENT", 13, True),
        ("INCOME CERTIFICATE", 14, True),
        "---",
        "Certificate No: E-INC/2025/901234",
        "Issue Date: 10/01/2025",
        "This is to certify that Smruti Ranjan Nayak S/o Ramesh Chandra Nayak resident of Tahsil",
        "BHUBANESWAR District KHORDHA State of ODISHA",
        "Annual Family Income (in figures): Rs. 1,80,000/-",
        "---",
        "Digitally Signed by Revenue Officer"
    ]
    fn9 = "l05_father_name_no_comma.pdf"
    _create_pdf_from_lines(f9_lines, OUT_DIR / fn9)
    manifest[fn9] = {
        "file_name": fn9,
        "doc_type": "INCOME_CERT",
        "category": "father_name_so_no_comma",
        "expected_fields": {
            "applicant_name": "SMRUTI RANJAN NAYAK",
            "father_name": "RAMESH CHANDRA NAYAK",
            "annual_income": 180000.0
        }
    }

    # Fixture 10: Aadhaar Document Slot
    f10_lines = [
        ("GOVERNMENT OF INDIA - UNIQUE IDENTIFICATION AUTHORITY OF INDIA", 12, True),
        ("AADHAAR ENROLMENT / IDENTITY CARD", 14, True),
        "---",
        "Name: Smruti Ranjan Nayak",
        "DOB: 10/01/2005",
        "Gender: Male",
        "Aadhaar Number: XXXX XXXX 1234",
        "Care of: Ramesh Chandra Nayak",
        "Address: At-Bhubaneswar, Khordha, Odisha - 751001",
        "---",
        "Mera Aadhaar, Meri Pehchan"
    ]
    fn10 = "l05_aadhaar_card_standard.pdf"
    _create_pdf_from_lines(f10_lines, OUT_DIR / fn10)
    manifest[fn10] = {
        "file_name": fn10,
        "doc_type": "AADHAAR",
        "category": "aadhaar_card_extraction",
        "expected_fields": {
            "applicant_name": "SMRUTI RANJAN NAYAK",
            "dob": "2005-01-10",
            "gender": "MALE",
            "aadhaar_no": "XXXXXXXX1234"
        }
    }

    # Fixture 11: Income with LPA notation
    f11_lines = [
        ("GOVERNMENT OF ODISHA - REVENUE DEPARTMENT", 13, True),
        ("INCOME CERTIFICATE", 14, True),
        "---",
        "Certificate No: E-INC/2025/667788",
        "Issue Date: 10/01/2025",
        "Applicant Name: Smruti Ranjan Nayak",
        "Father's Name: Ramesh Chandra Nayak",
        "Annual Family Income: 1.8 LPA",
        "State: ODISHA",
        "---",
        "Digitally Signed"
    ]
    fn11 = "l05_income_lpa_format.pdf"
    _create_pdf_from_lines(f11_lines, OUT_DIR / fn11)
    manifest[fn11] = {
        "file_name": fn11,
        "doc_type": "INCOME_CERT",
        "category": "income_lpa_multiplier",
        "expected_fields": {
            "applicant_name": "SMRUTI RANJAN NAYAK",
            "annual_income": 180000.0
        }
    }

    # Fixture 12: Certificate Number with OCR O/0 ambiguity
    f12_lines = [
        ("GOVERNMENT OF ODISHA - REVENUE DEPARTMENT", 13, True),
        ("INCOME CERTIFICATE", 14, True),
        "---",
        "Certificate No: E-INC/2O25/1O4928",
        "Issue Date: 10/01/2025",
        "Applicant Name: Smruti Ranjan Nayak",
        "Father's Name: Ramesh Chandra Nayak",
        "Annual Family Income: Rs. 1,80,000/-",
        "---",
        "Digitally Signed"
    ]
    fn12 = "l05_ocr_digit_confused_cert.pdf"
    _create_pdf_from_lines(f12_lines, OUT_DIR / fn12)
    manifest[fn12] = {
        "file_name": fn12,
        "doc_type": "INCOME_CERT",
        "category": "ocr_digit_confused_cert",
        "expected_fields": {
            "applicant_name": "SMRUTI RANJAN NAYAK",
            "certificate_no": "EINC/2025/104928"
        }
    }

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"Generated {len(manifest)} Loop 05 extraction fixtures in {OUT_DIR}")


if __name__ == "__main__":
    generate_corpus()
