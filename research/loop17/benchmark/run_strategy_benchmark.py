"""
Loop 17 Strategy Matrix Benchmark & Critical-Field Accuracy Evaluator
DocuReady Engineering Research

Runs the 10-strategy evaluation matrix across the full 20-document corpus (200 evaluations):
  - Primary Validation Cohort (14 documents)
  - Sealed Challenge Cohort (6 documents)
Strategies:
  A: English-only OCR
  B: Hindi-only OCR
  C: Odia-only OCR
  D: English + Hindi Compound
  E: English + Odia Compound
  F: Global Multilingual (eng+hin+ori)
  G: Loop 14 Whole-Page Script Routing
  H: Loop 15 Region-Aware Routing
  I: Loop 15 Region Routing + Fallback
  J: Loop 17 Optimized Adaptive Strategy Selector

Outputs:
  - research/loop17/results/loop17_strategy_benchmark_results.json
  - research/loop17/strategy_results.json
  - research/loop17/critical_field_results.json
  - research/loop17/failure_records.json
"""

from __future__ import annotations

import json
import math
import os
import re
import sys
import time
import tracemalloc
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

import fitz
import numpy as np
import pytesseract
from PIL import Image

from docuready.ingest.adaptive_ocr import execute_adaptive_ocr
from docuready.ingest.extractor import PageOCRData
from docuready.ingest.region_ocr import ocr_page_by_regions
from docuready.ingest.script_router import resolve_optimal_ocr_language
from docuready.ingest.tesseract_discovery import configure_pytesseract

CORPUS_DIR = ROOT / "research" / "loop17" / "corpus"
GT_DIR = ROOT / "research" / "loop17" / "ground_truth"
CF_DIR = ROOT / "research" / "loop17" / "critical_fields"
MANIFEST_PATH = ROOT / "research" / "loop17" / "dataset_manifest.json"
RESULTS_DIR = ROOT / "research" / "loop17" / "results"

configure_pytesseract()


def normalize_unicode(text: str) -> str:
    norm = unicodedata.normalize("NFC", text)
    norm = norm.replace("\u200c", "").replace("\u200d", "").replace("\ufeff", "")
    return " ".join(norm.split())


def compute_levenshtein(seq1: List[Any], seq2: List[Any]) -> int:
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
    norm_hyp = normalize_unicode(hypothesis)
    norm_ref = normalize_unicode(reference)

    if not norm_ref:
        return (0.0 if not norm_hyp else 1.0, 0.0 if not norm_hyp else 1.0)

    hyp_words = norm_hyp.split()
    ref_words = norm_ref.split()
    w_dist = compute_levenshtein(hyp_words, ref_words)
    wer = round(w_dist / max(1, len(ref_words)), 4)

    hyp_chars = list(norm_hyp)
    ref_chars = list(norm_ref)
    c_dist = compute_levenshtein(hyp_chars, ref_chars)
    cer = round(c_dist / max(1, len(ref_chars)), 4)

    return cer, wer


def compute_reading_order_inversion(lines: List[str], reference_lines: List[str]) -> float:
    if len(lines) < 2 or len(reference_lines) < 2:
        return 0.0

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


def evaluate_critical_fields(hyp_text: str, critical_fields: Dict[str, str]) -> Dict[str, Any]:
    """
    Evaluates exact match and character presence for structured critical fields.
    """
    if not critical_fields:
        return {"total_fields": 0, "exact_matches": 0, "match_rate": 1.0, "field_details": {}}

    norm_hyp = normalize_unicode(hyp_text).upper()
    total = len(critical_fields)
    matches = 0
    field_details = {}

    for f_name, f_val in critical_fields.items():
        norm_val = normalize_unicode(f_val).upper()
        # Direct exact substring match
        matched = norm_val in norm_hyp
        if not matched:
            # Check without spaces or dashes (common OCR artifact)
            clean_val = norm_val.replace(" ", "").replace("-", "").replace("/", "")
            clean_hyp = norm_hyp.replace(" ", "").replace("-", "").replace("/", "")
            matched = clean_val in clean_hyp

        if matched:
            matches += 1
        field_details[f_name] = {
            "expected": f_val,
            "matched": matched
        }

    return {
        "total_fields": total,
        "exact_matches": matches,
        "match_rate": round(matches / max(1, total), 4),
        "field_details": field_details
    }


def load_doc_image_and_meta(doc_id: str) -> Tuple[Image.Image, Optional[str], Optional[List[Dict[str, Any]]]]:
    pdf_path = CORPUS_DIR / f"{doc_id}.pdf"
    png_path = CORPUS_DIR / f"{doc_id}.png"

    if pdf_path.exists():
        doc = fitz.open(str(pdf_path))
        page = doc[0]
        pix = page.get_pixmap(dpi=200)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        native_text = page.get_text()
        native_blocks = page.get_text("blocks")
        blocks = [{"bbox": b[:4], "text": b[4]} for b in native_blocks] if native_blocks else None
        return img, native_text, blocks
    elif png_path.exists():
        img = Image.open(png_path).convert("RGB")
        return img, None, None
    else:
        raise FileNotFoundError(f"Neither {pdf_path} nor {png_path} found.")


def run_benchmark():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    samples = manifest["samples"]
    strategies = {
        "STRATEGY_A_ENG": "English-only OCR",
        "STRATEGY_B_HIN": "Hindi-only OCR",
        "STRATEGY_C_ORI": "Odia-only OCR",
        "STRATEGY_D_ENG_HIN": "English + Hindi compound",
        "STRATEGY_E_ENG_ORI": "English + Odia compound",
        "STRATEGY_F_GLOBAL_ALL": "Global English+Hindi+Odia",
        "STRATEGY_G_PAGE_ROUTING": "Loop 14 Whole-Page Script Routing",
        "STRATEGY_H_REGION_ROUTING": "Loop 15 Region-Aware Routing",
        "STRATEGY_I_REGION_FALLBACK": "Loop 15 Region Routing + Fallback",
        "STRATEGY_J_ADAPTIVE": "Loop 17 Optimized Adaptive Strategy Selector"
    }

    per_sample_results: Dict[str, Dict[str, Any]] = {}
    critical_field_evals: Dict[str, Dict[str, Any]] = {}
    failure_records: List[Dict[str, Any]] = []

    print(f"Beginning Loop 17 Strategy Benchmark: {len(samples)} documents across {len(strategies)} strategies = {len(samples)*len(strategies)} runs\n")

    for s_idx, sample in enumerate(samples, 1):
        s_id = sample["sample_id"]
        split = sample["split"]
        print(f"[{s_idx:02d}/{len(samples):02d}] Processing {s_id} ({split})...")

        img, native_text, native_blocks = load_doc_image_and_meta(s_id)
        gt_path = GT_DIR / f"{s_id}_gt.txt"
        gt_text = ""
        if gt_path.exists():
            with open(gt_path, "r", encoding="utf-8") as f:
                gt_text = f.read().strip()
        gt_lines = [l.strip() for l in gt_text.splitlines() if l.strip()]

        cf_path = CF_DIR / f"{s_id}_cf.json"
        crit_fields = {}
        if cf_path.exists():
            with open(cf_path, "r", encoding="utf-8") as f:
                crit_fields = json.load(f).get("critical_fields", {})

        per_sample_results[s_id] = {}
        critical_field_evals[s_id] = {}

        for strat_id, strat_name in strategies.items():
            tracemalloc.start()
            t0 = time.perf_counter()
            invocations = 1

            if strat_id == "STRATEGY_A_ENG":
                data = pytesseract.image_to_data(img, lang="eng", output_type=pytesseract.Output.DICT)
            elif strat_id == "STRATEGY_B_HIN":
                data = pytesseract.image_to_data(img, lang="hin", output_type=pytesseract.Output.DICT)
            elif strat_id == "STRATEGY_C_ORI":
                data = pytesseract.image_to_data(img, lang="ori", output_type=pytesseract.Output.DICT)
            elif strat_id == "STRATEGY_D_ENG_HIN":
                data = pytesseract.image_to_data(img, lang="eng+hin", output_type=pytesseract.Output.DICT)
            elif strat_id == "STRATEGY_E_ENG_ORI":
                data = pytesseract.image_to_data(img, lang="eng+ori", output_type=pytesseract.Output.DICT)
            elif strat_id == "STRATEGY_F_GLOBAL_ALL":
                data = pytesseract.image_to_data(img, lang="eng+hin+ori", output_type=pytesseract.Output.DICT)
            elif strat_id == "STRATEGY_G_PAGE_ROUTING":
                # Loop 14 whole-page routing
                page_lang = resolve_optimal_ocr_language(native_text=native_text, img=img, fallback_lang="eng")
                invocations = 1 if native_text else 2
                data = pytesseract.image_to_data(img, lang=page_lang, output_type=pytesseract.Output.DICT)
            elif strat_id == "STRATEGY_H_REGION_ROUTING":
                data = ocr_page_by_regions(img, dpi=200, native_blocks=native_blocks, enable_confidence_fallback=False)
                invocations = 2 if sample["sample_id"].startswith("DOC_MULTI") else 1
            elif strat_id == "STRATEGY_I_REGION_FALLBACK":
                data = ocr_page_by_regions(img, dpi=200, native_blocks=native_blocks, enable_confidence_fallback=True)
                invocations = 2 if sample["sample_id"].startswith("DOC_MULTI") else 1
            elif strat_id == "STRATEGY_J_ADAPTIVE":
                data, decision = execute_adaptive_ocr(img, dpi=200, native_text=native_text, native_blocks=native_blocks)
                invocations = decision.ocr_model_invocations

            lat_ms = (time.perf_counter() - t0) * 1000.0
            _, peak_mem = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            # Format words & lines
            words = [str(w).strip() for w, c in zip(data.get("text", []), data.get("conf", [])) if str(w).strip() and float(c) >= 0]
            hyp_text = " ".join(words)
            hyp_lines = [l for l in hyp_text.splitlines() if l.strip()]
            if not hyp_lines and hyp_text:
                hyp_lines = [hyp_text]

            cer, wer = calculate_metrics(hyp_text, gt_text)
            inversion_rate = compute_reading_order_inversion(hyp_lines, gt_lines)

            # Evaluate critical fields
            cf_result = evaluate_critical_fields(hyp_text, crit_fields)

            per_sample_results[s_id][strat_id] = {
                "cer": cer,
                "wer": wer,
                "inversion_rate": inversion_rate,
                "latency_ms": round(lat_ms, 2),
                "peak_ram_mb": round(peak_mem / (1024 * 1024), 2),
                "ocr_invocations": invocations,
                "critical_field_match_rate": cf_result["match_rate"]
            }

            if strat_id == "STRATEGY_J_ADAPTIVE":
                critical_field_evals[s_id] = cf_result

            if cer > 0.40 and strat_id in ("STRATEGY_H_REGION_ROUTING", "STRATEGY_J_ADAPTIVE"):
                failure_records.append({
                    "sample_id": s_id,
                    "strategy": strat_id,
                    "cer": cer,
                    "wer": wer,
                    "reason": "Elevated character error rate on complex/degraded layout"
                })

    # Summary Statistics Aggregation
    def compute_cohort_summary(doc_list: List[str]) -> Dict[str, Any]:
        summary = {}
        for strat in strategies.keys():
            cers = [per_sample_results[d][strat]["cer"] for d in doc_list]
            wers = [per_sample_results[d][strat]["wer"] for d in doc_list]
            invs = [per_sample_results[d][strat]["inversion_rate"] for d in doc_list]
            lats = [per_sample_results[d][strat]["latency_ms"] for d in doc_list]
            invocs = [per_sample_results[d][strat]["ocr_invocations"] for d in doc_list]
            cfrates = [per_sample_results[d][strat]["critical_field_match_rate"] for d in doc_list]

            lats_sorted = sorted(lats)
            p95_idx = min(len(lats_sorted) - 1, int(math.ceil(0.95 * len(lats_sorted))) - 1)

            summary[strat] = {
                "mean_cer": round(sum(cers) / len(cers), 4),
                "mean_wer": round(sum(wers) / len(wers), 4),
                "mean_inversion_rate": round(sum(invs) / len(invs), 2),
                "mean_latency_ms": round(sum(lats) / len(lats), 2),
                "median_latency_ms": round(lats_sorted[len(lats_sorted) // 2], 2),
                "p95_latency_ms": round(lats_sorted[p95_idx], 2),
                "mean_invocations": round(sum(invocs) / len(invocs), 2),
                "mean_critical_field_match_rate": round(sum(cfrates) / len(cfrates), 4)
            }
        return summary

    all_ids = [s["sample_id"] for s in samples]
    val_ids = [s["sample_id"] for s in samples if s["split"] == "PRIMARY_VALIDATION"]
    chal_ids = [s["sample_id"] for s in samples if s["split"] == "SEALED_CHALLENGE"]

    final_payload = {
        "metadata": {
            "loop": "17",
            "date": "2026-11-22",
            "total_documents": len(samples),
            "strategies": strategies
        },
        "summary_overall": compute_cohort_summary(all_ids),
        "summary_validation": compute_cohort_summary(val_ids),
        "summary_challenge": compute_cohort_summary(chal_ids),
        "per_sample_results": per_sample_results
    }

    with open(ROOT / "research" / "loop17" / "strategy_results.json", "w", encoding="utf-8") as f:
        json.dump(final_payload, f, indent=2)

    with open(ROOT / "research" / "loop17" / "results" / "loop17_strategy_benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(final_payload, f, indent=2)

    with open(ROOT / "research" / "loop17" / "critical_field_results.json", "w", encoding="utf-8") as f:
        json.dump(critical_field_evals, f, indent=2)

    with open(ROOT / "research" / "loop17" / "failure_records.json", "w", encoding="utf-8") as f:
        json.dump(failure_records, f, indent=2)

    print("\n=== BENCHMARK COMPLETED SUCCESSFULLY ===")
    print(f"Overall Results written to research/loop17/strategy_results.json")
    print(f"Critical Field Results written to research/loop17/critical_field_results.json")


if __name__ == "__main__":
    run_benchmark()
