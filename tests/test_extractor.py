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


def _make_blank_image(tmp_path: Path, name: str, fmt: str = "PNG") -> Path:
    img = Image.new("RGB", (400, 200), color="white")
    out_path = tmp_path / name
    img.save(str(out_path), format=fmt)
    return out_path


def test_image_extensions_resolve_pack_ocr_slots(tmp_path: Path):
    """Verify aadhaar.pdf/.png/.jpg receive eng+ori, bank_passbook.png receives eng, and replacement preserves config."""
    pack, _ = load_pack(_REPO_ROOT / "packs" / "odisha.subhadra")
    _make_blank_raster_pdf(tmp_path, "aadhaar.pdf")
    aadhaar_png = _make_blank_image(tmp_path, "aadhaar.png", fmt="PNG")
    _make_blank_image(tmp_path, "aadhaar.jpg", fmt="JPEG")
    _make_blank_image(tmp_path, "bank_passbook.png", fmt="PNG")

    # Test each file individually in its own sub-folder so identical stems don't overwrite in dict
    expected_cases = [
        ("case_pdf", "aadhaar.pdf", "eng+ori", DocumentType.AADHAAR),
        ("case_png", "aadhaar.png", "eng+ori", DocumentType.AADHAAR),
        ("case_jpg", "aadhaar.jpg", "eng+ori", DocumentType.AADHAAR),
        ("case_passbook_png", "bank_passbook.png", "eng", DocumentType.BANK_PASSBOOK),
    ]

    pipeline = AuditPipeline(pack=pack)
    for subdir_name, fname, expected_lang, expected_dt in expected_cases:
        sub = tmp_path / subdir_name
        sub.mkdir()
        src_file = tmp_path / fname
        (sub / fname).write_bytes(src_file.read_bytes())

        with patch("docuready.ingest.extractor.check_ocr_language_availability", return_value={
            "available": True, "binary_available": True, "requested_lang": expected_lang,
            "requested_langs": expected_lang.split("+"), "installed_langs": ["eng", "ori"],
            "missing_langs": [], "error": None,
        }):
            with patch("pytesseract.image_to_osd", side_effect=RuntimeError("no osd")):
                with patch("pytesseract.image_to_data", return_value=_mock_ocr_payload()) as mock_tess:
                    _, docs = pipeline.load_and_audit_packet(str(sub), packet_id=f"PKT_{subdir_name}")
                    assert mock_tess.call_count == 1
                    assert mock_tess.call_args.kwargs["lang"] == expected_lang
                    assert docs[expected_dt].ocr_lang == expected_lang

    # Replacement ingestion with image file also preserves eng+ori
    with patch("docuready.ingest.extractor.check_ocr_language_availability", return_value={
        "available": True, "binary_available": True, "requested_lang": "eng+ori",
        "requested_langs": ["eng", "ori"], "installed_langs": ["eng", "ori"], "missing_langs": [], "error": None,
    }):
        with patch("pytesseract.image_to_osd", side_effect=RuntimeError("no osd")):
            with patch("pytesseract.image_to_data", return_value=_mock_ocr_payload()) as mock_tess:
                _, repl_docs = pipeline.replace_document_and_reaudit(
                    {}, str(aadhaar_png), DocumentType.AADHAAR, packet_id="PKT_REPL_PNG"
                )
                assert mock_tess.call_count == 1
                assert mock_tess.call_args.kwargs["lang"] == "eng+ori"
                assert repl_docs[DocumentType.AADHAAR].ocr_lang == "eng+ori"


def test_uncached_tesseract_language_discovery_detects_newly_installed_ori():
    """Simulate ori traineddata installed in-process after initial eng-only check."""
    from types import SimpleNamespace

    list_outputs = [
        SimpleNamespace(returncode=0, stdout="List of available languages in \"/usr/share/tesseract-ocr/5/tessdata/\" (2):\neng\nosd\n"),
        SimpleNamespace(returncode=0, stdout="List of available languages in \"/usr/share/tesseract-ocr/5/tessdata/\" (3):\neng\nori\nosd\n"),
        SimpleNamespace(returncode=0, stdout="List of available languages in \"/usr/share/tesseract-ocr/5/tessdata/\" (3):\neng\nori\nosd\n"),
    ]

    with patch("docuready.ingest.tesseract_discovery.find_tesseract_binary_with_source", return_value=(Path("/usr/bin/tesseract"), "system_prerequisite")):
        with patch("pytesseract.get_tesseract_version", return_value="5.3.0"):
            with patch("docuready.ingest.tesseract_discovery.subprocess.run", side_effect=list_outputs) as mock_run:
                # 1. Initial runtime exposes only eng
                avail_before = check_ocr_language_availability(["eng", "ori"])
                assert avail_before["available"] is False
                assert avail_before["missing_langs"] == ["ori"]

                # 2. ori is installed afterward -> subsequent check detects ori without process restart
                avail_after = check_ocr_language_availability(["eng", "ori"])
                assert avail_after["available"] is True
                assert avail_after["missing_langs"] == []
                assert "ori" in avail_after["installed_langs"]

                # 3. Actually missing language (hin) is still rejected
                avail_hin = check_ocr_language_availability(["eng", "hin"])
                assert avail_hin["available"] is False
                assert avail_hin["missing_langs"] == ["hin"]

                assert mock_run.call_count == 3


def test_missing_language_diagnostics_distinct_from_unreadable_scan_in_reports(tmp_path: Path):
    """Missing ori produces actionable installation guidance in public reports; unreadable scans keep re-scan guidance."""
    from docuready.report.exporter import export_audit_report_json, generate_readiness_summary_markdown
    import json

    pack, _ = load_pack(_REPO_ROOT / "packs" / "odisha.subhadra")
    sub = tmp_path / "missing_ori_pkt"
    sub.mkdir()
    _make_blank_raster_pdf(sub, "aadhaar.pdf")

    pipeline = AuditPipeline(pack=pack)
    with patch("docuready.ingest.tesseract_discovery.get_ocr_runtime_info", return_value={
        "available": True, "version": "5.3.0", "binary_path": "tesseract", "languages": ["eng"],
        "source": "system_prerequisite", "is_bundled": False, "error": None,
    }):
        result_missing, _ = pipeline.load_and_audit_packet(str(sub), packet_id="PKT_MISSING_ORI")

    md_missing = generate_readiness_summary_markdown(result_missing, redact=True)
    json_path = tmp_path / "missing_ori.json"
    export_audit_report_json(result_missing, str(json_path), redact=True)
    payload_missing = json.loads(json_path.read_text(encoding="utf-8"))

    assert "ori" in md_missing
    assert "install" in md_missing.lower()
    assert "re-scan" not in md_missing.lower()
    missing_findings = [f for f in payload_missing["findings"] if f["rule_id"] == "RULE-DOC-02"]
    assert len(missing_findings) == 1
    assert missing_findings[0]["field"] == "OCR_LANGUAGE_PACK"
    assert "ori" in missing_findings[0]["message"]
    assert "install" in missing_findings[0]["remediation"].lower()

    # Genuinely unreadable scan retains SCAN_QUALITY and re-scan guidance
    unreadable_pkt = tmp_path / "unreadable_pkt"
    unreadable_pkt.mkdir()
    (unreadable_pkt / "income_cert.pdf").write_bytes(
        Path(get_doc_path("pkt_07_unreadable_doc/income_cert.pdf")).read_bytes()
    )
    plain_pipeline = AuditPipeline()
    result_unreadable, _ = plain_pipeline.load_and_audit_packet(str(unreadable_pkt), packet_id="PKT_UNREADABLE")
    md_unreadable = generate_readiness_summary_markdown(result_unreadable, redact=True)

    assert "re-scan" in md_unreadable.lower()
    assert "traineddata" not in md_unreadable.lower()
    unreadable_findings = [f for f in result_unreadable.to_public_dict()["findings"] if f["rule_id"] == "RULE-DOC-02"]
    assert len(unreadable_findings) == 1
    assert unreadable_findings[0]["field"] == "SCAN_QUALITY"


def test_tessdata_isolation_and_no_false_english_fallback(tmp_path: Path, monkeypatch):
    """Verify authoritative empty --list-langs, TESSDATA_PREFIX isolation, and no false eng fallback."""
    from types import SimpleNamespace
    from docuready.ingest.tesseract_discovery import get_ocr_runtime_info

    # 1. Authoritative empty --list-langs result must not fall back to filesystem or invent 'eng'
    fake_bin_dir = tmp_path / "bin"
    fake_bin_dir.mkdir()
    fake_bin = fake_bin_dir / "tesseract"
    fake_bin.write_text("", encoding="utf-8")
    (fake_bin_dir / "tessdata").mkdir()
    (fake_bin_dir / "tessdata" / "eng.traineddata").write_text("dummy", encoding="utf-8")

    empty_tessdata = tmp_path / "empty_tessdata"
    empty_tessdata.mkdir()
    monkeypatch.setenv("TESSDATA_PREFIX", str(empty_tessdata))

    empty_list_res = SimpleNamespace(
        returncode=0,
        stdout="List of available languages in \"empty\" (0):\n",
    )
    with patch("docuready.ingest.tesseract_discovery.find_tesseract_binary_with_source", return_value=(fake_bin, "system_prerequisite")):
        with patch("pytesseract.get_tesseract_version", return_value="5.3.0"):
            with patch("docuready.ingest.tesseract_discovery.subprocess.run", return_value=empty_list_res):
                info = get_ocr_runtime_info()
                assert info["available"] is True
                assert info["languages"] == []
                avail_eng = check_ocr_language_availability("eng")
                assert avail_eng["available"] is False
                assert avail_eng["binary_available"] is True
                assert avail_eng["missing_langs"] == ["eng"]

    # 2. When command discovery fails with TESSDATA_PREFIX set to empty dir, do NOT scan unrelated dirs
    with patch("docuready.ingest.tesseract_discovery.find_tesseract_binary_with_source", return_value=(fake_bin, "system_prerequisite")):
        with patch("pytesseract.get_tesseract_version", return_value="5.3.0"):
            with patch("docuready.ingest.tesseract_discovery.subprocess.run", side_effect=OSError("exec failed")):
                info_override_empty = get_ocr_runtime_info()
                assert info_override_empty["available"] is True
                assert info_override_empty["languages"] == []
                assert check_ocr_language_availability("eng")["available"] is False

    # 3. When command discovery fails with TESSDATA_PREFIX pointing to populated dir, scan ONLY that dir
    populated_override = tmp_path / "override_tessdata"
    populated_override.mkdir()
    (populated_override / "ori.traineddata").write_text("dummy", encoding="utf-8")
    monkeypatch.setenv("TESSDATA_PREFIX", str(populated_override))

    with patch("docuready.ingest.tesseract_discovery.find_tesseract_binary_with_source", return_value=(fake_bin, "system_prerequisite")):
        with patch("pytesseract.get_tesseract_version", return_value="5.3.0"):
            with patch("docuready.ingest.tesseract_discovery.subprocess.run", side_effect=OSError("exec failed")):
                info_override_ori = get_ocr_runtime_info()
                assert info_override_ori["languages"] == ["ori"]
                assert check_ocr_language_availability("eng")["available"] is False
                assert check_ocr_language_availability("ori")["available"] is True

    # 4. When TESSDATA_PREFIX is unset and command discovery fails, default location discovery works
    monkeypatch.delenv("TESSDATA_PREFIX", raising=False)
    with patch("docuready.ingest.tesseract_discovery.find_tesseract_binary_with_source", return_value=(fake_bin, "system_prerequisite")):
        with patch("pytesseract.get_tesseract_version", return_value="5.3.0"):
            with patch("docuready.ingest.tesseract_discovery.subprocess.run", side_effect=OSError("exec failed")):
                info_default = get_ocr_runtime_info()
                assert info_default["languages"] == ["eng"]
                assert check_ocr_language_availability("eng")["available"] is True
