"""
Loop 15 - Region-Aware Multilingual OCR Performance Profiler
DocuReady Engineering Research

Measures end-to-end performance metrics:
1. Region Segmentation Latency (ms)
2. Script Classification Latency (ms)
3. Sub-Image OCR Execution Latency (ms)
4. Evidence Assembly & Coordinate Mapping Latency (ms)
5. Peak Memory Allocation (tracemalloc)
6. Throughput (pages / sec)
"""

from __future__ import annotations

import json
import os
import sys
import time
import tracemalloc
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from PIL import Image
import pytesseract

from docuready.ingest.extractor import PageOCRData
from docuready.ingest.region_ocr import (
    classify_region_script,
    ocr_page_by_regions,
    segment_page_into_regions,
)
from docuready.ingest.tesseract_discovery import configure_pytesseract

CORPUS_DIR = ROOT / "research" / "loop15" / "corpus"
RESULTS_DIR = ROOT / "research" / "loop15" / "results"


def profile_performance():
    configure_pytesseract()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("DOCUREADY LOOP 15: REGION-AWARE PERFORMANCE & RESOURCE PROFILER")
    print("=" * 80)

    test_docs = [
        "DOC_MULTI_01_TRI_SCRIPT_GAZETTE",
        "DOC_MULTI_02_BILINGUAL_COLUMNS_HIN_ENG",
        "DOC_MULTI_03_BILINGUAL_COLUMNS_ORI_ENG",
        "DOC_MULTI_04_MARKSHEET_INDIC_GRID",
        "DOC_CTRL_01_ENGLISH_CERTIFICATE",
    ]

    breakdown_results = {
        "segmentation_ms": [],
        "classification_ms": [],
        "ocr_execution_ms": [],
        "assembly_ms": [],
        "total_ms": [],
        "peak_memory_mb": [],
    }

    per_doc_profiles = {}

    for doc_id in test_docs:
        img_path = CORPUS_DIR / f"{doc_id}.png"
        if not img_path.exists():
            continue

        img = Image.open(img_path)

        tracemalloc.start()
        t_start = time.perf_counter()

        # Stage 1: Segmentation
        t0 = time.perf_counter()
        regions = segment_page_into_regions(img)
        t_seg = (time.perf_counter() - t0) * 1000.0

        # Stage 2: Script Classification
        t0 = time.perf_counter()
        for reg in regions:
            crop = img.crop(reg.bbox_px)
            lang, script = classify_region_script(crop, native_text=reg.text_preview)
            reg.detected_lang = lang
            reg.primary_script = script
        t_class = (time.perf_counter() - t0) * 1000.0

        # Stage 3: Targeted OCR Execution & Remapping
        t0 = time.perf_counter()
        data = ocr_page_by_regions(img, dpi=200)
        t_ocr = (time.perf_counter() - t0) * 1000.0

        # Stage 4: Line Assembly & Spatial Reconstruction
        t0 = time.perf_counter()
        ocr_obj = PageOCRData(data, dpi=200)
        t_asm = (time.perf_counter() - t0) * 1000.0

        t_total = (time.perf_counter() - t_start) * 1000.0
        current_mem, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        peak_mb = round(peak_mem / (1024 * 1024), 2)

        breakdown_results["segmentation_ms"].append(t_seg)
        breakdown_results["classification_ms"].append(t_class)
        breakdown_results["ocr_execution_ms"].append(t_ocr)
        breakdown_results["assembly_ms"].append(t_asm)
        breakdown_results["total_ms"].append(t_total)
        breakdown_results["peak_memory_mb"].append(peak_mb)

        per_doc_profiles[doc_id] = {
            "image_size": f"{img.width}x{img.height}",
            "region_count": len(regions),
            "segmentation_ms": round(t_seg, 2),
            "classification_ms": round(t_class, 2),
            "ocr_execution_ms": round(t_ocr, 2),
            "assembly_ms": round(t_asm, 2),
            "total_ms": round(t_total, 2),
            "peak_memory_mb": peak_mb,
            "line_count": len(ocr_obj.lines),
        }

        print(f"[{doc_id}] Regions: {len(regions)} | Seg: {t_seg:.1f}ms | Class: {t_class:.1f}ms | OCR: {t_ocr:.1f}ms | Total: {t_total:.1f}ms | Peak RAM: {peak_mb}MB")

    summary = {
        "mean_segmentation_ms": round(sum(breakdown_results["segmentation_ms"]) / len(breakdown_results["segmentation_ms"]), 2),
        "mean_classification_ms": round(sum(breakdown_results["classification_ms"]) / len(breakdown_results["classification_ms"]), 2),
        "mean_ocr_execution_ms": round(sum(breakdown_results["ocr_execution_ms"]) / len(breakdown_results["ocr_execution_ms"]), 2),
        "mean_assembly_ms": round(sum(breakdown_results["assembly_ms"]) / len(breakdown_results["assembly_ms"]), 2),
        "mean_total_latency_ms": round(sum(breakdown_results["total_ms"]) / len(breakdown_results["total_ms"]), 2),
        "mean_peak_memory_mb": round(sum(breakdown_results["peak_memory_mb"]) / len(breakdown_results["peak_memory_mb"]), 2),
        "throughput_pages_per_minute": round(60000.0 / (sum(breakdown_results["total_ms"]) / len(breakdown_results["total_ms"])), 1),
    }

    out_file = RESULTS_DIR / "loop15_profiling_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({"per_doc": per_doc_profiles, "summary": summary}, f, indent=2)

    print("\n" + "=" * 80)
    print("PROFILING SUMMARY")
    print("=" * 80)
    for k, v in summary.items():
        print(f"  {k:<35}: {v}")
    print(f"\nProfiling results saved to {out_file}")
    return summary


if __name__ == "__main__":
    profile_performance()
