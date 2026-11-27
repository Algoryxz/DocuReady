"""
Unit tests for PyMuPDF document extraction and provenance tracking.
"""

import io
import os
from pathlib import Path
from unittest.mock import patch
import pymupdf
from PIL import Image
from docuready.domain.models import DocumentType, EvidenceProvenance, ExtractionMethod
from docuready.ingest.extractor import DocumentExtractor, get_slot_ocr_langs
from docuready.ingest.tesseract_discovery import check_ocr_language_availability, normalize_ocr_langs
from docuready.pipeline import AuditPipeline
from docuready.rules.loader import load_pack

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


def _make_blank_raster_pdf(tmp_path: Path, name: str = "scan.pdf") -> Path:
    img = Image.new("RGB", (400, 200), color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    pdf_path = tmp_path / name
    doc = pymupdf.open()
    page = doc.new_page(width=400, height=200)
    page.insert_image(page.rect, stream=buf.getvalue())
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


def _mock_ocr_payload():
    return {
        "text": [
            "INCOME", "CERTIFICATE", "Applicant", "Name:", "Pravasini", "Sahoo",
            "Annual", "Family", "Income:", "180000"
        ],
        "conf": [92, 93, 91, 90, 94, 95, 90, 91, 92, 93],
        "left": [10, 80, 10, 90, 160, 230, 10, 70, 130, 200],
        "top": [10, 10, 40, 40, 40, 40, 70, 70, 70, 70],
        "width": [50, 80, 70, 50, 60, 60, 50, 50, 60, 60],
        "height": [15, 15, 15, 15, 15, 15, 15, 15, 15, 15],
    }


def test_ocr_language_routing_eng_ori_and_eng_hin(tmp_path: Path):
    """Verify Tesseract receives explicit lang='eng+ori' and 'eng+hin' and records ocr_lang provenance."""
    pdf_path = _make_blank_raster_pdf(tmp_path, "income_scan.pdf")
    ext = DocumentExtractor()

    for langs, expected_lang_str in [(["eng", "ori"], "eng+ori"), (["eng", "hin"], "eng+hin")]:
        with patch("docuready.ingest.extractor.check_ocr_language_availability", return_value={
            "available": True, "binary_available": True, "requested_lang": expected_lang_str,
            "requested_langs": langs, "installed_langs": langs, "missing_langs": [], "error": None,
        }):
            with patch("pytesseract.image_to_osd", side_effect=RuntimeError("no osd")):
                with patch("pytesseract.image_to_data", return_value=_mock_ocr_payload()) as mock_tess:
                    doc = ext.extract_document(str(pdf_path), expected_type=DocumentType.INCOME_CERT, ocr_langs=langs)

        assert mock_tess.call_count == 1
        assert mock_tess.call_args.kwargs["lang"] == expected_lang_str
        assert doc.status == "VALID"
        assert doc.extraction_method == ExtractionMethod.LOCAL_OCR.value
        assert doc.ocr_lang == expected_lang_str
        assert "applicant_name" in doc.fields
        prov = doc.fields["applicant_name"].provenance
        assert prov is not None
        assert prov.ocr_lang == expected_lang_str
        assert prov.extraction_method == ExtractionMethod.LOCAL_OCR.value
        assert prov.model_dump(mode="json")["ocr_lang"] == expected_lang_str


def test_ocr_legacy_english_default_and_native_vector_provenance(tmp_path: Path):
    """Verify default OCR uses lang='eng' and native vector omits ocr_lang."""
    pdf_path = _make_blank_raster_pdf(tmp_path, "legacy_scan.pdf")
    ext = DocumentExtractor()

    with patch("pytesseract.image_to_osd", side_effect=RuntimeError("no osd")):
        with patch("pytesseract.image_to_data", return_value=_mock_ocr_payload()) as mock_tess:
            doc_ocr = ext.extract_document(str(pdf_path), expected_type=DocumentType.INCOME_CERT)

    assert mock_tess.call_args.kwargs["lang"] == "eng"
    assert doc_ocr.ocr_lang == "eng"
    assert doc_ocr.fields["applicant_name"].provenance.ocr_lang == "eng"

    # Native vector extraction must not invent ocr_lang
    vec_doc = ext.extract_document(get_doc_path("pkt_01_clean/income_cert.pdf"), expected_type=DocumentType.INCOME_CERT)
    assert vec_doc.extraction_method == ExtractionMethod.NATIVE_VECTOR.value
    assert vec_doc.ocr_lang is None
    vec_prov = vec_doc.fields["applicant_name"].provenance
    assert vec_prov is not None
    assert vec_prov.ocr_lang is None
    assert "ocr_lang" not in vec_prov.model_dump(mode="json")


def test_missing_traineddata_fails_without_silent_english_fallback(tmp_path: Path):
    """Missing requested traineddata must return UNREADABLE without downgrading to English."""
    pdf_path = _make_blank_raster_pdf(tmp_path, "missing_lang.pdf")
    ext = DocumentExtractor()

    with patch("docuready.ingest.tesseract_discovery.get_ocr_runtime_info", return_value={
        "available": True, "version": "5.0.0", "binary_path": "tesseract", "languages": ["eng"],
        "source": "system_prerequisite", "is_bundled": False, "error": None,
    }):
        avail = check_ocr_language_availability(["eng", "ori"])
        assert avail["available"] is False
        assert avail["missing_langs"] == ["ori"]
        assert "ori" in avail["error"]

        with patch("pytesseract.image_to_data") as mock_tess:
            doc = ext.extract_document(str(pdf_path), expected_type=DocumentType.INCOME_CERT, ocr_langs=["eng", "ori"])

    assert mock_tess.call_count == 0
    assert doc.status == "UNREADABLE"
    assert doc.ocr_lang == "eng+ori"
    assert doc.classification_details is not None
    assert "ori" in doc.classification_details["ocr_error"]


def test_pack_slot_ocr_langs_propagation_via_pipeline(tmp_path: Path):
    """Verify AuditPipeline propagates pack slot ocr_langs (e.g. odisha.subhadra) to DocumentExtractor."""
    pack, _ = load_pack(_REPO_ROOT / "packs" / "odisha.subhadra")
    assert get_slot_ocr_langs(pack, DocumentType.AADHAAR) == ["eng", "ori"]
    assert get_slot_ocr_langs(pack, DocumentType.BANK_PASSBOOK) == ["eng"]
    assert normalize_ocr_langs(get_slot_ocr_langs(pack, DocumentType.AADHAAR)) == "eng+ori"

    _make_blank_raster_pdf(tmp_path, "income_cert.pdf")
    pipeline = AuditPipeline(pack=pack)
    with patch.object(pipeline.extractor, "extract_document", wraps=pipeline.extractor.extract_document) as spy_ext:
        with patch("docuready.ingest.extractor.check_ocr_language_availability", return_value={
            "available": True, "binary_available": True, "requested_lang": "eng+ori",
            "requested_langs": ["eng", "ori"], "installed_langs": ["eng", "ori"], "missing_langs": [], "error": None,
        }):
            with patch("pytesseract.image_to_osd", side_effect=RuntimeError("no osd")):
                with patch("pytesseract.image_to_data", return_value=_mock_ocr_payload()):
                    pipeline.load_and_audit_packet(str(tmp_path), packet_id="PKT_SLOT_LANG")

    assert spy_ext.call_count == 1
    assert spy_ext.call_args.kwargs["ocr_langs"] == ["eng", "ori"]


def test_subhadra_slots_and_replacement_preserve_ocr_langs(tmp_path: Path):
    """Verify SUBHADRA Aadhaar=eng+ori, bank_passbook=eng, and replace_document_and_reaudit preserves slot config."""
    pack, _ = load_pack(_REPO_ROOT / "packs" / "odisha.subhadra")
    aadhaar_pdf = _make_blank_raster_pdf(tmp_path, "aadhaar.pdf")
    passbook_pdf = _make_blank_raster_pdf(tmp_path, "bank_passbook.pdf")

    pipeline = AuditPipeline(pack=pack)
    with patch("docuready.ingest.extractor.check_ocr_language_availability", return_value={
        "available": True, "binary_available": True, "requested_lang": "eng+ori",
        "requested_langs": ["eng", "ori"], "installed_langs": ["eng", "ori"], "missing_langs": [], "error": None,
    }):
        with patch("pytesseract.image_to_osd", side_effect=RuntimeError("no osd")):
            with patch("pytesseract.image_to_data", return_value=_mock_ocr_payload()) as mock_tess:
                _, docs = pipeline.load_and_audit_packet(str(tmp_path), packet_id="PKT_SLOTS")
                called_langs = sorted(call.kwargs["lang"] for call in mock_tess.call_args_list)
                assert called_langs == ["eng", "eng+ori"]

                # Replacement re-audit must also preserve Aadhaar -> eng+ori
                mock_tess.reset_mock()
                _, replaced_docs = pipeline.replace_document_and_reaudit(
                    docs, str(aadhaar_pdf), DocumentType.AADHAAR, packet_id="PKT_REPL"
                )
                assert mock_tess.call_count == 1
                assert mock_tess.call_args.kwargs["lang"] == "eng+ori"
                assert replaced_docs[DocumentType.AADHAAR].ocr_lang == "eng+ori"
