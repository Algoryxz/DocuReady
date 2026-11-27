"""
Loop 11 Experiment: Multilingual OCR Generalization (Hindi & Odia)
DocuReady - Research Loop 11

Hypothesis: Passing lang="eng+hin+ori" to Tesseract utilizing the bundled neural traineddata
models will recover Hindi and Odia script characters that are otherwise completely deleted
or substituted when defaulting to 'eng'.

Evaluates Control (eng) vs Treatment (eng+hin+ori) across accuracy and latency metrics.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import PIL.Image
import pymupdf
import pytesseract

REPO_ROOT = Path(__file__).resolve().parents[3]
BENCHMARK_DIR = REPO_ROOT / "research" / "loop11_benchmark"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from docuready.ingest.tesseract_discovery import configure_pytesseract, find_tesseract_binary
from research.loop11_benchmark.harness.metrics import compute_cer

configure_pytesseract()

GT_FILE = BENCHMARK_DIR / "ground_truth" / "indic_ground_truth.json"


def evaluate_multilingual_experiment() -> dict:
    manifest = json.loads(GT_FILE.read_text(encoding="utf-8"))

    # Test on a paired subset of 10 Hindi and 10 Odia samples
    hin_samples = [item for item in manifest if item["lang"] == "hin"][:10]
    ori_samples = [item for item in manifest if item["lang"] == "ori"][:10]
    test_set = hin_samples + ori_samples

    control_cers = []
    treatment_cers = []
    control_latencies = []
    treatment_latencies = []

    results = []

    print(f"Testing {len(test_set)} paired bilingual samples (Control: 'eng' vs Treatment: 'eng+hin+ori')...")

    # Check packaged/bundled tessdata first, then fallback to environment
    candidate_tessdata = [
        REPO_ROOT / "apps" / "desktop" / "out" / "DocuReady-win32-x64" / "resources" / "docuready_sidecar" / "tesseract" / "tessdata",
        REPO_ROOT / "sidecar" / "dist" / "docuready_sidecar" / "tesseract" / "tessdata",
        Path(os.environ.get("TESSDATA_PREFIX", "")) if os.environ.get("TESSDATA_PREFIX") else None,
    ]
    tessdata_dir = None
    for c_dir in candidate_tessdata:
        if c_dir and c_dir.is_dir() and (c_dir / "hin.traineddata").is_file():
            tessdata_dir = c_dir
            break

    if tessdata_dir:
        os.environ["TESSDATA_PREFIX"] = str(tessdata_dir)
        # Also point tesseract binary to bundled binary if needed
        bundled_tess = tessdata_dir.parent / "tesseract.exe"
        if bundled_tess.is_file():
            pytesseract.pytesseract.tesseract_cmd = str(bundled_tess)
    elif "TESSDATA_PREFIX" in os.environ:
        tessdata_dir = Path(os.environ["TESSDATA_PREFIX"])

    available_langs = []
    if tessdata_dir and tessdata_dir.is_dir():
        available_langs = [f.stem for f in tessdata_dir.glob("*.traineddata")]

    print(f"Configured Tesseract binary: {pytesseract.pytesseract.tesseract_cmd}")
    print(f"Configured Tesseract TESSDATA_PREFIX ({tessdata_dir}): {available_langs}")

    has_indic_models = "hin" in available_langs or "ori" in available_langs

    for item in test_set:
        pdf_path = BENCHMARK_DIR / item["pdf_path"]
        doc = pymupdf.open(str(pdf_path))
        page = doc[0]
        pix = page.get_pixmap(dpi=150)
        img = PIL.Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        doc.close()

        ref_text = f"{item['ground_truth']['indic_title']} {item['ground_truth']['indic_clause']}"

        # 1. Control: Default 'eng'
        t0 = time.perf_counter()
        data_ctrl = pytesseract.image_to_string(img, lang="eng")
        t_ctrl = (time.perf_counter() - t0) * 1000.0
        control_latencies.append(t_ctrl)
        cer_ctrl = compute_cer(ref_text, data_ctrl)
        control_cers.append(cer_ctrl)

        # 2. Treatment: Target multilingual model
        target_lang = "eng"
        if item["lang"] == "hin" and "hin" in available_langs:
            target_lang = "eng+hin"
        elif item["lang"] == "ori" and "ori" in available_langs:
            target_lang = "eng+ori"

        t1 = time.perf_counter()
        data_treat = pytesseract.image_to_string(img, lang=target_lang)
        t_treat = (time.perf_counter() - t1) * 1000.0
        treatment_latencies.append(t_treat)
        cer_treat = compute_cer(ref_text, data_treat)
        treatment_cers.append(cer_treat)

        results.append({
            "sample_id": item["sample_id"],
            "lang": item["lang"],
            "control_lang": "eng",
            "treatment_lang": target_lang,
            "control_cer": round(cer_ctrl, 4),
            "treatment_cer": round(cer_treat, 4),
            "control_ms": round(t_ctrl, 1),
            "treatment_ms": round(t_treat, 1),
            "cer_improvement": round(cer_ctrl - cer_treat, 4)
        })

    summary = {
        "sample_count": len(test_set),
        "has_indic_models": has_indic_models,
        "control_mean_cer": round(sum(control_cers) / len(control_cers), 4),
        "treatment_mean_cer": round(sum(treatment_cers) / len(treatment_cers), 4),
        "control_mean_latency_ms": round(sum(control_latencies) / len(control_latencies), 1),
        "treatment_mean_latency_ms": round(sum(treatment_latencies) / len(treatment_latencies), 1),
        "mean_cer_improvement": round((sum(control_cers) - sum(treatment_cers)) / len(test_set), 4),
        "latency_overhead_ratio": round(
            (sum(treatment_latencies) / max(1.0, sum(control_latencies))), 2
        ),
        "paired_results": results
    }

    out_file = BENCHMARK_DIR / "results" / "exp_multilingual_results.json"
    out_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("\n=== EXPERIMENT SUMMARY ===")
    print(f"Control ('eng') Mean CER: {summary['control_mean_cer']}")
    print(f"Treatment ('eng+hin+ori') Mean CER: {summary['treatment_mean_cer']}")
    print(f"CER Improvement: {summary['mean_cer_improvement']}")
    print(f"Latency Overhead: {summary['control_mean_latency_ms']}ms -> {summary['treatment_mean_latency_ms']}ms ({summary['latency_overhead_ratio']}x)")
    print(f"Saved results to: {out_file}")
    return summary


if __name__ == "__main__":
    evaluate_multilingual_experiment()
