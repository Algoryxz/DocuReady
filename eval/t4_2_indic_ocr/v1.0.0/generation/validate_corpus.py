"""Validation runner for DocuReady T4.2 Indic OCR Evaluation Corpus (v1.0.0).

Executes:
1. Rendering & rasterization validation (image readability, dimensions, zero native text layer,
   font glyph coverage, and live LOCAL_OCR smoke via DocumentExtractor when Tesseract is available).
2. Corpus integrity & determinism validation (manifest completeness, zero duplicate IDs/images,
   zero unreferenced files, SHA-256 verification, and deterministic regeneration into a temp dir).
3. Ground-truth consistency validation (raw Unicode preservation, canonical normalizer parity,
   provenance traceability).
"""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List

import pymupdf
from PIL import Image

_CORPUS_DIR = Path(__file__).resolve().parents[1]
_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from docuready.domain.models import DocumentType  # noqa: E402
from docuready.ingest.extractor import DocumentExtractor  # noqa: E402
from docuready.ingest.tesseract_discovery import get_ocr_runtime_info  # noqa: E402
from docuready.normalize.normalizer import (  # noqa: E402
    normalize_cert_number,
    normalize_income,
    normalize_indic_digits,
    parse_and_normalize_date,
)

# Load generator module from sibling file (directory name 'v1.0.0' contains dots)
_GEN_SPEC = importlib.util.spec_from_file_location(
    "t4_2_generator", str(_CORPUS_DIR / "generation" / "generator.py")
)
_gen = importlib.util.module_from_spec(_GEN_SPEC)
assert _GEN_SPEC is not None and _GEN_SPEC.loader is not None
_GEN_SPEC.loader.exec_module(_gen)


def run_validations(corpus_dir: Path = _CORPUS_DIR) -> Dict[str, Any]:
    manifest = json.loads((corpus_dir / "manifest.json").read_text(encoding="utf-8"))
    hashes_data = json.loads((corpus_dir / "document_hashes.json").read_text(encoding="utf-8"))
    font_prov = json.loads((corpus_dir / "generation" / "font_provenance.json").read_text(encoding="utf-8"))
    raw_gt = json.loads((corpus_dir / "ground_truth" / "raw.json").read_text(encoding="utf-8"))
    norm_gt = json.loads((corpus_dir / "ground_truth" / "normalized.json").read_text(encoding="utf-8"))

    # 1. Rendering & rasterization validation
    render_errors: List[str] = []
    dims_summary: List[Dict[str, Any]] = []
    for doc in manifest["documents"]:
        p = corpus_dir / doc["path"]
        if not p.is_file():
            render_errors.append(f"Missing image: {doc['path']}")
            continue
        with Image.open(p) as im:
            im.verify()
        with Image.open(p) as im2:
            w, h = im2.size
            mode = im2.mode
            fmt = im2.format
        if (w, h) != (doc["dimensions_px"]["width"], doc["dimensions_px"]["height"]):
            render_errors.append(f"Dimension mismatch for {doc['document_id']}: {(w, h)}")
        if fmt != "PNG" or mode != "RGB":
            render_errors.append(f"Format/mode mismatch for {doc['document_id']}: {fmt}/{mode}")

        # Verify zero native vector text layer when opened via PyMuPDF
        pdf_view = pymupdf.open(str(p))
        native_txt = "".join(page.get_text() for page in pdf_view)
        pdf_view.close()
        if native_txt.strip():
            render_errors.append(f"Unexpected native text in {doc['document_id']}")

        dims_summary.append({"document_id": doc["document_id"], "width": w, "height": h, "format": fmt, "mode": mode})

    glyph_ok = all(
        all(v is True for v in fmeta["glyph_coverage_verified"].values())
        for fmeta in font_prov["fonts"].values()
    )
    if not glyph_ok:
        render_errors.append("Font glyph coverage verification failed")

    # Live LOCAL_OCR smoke check via DocumentExtractor (paired eng vs eng+ori / eng+hin)
    runtime_info = get_ocr_runtime_info()
    ocr_smoke: Dict[str, Any] = {"ocr_runtime": runtime_info, "paired_smoke": []}
    if runtime_info.get("available"):
        extractor = DocumentExtractor()
        for doc_rel, langs in [
            ("documents/odia/T42_ORI_001.png", ("eng", "eng+ori")),
            ("documents/hindi/T42_HIN_001.png", ("eng", "eng+hin")),
        ]:
            target = str(corpus_dir / doc_rel)
            for lang in langs:
                res = extractor.extract_document(target, expected_type=DocumentType.INCOME_CERT, ocr_langs=lang)
                ocr_smoke["paired_smoke"].append({
                    "path": doc_rel,
                    "ocr_lang": lang,
                    "extraction_method": res.extraction_method,
                    "status": res.status,
                    "mean_ocr_confidence": res.mean_ocr_confidence,
                    "raw_text_length": len((res.raw_text or "").strip()),
                })

    rendering_report = {
        "corpus_version": manifest["corpus_version"],
        "status": "PASS" if not render_errors else "FAIL",
        "documents_checked": len(manifest["documents"]),
        "all_pure_raster_zero_native_text": len(render_errors) == 0,
        "font_glyph_coverage_verified": glyph_ok,
        "errors": render_errors,
        "ocr_smoke": ocr_smoke,
    }
    (corpus_dir / "reports" / "rendering_validation.json").write_text(
        json.dumps(rendering_report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    # 2. Integrity & determinism validation
    hash_res = _gen.verify_hashes(corpus_dir)
    doc_ids = [d["document_id"] for d in manifest["documents"]]
    img_hashes = [d["sha256"] for d in manifest["documents"]]
    actual_pngs = {
        p.relative_to(corpus_dir).as_posix()
        for p in (corpus_dir / "documents").rglob("*.png")
    }
    manifest_paths = {d["path"] for d in manifest["documents"]}
    unreferenced = sorted(actual_pngs - manifest_paths)
    missing_from_disk = sorted(manifest_paths - actual_pngs)

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        _gen.generate_corpus(tmp_path)
        tmp_hashes = json.loads((tmp_path / "document_hashes.json").read_text(encoding="utf-8"))
        determinism_mismatches = [
            rel for rel, info in hashes_data["documents"].items()
            if tmp_hashes["documents"].get(rel, {}).get("sha256") != info["sha256"]
        ]

    integrity_ok = (
        hash_res["verified"]
        and len(doc_ids) == len(set(doc_ids))
        and len(img_hashes) == len(set(img_hashes))
        and not unreferenced
        and not missing_from_disk
        and not determinism_mismatches
    )
    integrity_report = {
        "corpus_version": manifest["corpus_version"],
        "status": "PASS" if integrity_ok else "FAIL",
        "hash_verification": hash_res,
        "unique_document_ids": len(doc_ids) == len(set(doc_ids)),
        "unique_document_images": len(img_hashes) == len(set(img_hashes)),
        "unreferenced_files": unreferenced,
        "missing_files": missing_from_disk,
        "deterministic_regeneration_verified": len(determinism_mismatches) == 0,
        "determinism_mismatches": determinism_mismatches,
    }
    (corpus_dir / "reports" / "integrity_validation.json").write_text(
        json.dumps(integrity_report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    # 3. Ground-truth validation
    gt_errors: List[str] = []
    if len(raw_gt["records"]) != 96 or len(norm_gt["records"]) != 96:
        gt_errors.append(f"Expected 96 field records, got raw={len(raw_gt['records'])}, norm={len(norm_gt['records'])}")

    indic_raw_preserved = 0
    for r_rec, n_rec in zip(raw_gt["records"], norm_gt["records"]):
        if (r_rec["document_id"], r_rec["field_name"]) != (n_rec["document_id"], n_rec["field_name"]):
            gt_errors.append(f"Record alignment mismatch: {r_rec['document_id']} {r_rec['field_name']}")
            continue
        if r_rec["raw_value"] != n_rec["raw_value"]:
            gt_errors.append(f"Raw value mismatch for {r_rec['document_id']} {r_rec['field_name']}")

        raw_val = r_rec["raw_value"]
        if normalize_indic_digits(raw_val) != raw_val:
            indic_raw_preserved += 1

        fname = r_rec["field_name"]
        nv = n_rec["normalized_value"]
        if fname in ("dob", "issue_date"):
            dt, st, amb = parse_and_normalize_date(raw_val)
            if st != "VALID" or dt is None or nv["iso_date"] != dt.isoformat() or nv["is_ambiguous"] != amb:
                gt_errors.append(f"Date contract mismatch: {r_rec['document_id']} {fname}")
        elif fname == "annual_income":
            amt = normalize_income(raw_val)
            if amt is None or nv["amount_inr"] != amt:
                gt_errors.append(f"Income contract mismatch: {r_rec['document_id']} {fname}")
        elif fname == "certificate_number":
            cn = normalize_cert_number(raw_val)
            if not cn or nv["canonical_cert"] != cn:
                gt_errors.append(f"Cert contract mismatch: {r_rec['document_id']} {fname}")

    gt_report = {
        "corpus_version": manifest["corpus_version"],
        "status": "PASS" if not gt_errors else "FAIL",
        "record_count": len(norm_gt["records"]),
        "indic_digit_raw_records_preserved": indic_raw_preserved,
        "errors": gt_errors,
    }
    (corpus_dir / "reports" / "ground_truth_validation.json").write_text(
        json.dumps(gt_report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    return {
        "rendering": rendering_report["status"],
        "integrity": integrity_report["status"],
        "ground_truth": gt_report["status"],
        "ocr_smoke_count": len(ocr_smoke["paired_smoke"]),
    }


if __name__ == "__main__":
    summary = run_validations()
    print(json.dumps(summary, indent=2))
    if any(v != "PASS" for k, v in summary.items() if k != "ocr_smoke_count"):
        raise SystemExit(1)
