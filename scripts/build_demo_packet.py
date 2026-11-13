"""
Builder script for the Loop 2 Realistic Demonstration Packet
Creates a realistic hybrid packet containing:
1. Clean vector PDF: application_form.pdf
2. Scanned raster PDF: caste_cert.pdf (200 DPI OCR)
3. Degraded scanned PDF with defect: income_cert.pdf (mismatch ₹2,80,000 vs declared ₹1,80,000)
4. Ambiguous date document: marksheet.pdf (DOB: 05/06/2003)
5. Scanned raster PDF: bank_passbook.pdf
6. Scanned raster PDF: residence_cert.pdf
And generates the compliant replacement income certificate: clean_income_cert_compliant.pdf
"""

import os
import shutil
from src.generator import (
    generate_application_form, generate_income_certificate,
    generate_caste_certificate, generate_residence_certificate,
    generate_marksheet, generate_bank_passbook
)
from src.corpus_builder_60 import _render_pdf_to_image, _save_image_as_scanned_pdf, apply_shadow_and_uneven_lighting

DEMO_DIR = "docuready-mvp/synthetic_data/pkt_realistic_demo"
REPLACE_DIR = "docuready-mvp/synthetic_data/replacement_docs"
os.makedirs(DEMO_DIR, exist_ok=True)
os.makedirs(REPLACE_DIR, exist_ok=True)

# 1. Clean Vector Application Form
app_path = os.path.join(DEMO_DIR, "application_form.pdf")
generate_application_form(
    app_path,
    applicant_name="Smruti Ranjan Nayak",
    father_name="Ramesh Chandra Nayak",
    dob="05/06/2003",
    annual_income="Rs. 1,80,000/-",
    caste_category="SCHEDULED CASTE (SC)",
    income_cert_no="E-INC/2025/104928",
    caste_cert_no="E-CST/2024/991204",
    residence_cert_no="E-RES/2025/441029",
    account_no="123456789012",
    ifsc="SBIN0001234"
)

# 2. Scanned Caste Certificate (Raster 200 DPI)
cst_temp = os.path.join(DEMO_DIR, "_tmp_cst.pdf")
generate_caste_certificate(
    cst_temp,
    applicant_name="Smruti Ranjan Nayak",
    father_name="Ramesh Chandra Nayak",
    caste_category="SCHEDULED CASTE (SC)",
    sub_caste="Dhoba",
    issue_date="15/01/2025",
    certificate_no="E-CST/2024/991204"
)
img_cst = _render_pdf_to_image(cst_temp, dpi=200)
cst_final = os.path.join(DEMO_DIR, "caste_cert.pdf")
_save_image_as_scanned_pdf(img_cst, cst_final)
if os.path.exists(cst_temp):
    os.remove(cst_temp)

# 3. Defective / Mismatched Scanned Income Certificate (Income = 2,80,000 exceeds ceiling and declared 1,80,000)
inc_temp = os.path.join(DEMO_DIR, "_tmp_inc.pdf")
generate_income_certificate(
    inc_temp,
    applicant_name="Smruti Ranjan Nayak",
    father_name="Ramesh Chandra Nayak",
    annual_income="Rs. 2,80,000/-",  # Defect: Breaches ₹2.5L ceiling and mismatches application form
    issue_date="10/01/2025",
    certificate_no="E-INC/2025/999999"  # Defect: Reference number mismatch
)
img_inc = _render_pdf_to_image(inc_temp, dpi=200)
img_inc_degraded = apply_shadow_and_uneven_lighting(img_inc)
inc_final = os.path.join(DEMO_DIR, "income_cert.pdf")
_save_image_as_scanned_pdf(img_inc_degraded, inc_final)
if os.path.exists(inc_temp):
    os.remove(inc_temp)

# 4. Marksheet with Ambiguous Date (05/06/2003) and 68.5%
mrk_path = os.path.join(DEMO_DIR, "marksheet.pdf")
generate_marksheet(
    mrk_path,
    applicant_name="Smruti Ranjan Nayak",
    father_name="Ramesh Chandra Nayak",
    dob="05/06/2003",
    percentage=68.5,
    roll_no="24-HSC-10842"
)

# 5. Scanned Bank Passbook (Raster 200 DPI)
bnk_temp = os.path.join(DEMO_DIR, "_tmp_bnk.pdf")
generate_bank_passbook(
    bnk_temp,
    applicant_name="Smruti Ranjan Nayak",
    account_no="123456789012",
    ifsc="SBIN0001234",
    dbt_status="NPCI Aadhaar Mapped / DBT Active"
)
img_bnk = _render_pdf_to_image(bnk_temp, dpi=200)
bnk_final = os.path.join(DEMO_DIR, "bank_passbook.pdf")
_save_image_as_scanned_pdf(img_bnk, bnk_final)
if os.path.exists(bnk_temp):
    os.remove(bnk_temp)

# 6. Scanned Residence Certificate (Raster 200 DPI)
res_temp = os.path.join(DEMO_DIR, "_tmp_res.pdf")
generate_residence_certificate(
    res_temp,
    applicant_name="Smruti Ranjan Nayak",
    father_name="Ramesh Chandra Nayak",
    address="Plot 104, Shaheed Nagar, Bhubaneswar",
    state="ODISHA",
    certificate_no="E-RES/2025/441029"
)
img_res = _render_pdf_to_image(res_temp, dpi=200)
res_final = os.path.join(DEMO_DIR, "residence_cert.pdf")
_save_image_as_scanned_pdf(img_res, res_final)
if os.path.exists(res_temp):
    os.remove(res_temp)

# 7. Compliant Replacement Document
replace_inc_path = os.path.join(REPLACE_DIR, "clean_income_cert_compliant.pdf")
generate_income_certificate(
    replace_inc_path,
    applicant_name="Smruti Ranjan Nayak",
    father_name="Ramesh Chandra Nayak",
    annual_income="Rs. 1,80,000/-",  # Exact match with application form and within ceiling
    issue_date="10/01/2025",
    certificate_no="E-INC/2025/104928"  # Exact match with reference on form
)

print(f"Generated Loop 2 Demonstration Packet in '{DEMO_DIR}'.")
print(f"Generated Compliant Replacement Document in '{replace_inc_path}'.")
