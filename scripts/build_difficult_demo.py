"""
Loop 3 Difficult Demonstration Packet Builder: pkt_loop3_demo
Creates a demonstration packet with mixed evidence modalities:
- Clean vector text: application_form.pdf, income_cert.pdf
- Low-resolution scan: bank_passbook.pdf
- Shadowed / uneven lighting scan: residence_cert.pdf
- Perspective distortion scan: marksheet.pdf
- Defective scanned document: caste_cert.pdf (OBC vs SC discrepancy)
And generates the compliant replacement document:
- clean_caste_cert_compliant.pdf (SCHEDULED CASTE)
"""

import os
from docuready.generator import (
    generate_application_form, generate_income_certificate,
    generate_caste_certificate, generate_residence_certificate,
    generate_marksheet, generate_bank_passbook
)
from corpus_builder_60 import (
    _render_pdf_to_image, _save_image_as_scanned_pdf,
    apply_shadow_and_uneven_lighting, apply_perspective_distortion,
    apply_low_resolution
)

DEMO_DIR = "synthetic_data/pkt_loop3_demo"
REPLACE_DIR = "synthetic_data/replacement_docs"


def build_loop3_demo_packet():
    os.makedirs(DEMO_DIR, exist_ok=True)
    os.makedirs(REPLACE_DIR, exist_ok=True)

    # 1. Clean Vector Application Form
    app_path = os.path.join(DEMO_DIR, "application_form.pdf")
    generate_application_form(
        app_path,
        applicant_name="Smruti Ranjan Nayak",
        father_name="Ramesh Chandra Nayak",
        dob="10/01/2003",
        annual_income="Rs. 1,80,000/-",
        caste_category="SCHEDULED CASTE (SC)",
        income_cert_no="E-INC/2025/104928",
        caste_cert_no="CST/2024/991204",
        residence_cert_no="RES/2025/441029",
        account_no="30987654301",
        ifsc="SBIN0001234"
    )

    # 2. Clean Vector Income Certificate
    inc_path = os.path.join(DEMO_DIR, "income_cert.pdf")
    generate_income_certificate(
        inc_path,
        applicant_name="Smruti Ranjan Nayak",
        father_name="Ramesh Chandra Nayak",
        annual_income="Rs. 1,80,000/-",
        issue_date="10/01/2025",
        certificate_no="E-INC/2025/104928",
        state="ODISHA"
    )

    # 3. Defective Scanned Caste Certificate (OBC vs Form's SC)
    cst_tmp = os.path.join(DEMO_DIR, "_tmp_cst.pdf")
    generate_caste_certificate(
        cst_tmp,
        applicant_name="Smruti Ranjan Nayak",
        father_name="Ramesh Chandra Nayak",
        caste_category="OTHER BACKWARD CLASSES (OBC)",  # Defect! Mismatches SC on form
        sub_caste="Gope",
        issue_date="12/03/2024",
        certificate_no="CST/2024/991204",
        state="ODISHA"
    )
    img_cst = _render_pdf_to_image(cst_tmp, dpi=200)
    cst_path = os.path.join(DEMO_DIR, "caste_cert.pdf")
    _save_image_as_scanned_pdf(img_cst, cst_path)
    if os.path.exists(cst_tmp):
        os.remove(cst_tmp)

    # 4. Residence Certificate with Shadow / Uneven Lighting
    res_tmp = os.path.join(DEMO_DIR, "_tmp_res.pdf")
    generate_residence_certificate(
        res_tmp,
        applicant_name="Smruti Ranjan Nayak",
        father_name="Ramesh Chandra Nayak",
        address="Plot 104, Saheed Nagar, Bhubaneswar",
        state="ODISHA",
        issue_date="15/01/2025",
        certificate_no="RES/2025/441029"
    )
    img_res = _render_pdf_to_image(res_tmp, dpi=200)
    img_res_shadow = apply_shadow_and_uneven_lighting(img_res)
    res_path = os.path.join(DEMO_DIR, "residence_cert.pdf")
    _save_image_as_scanned_pdf(img_res_shadow, res_path)
    if os.path.exists(res_tmp):
        os.remove(res_tmp)

    # 5. Marksheet with Mobile Perspective Distortion
    mrk_tmp = os.path.join(DEMO_DIR, "_tmp_mrk.pdf")
    generate_marksheet(
        mrk_tmp,
        applicant_name="Smruti Ranjan Nayak",
        father_name="Ramesh Chandra Nayak",
        dob="10/01/2003",
        roll_no="2409BA1042",
        percentage=74.5
    )
    img_mrk = _render_pdf_to_image(mrk_tmp, dpi=200)
    img_mrk_warp = apply_perspective_distortion(img_mrk)
    mrk_path = os.path.join(DEMO_DIR, "marksheet.pdf")
    _save_image_as_scanned_pdf(img_mrk_warp, mrk_path)
    if os.path.exists(mrk_tmp):
        os.remove(mrk_tmp)

    # 6. Bank Passbook with Low Resolution (0.45 downscale)
    bnk_tmp = os.path.join(DEMO_DIR, "_tmp_bnk.pdf")
    generate_bank_passbook(
        bnk_tmp,
        applicant_name="Smruti Ranjan Nayak",
        account_no="30987654301",
        ifsc="SBIN0001234"
    )
    img_bnk = _render_pdf_to_image(bnk_tmp, dpi=200)
    img_bnk_low = apply_low_resolution(img_bnk, factor=0.45)
    bnk_path = os.path.join(DEMO_DIR, "bank_passbook.pdf")
    _save_image_as_scanned_pdf(img_bnk_low, bnk_path)
    if os.path.exists(bnk_tmp):
        os.remove(bnk_tmp)

    # 7. Compliant Replacement Caste Certificate (SCHEDULED CASTE)
    replace_cst_tmp = os.path.join(REPLACE_DIR, "_tmp_replace_cst.pdf")
    generate_caste_certificate(
        replace_cst_tmp,
        applicant_name="Smruti Ranjan Nayak",
        father_name="Ramesh Chandra Nayak",
        caste_category="SCHEDULED CASTE (SC)",  # Corrected!
        sub_caste="Dhoba",
        issue_date="12/03/2024",
        certificate_no="CST/2024/991204",
        state="ODISHA"
    )
    img_replace = _render_pdf_to_image(replace_cst_tmp, dpi=200)
    replace_cst_path = os.path.join(REPLACE_DIR, "clean_caste_cert_compliant.pdf")
    _save_image_as_scanned_pdf(img_replace, replace_cst_path)
    if os.path.exists(replace_cst_tmp):
        os.remove(replace_cst_tmp)

    print(f"Generated Loop 3 Difficult Demo Packet in '{DEMO_DIR}'")
    print(f"Generated Replacement Document: '{replace_cst_path}'")


if __name__ == "__main__":
    build_loop3_demo_packet()
