"""Focused integrity, rasterization, and ground-truth tests for T4.2 Indic OCR Corpus v1.0.0."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pymupdf
from PIL import Image

from docuready.normalize.normalizer import (
    normalize_cert_number,
    normalize_income,
    normalize_indic_digits,
    parse_and_normalize_date,
)

_CORPUS_DIR = Path(__file__).resolve().parent.parent / "eval" / "t4_2_indic_ocr" / "v1.0.0"

_GEN_SPEC = importlib.util.spec_from_file_location(
    "t4_2_corpus_generator",
    str(_CORPUS_DIR / "generation" / "generator.py"),
)
_gen = importlib.util.module_from_spec(_GEN_SPEC)
assert _GEN_SPEC is not None and _GEN_SPEC.loader is not None
_GEN_SPEC.loader.exec_module(_gen)


def test_t4_2_manifest_and_hashes_valid() -> None:
    manifest = json.loads((_CORPUS_DIR / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["corpus_version"] == "1.0.0"
    assert manifest["evaluation_role"] == "held_out"
    assert manifest["training_eligible"] is False
    assert manifest["extraction_mode"] == "LOCAL_OCR"
    assert manifest["native_text_layer"] is False
    assert manifest["sample_counts"] == {"ori": 12, "hin": 12, "total": 24}

    res = _gen.verify_hashes(_CORPUS_DIR)
    assert res["verified"] is True, f"Hash mismatches: {res['mismatches']}"
    assert res["files_checked"] == 27


def test_t4_2_no_duplicate_or_unreferenced_images() -> None:
    manifest = json.loads((_CORPUS_DIR / "manifest.json").read_text(encoding="utf-8"))
    doc_ids = [d["document_id"] for d in manifest["documents"]]
    doc_hashes = [d["sha256"] for d in manifest["documents"]]
    assert len(doc_ids) == len(set(doc_ids)) == 24
    assert len(doc_hashes) == len(set(doc_hashes)) == 24

    actual_pngs = {
        p.relative_to(_CORPUS_DIR).as_posix()
        for p in (_CORPUS_DIR / "documents").rglob("*.png")
    }
    manifest_paths = {d["path"] for d in manifest["documents"]}
    assert actual_pngs == manifest_paths


def test_t4_2_images_are_pure_raster_zero_native_text() -> None:
    manifest = json.loads((_CORPUS_DIR / "manifest.json").read_text(encoding="utf-8"))
    for doc in manifest["documents"]:
        img_path = _CORPUS_DIR / doc["path"]
        assert img_path.is_file()
        with Image.open(img_path) as im:
            assert im.format == "PNG"
            assert im.mode == "RGB"
            assert im.size == (doc["dimensions_px"]["width"], doc["dimensions_px"]["height"])
            assert im.size[0] > 0 and im.size[1] > 0

        pdf_view = pymupdf.open(str(img_path))
        native_text = "".join(p.get_text() for p in pdf_view)
        pdf_view.close()
        assert native_text.strip() == ""


def test_t4_2_ground_truth_raw_and_normalized_consistency() -> None:
    raw_gt = json.loads((_CORPUS_DIR / "ground_truth" / "raw.json").read_text(encoding="utf-8"))
    norm_gt = json.loads((_CORPUS_DIR / "ground_truth" / "normalized.json").read_text(encoding="utf-8"))
    assert raw_gt["record_count"] == 96
    assert norm_gt["record_count"] == 96

    indic_preserved = 0
    for r_rec, n_rec in zip(raw_gt["records"], norm_gt["records"]):
        assert (r_rec["document_id"], r_rec["field_name"]) == (n_rec["document_id"], n_rec["field_name"])
        assert r_rec["raw_value"] == n_rec["raw_value"]
        raw_val = r_rec["raw_value"]
        if normalize_indic_digits(raw_val) != raw_val:
            indic_preserved += 1

        fname = r_rec["field_name"]
        nv = n_rec["normalized_value"]
        if fname in ("dob", "issue_date"):
            dt, status, amb = parse_and_normalize_date(raw_val)
            assert status == "VALID" and dt is not None
            assert nv["iso_date"] == dt.isoformat()
            assert nv["is_ambiguous"] is amb
        elif fname == "annual_income":
            assert nv["amount_inr"] == normalize_income(raw_val)
        elif fname == "certificate_number":
            assert nv["canonical_cert"] == normalize_cert_number(raw_val)

    assert indic_preserved == 80


def test_t4_2_validation_reports_are_pass() -> None:
    for report_name in ("rendering_validation.json", "integrity_validation.json", "ground_truth_validation.json"):
        data = json.loads((_CORPUS_DIR / "reports" / report_name).read_text(encoding="utf-8"))
        assert data["status"] == "PASS", f"{report_name} failed: {data}"
