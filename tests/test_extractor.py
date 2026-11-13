"""
Unit tests for PyMuPDF document extraction and provenance tracking.
"""

import os
from src.models import DocumentType
from src.extractor import DocumentExtractor


def get_doc_path(relative_subpath):
    candidates = [
        os.path.join("synthetic_data", relative_subpath),
        os.path.join("docuready-mvp/synthetic_data", relative_subpath),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return candidates[0]


def test_extractor_income_cert():
    ext = DocumentExtractor()
    doc_path = get_doc_path("pkt_01_clean/income_cert.pdf")
    assert os.path.exists(doc_path)

    doc = ext.extract_document(doc_path, expected_type=DocumentType.INCOME_CERT)
    assert doc.doc_type == DocumentType.INCOME_CERT
    assert doc.status == "VALID"
    assert "applicant_name" in doc.fields
    assert doc.fields["applicant_name"].normalized_value == "SMRUTI RANJAN NAYAK"
    assert doc.fields["annual_income"].normalized_value == 180000.0

    # Provenance verification
    prov = doc.fields["applicant_name"].provenance
    assert prov is not None
    assert prov.page_number == 1
    assert prov.bounding_box is not None
    assert len(prov.bounding_box) == 4


def test_extractor_unreadable_file():
    ext = DocumentExtractor()
    doc_path = get_doc_path("pkt_07_unreadable_doc/income_cert.pdf")
    assert os.path.exists(doc_path)

    doc = ext.extract_document(doc_path, expected_type=DocumentType.INCOME_CERT)
    assert doc.status == "UNREADABLE"


def test_extractor_missing_file():
    ext = DocumentExtractor()
    doc = ext.extract_document("non_existent_file.pdf", expected_type=DocumentType.MARKSHEET)
    assert doc.status == "MISSING"
