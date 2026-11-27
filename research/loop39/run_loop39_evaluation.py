"""
Loop 39 Controlled Evaluation Runner:
1. Multilingual CER & WER against ground truth (English, Hindi, Odia, Mixed Eng+Hin, Mixed Eng+Ori)
   comparing Global 3-lang vs Adaptive OCR.
2. Loop 17 (30 reps) & Loop 18 (10 reps) profiling latency statistics (mean, median, p90, p95, stdev, min, max).
3. Alternating Paired Trials (A1, B1, A2, B2, A3, B3) of Variant A (Original) vs Variant B (Minimized).
"""

import json
import math
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from PIL import Image
import pytesseract

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from docuready.ingest.tesseract_discovery import configure_pytesseract
from docuready.ingest.adaptive_ocr import execute_adaptive_ocr, profile_document
from tests.test_loop17_adaptive_efficiency import _load_page_image
from tests.test_loop18_accuracy_and_critical_fields import _load_doc_image

OUT_DIR = ROOT / "research" / "loop39"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def levenshtein(s1, s2):
    if len(s1) < len(s2):
        return levenshtein(s2, s1)
    if not s2:
        return len(s1)
    prev = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        curr = [i + 1]
        for j, c2 in enumerate(s2):
            curr.append(min(prev[j + 1] + 1, curr[j] + 1, prev[j] + (c1 != c2)))
        prev = curr
    return prev[-1]


def cer_wer(ref: str, hyp: str):
    ref_n = " ".join(ref.split())
    hyp_n = " ".join(hyp.split())
    cer = min(1.0, levenshtein(ref_n, hyp_n) / max(1, len(ref_n)))
    rw = ref_n.split()
    hw = hyp_n.split()
    wer = min(1.0, levenshtein(rw, hw) / max(1, len(rw)))
    return round(cer * 100.0, 2), round(wer * 100.0, 2)


def percentile(vals, p):
    s = sorted(vals)
    return s[min(len(s) - 1, max(0, int(math.ceil(p * len(s))) - 1))]


def summarize(vals):
    return {
        "n": len(vals),
        "mean_ms": round(statistics.mean(vals), 2),
        "median_ms": round(statistics.median(vals), 2),
        "p90_ms": round(percentile(vals, 0.90), 2),
        "p95_ms": round(percentile(vals, 0.95), 2),
        "stdev_ms": round(statistics.stdev(vals), 2) if len(vals) > 1 else 0.0,
        "min_ms": round(min(vals), 2),
        "max_ms": round(max(vals), 2),
    }


def evaluate_multilingual_cer_wer():
    configure_pytesseract()
    gt_dir = ROOT / "research" / "loop14" / "ground_truth"
    docs = [
        ("DOC_CTRL_01_ENGLISH_CERTIFICATE", "English"),
        ("DOC_HIN_01_ADMIN_CIRCULAR", "Hindi"),
        ("DOC_ORI_01_ADMIN_CIRCULAR", "Odia"),
        ("DOC_MIX_01_HIN_ENG_SCHOLARSHIP", "Mixed_Eng_Hin"),
        ("DOC_MIX_02_ORI_ENG_SCHOLARSHIP", "Mixed_Eng_Ori"),
    ]
    rows = []
    for doc_id, lang_label in docs:
        img = _load_page_image(doc_id)
        gt_candidates = list(gt_dir.glob(f"{doc_id}*.txt")) if gt_dir.exists() else []
        gt_text = gt_candidates[0].read_text(encoding="utf-8") if gt_candidates else ""

        t0 = time.perf_counter()
        d_glob = pytesseract.image_to_data(img, lang="eng+hin+ori", output_type=pytesseract.Output.DICT, timeout=15)
        t_glob = round((time.perf_counter() - t0) * 1000.0, 2)
        txt_glob = " ".join(str(w).strip() for w, c in zip(d_glob["text"], d_glob["conf"]) if str(w).strip() and float(c) >= 0)

        d_adap, dec = execute_adaptive_ocr(img)
        txt_adap = " ".join(str(w).strip() for w, c in zip(d_adap["text"], d_adap["conf"]) if str(w).strip() and float(c) >= 0)

        g_cer, g_wer = cer_wer(gt_text, txt_glob) if gt_text else (None, None)
        a_cer, a_wer = cer_wer(gt_text, txt_adap) if gt_text else (None, None)
        rows.append({
            "doc_id": doc_id,
            "language": lang_label,
            "has_gt": bool(gt_text),
            "gt_chars": len(gt_text),
            "global_ms": t_glob,
            "global_cer_pct": g_cer,
            "global_wer_pct": g_wer,
            "adaptive_strategy": dec.selected_strategy,
            "adaptive_lang": dec.selected_lang,
            "adaptive_ms": dec.total_latency_ms,
            "adaptive_cer_pct": a_cer,
            "adaptive_wer_pct": a_wer,
            "ocr_invocations": dec.ocr_model_invocations + (0 if dec.profile.has_native_text else 1),
        })
    return rows


def evaluate_loop17_18_stats():
    img17 = _load_page_image("DOC_CTRL_01_ENGLISH_CERTIFICATE")
    l17_times = [profile_document(img17).profiling_latency_ms for _ in range(30)]

    img18 = _load_doc_image("DOC_EXT_06_ODIA_REVENUE_NOTICE")
    l18_times = [profile_document(img18).profiling_latency_ms for _ in range(10)]
    return {
        "loop17_30_reps_threshold_850ms": summarize(l17_times),
        "loop18_10_reps_threshold_1400ms": summarize(l18_times),
    }


def evaluate_paired_ab_trials():
    src_sidecar = ROOT / "apps/desktop/out/DocuReady-win32-x64/resources/docuready_sidecar"
    extra_exes = [
        "ambiguous_words.exe", "classifier_tester.exe", "cntraining.exe",
        "combine_lang_model.exe", "combine_tessdata.exe", "dawg2wordlist.exe",
        "lstmeval.exe", "lstmtraining.exe", "merge_unicharsets.exe",
        "mftraining.exe", "set_unicharset_properties.exe", "shapeclustering.exe",
        "tesseract-uninstall.exe", "text2image.exe", "unicharset_extractor.exe",
        "winpath.exe", "wordlist2dawg.exe"
    ]
    test_docs = {
        name: _load_page_image(name)
        for name in ["DOC_CTRL_01_ENGLISH_CERTIFICATE", "DOC_HIN_01_ADMIN_CIRCULAR", "DOC_ORI_01_ADMIN_CIRCULAR", "DOC_MIX_01_HIN_ENG_SCHOLARSHIP", "DOC_MIX_02_ORI_ENG_SCHOLARSHIP"]
    }

    with tempfile.TemporaryDirectory(prefix="l39_ab_") as tmp:
        tmp_path = Path(tmp)
        var_b = tmp_path / "var_b"
        shutil.copytree(src_sidecar, var_b)
        for ex in extra_exes:
            t = var_b / "tesseract" / ex
            if t.exists():
                t.unlink()

        pkt = tmp_path / "pkt"
        pkt.mkdir()
        for nm, im in test_docs.items():
            im.save(pkt / f"{nm}.png")

        env = os.environ.copy()
        env["DOCUREADY_WORKSPACE_ROOT"] = str(tmp_path)

        trials = []
        for trial_idx in range(1, 4):
            for label, sdir in [("A", src_sidecar), ("B", var_b)]:
                exe = sdir / "docuready_sidecar.exe"
                req_a = json.dumps({
                    "protocol": 1, "id": f"{label}-{trial_idx}", "method": "audit_packet",
                    "params": {"packet_dir": str(pkt), "packet_id": f"PKT-{label}-{trial_idx}", "as_of": "2026-11-13"}
                }) + "\n"
                t0 = time.perf_counter()
                p = subprocess.run([str(exe)], input=req_a, text=True, capture_output=True, env=env, timeout=60)
                dt = round((time.perf_counter() - t0) * 1000.0, 2)
                lines = [ln for ln in p.stdout.strip().splitlines() if ln.strip().startswith("{")]
                out = json.loads(lines[-1]) if lines else {}
                trials.append({
                    "trial": trial_idx,
                    "variant": label,
                    "rc": p.returncode,
                    "ok": out.get("ok", False),
                    "latency_ms": dt,
                })

        a_times = [t["latency_ms"] for t in trials if t["variant"] == "A"]
        b_times = [t["latency_ms"] for t in trials if t["variant"] == "B"]
        return {
            "trials": trials,
            "variant_a_summary": summarize(a_times),
            "variant_b_summary": summarize(b_times),
        }


def main():
    print("1. Evaluating multilingual CER/WER...")
    ml = evaluate_multilingual_cer_wer()
    with open(OUT_DIR / "accuracy_results.json", "w", encoding="utf-8") as f:
        json.dump({"multilingual_results": ml}, f, indent=2)

    print("2. Evaluating Loop 17 (30 reps) & Loop 18 (10 reps) stats...")
    pstats = evaluate_loop17_18_stats()
    with open(OUT_DIR / "performance_results.json", "w", encoding="utf-8") as f:
        json.dump(pstats, f, indent=2)

    print("3. Running alternating paired Variant A vs B trials...")
    ab = evaluate_paired_ab_trials()
    with open(OUT_DIR / "ab_paired_trials.json", "w", encoding="utf-8") as f:
        json.dump(ab, f, indent=2)

    print("Loop 39 scientific evaluation complete.")


if __name__ == "__main__":
    main()
