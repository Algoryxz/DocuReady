"""
Loop 13 - Sub-Stage Performance & Memory Profiler
DocuReady Engineering Research

Measures the microsecond-level latency and memory impact of spatial layout analysis
and de-interleaving across 1000 simulated pages.
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

from src.docuready.ingest.extractor import PageOCRData
from src.docuready.ingest.spatial_layout import (
    detect_page_layout_structure,
    cluster_and_order_words,
    _cluster_words_raw
)


def generate_synthetic_page(num_lines: int = 40, two_column: bool = True) -> list:
    """Generates a realistic page of OCR words (approx 250-400 words)."""
    words = []
    y = 50.0
    for l in range(num_lines):
        if two_column:
            # Col 1: 4 words
            x = 50.0
            for w_idx in range(4):
                words.append({
                    "word": f"word_c1_{l}_{w_idx}",
                    "conf": 95.0,
                    "box": [x, y, x + 40.0, y + 12.0],
                    "x0": x,
                    "y0": y,
                    "h": 12.0
                })
                x += 50.0
            # Col 2: 4 words (starts at 350.0)
            x = 350.0
            for w_idx in range(4):
                words.append({
                    "word": f"word_c2_{l}_{w_idx}",
                    "conf": 95.0,
                    "box": [x, y, x + 40.0, y + 12.0],
                    "x0": x,
                    "y0": y,
                    "h": 12.0
                })
                x += 50.0
        else:
            # Single column: 8 words across line
            x = 50.0
            for w_idx in range(8):
                words.append({
                    "word": f"word_sc_{l}_{w_idx}",
                    "conf": 95.0,
                    "box": [x, y, x + 40.0, y + 12.0],
                    "x0": x,
                    "y0": y,
                    "h": 12.0
                })
                x += 50.0
        y += 18.0
    return words


def profile_spatial_reconstruction(iterations: int = 500):
    print("=" * 80)
    print("DOCUREADY LOOP 13: SUB-STAGE PERFORMANCE & MEMORY PROFILER")
    print(f"Running {iterations} iterations on 40-line pages (320 words/page)...")
    print("=" * 80)

    two_col_words = generate_synthetic_page(num_lines=40, two_column=True)
    single_col_words = generate_synthetic_page(num_lines=40, two_column=False)

    # 1. Warm-up
    for _ in range(20):
        cluster_and_order_words(two_col_words)
        cluster_and_order_words(single_col_words)

    # 2. Timing Two-Column Layout
    gc.collect()
    t0 = time.perf_counter()
    for _ in range(iterations):
        cluster_and_order_words(two_col_words)
    t_two_col = (time.perf_counter() - t0) * 1000.0 / iterations

    # 3. Timing Single-Column Layout (Early exit / bypass)
    gc.collect()
    t0 = time.perf_counter()
    for _ in range(iterations):
        cluster_and_order_words(single_col_words)
    t_single_col = (time.perf_counter() - t0) * 1000.0 / iterations

    # 4. Memory Profiling with tracemalloc
    gc.collect()
    tracemalloc.start()
    snapshot_before = tracemalloc.take_snapshot()
    for _ in range(iterations):
        _ = cluster_and_order_words(two_col_words)
    snapshot_after = tracemalloc.take_snapshot()
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    peak_kb = peak / 1024.0

    profile_results = {
        "iterations": iterations,
        "page_size_words": len(two_col_words),
        "two_column_reconstruction_ms": round(t_two_col, 4),
        "single_column_bypass_ms": round(t_single_col, 4),
        "peak_memory_allocated_kb": round(peak_kb, 2),
        "pipeline_budget_fraction_pct": round((t_two_col / 834.0) * 100.0, 3)  # vs 834ms total OCR pipeline
    }

    print(f"Two-Column Spatial Reconstruction: {profile_results['two_column_reconstruction_ms']:.4f} ms per page")
    print(f"Single-Column Bypass Check:        {profile_results['single_column_bypass_ms']:.4f} ms per page")
    print(f"Peak Memory Overhead:             {profile_results['peak_memory_allocated_kb']:.2f} KB")
    print(f"Fraction of ~834ms Page Pipeline: {profile_results['pipeline_budget_fraction_pct']:.3f}%")
    print("=" * 80)

    out_path = ROOT / "research" / "loop13" / "results" / "loop13_profiling_results.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(profile_results, f, indent=2)

    print(f"Profiling artifact written to {out_path}")
    return profile_results


if __name__ == "__main__":
    profile_spatial_reconstruction(iterations=500)
