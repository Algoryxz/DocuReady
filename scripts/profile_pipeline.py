"""
Performance Profiling Script for DocuReady Loop 3 Pipeline
Measures execution time breakdown across rendering, OSD, OCR, spatial clustering, calibration,
validation, and decision safety firewall.
"""

import os
import io
import time
import json
from typing import Dict, Any, List
import PIL.Image
import pymupdf
import pytesseract

from docuready.domain.models import DocumentType, ExtractionMethod
from docuready.ingest.extractor import DocumentExtractor, PageOCRData, _find_field_in_ocr_page
from docuready.evidence.calibrator import ConfidenceCalibrator
from docuready.rules.validator import DocuReadyValidator
from docuready.outcome.safety_layer import DecisionSafetyLayer


def profile_pipeline():
    sample_vector = "synthetic_data/pkt_loop3_demo/application_form.pdf"
    sample_scan = "synthetic_data/pkt_loop3_demo/caste_cert.pdf"

    print("==================================================")
    print("DOCUREADY PIPELINE PERFORMANCE PROFILING")
    print("==================================================")

    # 1. Native Vector Profile
    doc_v = pymupdf.open(sample_vector)
    t0 = time.perf_counter()
    p_v = doc_v[0]
    txt_v = p_v.get_text()
    t_mupdf_text = (time.perf_counter() - t0) * 1000.0

    t0 = time.perf_counter()
    cal = ConfidenceCalibrator()
    cal_res = cal.calibrate("applicant_name", "Smruti Ranjan Nayak", ExtractionMethod.NATIVE_VECTOR)
    t_cal_vector = (time.perf_counter() - t0) * 1000.0
    doc_v.close()

    total_vector_ms = t_mupdf_text + t_cal_vector

    print(f"\n1. Native Vector Stage (Per Page):")
    print(f"   - PyMuPDF text extraction:  {t_mupdf_text:.2f} ms")
    print(f"   - Syntax & Calibrator:      {t_cal_vector:.2f} ms")
    print(f"   - Total Native Vector:      {total_vector_ms:.2f} ms")

    # 2. Local OCR Stage Breakdown
    doc_s = pymupdf.open(sample_scan)
    p_s = doc_s[0]

    # Stage 2a: Rendering Pixmap
    t0 = time.perf_counter()
    pix = p_s.get_pixmap(dpi=200)
    img = PIL.Image.open(io.BytesIO(pix.tobytes()))
    t_render_200 = (time.perf_counter() - t0) * 1000.0

    # Stage 2b: Full-Res OSD vs Downsampled OSD
    t0 = time.perf_counter()
    try:
        osd_full = pytesseract.image_to_osd(img, timeout=10)
    except Exception:
        pass
    t_osd_full = (time.perf_counter() - t0) * 1000.0

    t0 = time.perf_counter()
    try:
        # Optimization: Downsample to 72 DPI thumbnail for OSD
        small_img = img.resize((img.width // 2, img.height // 2), resample=PIL.Image.Resampling.BILINEAR)
        osd_opt = pytesseract.image_to_osd(small_img, timeout=10)
    except Exception:
        pass
    t_osd_opt = (time.perf_counter() - t0) * 1000.0

    # Stage 2c: Tesseract image_to_data
    t0 = time.perf_counter()
    ocr_dict = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT, timeout=15)
    t_tesseract_ocr = (time.perf_counter() - t0) * 1000.0

    # Stage 2d: Spatial Y-Clustering & Line Building
    t0 = time.perf_counter()
    ocr_data = PageOCRData(ocr_dict, dpi=200)
    t_clustering = (time.perf_counter() - t0) * 1000.0

    # Stage 2e: Field Extraction & Proximity Search
    t0 = time.perf_counter()
    patterns = [r"(?:THIS\s+IS\s+TO\s+CERTIFY\s+THAT|NAME\s*OF\s*APPLICANT)[:\s]+([A-Z\s]+)"]
    val, bbox, snip, conf, lbl_det, lbl_dist, c_count = _find_field_in_ocr_page(ocr_data, patterns)
    t_proximity_search = (time.perf_counter() - t0) * 1000.0

    # Stage 2f: Field Calibration
    t0 = time.perf_counter()
    cal_ocr_res = cal.calibrate(
        field_name="applicant_name",
        raw_value=val or "Smruti Nayak",
        extraction_method=ExtractionMethod.LOCAL_OCR,
        token_confidence=conf,
        label_detected=lbl_det,
        label_distance_pt=lbl_dist,
        candidate_count=c_count
    )
    t_cal_ocr = (time.perf_counter() - t0) * 1000.0
    doc_s.close()

    total_ocr_unoptimized = t_render_200 + t_osd_full + t_tesseract_ocr + t_clustering + t_proximity_search + t_cal_ocr
    total_ocr_optimized = t_render_200 + t_osd_opt + t_tesseract_ocr + t_clustering + t_proximity_search + t_cal_ocr

    print(f"\n2. Local OCR Stage Breakdown (Per Page):")
    print(f"   - PyMuPDF 200 DPI render:   {t_render_200:.2f} ms")
    print(f"   - Tesseract OSD (Full Res): {t_osd_full:.2f} ms")
    print(f"   - Tesseract OSD (Downsampled): {t_osd_opt:.2f} ms (Speedup: {t_osd_full / max(1.0, t_osd_opt):.1f}x)")
    print(f"   - Tesseract Token OCR:      {t_tesseract_ocr:.2f} ms")
    print(f"   - Spatial Y-Clustering:     {t_clustering:.2f} ms")
    print(f"   - Multi-Candidate Search:   {t_proximity_search:.2f} ms")
    print(f"   - Multi-Feature Calibrator: {t_cal_ocr:.2f} ms")
    print(f"   ----------------------------------------")
    print(f"   - Total OCR Unoptimized:    {total_ocr_unoptimized:.2f} ms (~{total_ocr_unoptimized/1000.0:.2f} s)")
    print(f"   - Total OCR Optimized:      {total_ocr_optimized:.2f} ms (~{total_ocr_optimized/1000.0:.2f} s)")

    # 3. Validation & Safety Firewall Profile
    from docuready.pipeline import AuditPipeline
    pipeline = AuditPipeline()
    t0 = time.perf_counter()
    res, _ = pipeline.load_and_audit_packet("synthetic_data/pkt_loop3_demo")
    t_full_audit = (time.perf_counter() - t0) * 1000.0

    print(f"\n3. Full Packet Audit (6 Documents, Hybrid Vector + OCR):")
    print(f"   - Full End-to-End Latency:  {t_full_audit:.2f} ms (~{t_full_audit/1000.0:.2f} s)")
    print(f"   - Findings Evaluated:       {len(res.findings)}")
    print(f"   - Overall Determination:    {res.overall_status}")

    profile_data = {
        "native_vector_per_page_ms": round(total_vector_ms, 2),
        "ocr_render_200dpi_ms": round(t_render_200, 2),
        "ocr_osd_full_res_ms": round(t_osd_full, 2),
        "ocr_osd_downsampled_ms": round(t_osd_opt, 2),
        "ocr_token_extraction_ms": round(t_tesseract_ocr, 2),
        "spatial_clustering_ms": round(t_clustering, 2),
        "field_search_ms": round(t_proximity_search, 2),
        "calibrator_ms": round(t_cal_ocr, 2),
        "total_ocr_page_unoptimized_ms": round(total_ocr_unoptimized, 2),
        "total_ocr_page_optimized_ms": round(total_ocr_optimized, 2),
        "full_packet_6docs_ms": round(t_full_audit, 2)
    }

    with open("docuready-mvp/PERFORMANCE_PROFILE.json", "w", encoding="utf-8") as f:
        json.dump(profile_data, f, indent=2)
    print("\nSaved profile data to 'docuready-mvp/PERFORMANCE_PROFILE.json'")


if __name__ == "__main__":
    profile_pipeline()
