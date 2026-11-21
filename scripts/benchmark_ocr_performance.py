"""
DocuReady Loop 01 — Comprehensive OCR & OSD Benchmark Harness
Measures granular per-stage latency, peak memory (RSS), and extraction metrics across
the required workload matrix (Native vector, Clean scan, Rotated 90/180/270, Multipage,
Low-DPI, and Mixed Packets).
"""
import os
import io
import sys
import time
import json
import statistics
import platform
from pathlib import Path
from typing import Dict, Any, List

import psutil
import pymupdf
import PIL.Image
import pytesseract

from docuready.ingest.tesseract_discovery import configure_pytesseract, get_ocr_runtime_info
from docuready.ingest.extractor import DocumentExtractor, PageOCRData, _find_field_in_ocr_page, _is_demonstrably_upright, _ocr_page
from docuready.domain.models import DocumentType, ExtractionMethod
from docuready.evidence.calibrator import ConfidenceCalibrator
from docuready.pipeline import AuditPipeline

configure_pytesseract()

WORKLOADS = [
    {
        "id": "1_native_text",
        "category": "Native-text PDF",
        "path": "synthetic_data/realistic_corpus_60/smp_01_income_cert_clean.pdf",
        "doc_type": DocumentType.INCOME_CERT,
        "is_packet": False,
        "expected_rotation": 0,
    },
    {
        "id": "2_clean_scan",
        "category": "Clean scanned PDF",
        "path": "synthetic_data/realistic_corpus_60/smp_11_raster_scan.pdf",
        "doc_type": DocumentType.INCOME_CERT,
        "is_packet": False,
        "expected_rotation": 0,
    },
    {
        "id": "3_rotated_90",
        "category": "Rotated scanned page (90°)",
        "path": "synthetic_data/realistic_corpus_60/smp_23_rotated_90deg.pdf",
        "doc_type": DocumentType.INCOME_CERT,
        "is_packet": False,
        "expected_rotation": 90,
    },
    {
        "id": "4_rotated_180",
        "category": "Rotated scanned page (180°)",
        "path": "synthetic_data/realistic_corpus_60/smp_24_rotated_180deg.pdf",
        "doc_type": DocumentType.INCOME_CERT,
        "is_packet": False,
        "expected_rotation": 180,
    },
    {
        "id": "5_rotated_270",
        "category": "Rotated scanned page (270°)",
        "path": "synthetic_data/realistic_corpus_60/smp_61_rotated_270deg.pdf",
        "doc_type": DocumentType.INCOME_CERT,
        "is_packet": False,
        "expected_rotation": 270,
    },
    {
        "id": "6_low_quality_dpi",
        "category": "Low-quality scan (Low DPI)",
        "path": "synthetic_data/realistic_corpus_60/smp_25_low_dpi.pdf",
        "doc_type": DocumentType.INCOME_CERT,
        "is_packet": False,
        "expected_rotation": 0,
    },
    {
        "id": "7_low_quality_shadow",
        "category": "Low-quality scan (Shadow gradient)",
        "path": "synthetic_data/realistic_corpus_60/smp_37_shadow_gradient.pdf",
        "doc_type": DocumentType.INCOME_CERT,
        "is_packet": False,
        "expected_rotation": 0,
    },
    {
        "id": "8_multipage_packet",
        "category": "Multi-page layout (4 pages)",
        "path": "synthetic_data/realistic_corpus_60/smp_55_multipage_layout_1.pdf",
        "doc_type": DocumentType.APPLICATION_FORM,
        "is_packet": False,
        "expected_rotation": 0,
    },
    {
        "id": "9_mixed_packet_6docs",
        "category": "Mixed native/scanned PDF packet (6 docs)",
        "path": "synthetic_data/pkt_loop3_demo",
        "doc_type": None,
        "is_packet": True,
        "expected_rotation": 0,
    },
]

def get_sys_info() -> Dict[str, Any]:
    ocr_info = get_ocr_runtime_info()
    return {
        "os": f"{platform.system()} {platform.release()} ({platform.machine()})",
        "python": sys.version.split()[0],
        "cpu_count": psutil.cpu_count(logical=True),
        "total_ram_gb": round(psutil.virtual_memory().total / (1024**3), 2),
        "tesseract_version": ocr_info.get("version", "unknown"),
        "tesseract_languages": ocr_info.get("languages", []),
        "pymupdf_version": pymupdf.__version__,
        "pillow_version": PIL.__version__,
    }

def run_single_doc_benchmark(path: str, doc_type: DocumentType, iterations: int = 5) -> Dict[str, Any]:
    ext = DocumentExtractor()
    process = psutil.Process(os.getpid())

    render_times = []
    total_doc_times = []
    peak_rss_mb = []
    extracted_fields_counts = []
    extracted_statuses = []

    for _ in range(iterations):
        t0 = time.perf_counter()
        doc = ext.extract_document(path, expected_type=doc_type)
        dur = (time.perf_counter() - t0) * 1000.0

        total_doc_times.append(dur)
        extracted_fields_counts.append(len(doc.fields))
        extracted_statuses.append(doc.status)
        peak_rss_mb.append(process.memory_info().rss / (1024 * 1024))

    return {
        "iterations": iterations,
        "total_ms": {
            "mean": round(statistics.mean(total_doc_times), 2),
            "median": round(statistics.median(total_doc_times), 2),
            "min": round(min(total_doc_times), 2),
            "max": round(max(total_doc_times), 2),
        },
        "peak_rss_mb": round(max(peak_rss_mb), 2),
        "status": extracted_statuses[0],
        "fields_count": extracted_fields_counts[0],
    }

def run_packet_benchmark(packet_dir: str, iterations: int = 5) -> Dict[str, Any]:
    pipeline = AuditPipeline()
    process = psutil.Process(os.getpid())
    packet_times = []
    peak_rss_mb = []
    findings_counts = []
    statuses = []

    for _ in range(iterations):
        t0 = time.perf_counter()
        res, _ = pipeline.load_and_audit_packet(packet_dir)
        dur = (time.perf_counter() - t0) * 1000.0
        packet_times.append(dur)
        findings_counts.append(len(res.findings))
        statuses.append(str(res.overall_status.value if hasattr(res.overall_status, "value") else res.overall_status))
        peak_rss_mb.append(process.memory_info().rss / (1024 * 1024))

    return {
        "iterations": iterations,
        "total_ms": {
            "mean": round(statistics.mean(packet_times), 2),
            "median": round(statistics.median(packet_times), 2),
            "min": round(min(packet_times), 2),
            "max": round(max(packet_times), 2),
        },
        "peak_rss_mb": round(max(peak_rss_mb), 2),
        "status": statuses[0],
        "findings_count": findings_counts[0],
    }

def run_granular_ocr_stage_breakdown(scanned_pdf: str, iterations: int = 5) -> Dict[str, Any]:
    doc = pymupdf.open(scanned_pdf)
    page = doc[0]

    render_times = []
    render_direct_times = []
    osd_full_times = []
    token_ocr_times = []
    fast_path_gate_times = []
    clustering_times = []
    search_times = []
    full_ocr_page_times = []

    cal = ConfidenceCalibrator()
    ext = DocumentExtractor()

    for _ in range(iterations):
        # 1. Render legacy (BytesIO PNG)
        t0 = time.perf_counter()
        pix = page.get_pixmap(dpi=200)
        img = PIL.Image.open(io.BytesIO(pix.tobytes()))
        render_times.append((time.perf_counter() - t0) * 1000.0)

        # 1b. Render optimized (Direct Buffer)
        t0 = time.perf_counter()
        pix_opt = page.get_pixmap(dpi=200)
        img_opt = PIL.Image.frombytes("RGB", [pix_opt.width, pix_opt.height], pix_opt.samples)
        pix_opt = None
        render_direct_times.append((time.perf_counter() - t0) * 1000.0)

        # 2. OSD
        t0 = time.perf_counter()
        try:
            osd = pytesseract.image_to_osd(img, timeout=15)
        except Exception:
            pass
        osd_full_times.append((time.perf_counter() - t0) * 1000.0)

        # 3. Token OCR
        t0 = time.perf_counter()
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT, timeout=15)
        token_ocr_times.append((time.perf_counter() - t0) * 1000.0)

        # 3b. Fast-path gate evaluation
        t0 = time.perf_counter()
        is_upright = _is_demonstrably_upright(data)
        fast_path_gate_times.append((time.perf_counter() - t0) * 1000.0)

        # 4. Spatial clustering
        t0 = time.perf_counter()
        p_ocr = PageOCRData(data, dpi=200)
        clustering_times.append((time.perf_counter() - t0) * 1000.0)

        # 5. Field Search
        t0 = time.perf_counter()
        patterns = [r"(?:THIS\s+IS\s+TO\s+CERTIFY\s+THAT|NAME\s*OF\s*APPLICANT)[:\s]+([A-Z\s]+)"]
        _find_field_in_ocr_page(p_ocr, patterns)
        search_times.append((time.perf_counter() - t0) * 1000.0)

        # 6. Full end-to-end _ocr_page (production pipeline)
        t0 = time.perf_counter()
        page_ocr = _ocr_page(page, dpi=200)
        full_ocr_page_times.append((time.perf_counter() - t0) * 1000.0)

    doc.close()

    return {
        "render_legacy_ms": {
            "median": round(statistics.median(render_times), 2),
            "mean": round(statistics.mean(render_times), 2),
        },
        "render_direct_buffer_ms": {
            "median": round(statistics.median(render_direct_times), 2),
            "mean": round(statistics.mean(render_direct_times), 2),
        },
        "osd_full_ms": {
            "median": round(statistics.median(osd_full_times), 2),
            "mean": round(statistics.mean(osd_full_times), 2),
        },
        "token_ocr_ms": {
            "median": round(statistics.median(token_ocr_times), 2),
            "mean": round(statistics.mean(token_ocr_times), 2),
        },
        "fast_path_gate_eval_ms": {
            "median": round(statistics.median(fast_path_gate_times), 2),
            "mean": round(statistics.mean(fast_path_gate_times), 2),
        },
        "clustering_ms": {
            "median": round(statistics.median(clustering_times), 2),
            "mean": round(statistics.mean(clustering_times), 2),
        },
        "search_ms": {
            "median": round(statistics.median(search_times), 2),
            "mean": round(statistics.mean(search_times), 2),
        },
        "optimized_ocr_page_ms": {
            "median": round(statistics.median(full_ocr_page_times), 2),
            "mean": round(statistics.mean(full_ocr_page_times), 2),
        },
    }

def main():
    print("=" * 70)
    print("DOCUREADY LOOP 01 — OCR PERFORMANCE BENCHMARK HARNESS")
    print("=" * 70)

    sys_info = get_sys_info()
    print("Execution Environment:")
    for k, v in sys_info.items():
        print(f"  {k}: {v}")
    print()

    print("Running Granular OCR Stage Breakdown (5 iterations on smp_11_raster_scan.pdf)...")
    stage_breakdown = run_granular_ocr_stage_breakdown("synthetic_data/realistic_corpus_60/smp_11_raster_scan.pdf", iterations=5)
    for stage, vals in stage_breakdown.items():
        print(f"  {stage}: median={vals['median']:.2f} ms, mean={vals['mean']:.2f} ms")
    print()

    workload_results = []
    print("Running Workload Matrix (5 iterations each)...")
    for w in WORKLOADS:
        print(f"--> Benchmarking {w['category']} ({w['path']})...")
        if w["is_packet"]:
            res = run_packet_benchmark(w["path"], iterations=5)
        else:
            res = run_single_doc_benchmark(w["path"], w["doc_type"], iterations=5)
        
        entry = {
            "id": w["id"],
            "category": w["category"],
            "path": w["path"],
            "is_packet": w["is_packet"],
            "results": res,
        }
        workload_results.append(entry)
        print(f"    Median: {res['total_ms']['median']:.2f} ms | Status: {res['status']} | Peak RSS: {res['peak_rss_mb']} MB")

    output = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "system_info": sys_info,
        "stage_breakdown": stage_breakdown,
        "workload_results": workload_results,
    }

    out_file = "docs/04-VALIDATION/LOOP_01_OCR_BENCHMARK_DATA.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    print(f"\nAll benchmark results written to {out_file}")

    opt_file = "docs/04-VALIDATION/LOOP_01_OCR_OPTIMIZED_DATA.json"
    with open(opt_file, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    print(f"Optimized benchmark results written to {opt_file}")

if __name__ == "__main__":
    main()
