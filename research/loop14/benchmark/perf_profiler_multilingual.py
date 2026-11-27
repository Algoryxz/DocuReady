"""
Loop 14 - Multilingual Sub-Stage Performance & Memory Profiler
DocuReady Engineering Research

Measures script detection latency, language routing overhead, OCR runtime,
and memory consumption across English, Hindi, and Odia documents.
"""

from __future__ import annotations

import gc
import json
import os
import sys
import time
import tracemalloc
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import pytesseract
from PIL import Image, ImageDraw, ImageFont

from src.docuready.ingest.script_router import detect_unicode_script, resolve_optimal_ocr_language
from src.docuready.ingest.tesseract_discovery import configure_pytesseract


def profile_multilingual_engine(iterations: int = 200):
    configure_pytesseract()

    print("=" * 80)
    print("DOCUREADY LOOP 14: MULTILINGUAL PERFORMANCE & MEMORY PROFILING")
    print(f"Running {iterations} iterations on synthetic documents...")
    print("=" * 80)

    try:
        font = ImageFont.truetype(r"C:\Windows\Fonts\Nirmala.ttc", 28)
    except Exception:
        font = ImageFont.load_default()

    # Create test images
    img_eng = Image.new("RGB", (800, 300), (255, 255, 255))
    ImageDraw.Draw(img_eng).text((30, 40), "Government of India Department of Higher Education Notification 2026", (0, 0, 0), font=font)

    img_hin = Image.new("RGB", (800, 300), (255, 255, 255))
    ImageDraw.Draw(img_hin).text((30, 40), "भारत सरकार उच्च शिक्षा विभाग राष्ट्रीय छात्रवृत्ति योजना २०२६", (0, 0, 0), font=font)

    img_ori = Image.new("RGB", (800, 300), (255, 255, 255))
    ImageDraw.Draw(img_ori).text((30, 40), "ଓଡ଼ିଶା ସରକାର ଉଚ୍ଚଶିକ୍ଷା ବିଭାଗ ଛାତ୍ରବୃତ୍ତି ଯୋଜନା ନିର୍ଦ୍ଦେଶାବଳୀ ୨୦୨୬", (0, 0, 0), font=font)

    # 1. Script Detection Latency (pure Python Unicode inspection)
    sample_text = "Government of India / भारत सरकार - Annual Household Income: ₹ 1,80,000"
    t0 = time.perf_counter()
    for _ in range(iterations * 5):
        _ = detect_unicode_script(sample_text)
    t_script_detect_us = ((time.perf_counter() - t0) * 1_000_000.0) / (iterations * 5)

    # 2. OCR Execution Latencies (English vs Hindi vs Odia)
    gc.collect()
    t0 = time.perf_counter()
    for _ in range(iterations // 10):
        _ = pytesseract.image_to_data(img_eng, lang="eng", output_type=pytesseract.Output.DICT)
    t_ocr_eng_ms = ((time.perf_counter() - t0) * 1000.0) / (iterations // 10)

    gc.collect()
    t0 = time.perf_counter()
    for _ in range(iterations // 10):
        _ = pytesseract.image_to_data(img_hin, lang="hin", output_type=pytesseract.Output.DICT)
    t_ocr_hin_ms = ((time.perf_counter() - t0) * 1000.0) / (iterations // 10)

    gc.collect()
    t0 = time.perf_counter()
    for _ in range(iterations // 10):
        _ = pytesseract.image_to_data(img_ori, lang="ori", output_type=pytesseract.Output.DICT)
    t_ocr_ori_ms = ((time.perf_counter() - t0) * 1000.0) / (iterations // 10)

    # 3. Memory Profiling with tracemalloc
    gc.collect()
    tracemalloc.start()
    for _ in range(20):
        _ = pytesseract.image_to_data(img_hin, lang="hin", output_type=pytesseract.Output.DICT)
        _ = pytesseract.image_to_data(img_ori, lang="ori", output_type=pytesseract.Output.DICT)
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    peak_kb = peak / 1024.0

    profile_results = {
        "iterations": iterations,
        "script_detection_latency_microseconds": round(t_script_detect_us, 2),
        "ocr_latency_english_ms": round(t_ocr_eng_ms, 2),
        "ocr_latency_hindi_ms": round(t_ocr_hin_ms, 2),
        "ocr_latency_odia_ms": round(t_ocr_ori_ms, 2),
        "peak_memory_overhead_kb": round(peak_kb, 2)
    }

    print(f"Unicode Script Detection: {profile_results['script_detection_latency_microseconds']} microseconds/doc")
    print(f"English OCR Latency:      {profile_results['ocr_latency_english_ms']} ms/page")
    print(f"Hindi OCR Latency:        {profile_results['ocr_latency_hindi_ms']} ms/page")
    print(f"Odia OCR Latency:         {profile_results['ocr_latency_odia_ms']} ms/page")
    print(f"Peak Memory Overhead:     {profile_results['peak_memory_overhead_kb']} KB")
    print("=" * 80)

    out_file = ROOT / "research" / "loop14" / "results" / "loop14_profiling_results.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(profile_results, f, indent=2)

    print(f"Profiling results written to {out_file}")
    return profile_results


if __name__ == "__main__":
    profile_multilingual_engine()
