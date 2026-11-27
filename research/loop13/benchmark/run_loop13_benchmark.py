"""
Loop 13 - Column-Aware Spatial Reading Order Benchmark Runner
DocuReady Engineering Research

Benchmarks reading order accuracy, pairwise inversion rate, character/word error rate,
and processing latency between the Loop 12 baseline (naive scanline) and
Loop 13 column-aware spatial reconstruction.
"""

from __future__ import annotations

import json
import time
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Add root directory to python path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from src.docuready.ingest.extractor import PageOCRData
from src.docuready.ingest.spatial_layout import (
    detect_page_layout_structure,
    cluster_and_order_words,
    _cluster_words_raw
)


def calculate_cer_wer(hypothesis: str, reference: str) -> Tuple[float, float]:
    """Computes Character Error Rate and Word Error Rate using Levenshtein distance."""
    # WER
    r_words = reference.split()
    h_words = hypothesis.split()
    
    # Simple edit distance for words
    d_w = [[0] * (len(h_words) + 1) for _ in range(len(r_words) + 1)]
    for i in range(len(r_words) + 1):
        d_w[i][0] = i
    for j in range(len(h_words) + 1):
        d_w[0][j] = j
    for i in range(1, len(r_words) + 1):
        for j in range(1, len(h_words) + 1):
            if r_words[i - 1] == h_words[j - 1]:
                d_w[i][j] = d_w[i - 1][j - 1]
            else:
                d_w[i][j] = 1 + min(d_w[i - 1][j], d_w[i][j - 1], d_w[i - 1][j - 1])
    wer = d_w[len(r_words)][len(h_words)] / max(1, len(r_words))

    # CER
    r_chars = list(reference)
    h_chars = list(hypothesis)
    d_c = [[0] * (len(h_chars) + 1) for _ in range(len(r_chars) + 1)]
    for i in range(len(r_chars) + 1):
        d_c[i][0] = i
    for j in range(len(h_chars) + 1):
        d_c[0][j] = j
    for i in range(1, len(r_chars) + 1):
        for j in range(1, len(h_chars) + 1):
            if r_chars[i - 1] == h_chars[j - 1]:
                d_c[i][j] = d_c[i - 1][j - 1]
            else:
                d_c[i][j] = 1 + min(d_c[i - 1][j], d_c[i][j - 1], d_c[i - 1][j - 1])
    cer = d_c[len(r_chars)][len(h_chars)] / max(1, len(r_chars))

    return round(cer, 4), round(wer, 4)


def pairwise_inversion_rate(hypothesis_words: List[str], reference_words: List[str]) -> float:
    """
    Computes fraction of word pairs whose relative order in hypothesis is inverted
    compared to their ground truth order in reference.
    """
    # Create word to first-seen position map in reference
    ref_pos = {}
    for idx, w in enumerate(reference_words):
        if w not in ref_pos:
            ref_pos[w] = []
        ref_pos[w].append(idx)

    # For unique words or greedy matching
    hyp_indices = []
    consumed = {w: 0 for w in ref_pos}
    for w in hypothesis_words:
        if w in ref_pos and consumed[w] < len(ref_pos[w]):
            hyp_indices.append(ref_pos[w][consumed[w]])
            consumed[w] += 1

    if len(hyp_indices) < 2:
        return 0.0

    inversions = 0
    total_pairs = 0
    for i in range(len(hyp_indices)):
        for j in range(i + 1, len(hyp_indices)):
            total_pairs += 1
            if hyp_indices[i] > hyp_indices[j]:
                inversions += 1

    return round(inversions / total_pairs, 4) if total_pairs > 0 else 0.0


# Synthetic benchmark test documents representing diverse layout typologies
BENCHMARK_CORPUS = [
    {
        "id": "DOC_01_TWO_COL_NARRATIVE",
        "category": "Multi-Column Text",
        "description": "Standard two-column official notification layout with parallel text flow",
        "words": [
            # Col 1: 3 lines
            ("The", 50, 100, 25, 12), ("post-matric", 80, 100, 75, 12), ("scholarship", 160, 100, 70, 12),
            ("scheme", 50, 120, 45, 12), ("guidelines", 100, 120, 65, 12), ("require", 170, 120, 45, 12),
            ("strict", 50, 140, 35, 12), ("physical", 90, 140, 50, 12), ("verification.", 145, 140, 75, 12),
            # Col 2: 3 lines
            ("State", 350, 100, 35, 12), ("verification", 390, 100, 75, 12), ("offices", 470, 100, 45, 12),
            ("shall", 350, 120, 30, 12), ("inspect", 385, 120, 45, 12), ("educational", 435, 120, 75, 12),
            ("institutions", 350, 140, 75, 12), ("annually", 430, 140, 50, 12), ("strictly.", 485, 140, 45, 12)
        ],
        "ground_truth_order": (
            "The post-matric scholarship scheme guidelines require strict physical verification. "
            "State verification offices shall inspect educational institutions annually strictly."
        )
    },
    {
        "id": "DOC_02_HEADER_FOOTER_BRACKET",
        "category": "Bracketed Multi-Column",
        "description": "Full-width spanning header and footer bracketing a two-column body",
        "words": [
            # Header
            ("GOVERNMENT", 200, 50, 100, 14), ("OF", 310, 50, 25, 14), ("INDIA", 345, 50, 50, 14),
            # Col 1
            ("Ministry", 50, 100, 55, 12), ("of", 110, 100, 15, 12), ("Education", 130, 100, 60, 12),
            ("New", 50, 120, 30, 12), ("Delhi", 85, 120, 35, 12), ("Headquarters", 125, 120, 80, 12),
            # Col 2
            ("Department", 350, 100, 75, 12), ("of", 430, 100, 15, 12), ("Higher", 450, 100, 40, 12),
            ("Annual", 350, 120, 45, 12), ("Budget", 400, 120, 45, 12), ("Division", 450, 120, 50, 12),
            # Footer
            ("Official", 180, 220, 50, 12), ("Gazette", 235, 220, 50, 12), ("Notification", 290, 220, 80, 12), ("2026", 375, 220, 35, 12)
        ],
        "ground_truth_order": (
            "GOVERNMENT OF INDIA "
            "Ministry of Education New Delhi Headquarters "
            "Department of Higher Annual Budget Division "
            "Official Gazette Notification 2026"
        )
    },
    {
        "id": "DOC_03_ASYMMETRIC_COLUMNS",
        "category": "Asymmetric Multi-Column",
        "description": "Left column has 4 lines, right column has 2 lines",
        "words": [
            # Left Col: 4 lines
            ("Primary", 50, 100, 50, 12), ("Objective:", 105, 100, 65, 12),
            ("Direct", 50, 120, 40, 12), ("benefit", 95, 120, 40, 12), ("transfer.", 140, 120, 50, 12),
            ("Secondary", 50, 140, 65, 12), ("Goal:", 120, 140, 35, 12),
            ("Aadhaar", 50, 160, 50, 12), ("seed", 105, 160, 30, 12), ("coverage.", 140, 160, 55, 12),
            # Right Col: 2 lines
            ("Disbursement", 350, 100, 80, 12), ("Window:", 435, 100, 50, 12),
            ("March", 350, 120, 40, 12), ("31", 395, 120, 15, 12), ("annually.", 415, 120, 55, 12)
        ],
        "ground_truth_order": (
            "Primary Objective: Direct benefit transfer. Secondary Goal: Aadhaar seed coverage. "
            "Disbursement Window: March 31 annually."
        )
    },
    {
        "id": "DOC_04_KEY_VALUE_FORM",
        "category": "Tabular Form",
        "description": "Standard key-value form fields with horizontal alignment (must NOT be split)",
        "words": [
            ("Applicant", 50, 100, 55, 12), ("Name:", 110, 100, 35, 12), ("ROHIT", 300, 100, 40, 12), ("VERMA", 345, 100, 45, 12),
            ("Roll", 50, 125, 30, 12), ("Number:", 85, 125, 45, 12), ("DHE-2026-5541", 300, 125, 85, 12),
            ("Annual", 50, 150, 40, 12), ("Income:", 95, 150, 45, 12), ("INR", 300, 150, 25, 12), ("180000", 330, 150, 45, 12),
            ("Verification", 50, 175, 75, 12), ("Status:", 130, 175, 40, 12), ("VERIFIED", 300, 175, 60, 12)
        ],
        "ground_truth_order": (
            "Applicant Name: ROHIT VERMA "
            "Roll Number: DHE-2026-5541 "
            "Annual Income: INR 180000 "
            "Verification Status: VERIFIED"
        )
    },
    {
        "id": "DOC_05_MARKSHEET_TABLE_GRID",
        "category": "3-Column Data Grid",
        "description": "3-column table grid with numbers and headers (must preserve row-wise order)",
        "words": [
            # Header
            ("Subject", 50, 100, 45, 12), ("Max_Marks", 200, 100, 65, 12), ("Marks_Obtained", 350, 100, 85, 12),
            # Row 1
            ("Mathematics", 50, 125, 75, 12), ("100", 200, 125, 25, 12), ("92", 350, 125, 20, 12),
            # Row 2
            ("Physics", 50, 150, 50, 12), ("100", 200, 150, 25, 12), ("88", 350, 150, 20, 12),
            # Row 3
            ("Chemistry", 50, 175, 60, 12), ("100", 200, 175, 25, 12), ("95", 350, 175, 20, 12)
        ],
        "ground_truth_order": (
            "Subject Max_Marks Marks_Obtained "
            "Mathematics 100 92 "
            "Physics 100 88 "
            "Chemistry 100 95"
        )
    },
    {
        "id": "DOC_06_SINGLE_COLUMN_CERTIFICATE",
        "category": "Single Column Narrative",
        "description": "Single-column certificate paragraph (control baseline - must never split)",
        "words": [
            ("This", 50, 100, 25, 12), ("is", 80, 100, 15, 12), ("to", 100, 100, 15, 12), ("certify", 120, 100, 40, 12),
            ("that", 165, 100, 25, 12), ("the", 195, 100, 20, 12), ("candidate", 220, 100, 55, 12), ("has", 280, 100, 20, 12),
            ("satisfied", 50, 125, 55, 12), ("all", 110, 125, 20, 12), ("statutory", 135, 125, 50, 12), ("criteria", 190, 125, 45, 12),
            ("for", 240, 125, 20, 12), ("the", 265, 125, 20, 12), ("2026", 290, 125, 30, 12), ("grant.", 325, 125, 35, 12)
        ],
        "ground_truth_order": (
            "This is to certify that the candidate has "
            "satisfied all statutory criteria for the 2026 grant."
        )
    }
]


def run_benchmark():
    print("=" * 80)
    print("DOCUREADY LOOP 13: SPATIAL READING ORDER & GENERALIZATION BENCHMARK")
    print("=" * 80)

    results = []

    total_base_inversions = 0
    total_l13_inversions = 0
    total_base_wer = 0.0
    total_l13_wer = 0.0
    total_base_cer = 0.0
    total_l13_cer = 0.0

    total_base_time = 0.0
    total_l13_time = 0.0

    for doc in BENCHMARK_CORPUS:
        doc_id = doc["id"]
        words_tuples = doc["words"]
        ground_truth = doc["ground_truth_order"]
        gt_words = ground_truth.split()

        raw_data = {
            "text": [w[0] for w in words_tuples],
            "conf": [95.0] * len(words_tuples),
            "left": [w[1] for w in words_tuples],
            "top": [w[2] for w in words_tuples],
            "width": [w[3] for w in words_tuples],
            "height": [w[4] for w in words_tuples]
        }

        # 1. Baseline: Naive Scanline Clustering (Loop 12 behavior)
        # Prepare words_meta
        words_meta = [
            {
                "word": w[0],
                "conf": 95.0,
                "box": [float(w[1]), float(w[2]), float(w[1] + w[3]), float(w[2] + w[4])],
                "x0": float(w[1]),
                "y0": float(w[2]),
                "h": float(w[4])
            }
            for w in words_tuples
        ]

        t0 = time.perf_counter()
        base_raw_lines = _cluster_words_raw(words_meta, y_tol=8.0)
        base_lines_text = [" ".join(w["word"] for w in l) for l in base_raw_lines]
        base_text = " ".join(base_lines_text)
        t_base = (time.perf_counter() - t0) * 1000.0

        base_cer, base_wer = calculate_cer_wer(base_text, ground_truth)
        base_inv = pairwise_inversion_rate(base_text.split(), gt_words)

        # 2. Loop 13: Column-Aware Spatial Reconstruction
        t1 = time.perf_counter()
        page_ocr = PageOCRData(raw_data, dpi=72)
        l13_lines_text = [l["text"] for l in page_ocr.lines]
        l13_text = " ".join(l13_lines_text)
        t_l13 = (time.perf_counter() - t1) * 1000.0

        l13_cer, l13_wer = calculate_cer_wer(l13_text, ground_truth)
        l13_inv = pairwise_inversion_rate(l13_text.split(), gt_words)

        total_base_inversions += base_inv
        total_l13_inversions += l13_inv
        total_base_wer += base_wer
        total_l13_wer += l13_wer
        total_base_cer += base_cer
        total_l13_cer += l13_cer
        total_base_time += t_base
        total_l13_time += t_l13

        doc_result = {
            "id": doc_id,
            "category": doc["category"],
            "description": doc["description"],
            "word_count": len(words_tuples),
            "baseline": {
                "text": base_text,
                "cer": base_cer,
                "wer": base_wer,
                "inversion_rate": base_inv,
                "latency_ms": round(t_base, 3)
            },
            "loop13": {
                "text": l13_text,
                "cer": l13_cer,
                "wer": l13_wer,
                "inversion_rate": l13_inv,
                "latency_ms": round(t_l13, 3)
            },
            "delta": {
                "wer_reduction": round(base_wer - l13_wer, 4),
                "cer_reduction": round(base_cer - l13_cer, 4),
                "inversion_reduction": round(base_inv - l13_inv, 4),
                "latency_overhead_ms": round(t_l13 - t_base, 3)
            }
        }
        results.append(doc_result)

        print(f"[{doc_id}] ({doc['category']})")
        print(f"  Baseline WER: {base_wer:.2%}, InvRate: {base_inv:.2%}, Latency: {t_base:.3f}ms")
        print(f"  Loop 13  WER: {l13_wer:.2%}, InvRate: {l13_inv:.2%}, Latency: {t_l13:.3f}ms")
        print(f"  Verdict: WER Delta: {-doc_result['delta']['wer_reduction']:.2%}, Overhead: {doc_result['delta']['latency_overhead_ms']:.3f}ms")
        print()

    n = len(BENCHMARK_CORPUS)
    summary = {
        "corpus_size": n,
        "mean_baseline_wer": round(total_base_wer / n, 4),
        "mean_loop13_wer": round(total_l13_wer / n, 4),
        "mean_baseline_cer": round(total_base_cer / n, 4),
        "mean_loop13_cer": round(total_l13_cer / n, 4),
        "mean_baseline_inversion_rate": round(total_base_inversions / n, 4),
        "mean_loop13_inversion_rate": round(total_l13_inversions / n, 4),
        "mean_baseline_latency_ms": round(total_base_time / n, 3),
        "mean_loop13_latency_ms": round(total_l13_time / n, 3),
        "mean_latency_overhead_ms": round((total_l13_time - total_base_time) / n, 3)
    }

    print("=" * 80)
    print("BENCHMARK SUMMARY")
    print(f"  Corpus Documents: {summary['corpus_size']}")
    print(f"  Baseline WER: {summary['mean_baseline_wer']:.2%} -> Loop 13 WER: {summary['mean_loop13_wer']:.2%}")
    print(f"  Baseline CER: {summary['mean_baseline_cer']:.2%} -> Loop 13 CER: {summary['mean_loop13_cer']:.2%}")
    print(f"  Baseline Inversion Rate: {summary['mean_baseline_inversion_rate']:.2%} -> Loop 13: {summary['mean_loop13_inversion_rate']:.2%}")
    print(f"  Average Spatial Overhead: {summary['mean_latency_overhead_ms']:.3f} ms")
    print("=" * 80)

    output_dir = ROOT / "research" / "loop13" / "results"
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / "loop13_benchmark_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "documents": results}, f, indent=2)

    print(f"Benchmark artifact written to {out_path}")
    return summary


if __name__ == "__main__":
    run_benchmark()
