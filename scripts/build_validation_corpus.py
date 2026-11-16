"""Builds the dedicated, synthetic Loop 4 Validation Corpus and generates a machine-readable manifest.

This corpus is completely isolated from production golden baselines and includes:
- Clean vector statutory scholarship documents (Application, Income, Caste, Residence, Passbook, Marksheet)
- Deliberate conflicts (name mismatch, income ceiling exceeded)
- Invalid / hostile documents (0-byte, corrupted header, encrypted, spoofed extension)
- Negative / irrelevant documents (resume with zero scholarship slots)
- Scanned raster PDFs (200 DPI bitmap for OCR verification)
- Rotated pages (90 deg clockwise)
"""
from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path

import pymupdf
from PIL import Image

from docuready.generator import (
    generate_application_form,
    generate_bank_passbook,
    generate_caste_certificate,
    generate_income_certificate,
    generate_marksheet,
    generate_residence_certificate,
)

CORPUS_DIR = Path("tests/validation_corpus")
MANIFEST_PATH = Path("docs/validation_corpus_manifest.json")


def sha256_file(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def render_pdf_to_scanned_pdf(input_pdf: Path, output_pdf: Path, dpi: int = 200) -> None:
    """Renders a PDF page into a raster bitmap and saves as an image-only PDF."""
    doc = pymupdf.open(str(input_pdf))
    page = doc[0]
    pix = page.get_pixmap(dpi=dpi)
    img_data = pix.tobytes("png")
    doc.close()

    img = Image.open(io.BytesIO(img_data)).convert("RGB")
    img.save(str(output_pdf), "PDF", resolution=float(dpi))


def build_corpus() -> list[dict]:
    CORPUS_DIR.mkdir(parents=True, exist_ok=True)
    manifest_entries = []

    # 1. VAL-01-CLEAN-APP (Vector PDF)
    f1 = CORPUS_DIR / "VAL_01_application_form.pdf"
    generate_application_form(
        str(f1),
        applicant_name="Aarav Sharma",
        father_name="Mukesh Sharma",
        dob="15/08/2003",
        annual_income="Rs. 1,20,000/-",
        caste_category="SCHEDULED CASTE (SC)",
        income_cert_no="E-INC/2025/110294",
        caste_cert_no="E-CST/2024/774019",
        residence_cert_no="E-RES/2025/330912",
        account_no="123456789012",
        ifsc="SBIN0001234",
    )
    manifest_entries.append({
        "document_id": "VAL-01-CLEAN-APP",
        "file_name": f1.name,
        "format": "PDF",
        "page_count": 1,
        "category": "VALID_VECTOR",
        "expected_ingestion": "ACCEPTED",
        "expected_extraction": "NATIVE_VECTOR",
        "expected_evidence": "HIGH_CONFIDENCE_ALL_SLOTS",
        "expected_audit_status": "READY_WHEN_PACKET_COMPLETE",
        "sha256": sha256_file(f1),
    })

    # 2. VAL-02-CLEAN-INC (Vector PDF)
    f2 = CORPUS_DIR / "VAL_02_income_cert_clean.pdf"
    generate_income_certificate(
        str(f2),
        applicant_name="Aarav Sharma",
        father_name="Mukesh Sharma",
        annual_income="1,20,000",
        issue_date="10/01/2025",
        certificate_no="E-INC/2025/110294",
    )
    manifest_entries.append({
        "document_id": "VAL-02-CLEAN-INC",
        "file_name": f2.name,
        "format": "PDF",
        "page_count": 1,
        "category": "VALID_VECTOR",
        "expected_ingestion": "ACCEPTED",
        "expected_extraction": "NATIVE_VECTOR",
        "expected_evidence": "HIGH_CONFIDENCE_INCOME",
        "expected_audit_status": "PASS",
        "sha256": sha256_file(f2),
    })

    # 3. VAL-03-CLEAN-CST (Vector PDF)
    f3 = CORPUS_DIR / "VAL_03_caste_cert_clean.pdf"
    generate_caste_certificate(
        str(f3),
        applicant_name="Aarav Sharma",
        father_name="Mukesh Sharma",
        caste_category="SCHEDULED CASTE (SC)",
        sub_caste="Dhoba",
        issue_date="05/11/2024",
        certificate_no="E-CST/2024/774019",
    )
    manifest_entries.append({
        "document_id": "VAL-03-CLEAN-CST",
        "file_name": f3.name,
        "format": "PDF",
        "page_count": 1,
        "category": "VALID_VECTOR",
        "expected_ingestion": "ACCEPTED",
        "expected_extraction": "NATIVE_VECTOR",
        "expected_evidence": "HIGH_CONFIDENCE_CASTE",
        "expected_audit_status": "PASS",
        "sha256": sha256_file(f3),
    })

    # 4. VAL-04-CLEAN-RES (Vector PDF)
    f4 = CORPUS_DIR / "VAL_04_residence_cert_clean.pdf"
    generate_residence_certificate(
        str(f4),
        applicant_name="Aarav Sharma",
        father_name="Mukesh Sharma",
        address="Plot 104, Saheed Nagar, Bhubaneswar",
        state="ODISHA",
        district="KHORDHA",
        issue_date="15/01/2025",
        certificate_no="E-RES/2025/330912",
    )
    manifest_entries.append({
        "document_id": "VAL-04-CLEAN-RES",
        "file_name": f4.name,
        "format": "PDF",
        "page_count": 1,
        "category": "VALID_VECTOR",
        "expected_ingestion": "ACCEPTED",
        "expected_extraction": "NATIVE_VECTOR",
        "expected_evidence": "HIGH_CONFIDENCE_RESIDENCE",
        "expected_audit_status": "PASS",
        "sha256": sha256_file(f4),
    })

    # 5. VAL-05-CLEAN-PASSBOOK (Vector PDF)
    f5 = CORPUS_DIR / "VAL_05_bank_passbook_clean.pdf"
    generate_bank_passbook(
        str(f5),
        applicant_name="Aarav Sharma",
        account_no="123456789012",
        ifsc="SBIN0001234",
        dbt_status="NPCI Aadhaar Mapped / DBT Active",
    )
    manifest_entries.append({
        "document_id": "VAL-05-CLEAN-PASSBOOK",
        "file_name": f5.name,
        "format": "PDF",
        "page_count": 1,
        "category": "VALID_VECTOR",
        "expected_ingestion": "ACCEPTED",
        "expected_extraction": "NATIVE_VECTOR",
        "expected_evidence": "HIGH_CONFIDENCE_BANK_DBT",
        "expected_audit_status": "PASS",
        "sha256": sha256_file(f5),
    })

    # 6. VAL-06-CLEAN-MARKSHEET (Vector PDF)
    f6 = CORPUS_DIR / "VAL_06_marksheet_clean.pdf"
    generate_marksheet(
        str(f6),
        applicant_name="Aarav Sharma",
        father_name="Mukesh Sharma",
        dob="15/08/2003",
        roll_no="043-BS-9912",
        percentage=84.5,
    )
    manifest_entries.append({
        "document_id": "VAL-06-CLEAN-MARKSHEET",
        "file_name": f6.name,
        "format": "PDF",
        "page_count": 1,
        "category": "VALID_VECTOR",
        "expected_ingestion": "ACCEPTED",
        "expected_extraction": "NATIVE_VECTOR",
        "expected_evidence": "HIGH_CONFIDENCE_MARKSHEET",
        "expected_audit_status": "PASS",
        "sha256": sha256_file(f6),
    })

    # 7. VAL-07-NAME-CONFLICT-INC (Vector PDF with Mismatched Name)
    f7 = CORPUS_DIR / "VAL_07_income_cert_name_conflict.pdf"
    generate_income_certificate(
        str(f7),
        applicant_name="Vikramaditya Roy",  # Severe mismatch vs Aarav Sharma
        father_name="Mukesh Sharma",
        annual_income="1,20,000",
        issue_date="10/01/2025",
        certificate_no="E-INC/2025/110294",
    )
    manifest_entries.append({
        "document_id": "VAL-07-NAME-CONFLICT-INC",
        "file_name": f7.name,
        "format": "PDF",
        "page_count": 1,
        "category": "DELIBERATE_CONFLICT",
        "expected_ingestion": "ACCEPTED",
        "expected_extraction": "NATIVE_VECTOR",
        "expected_evidence": "EXTRACTED_CONTRADICTORY_NAME",
        "expected_audit_status": "FAIL_RULE_NAME_01",
        "sha256": sha256_file(f7),
    })

    # 8. VAL-08-INCOME-CEIL-EXCEEDED (Vector PDF with > 2.5L Income)
    f8 = CORPUS_DIR / "VAL_08_income_cert_ceiling_exceeded.pdf"
    generate_income_certificate(
        str(f8),
        applicant_name="Aarav Sharma",
        father_name="Mukesh Sharma",
        annual_income="4,50,000",  # Exceeds Rs. 2,50,000 limit
        issue_date="10/01/2025",
        certificate_no="E-INC/2025/110294",
    )
    manifest_entries.append({
        "document_id": "VAL-08-INCOME-CEIL-EXCEEDED",
        "file_name": f8.name,
        "format": "PDF",
        "page_count": 1,
        "category": "DELIBERATE_CONFLICT",
        "expected_ingestion": "ACCEPTED",
        "expected_extraction": "NATIVE_VECTOR",
        "expected_evidence": "EXTRACTED_EXCESS_INCOME",
        "expected_audit_status": "FAIL_RULE_INC_01",
        "sha256": sha256_file(f8),
    })

    # 9. VAL-09-CORRUPTED-HEADER (Malformed PDF header)
    f9 = CORPUS_DIR / "VAL_09_corrupted_header.pdf"
    with open(f9, "wb") as f:
        f.write(b"%NOT_A_PDF_STREAM_CORRUPTED_HEADER_DATA_123456789\n%%EOF\n")
    manifest_entries.append({
        "document_id": "VAL-09-CORRUPTED-HEADER",
        "file_name": f9.name,
        "format": "PDF",
        "page_count": 0,
        "category": "HOSTILE_INPUT",
        "expected_ingestion": "CORRUPTED_DOCUMENT_STATUS",
        "expected_extraction": "ZERO_FIELDS_EXTRACTED",
        "expected_evidence": "NO_EVIDENCE_FABRICATION",
        "expected_audit_status": "FAIL_CORRUPTED",
        "sha256": sha256_file(f9),
    })

    # 10. VAL-10-EMPTY-ZERO-BYTE (0-byte file)
    f10 = CORPUS_DIR / "VAL_10_empty_zero_byte.pdf"
    with open(f10, "wb") as f:
        pass
    manifest_entries.append({
        "document_id": "VAL-10-EMPTY-ZERO-BYTE",
        "file_name": f10.name,
        "format": "PDF",
        "page_count": 0,
        "category": "HOSTILE_INPUT",
        "expected_ingestion": "REJECTED_AT_INGESTION_BOUNDARY",
        "expected_extraction": "NONE",
        "expected_evidence": "NONE",
        "expected_audit_status": "INVALID_PARAMS_ERROR",
        "sha256": sha256_file(f10),
    })

    # 11. VAL-11-PASSWORD-ENCRYPTED (Password protected PDF)
    f11 = CORPUS_DIR / "VAL_11_encrypted_password.pdf"
    doc_enc = pymupdf.open()
    doc_enc.new_page(width=595, height=842)
    doc_enc.save(
        str(f11),
        encryption=pymupdf.PDF_ENCRYPT_AES_256,
        user_pw="secure_user_pass",
        owner_pw="secure_owner_pass",
        permissions=pymupdf.PDF_PERM_ACCESSIBILITY,
    )
    doc_enc.close()
    manifest_entries.append({
        "document_id": "VAL-11-PASSWORD-ENCRYPTED",
        "file_name": f11.name,
        "format": "PDF",
        "page_count": 1,
        "category": "HOSTILE_INPUT",
        "expected_ingestion": "REJECTED_NEEDS_PASSWORD",
        "expected_extraction": "NONE",
        "expected_evidence": "NO_CREDENTIAL_LEAK",
        "expected_audit_status": "UNREADABLE_ENCRYPTED",
        "sha256": sha256_file(f11),
    })

    # 12. VAL-12-SPOOFED-EXTENSION (Text file named as .pdf)
    f12 = CORPUS_DIR / "VAL_12_spoofed_text_as_pdf.pdf"
    with open(f12, "w", encoding="utf-8") as f:
        f.write("This is a plain UTF-8 text document spoofing the .pdf extension to test MIME detection.")
    manifest_entries.append({
        "document_id": "VAL-12-SPOOFED-EXTENSION",
        "file_name": f12.name,
        "format": "TXT_SPOOFED_AS_PDF",
        "page_count": 0,
        "category": "HOSTILE_INPUT",
        "expected_ingestion": "SIGNATURE_VALIDATION_FAILURE",
        "expected_extraction": "NONE",
        "expected_evidence": "NONE",
        "expected_audit_status": "INVALID_MAGIC_BYTES_REJECTED",
        "sha256": sha256_file(f12),
    })

    # 13. VAL-13-IRRELEVANT-RESUME (Unmapped document with no scholarship slots)
    f13 = CORPUS_DIR / "VAL_13_irrelevant_resume.pdf"
    doc_neg = pymupdf.open()
    p_neg = doc_neg.new_page(width=595, height=842)
    p_neg.insert_text(
        pymupdf.Point(50, 50),
        "CURRICULUM VITAE\nSoftware Engineer & Open Source Contributor\nExperience with Rust, TypeScript, and Go.",
        fontsize=12,
    )
    doc_neg.save(str(f13))
    doc_neg.close()
    manifest_entries.append({
        "document_id": "VAL-13-IRRELEVANT-RESUME",
        "file_name": f13.name,
        "format": "PDF",
        "page_count": 1,
        "category": "NEGATIVE_UNMAPPED",
        "expected_ingestion": "ACCEPTED_AS_UNRECOGNIZED_SLOT",
        "expected_extraction": "ZERO_SCHOLARSHIP_FIELDS",
        "expected_evidence": "NO_FALSE_POSITIVE_EVIDENCE",
        "expected_audit_status": "UNMAPPED_DOCUMENT_PASS_THROUGH",
        "sha256": sha256_file(f13),
    })

    # 14. VAL-14-SCANNED-RES (Scanned Raster PDF)
    f14 = CORPUS_DIR / "VAL_14_residence_cert_scanned.pdf"
    render_pdf_to_scanned_pdf(f4, f14, dpi=200)
    manifest_entries.append({
        "document_id": "VAL-14-SCANNED-RES",
        "file_name": f14.name,
        "format": "PDF",
        "page_count": 1,
        "category": "SCANNED_RASTER",
        "expected_ingestion": "ACCEPTED",
        "expected_extraction": "OCR_REQUIRED",
        "expected_evidence": "OCR_CONFIDENCE_ESTIMATED",
        "expected_audit_status": "PASS_OR_REVIEW_IF_NO_OCR",
        "sha256": sha256_file(f14),
    })

    # 15. VAL-15-SCANNED-PASSBOOK (Scanned Raster PDF)
    f15 = CORPUS_DIR / "VAL_15_bank_passbook_scanned.pdf"
    render_pdf_to_scanned_pdf(f5, f15, dpi=200)
    manifest_entries.append({
        "document_id": "VAL-15-SCANNED-PASSBOOK",
        "file_name": f15.name,
        "format": "PDF",
        "page_count": 1,
        "category": "SCANNED_RASTER",
        "expected_ingestion": "ACCEPTED",
        "expected_extraction": "OCR_REQUIRED",
        "expected_evidence": "OCR_CONFIDENCE_ESTIMATED",
        "expected_audit_status": "PASS_OR_REVIEW_IF_NO_OCR",
        "sha256": sha256_file(f15),
    })

    # 16. VAL-16-ROTATED-MARKSHEET (90 deg Clockwise Vector PDF)
    f16 = CORPUS_DIR / "VAL_16_marksheet_rotated_90.pdf"
    doc_rot = pymupdf.open(str(f6))
    doc_rot[0].set_rotation(90)
    doc_rot.save(str(f16))
    doc_rot.close()
    manifest_entries.append({
        "document_id": "VAL-16-ROTATED-MARKSHEET",
        "file_name": f16.name,
        "format": "PDF",
        "page_count": 1,
        "category": "ROTATED_GEOMETRY",
        "expected_ingestion": "ACCEPTED",
        "expected_extraction": "NATIVE_VECTOR_ROTATED",
        "expected_evidence": "COORDINATE_ROTATION_TRANSFORM_VERIFIED",
        "expected_audit_status": "PASS",
        "sha256": sha256_file(f16),
    })

    manifest = {
        "corpus_version": "1.0.0",
        "total_documents": len(manifest_entries),
        "documents": manifest_entries,
    }

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"Generated {len(manifest_entries)} validation documents in {CORPUS_DIR}")
    print(f"Manifest written to {MANIFEST_PATH}")
    return manifest_entries


if __name__ == "__main__":
    build_corpus()
