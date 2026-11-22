"""
Loop 15 - Region-Aware Multilingual OCR Benchmark Suite
DocuReady Engineering Research

Evaluates 9 configurations across all Loop 15 corpus documents:
  - Config A: 'eng' only
  - Config B: 'hin' only
  - Config C: 'ori' only
  - Config D: 'eng+hin'
  - Config E: 'eng+ori'
  - Config F: 'eng+hin+ori'
  - Config G: Page-level routing (Loop 14)
  - Config H: Region-level routing (Loop 15)
  - Config I: Region-level routing with confidence fallback (Loop 15 Enhanced)

Computes Character Error Rate (CER), Word Error Rate (WER), Reading Order Inversion Rate,
and Processing Latency. Outputs research/loop15/results/loop15_benchmark_results.json.
"""

from __future__ import annotations

import json
import os
import sys
import time
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import pytesseract
from PIL import Image

from docuready.ingest.extractor import PageOCRData
from docuready.ingest.region_ocr import ocr_page_by_regions
from docuready.ingest.script_router import detect_unicode_script, resolve_optimal_ocr_language
from docuready.ingest.tesseract_discovery import configure_pytesseract

CORPUS_DIR = ROOT / "research" / "loop15" / "corpus"
GT_DIR = ROOT / "research" / "loop15" / "ground_truth"
RESULTS_DIR = ROOT / "research" / "loop15" / "results"


def normalize_unicode(text: str) -> str:
    """Applies Unicode NFC canonical normalization and whitespace normalization."""
    if not text:
        return ""
    norm = unicodedata.normalize("NFC", text)
    norm = norm.replace("\u200c", "").replace("\u200d", "").replace("\ufeff", "")
    return " ".join(norm.split())


def compute_levenshtein(seq1: List[Any], seq2: List[Any]) -> int:
    """Computes Levenshtein edit distance between two sequences."""
    n, m = len(seq1), len(seq2)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if seq1[i - 1] == seq2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1]
            else:
                dp[i][j] = 1 + min(dp[i - 1][j], dp[i][j - 1], dp[i - 1][j - 1])
    return dp[n][m]


def calculate_metrics(hypothesis: str, reference: str) -> Tuple[float, float]:
    """Computes CER and WER."""
    norm_hyp = normalize_unicode(hypothesis)
    norm_ref = normalize_unicode(reference)

    if not norm_ref:
        return (0.0 if not norm_hyp else 1.0, 0.0 if not norm_hyp else 1.0)

    # Word Error Rate
    hyp_words = norm_hyp.split()
    ref_words = norm_ref.split()
    w_dist = compute_levenshtein(hyp_words, ref_words)
    wer = round(w_dist / max(1, len(ref_words)), 4)

    # Character Error Rate
    hyp_chars = list(norm_hyp)
    ref_chars = list(norm_ref)
    c_dist = compute_levenshtein(hyp_chars, ref_chars)
    cer = round(c_dist / max(1, len(ref_chars)), 4)

    return cer, wer


def compute_reading_order_inversion(lines: List[str], reference_lines: List[str]) -> float:
    """Estimates reading order inversion rate between hypothesis lines and reference."""
    if len(lines) < 2 or len(reference_lines) < 2:
        return 0.0

    # Map words to their first appearance line index in reference
    ref_word_order = {}
    for l_idx, ref_line in enumerate(reference_lines):
        for w in ref_line.split():
            clean_w = w.lower().strip(".,:;()-")
            if clean_w and clean_w not in ref_word_order:
                ref_word_order[clean_w] = l_idx

    hyp_line_ranks = []
    for line in lines:
        ranks = [ref_word_order[w.lower().strip(".,:;()-")] for w in line.split() if w.lower().strip(".,:;()-") in ref_word_order]
        if ranks:
            hyp_line_ranks.append(sum(ranks) / len(ranks))

    if len(hyp_line_ranks) < 2:
        return 0.0

    inversions = 0
    total_pairs = 0
    for i in range(len(hyp_line_ranks)):
        for j in range(i + 1, len(hyp_line_ranks)):
            total_pairs += 1
            if hyp_line_ranks[i] > hyp_line_ranks[j]:
                inversions += 1

    return round((inversions / max(1, total_pairs)) * 100.0, 2)


def run_benchmark():
    configure_pytesseract()
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 85)
    print("DOCUREADY LOOP 15: REGION-AWARE MULTILINGUAL OCR BENCHMARK")
    print("=" * 85)

    test_docs = [
        "DOC_MULTI_01_TRI_SCRIPT_GAZETTE",
        "DOC_MULTI_02_BILINGUAL_COLUMNS_HIN_ENG",
        "DOC_MULTI_03_BILINGUAL_COLUMNS_ORI_ENG",
        "DOC_MULTI_04_MARKSHEET_INDIC_GRID",
        "DOC_MIX_01_HIN_ENG_SCHOLARSHIP",
        "DOC_MIX_02_ORI_ENG_SCHOLARSHIP",
        "DOC_HIN_01_ADMIN_CIRCULAR",
        "DOC_ORI_01_ADMIN_CIRCULAR",
        "DOC_CTRL_01_ENGLISH_CERTIFICATE",
        "DOC_DEG_01_MULTI_SCRIPT_SKEWED",
    ]

    configs = {
        "CONFIG_A_ENG": {"mode": "fixed", "lang": "eng", "desc": "Tesseract eng only"},
        "CONFIG_B_HIN": {"mode": "fixed", "lang": "hin", "desc": "Tesseract hin only"},
        "CONFIG_C_ORI": {"mode": "fixed", "lang": "ori", "desc": "Tesseract ori only"},
        "CONFIG_D_ENG_HIN": {"mode": "fixed", "lang": "eng+hin", "desc": "Tesseract eng+hin"},
        "CONFIG_E_ENG_ORI": {"mode": "fixed", "lang": "eng+ori", "desc": "Tesseract eng+ori"},
        "CONFIG_F_ENG_HIN_ORI": {"mode": "fixed", "lang": "eng+hin+ori", "desc": "Tesseract eng+hin+ori"},
        "CONFIG_G_PAGE_ROUTING": {"mode": "page_routing", "desc": "Loop 14 Whole-Page Script Routing"},
        "CONFIG_H_REGION_ROUTING": {"mode": "region_routing", "fallback": False, "desc": "Loop 15 Region-Aware Routing"},
        "CONFIG_I_REGION_FALLBACK": {"mode": "region_routing", "fallback": True, "desc": "Loop 15 Region Routing + Fallback"},
    }

    benchmark_data: Dict[str, Any] = {
        "configurations": {k: v["desc"] for k, v in configs.items()},
        "results_by_doc": {},
        "summary": {}
    }

    summary_metrics = {cfg_key: {"cer": [], "wer": [], "inversions": [], "latency": []} for cfg_key in configs}

    for doc_id in test_docs:
        img_path = CORPUS_DIR / f"{doc_id}.png"
        gt_path = GT_DIR / f"{doc_id}_gt.txt"

        if not img_path.exists() or not gt_path.exists():
            continue

        with open(gt_path, "r", encoding="utf-8") as f:
            gt_text = f.read().strip()
        gt_lines = [l.strip() for l in gt_text.splitlines() if l.strip()]

        img = Image.open(img_path)
        print(f"\n[+] Testing {doc_id} ({img.width}x{img.height})")
        doc_results = {}

        for cfg_id, cfg_spec in configs.items():
            t0 = time.perf_counter()
            mode = cfg_spec["mode"]

            if mode == "fixed":
                lang = cfg_spec["lang"]
                try:
                    data = pytesseract.image_to_data(img, lang=lang, output_type=pytesseract.Output.DICT, timeout=15)
                except Exception:
                    data = {"text": [], "conf": [], "left": [], "top": [], "width": [], "height": []}
                ocr_obj = PageOCRData(data, dpi=200)

            elif mode == "page_routing":
                # Loop 14: detect script on whole document or fast thumbnail
                page_lang = resolve_optimal_ocr_language(img=img, fallback_lang="eng")
                try:
                    data = pytesseract.image_to_data(img, lang=page_lang, output_type=pytesseract.Output.DICT, timeout=15)
                except Exception:
                    data = {"text": [], "conf": [], "left": [], "top": [], "width": [], "height": []}
                ocr_obj = PageOCRData(data, dpi=200)

            elif mode == "region_routing":
                # Loop 15: Region-aware segmentation and targeted language routing
                use_fallback = cfg_spec.get("fallback", True)
                data = ocr_page_by_regions(img, dpi=200, enable_confidence_fallback=use_fallback)
                ocr_obj = PageOCRData(data, dpi=200)

            elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)

            hyp_lines = [l["text"] for l in ocr_obj.lines]
            hyp_text = "\n".join(hyp_lines)

            cer, wer = calculate_metrics(hyp_text, gt_text)
            inversion_rate = compute_reading_order_inversion(hyp_lines, gt_lines)

            doc_results[cfg_id] = {
                "cer": cer,
                "wer": wer,
                "inversion_rate": inversion_rate,
                "latency_ms": elapsed_ms,
                "line_count": len(hyp_lines),
            }

            summary_metrics[cfg_id]["cer"].append(cer)
            summary_metrics[cfg_id]["wer"].append(wer)
            summary_metrics[cfg_id]["inversions"].append(inversion_rate)
            summary_metrics[cfg_id]["latency"].append(elapsed_ms)

            print(f"    {cfg_id:25} -> CER: {cer*100:5.2f}% | WER: {wer*100:5.2f}% | Inv: {inversion_rate:4.1f}% | Latency: {elapsed_ms:6.1f} ms")

        benchmark_data["results_by_doc"][doc_id] = doc_results

    # Compute macro-averages
    for cfg_id, m in summary_metrics.items():
        if m["cer"]:
            benchmark_data["summary"][cfg_id] = {
                "mean_cer": round(sum(m["cer"]) / len(m["cer"]), 4),
                "mean_wer": round(sum(m["wer"]) / len(m["wer"]), 4),
                "mean_inversion_rate": round(sum(m["inversions"]) / len(m["inversions"]), 2),
                "mean_latency_ms": round(sum(m["latency"]) / len(m["latency"]), 2),
            }

    out_file = RESULTS_DIR / "loop15_benchmark_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(benchmark_data, f, indent=2)

    print("\n" + "=" * 85)
    print("BENCHMARK SUMMARY ACROSS 10 TEST DOCUMENTS")
    print("=" * 85)
    print(f"{'Configuration':<28} | {'Mean CER':<10} | {'Mean WER':<10} | {'Mean Inv Rate':<14} | {'Mean Latency':<12}")
    print("-" * 85)
    for cfg_id, s in benchmark_data["summary"].items():
        print(f"{cfg_id:<28} | {s['mean_cer']*100:6.2f}%    | {s['mean_wer']*100:6.2f}%    | {s['mean_inversion_rate']:5.2f}%        | {s['mean_latency_ms']:6.1f} ms")

    print(f"\nFull results saved to {out_file}")
    return benchmark_data


if __name__ == "__main__":
    run_benchmark()
