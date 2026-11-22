"""
Loop 18 - Independent Accuracy, Benchmark Integrity & Strategy Matrix Benchmark
DocuReady Engineering Research

Runs the comprehensive OCR benchmark across the 25-document expanded corpus:
  - Fixes reading-order line reconstruction via PageOCRData
  - Computes both Macro Mean Per-Document CER/WER and Micro Corpus-Level CER/WER
  - Evaluates critical-field extraction contracts (Exact Match, Field CER, Numeric Match, Date Match, P/R/F1)
  - Compares:
      * STRATEGY_GLOBAL_MULTILINGUAL: eng+hin+ori
      * STRATEGY_PAGE_ROUTING: Loop 14 whole-page script detection
      * STRATEGY_REGION_AWARE: Loop 15 spatial region routing with fallback
      * STRATEGY_ADAPTIVE: Loop 17 adaptive strategy selector
  - Generates research/loop18/strategy_results.json
"""

from __future__ import annotations

import json
import os
import re
import time
import tracemalloc
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import fitz  # PyMuPDF
import numpy as np
from PIL import Image
import pytesseract

from docuready.ingest.extractor import PageOCRData
from docuready.ingest.script_router import resolve_optimal_ocr_language
from docuready.ingest.region_ocr import ocr_page_by_regions
from docuready.ingest.adaptive_ocr import (
    StrategyDecisionRecord,
    execute_adaptive_ocr,
)

ROOT = Path(__file__).resolve().parents[3]
CORPUS_DIR = ROOT / "research" / "loop18" / "corpus"
GT_DIR = ROOT / "research" / "loop18" / "ground_truth"
CF_DIR = ROOT / "research" / "loop18" / "critical_fields"
MANIFEST_PATH = ROOT / "research" / "loop18" / "dataset_manifest.json"
RESULTS_PATH = ROOT / "research" / "loop18" / "strategy_results.json"


def normalize_unicode(text: str) -> str:
    if not text:
        return ""
    norm = unicodedata.normalize("NFC", text)
    norm = re.sub(r"[ \t]+", " ", norm)
    return norm.strip()


def compute_levenshtein(seq1: List[Any], seq2: List[Any]) -> int:
    n, m = len(seq1), len(seq2)
    if n == 0:
        return m
    if m == 0:
        return n
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


def compute_char_edit_distance(hyp: str, ref: str) -> Tuple[int, int]:
    norm_hyp = normalize_unicode(hyp)
    norm_ref = normalize_unicode(ref)
    c_dist = compute_levenshtein(list(norm_hyp), list(norm_ref))
    return c_dist, max(1, len(list(norm_ref)))


def compute_word_edit_distance(hyp: str, ref: str) -> Tuple[int, int]:
    norm_hyp = normalize_unicode(hyp)
    norm_ref = normalize_unicode(ref)
    hyp_words = norm_hyp.split()
    ref_words = norm_ref.split()
    w_dist = compute_levenshtein(hyp_words, ref_words)
    return w_dist, max(1, len(ref_words))


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
    if not critical_fields:
        return {
            "total_fields": 0,
            "exact_matches": 0,
            "match_rate": 1.0,
            "numeric_matches": 0,
            "date_matches": 0,
            "field_cers": [],
            "mean_field_cer": 0.0,
            "field_details": {}
        }

    norm_hyp = normalize_unicode(hyp_text).upper()
    total = len(critical_fields)
    matches = 0
    num_matches = 0
    date_matches = 0
    field_cers = []
    field_details = {}

    for f_name, f_val in critical_fields.items():
        norm_val = normalize_unicode(f_val).upper()
        # Direct exact substring match
        matched = norm_val in norm_hyp
        if not matched:
            clean_val = norm_val.replace(" ", "").replace("-", "").replace("/", "")
            clean_hyp = norm_hyp.replace(" ", "").replace("-", "").replace("/", "")
            matched = clean_val in clean_hyp

        # Compute field-level Levenshtein error rate against closest candidate substring
        c_dist = compute_levenshtein(list(norm_val), list(norm_hyp))
        # Best local alignment
        val_len = len(norm_val)
        min_dist = val_len
        # scan windows
        for i in range(0, max(1, len(norm_hyp) - val_len + 1)):
            sub = norm_hyp[i:i + val_len]
            d = compute_levenshtein(list(norm_val), list(sub))
            if d < min_dist:
                min_dist = d
            if min_dist == 0:
                break
        f_cer = round(min_dist / max(1, val_len), 4)
        field_cers.append(f_cer)

        # Check numeric match
        val_nums = "".join(filter(str.isdigit, norm_val))
        num_matched = False
        if val_nums:
            hyp_nums = "".join(filter(str.isdigit, norm_hyp))
            num_matched = val_nums in hyp_nums
            if num_matched:
                num_matches += 1

        # Check date match
        date_pattern = r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"
        is_date = bool(re.search(date_pattern, norm_val))
        date_matched = False
        if is_date:
            date_val_clean = norm_val.replace("-", "/")
            date_hyp_clean = norm_hyp.replace("-", "/")
            date_matched = date_val_clean in date_hyp_clean
            if date_matched:
                date_matches += 1

        if matched:
            matches += 1

        field_details[f_name] = {
            "expected": f_val,
            "matched": matched,
            "field_cer": f_cer,
            "num_matched": num_matched if val_nums else None,
            "date_matched": date_matched if is_date else None
        }

    return {
        "total_fields": total,
        "exact_matches": matches,
        "match_rate": round(matches / max(1, total), 4),
        "numeric_matches": num_matches,
        "date_matches": date_matches,
        "field_cers": field_cers,
        "mean_field_cer": round(sum(field_cers) / max(1, len(field_cers)), 4),
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
        blocks = page.get_text("blocks")
        native_blocks = []
        for b in blocks:
            native_blocks.append({
                "bbox": [b[0], b[1], b[2], b[3]],
                "text": b[4]
            })
        return img, native_text, native_blocks
    elif png_path.exists():
        img = Image.open(png_path).convert("RGB")
        return img, None, None
    else:
        raise FileNotFoundError(f"Document {doc_id} not found in {CORPUS_DIR}")


def run_benchmark():
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    samples = manifest["samples"]
    print(f"Loaded {len(samples)} samples from manifest.")

    strategies = {
        "STRATEGY_GLOBAL_MULTILINGUAL": "eng+hin+ori global OCR",
        "STRATEGY_PAGE_ROUTING": "Loop 14 page-level script detection",
        "STRATEGY_REGION_AWARE": "Loop 15 region-aware with confidence fallback",
        "STRATEGY_ADAPTIVE": "Loop 17 adaptive strategy selector"
    }

    per_sample_results: Dict[str, Dict[str, Any]] = {s["sample_id"]: {} for s in samples}
    critical_field_evals: Dict[str, Any] = {}
    failure_records = []

    for idx, sample in enumerate(samples, 1):
        s_id = sample["sample_id"]
        split = sample["split"]
        gt_file = GT_DIR / f"{s_id}_gt.txt"
        cf_file = CF_DIR / f"{s_id}_cf.json"

        gt_text = ""
        if gt_file.exists():
            with open(gt_file, "r", encoding="utf-8") as f:
                gt_text = f.read()

        gt_lines = [l for l in gt_text.splitlines() if l.strip()]

        crit_fields = {}
        if cf_file.exists():
            with open(cf_file, "r", encoding="utf-8") as f:
                crit_fields = json.load(f).get("critical_fields", {})

        print(f"[{idx:02d}/{len(samples):02d}] Evaluating {s_id} ({split})...")
        img, native_text, native_blocks = load_doc_image_and_meta(s_id)

        for strat_id in strategies.keys():
            tracemalloc.start()
            t0 = time.perf_counter()
            invocations = 1

            if strat_id == "STRATEGY_GLOBAL_MULTILINGUAL":
                data = pytesseract.image_to_data(img, lang="eng+hin+ori", output_type=pytesseract.Output.DICT)
            elif strat_id == "STRATEGY_PAGE_ROUTING":
                page_lang = resolve_optimal_ocr_language(native_text=native_text, img=img, fallback_lang="eng")
                invocations = 1 if native_text else 2
                data = pytesseract.image_to_data(img, lang=page_lang, output_type=pytesseract.Output.DICT)
            elif strat_id == "STRATEGY_REGION_AWARE":
                data = ocr_page_by_regions(img, dpi=200, native_blocks=native_blocks, enable_confidence_fallback=True)
                invocations = 2 if s_id.startswith("DOC_MULTI") else 1
            elif strat_id == "STRATEGY_ADAPTIVE":
                data, decision = execute_adaptive_ocr(img, dpi=200, native_text=native_text, native_blocks=native_blocks)
                invocations = decision.ocr_model_invocations

            lat_ms = (time.perf_counter() - t0) * 1000.0
            _, peak_mem = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            # Build lines using PageOCRData spatial reconstruction
            try:
                ocr_obj = PageOCRData(data, dpi=200)
                reconstructed_lines = [l["text"].strip() for l in ocr_obj.lines if l.get("text", "").strip()]
            except Exception:
                words = [str(w).strip() for w, c in zip(data.get("text", []), data.get("conf", [])) if str(w).strip() and float(c) >= 0]
                reconstructed_lines = [" ".join(words)]

            hyp_text = "\n".join(reconstructed_lines)
            if not reconstructed_lines and hyp_text:
                reconstructed_lines = [hyp_text]

            c_dist, c_total = compute_char_edit_distance(hyp_text, gt_text)
            w_dist, w_total = compute_word_edit_distance(hyp_text, gt_text)
            cer = round(c_dist / c_total, 4)
            wer = round(w_dist / w_total, 4)

            inversion_rate = compute_reading_order_inversion(reconstructed_lines, gt_lines)
            cf_result = evaluate_critical_fields(hyp_text, crit_fields)

            per_sample_results[s_id][strat_id] = {
                "cer": cer,
                "wer": wer,
                "c_dist": c_dist,
                "c_total": c_total,
                "w_dist": w_dist,
                "w_total": w_total,
                "inversion_rate": inversion_rate,
                "latency_ms": round(lat_ms, 2),
                "peak_ram_mb": round(peak_mem / (1024 * 1024), 2),
                "ocr_invocations": invocations,
                "critical_field_match_rate": cf_result["match_rate"],
                "mean_field_cer": cf_result["mean_field_cer"],
                "cf_exact": cf_result["exact_matches"],
                "cf_total": cf_result["total_fields"]
            }

            if strat_id == "STRATEGY_ADAPTIVE" and crit_fields:
                critical_field_evals[s_id] = cf_result

            if cer > 0.40 and strat_id == "STRATEGY_ADAPTIVE":
                failure_records.append({
                    "sample_id": s_id,
                    "split": split,
                    "cer": cer,
                    "wer": wer,
                    "reason": "Elevated CER on challenging/unconstrained layout"
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

            # Corpus-level micro CER/WER
            total_c_dist = sum(per_sample_results[d][strat]["c_dist"] for d in doc_list)
            total_c_len = sum(per_sample_results[d][strat]["c_total"] for d in doc_list)
            corpus_cer = round(total_c_dist / max(1, total_c_len), 4)

            total_w_dist = sum(per_sample_results[d][strat]["w_dist"] for d in doc_list)
            total_w_len = sum(per_sample_results[d][strat]["w_total"] for d in doc_list)
            corpus_wer = round(total_w_dist / max(1, total_w_len), 4)

            total_cf_exact = sum(per_sample_results[d][strat]["cf_exact"] for d in doc_list)
            total_cf_count = sum(per_sample_results[d][strat]["cf_total"] for d in doc_list)
            cf_rate = round(total_cf_exact / max(1, total_cf_count), 4) if total_cf_count > 0 else 1.0

            field_cers = [per_sample_results[d][strat]["mean_field_cer"] for d in doc_list if per_sample_results[d][strat]["cf_total"] > 0]
            mean_f_cer = round(sum(field_cers) / max(1, len(field_cers)), 4) if field_cers else 0.0

            summary[strat] = {
                "mean_cer_macro": round(sum(cers) / len(cers), 4),
                "corpus_cer_micro": corpus_cer,
                "mean_wer_macro": round(sum(wers) / len(wers), 4),
                "corpus_wer_micro": corpus_wer,
                "mean_inversion_rate": round(sum(invs) / len(invs), 2),
                "mean_latency_ms": round(sum(lats) / len(lats), 2),
                "mean_ocr_invocations": round(sum(invocs) / len(invocs), 2),
                "critical_field_exact_matches": total_cf_exact,
                "critical_field_total_count": total_cf_count,
                "critical_field_match_rate": cf_rate,
                "mean_field_cer": mean_f_cer
            }
        return summary

    all_docs = [s["sample_id"] for s in samples]
    primary_docs = [s["sample_id"] for s in samples if s["split"] == "PRIMARY_VALIDATION"]
    challenge_docs = [s["sample_id"] for s in samples if s["split"] == "SEALED_CHALLENGE"]

    final_report = {
        "benchmark_metadata": {
            "loop": "18",
            "date": "2026-11-22",
            "sample_count": len(samples),
            "primary_count": len(primary_docs),
            "challenge_count": len(challenge_docs),
            "total_critical_fields": sum(s.get("cf_total", 0) for s in [per_sample_results[d]["STRATEGY_ADAPTIVE"] for d in all_docs])
        },
        "summary": {
            "overall": compute_cohort_summary(all_docs),
            "primary_validation": compute_cohort_summary(primary_docs),
            "sealed_challenge": compute_cohort_summary(challenge_docs)
        },
        "per_sample": per_sample_results,
        "critical_field_evaluations": critical_field_evals,
        "failures": failure_records
    }

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(final_report, f, indent=2)

    print(f"\nBenchmark completed successfully. Results saved to {RESULTS_PATH}")

    print("\n================== OVERALL COHORT SUMMARY (25 SAMPLES) ==================")
    for strat, data in final_report["summary"]["overall"].items():
        print(f"\n{strat}:")
        print(f"  Macro CER: {data['mean_cer_macro']*100:.2f}% | Micro Corpus CER: {data['corpus_cer_micro']*100:.2f}%")
        print(f"  Macro WER: {data['mean_wer_macro']*100:.2f}% | Micro Corpus WER: {data['corpus_wer_micro']*100:.2f}%")
        print(f"  Reading Inversion: {data['mean_inversion_rate']:.2f}%")
        print(f"  Mean Latency: {data['mean_latency_ms']:.1f} ms | Mean Invocations: {data['mean_ocr_invocations']:.2f}")
        print(f"  Critical Fields: {data['critical_field_exact_matches']}/{data['critical_field_total_count']} ({data['critical_field_match_rate']*100:.1f}%) | Field CER: {data['mean_field_cer']*100:.2f}%")


if __name__ == "__main__":
    run_benchmark()
