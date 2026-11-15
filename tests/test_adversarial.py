"""
Adversarial Test Suite for DocuReady MVP
Verifies resilience against 13 edge cases and malformed inputs:
1. Similar but different names
2. Initials vs full names
3. DD/MM and MM/DD date ambiguity
4. Missing fields
5. Contradictory values
6. Invalid PDF files (corrupt bytes)
7. Empty / blank PDFs
8. Multi-page PDFs
9. Text positioned unusually on page
10. Duplicate documents
11. Incorrect document types
12. Extremely large files / high token volume
13. Malformed income expressions
"""

import os
import pytest
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from pathlib import Path
from docuready.domain.enums import Status
from docuready.domain.models import (
    DocumentType, ExtractedDocument, ExtractedField, FindingStatus, Severity
)
from docuready.ingest.extractor import DocumentExtractor, detect_document_type
from docuready.normalize.normalizer import (
    compare_names, parse_and_normalize_date, normalize_income
)
from docuready.rules.validator import DocuReadyValidator, SchemeConfig
from docuready.pipeline import AuditPipeline

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SYNTHETIC_DIR = _REPO_ROOT / "synthetic_data" if (_REPO_ROOT / "synthetic_data").is_dir() else Path.cwd() / "synthetic_data"
ADVERSARIAL_TMP = str(_SYNTHETIC_DIR / "adversarial_tmp")
os.makedirs(ADVERSARIAL_TMP, exist_ok=True)


# 1. Similar but different names
def test_similar_but_different_names():
    # Names with partial overlap but different identity
    res1 = compare_names("Smruti Ranjan Nayak", "Smruti Ranjan Rout")
    assert res1["status"] in ["FAIL", "REVIEW"]

    res2 = compare_names("Smruti Nayak", "Smita Nayak")
    assert res2["status"] in ["FAIL", "REVIEW"]


# 2. Initials versus full names
def test_initials_versus_full_names():
    res = compare_names("S R Nayak", "Smruti Ranjan Nayak")
    assert res["status"] == "REVIEW"
    assert res["type"] == "INITIALS_EXPANSION"


# 3. DD/MM and MM/DD ambiguity
def test_dd_mm_ambiguity():
    dt1, st1, amb1 = parse_and_normalize_date("04/05/2003")
    dt2, st2, amb2 = parse_and_normalize_date("05/04/2003")
    assert amb1 is True
    assert amb2 is True

    # Validate how validator treats ambiguous dates
    validator = DocuReadyValidator()
    docs = {
        DocumentType.APPLICATION_FORM: ExtractedDocument(
            doc_type=DocumentType.APPLICATION_FORM,
            file_path="app.pdf",
            fields={"dob": ExtractedField(field_name="dob", raw_value="04/05/2003", normalized_value="2003-05-04")}
        ),
        DocumentType.MARKSHEET: ExtractedDocument(
            doc_type=DocumentType.MARKSHEET,
            file_path="mark.pdf",
            fields={"dob": ExtractedField(field_name="dob", raw_value="05/04/2003", normalized_value="2003-04-05")}
        )
    }
    res = validator.validate_packet("TEST_AMB", docs)
    amb_findings = [f for f in res.findings if f.rule_id == "RULE-DOB-02"]
    assert len(amb_findings) == 1
    assert amb_findings[0].status == FindingStatus.REVIEW


# 4. Missing fields
def test_missing_mandatory_fields():
    validator = DocuReadyValidator()
    # Income cert with missing annual income
    docs = {
        DocumentType.INCOME_CERT: ExtractedDocument(
            doc_type=DocumentType.INCOME_CERT,
            file_path="inc.pdf",
            fields={"applicant_name": ExtractedField(field_name="applicant_name", raw_value="Smruti Nayak")}
        )
    }
    res = validator.validate_packet("TEST_MISSING_FLD", docs)
    missing_fld_findings = [f for f in res.findings if f.rule_id == "RULE-FLD-01"]
    assert len(missing_fld_findings) > 0
    assert any(f.field == "ANNUAL_INCOME" for f in missing_fld_findings)


# 5. Contradictory values
def test_contradictory_values():
    validator = DocuReadyValidator()
    docs = {
        DocumentType.APPLICATION_FORM: ExtractedDocument(
            doc_type=DocumentType.APPLICATION_FORM,
            file_path="app.pdf",
            fields={"dob": ExtractedField(field_name="dob", raw_value="14/05/2003", normalized_value="2003-05-14")}
        ),
        DocumentType.MARKSHEET: ExtractedDocument(
            doc_type=DocumentType.MARKSHEET,
            file_path="mark.pdf",
            fields={"dob": ExtractedField(field_name="dob", raw_value="14/05/2006", normalized_value="2006-05-14")}
        )
    }
    res = validator.validate_packet("TEST_CONTRADICT", docs)
    fail_findings = [f for f in res.findings if f.rule_id == "RULE-DOB-01"]
    assert len(fail_findings) == 1
    assert fail_findings[0].status == FindingStatus.FAIL


# 6. Invalid PDF files (corrupt bytes, truncated)
def test_invalid_pdf_files():
    extractor = DocumentExtractor()
    bad_pdf_path = os.path.join(ADVERSARIAL_TMP, "corrupted_stream.pdf")
    with open(bad_pdf_path, "wb") as f:
        f.write(b"NOT_A_REAL_PDF_HEADER\x00\x01\x02\x03\x04")

    doc = extractor.extract_document(bad_pdf_path)
    assert doc.status in ["CORRUPTED", "UNREADABLE"]


# 7. Empty / blank PDFs
def test_empty_blank_pdf():
    extractor = DocumentExtractor()
    blank_pdf_path = os.path.join(ADVERSARIAL_TMP, "blank_page.pdf")
    c = canvas.Canvas(blank_pdf_path, pagesize=letter)
    c.showPage() # Empty page with no text
    c.save()

    doc = extractor.extract_document(blank_pdf_path)
    assert doc.status in ["UNREADABLE", "CORRUPTED"]


# 8. Multi-page PDFs (data on page 2)
def test_multi_page_pdf():
    extractor = DocumentExtractor()
    multipage_path = os.path.join(ADVERSARIAL_TMP, "multipage_marksheet.pdf")
    c = canvas.Canvas(multipage_path, pagesize=letter)
    # Page 1: Intro
    c.drawString(100, 750, "BOARD OF SECONDARY EDUCATION, ODISHA")
    c.drawString(100, 720, "HIGH SCHOOL CERTIFICATE EXAMINATION")
    c.showPage()
    # Page 2: Candidate data
    c.drawString(100, 750, "Candidate Name: Smruti Ranjan Nayak")
    c.drawString(100, 720, "Date of Birth: 14/05/2003")
    c.drawString(100, 690, "AGGREGATE RESULT: 480 (80.0%)")
    c.showPage()
    c.save()

    doc = extractor.extract_document(multipage_path, expected_type=DocumentType.MARKSHEET)
    assert doc.status == "VALID"
    assert doc.page_count == 2
    assert "applicant_name" in doc.fields


# 9. Text positioned unusually on page (e.g. at bottom or rotated)
def test_unusual_positioning():
    extractor = DocumentExtractor()
    unusual_path = os.path.join(ADVERSARIAL_TMP, "unusual_position.pdf")
    c = canvas.Canvas(unusual_path, pagesize=letter)
    # Place text near bottom edge
    c.drawString(50, 40, "GOVERNMENT OF ODISHA")
    c.drawString(50, 25, "INCOME CERTIFICATE")
    c.drawString(200, 25, "Certificate No: INC-OD-9921")
    c.drawString(50, 10, "Applicant Name: Smruti Ranjan Nayak")
    c.save()

    doc = extractor.extract_document(unusual_path, expected_type=DocumentType.INCOME_CERT)
    assert doc.status == "VALID"
    assert "applicant_name" in doc.fields
    # Verify BBox was captured even at low Y
    assert doc.fields["applicant_name"].provenance.bounding_box is not None


# 10. Duplicate documents handling
def test_duplicate_documents():
    pipeline = AuditPipeline()
    # Create temp dir with two files having similar names
    dup_dir = os.path.join(ADVERSARIAL_TMP, "dup_packet")
    os.makedirs(dup_dir, exist_ok=True)
    c1 = canvas.Canvas(os.path.join(dup_dir, "marksheet.pdf"), pagesize=letter)
    c1.drawString(100, 700, "Candidate Name: Smruti Ranjan Nayak")
    c1.save()
    c2 = canvas.Canvas(os.path.join(dup_dir, "marksheet_copy.pdf"), pagesize=letter)
    c2.drawString(100, 700, "Candidate Name: Smruti Ranjan Nayak")
    c2.save()

    res, docs = pipeline.load_and_audit_packet(dup_dir)
    assert isinstance(res.readiness_score, int)


# 11. Incorrect document types (e.g. Electricity bill uploaded as Caste Cert)
def test_incorrect_document_type():
    extractor = DocumentExtractor()
    other_path = os.path.join(ADVERSARIAL_TMP, "electricity_bill.pdf")
    c = canvas.Canvas(other_path, pagesize=letter)
    c.drawString(100, 750, "TPCODL ELECTRICITY DISTRIBUTION COMPANY")
    c.drawString(100, 720, "CONSUMER BILL RECEIPT")
    c.drawString(100, 690, "Consumer Name: Ramesh Nayak")
    c.save()

    # Pass with expected_type = CASTE_CERT
    doc = extractor.extract_document(other_path, expected_type=DocumentType.CASTE_CERT)
    # The document shouldn't have caste_category extracted
    assert "caste_category" not in doc.fields


# 12. Extremely large files / high token volume
def test_large_token_volume():
    extractor = DocumentExtractor()
    large_path = os.path.join(ADVERSARIAL_TMP, "large_file.pdf")
    c = canvas.Canvas(large_path, pagesize=letter)
    c.drawString(50, 750, "GOVERNMENT OF ODISHA - INCOME CERTIFICATE")
    c.drawString(50, 730, "Applicant Name: Smruti Ranjan Nayak")
    c.drawString(50, 710, "Annual Family Income: 1,80,000")
    for i in range(150):
        c.drawString(50, 690 - (i % 30) * 15, f"Line {i}: Standard Gazette administrative regulation text payload paragraph")
        if i % 30 == 29:
            c.showPage()
    c.save()

    doc = extractor.extract_document(large_path, expected_type=DocumentType.INCOME_CERT)
    assert doc.status == "VALID"
    assert "applicant_name" in doc.fields
    assert doc.fields["applicant_name"].normalized_value == "SMRUTI RANJAN NAYAK"


# 13. Malformed income expressions
def test_malformed_income_expressions():
    assert normalize_income("NIL") is None
    assert normalize_income("Zero") is None
    assert normalize_income("Not Disclosed") is None
    assert normalize_income("₹ 0/-") == 0.0
    assert normalize_income("Ten Lakhs") is None  # Word representation without numbers
    assert normalize_income("₹ 1,80,000/- per annum") == 180000.0

    # Ensure validator handles None income safely with UNKNOWN
    validator = DocuReadyValidator()
    docs = {
        DocumentType.INCOME_CERT: ExtractedDocument(
            doc_type=DocumentType.INCOME_CERT,
            file_path="dummy.pdf",
            fields={"annual_income": ExtractedField(field_name="annual_income", raw_value="NOT_DISCLOSED", normalized_value=None)}
        )
    }
    res = validator.validate_packet("TEST_MALFORMED_INC", docs)
    unknown_inc = [f for f in res.findings if f.rule_id == "RULE-INC-03"]
    assert len(unknown_inc) == 1
    assert unknown_inc[0].status == Status.REVIEW
