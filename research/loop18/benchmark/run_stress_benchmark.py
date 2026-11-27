"""
Loop 18 - Adversarial Critical-Field Stress Benchmark
DocuReady Engineering Research

Tests DocuReady's Adaptive OCR and baseline strategies on 4 controlled adversarial fixtures:
  1. STRESS_01_SIMILAR_DIGIT_CONFUSION (0/O, 8/B, 1/I, 5/S)
  2. STRESS_02_FAINT_RUBBER_STAMP_OVERLAY (translucent stamp over numeric fields)
  3. STRESS_03_MULTICOLUMN_EMBEDDED_AMOUNTS (dual-column ledger with embedded amounts)
  4. STRESS_04_SKEW_LOW_CONTRAST (2.8 degree tilt, 40% contrast reduction)

Outputs results to research/loop18/results/stress_benchmark_results.json
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pytesseract
from PIL import Image

from docuready.ingest.extractor import PageOCRData
from docuready.ingest.adaptive_ocr import execute_adaptive_ocr

ROOT = Path(__file__).resolve().parents[3]
STRESS_DIR = ROOT / "research" / "loop18" / "stress_fixtures"
RESULTS_DIR = ROOT / "research" / "loop18" / "results"


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


def evaluate_stress_fields(hyp_text: str, critical_fields: Dict[str, str]) -> Dict[str, Any]:
    norm_hyp = hyp_text.upper()
    total = len(critical_fields)
    exact_matches = 0
    numeric_matches = 0
    field_details = {}

    for f_name, expected_val in critical_fields.items():
        exp_norm = expected_val.upper()
        # Exact match
        exact = exp_norm in norm_hyp
        if not exact:
            clean_exp = exp_norm.replace(" ", "").replace("-", "").replace("/", "")
            clean_hyp = norm_hyp.replace(" ", "").replace("-", "").replace("/", "")
            exact = clean_exp in clean_hyp

        # Best local Levenshtein distance
        val_len = len(exp_norm)
        min_dist = val_len
        for i in range(0, max(1, len(norm_hyp) - val_len + 1)):
            sub = norm_hyp[i:i + val_len]
            d = compute_levenshtein(list(exp_norm), list(sub))
            if d < min_dist:
                min_dist = d
            if min_dist == 0:
                break
        f_cer = round(min_dist / max(1, val_len), 4)

        # Numeric match
        val_digits = "".join(filter(str.isdigit, exp_norm))
        num_match = False
        if val_digits:
            hyp_digits = "".join(filter(str.isdigit, norm_hyp))
            num_match = val_digits in hyp_digits
            if num_match:
                numeric_matches += 1

        if exact:
            exact_matches += 1

        field_details[f_name] = {
            "expected": expected_val,
            "exact_matched": exact,
            "numeric_matched": num_match if val_digits else None,
            "field_cer": f_cer
        }

    return {
        "total_fields": total,
        "exact_matches": exact_matches,
        "match_rate": round(exact_matches / max(1, total), 4),
        "numeric_matches": numeric_matches,
        "field_details": field_details
    }


def run_stress_suite():
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    fixtures = [
        "STRESS_01_SIMILAR_DIGIT_CONFUSION",
        "STRESS_02_FAINT_RUBBER_STAMP_OVERLAY",
        "STRESS_03_MULTICOLUMN_EMBEDDED_AMOUNTS",
        "STRESS_04_SKEW_LOW_CONTRAST"
    ]

    results = {}
    print("Executing Adversarial Critical-Field Stress Suite...")

    for f_name in fixtures:
        img_path = STRESS_DIR / f"{f_name}.png"
        gt_path = STRESS_DIR / f"{f_name}_gt.txt"
        cf_path = STRESS_DIR / f"{f_name}_cf.json"

        img = Image.open(img_path).convert("RGB")
        with open(gt_path, "r", encoding="utf-8") as f:
            gt_text = f.read()
        with open(cf_path, "r", encoding="utf-8") as f:
            cf_data = json.load(f).get("critical_fields", {})

        print(f"\nEvaluating fixture: {f_name}")

        # Evaluate Adaptive OCR
        t0 = time.perf_counter()
        data, decision = execute_adaptive_ocr(img, dpi=200)
        lat_ms = (time.perf_counter() - t0) * 1000.0

        ocr_obj = PageOCRData(data, dpi=200)
        reconstructed_lines = [l["text"].strip() for l in ocr_obj.lines if l.get("text", "").strip()]
        hyp_text = "\n".join(reconstructed_lines)

        c_dist = compute_levenshtein(list(hyp_text), list(gt_text))
        cer = round(c_dist / max(1, len(gt_text)), 4)

        cf_eval = evaluate_stress_fields(hyp_text, cf_data)

        results[f_name] = {
            "strategy": decision.selected_strategy,
            "language": decision.selected_lang,
            "latency_ms": round(lat_ms, 2),
            "invocations": decision.ocr_model_invocations,
            "cer": cer,
            "critical_fields_eval": cf_eval,
            "extracted_lines": reconstructed_lines[:5]
        }

        print(f"  Selected: {decision.selected_strategy} ({decision.selected_lang})")
        print(f"  CER: {cer*100:.2f}% | Latency: {lat_ms:.1f} ms")
        print(f"  Critical Fields Matched: {cf_eval['exact_matches']}/{cf_eval['total_fields']} ({cf_eval['match_rate']*100:.1f}%)")
        for k, v in cf_eval["field_details"].items():
            status = "PASS" if v["exact_matched"] else "FAIL"
            print(f"    - {k} ({v['expected']}): {status} (CER: {v['field_cer']*100:.1f}%)")

    out_path = RESULTS_DIR / "stress_benchmark_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\nStress suite completed. Results written to {out_path}")


if __name__ == "__main__":
    run_stress_suite()
