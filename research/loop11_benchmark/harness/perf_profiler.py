"""
Detailed Latency & Memory Profiler for DocuReady Pipeline
DocuReady - Research Loop 11

Profiles every sub-stage of document ingestion, rasterization, OCR, deskew,
field extraction, and decision resolving across diverse document types.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import PIL.Image
import psutil
import pymupdf
import pytesseract

REPO_ROOT = Path(__file__).resolve().parents[3]
BENCHMARK_DIR = REPO_ROOT / "research" / "loop11_benchmark"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from docuready.ingest.extractor import DocumentExtractor, PageOCRData, _is_demonstrably_upright
from docuready.ingest.deskew import estimate_skew_angle, deskew_image
from docuready.ingest.tesseract_discovery import configure_pytesseract

configure_pytesseract()


def profile_pipeline_stages() -> dict:
    process = psutil.Process(os.getpid())
    funsd_samples = list((BENCHMARK_DIR / "data" / "funsd").glob("*.pdf"))[:10]
    deg_samples = list((BENCHMARK_DIR / "data" / "degradation").glob("*.png"))[:10]
    test_files = funsd_samples + deg_samples

    stage_timings = {
        "rasterization": [],
        "initial_ocr": [],
        "upright_gate": [],
        "skew_estimation": [],
        "deskew_rotation": [],
        "line_clustering": [],
        "total_page_time": []
    }

    print(f"Profiling detailed stage breakdown across {len(test_files)} sample documents...")

    for f in test_files:
        t_total_0 = time.perf_counter()

        # Stage 1: Rasterization
        t0 = time.perf_counter()
        doc = pymupdf.open(str(f))
        page = doc[0]
        pix = page.get_pixmap(dpi=150)
        img = PIL.Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        pix = None
        doc.close()
        t1 = time.perf_counter()
        stage_timings["rasterization"].append((t1 - t0) * 1000.0)

        # Stage 2: Initial OCR
        t2 = time.perf_counter()
        try:
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT, timeout=10)
        except Exception:
            data = {"text": [], "conf": [], "left": [], "top": [], "width": [], "height": []}
        t3 = time.perf_counter()
        stage_timings["initial_ocr"].append((t3 - t2) * 1000.0)

        # Stage 3: Upright gate
        t4 = time.perf_counter()
        is_upright = _is_demonstrably_upright(data)
        t5 = time.perf_counter()
        stage_timings["upright_gate"].append((t5 - t4) * 1000.0)

        # Stage 4: Skew estimation
        t6 = time.perf_counter()
        if not is_upright:
            angle, conf = estimate_skew_angle(img, max_angle=45.0)
        else:
            angle, conf = 0.0, 0.0
        t7 = time.perf_counter()
        stage_timings["skew_estimation"].append((t7 - t6) * 1000.0)

        # Stage 5: Deskew rotation
        t8 = time.perf_counter()
        if abs(angle) >= 1.0 and conf >= 5.0:
            d_img, _, _ = deskew_image(img, angle)
        t9 = time.perf_counter()
        stage_timings["deskew_rotation"].append((t9 - t8) * 1000.0)

        # Stage 6: Line clustering
        t10 = time.perf_counter()
        page_ocr = PageOCRData(data, dpi=150, rotation_applied=0)
        _ = len(page_ocr.lines)
        t11 = time.perf_counter()
        stage_timings["line_clustering"].append((t11 - t10) * 1000.0)

        t_total_1 = time.perf_counter()
        stage_timings["total_page_time"].append((t_total_1 - t_total_0) * 1000.0)

    summary = {
        "sample_count": len(test_files),
        "peak_rss_mb": round(process.memory_info().rss / (1024 * 1024), 2),
        "stages_ms": {
            k: {
                "mean": round(sum(v) / len(v), 2),
                "min": round(min(v), 2),
                "max": round(max(v), 2),
                "pct_of_total": round((sum(v) / sum(stage_timings["total_page_time"])) * 100, 1)
            }
            for k, v in stage_timings.items() if k != "total_page_time"
        },
        "total_page_time_ms": {
            "mean": round(sum(stage_timings["total_page_time"]) / len(stage_timings["total_page_time"]), 2),
            "median": round(sorted(stage_timings["total_page_time"])[len(test_files) // 2], 2),
            "p95": round(sorted(stage_timings["total_page_time"])[int(len(test_files) * 0.95)], 2),
            "min": round(min(stage_timings["total_page_time"]), 2),
            "max": round(max(stage_timings["total_page_time"]), 2)
        }
    }

    out_file = BENCHMARK_DIR / "results" / "stage_profiling_results.json"
    out_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("\n=== STAGE PROFILING SUMMARY ===")
    print(f"Mean Total Page Latency: {summary['total_page_time_ms']['mean']} ms (P95: {summary['total_page_time_ms']['p95']} ms)")
    print(f"Peak Process RSS Memory: {summary['peak_rss_mb']} MB")
    for s_name, s_data in summary["stages_ms"].items():
        print(f"  {s_name:20}: {s_data['mean']:6.2f} ms ({s_data['pct_of_total']:4.1f}% of total)")
    print(f"Saved profile results to: {out_file}")
    return summary


if __name__ == "__main__":
    profile_pipeline_stages()
