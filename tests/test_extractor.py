"""
Unit tests for PyMuPDF document extraction and provenance tracking.
"""

import os
from pathlib import Path
from docuready.domain.models import DocumentType
from docuready.ingest.extractor import DocumentExtractor

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SYNTHETIC_DIR = _REPO_ROOT / "synthetic_data" if (_REPO_ROOT / "synthetic_data").is_dir() else Path.cwd() / "synthetic_data"


def get_doc_path(relative_subpath):
    candidates = [
        _SYNTHETIC_DIR / relative_subpath,
        Path.cwd() / "synthetic_data" / relative_subpath,
    ]
    for c in candidates:
        if c.is_file():
            return str(c)
    return str(candidates[0])


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
