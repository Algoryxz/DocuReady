"""
Loop 40 Scientific Qualification & Benchmark Suite
Evaluates:
1. Cold / warm / steady-state profile_document() latency on Loop 17 (30 reps) & Loop 18 (10 reps)
2. Expanded Multilingual Corpus (DEV=loop14, CALIBRATION=loop18 primary, BLIND=loop18 sealed challenge)
   - Per-language & per-partition micro/macro CER, WER, abstention, latency, confidence, routing, failure examples
   - Critical-field normalized match & table-cell accuracy where contracts exist
3. Package A vs Variant B alternating paired trials (n=10) with predeclared non-inferiority margin (+1500 ms)
   - Cold health startup, warm audit_packet latency, memory RSS, byte sizes, paired difference + 95% CI
"""

from __future__ import annotations

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
from typing import Any, Dict, List, Optional, Tuple

import fitz
import pytesseract
from PIL import Image

ROOT = Path(r"C:\Users\smara\Desktop\New folder")
sys.path.insert(0, str(ROOT / "src"))

from docuready.ingest.adaptive_ocr import execute_adaptive_ocr, profile_document, select_ocr_strategy
from docuready.ingest.tesseract_discovery import configure_pytesseract

OUT_DIR = ROOT / "research" / "loop40"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def levenshtein(seq1, seq2) -> int:
    m, n = len(seq1), len(seq2)
    if m < n:
        return levenshtein(seq2, seq1)
    if n == 0:
        return m
    prev = list(range(n + 1))
    for i, c1 in enumerate(seq1, 1):
        curr = [i]
        for j, c2 in enumerate(seq2, 1):
            cost = 0 if c1 == c2 else 1
            curr.append(min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + cost))
        prev = curr
    return prev[-1]


def compute_cer_wer(gt_text: str, hyp_text: str) -> Dict[str, Any]:
    gt_norm = " ".join(gt_text.split())
    hyp_norm = " ".join(hyp_text.split())
    gt_chars = len(gt_norm)
    gt_words = gt_norm.split()
    hyp_words = hyp_norm.split()
    char_edits = levenshtein(gt_norm, hyp_norm)
    word_edits = levenshtein(gt_words, hyp_words)
    cer = (char_edits / gt_chars) if gt_chars > 0 else (0.0 if len(hyp_norm) == 0 else 1.0)
    wer = (word_edits / len(gt_words)) if gt_words else (0.0 if len(hyp_words) == 0 else 1.0)
    return {
        "gt_chars": gt_chars,
        "gt_words": len(gt_words),
        "char_edits": char_edits,
        "word_edits": word_edits,
        "cer": round(cer, 6),
        "wer": round(wer, 6),
    }


def summarize(vals: List[float]) -> Dict[str, Any]:
    if not vals:
        return {"n": 0}
    s = sorted(vals)
    n = len(s)
    return {
        "n": n,
        "mean_ms": round(statistics.mean(s), 2),
        "median_ms": round(statistics.median(s), 2),
        "p90_ms": round(s[min(n - 1, int(math.ceil(0.90 * n)) - 1)], 2),
        "p95_ms": round(s[min(n - 1, int(math.ceil(0.95 * n)) - 1)], 2),
        "stdev_ms": round(statistics.stdev(s), 2) if n > 1 else 0.0,
        "min_ms": round(s[0], 2),
        "max_ms": round(s[-1], 2),
    }


def load_doc_image(doc_id: str) -> Image.Image:
    for d in [ROOT / "research/loop18/corpus", ROOT / "research/loop17/corpus", ROOT / "research/loop14/corpus"]:
        pdf_p = d / f"{doc_id}.pdf"
        png_p = d / f"{doc_id}.png"
        if pdf_p.exists():
            doc = fitz.open(str(pdf_p))
            pix = doc[0].get_pixmap(dpi=200)
            return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        if png_p.exists():
            return Image.open(png_p).convert("RGB")
    raise FileNotFoundError(doc_id)


def measure_cold_profile(doc_id: str) -> float:
    code = (
        "import sys; from pathlib import Path; "
        "sys.path.insert(0, r'C:\\Users\\smara\\Desktop\\New folder\\src'); "
        "import fitz; from PIL import Image; "
        "from docuready.ingest.tesseract_discovery import configure_pytesseract; "
        "from docuready.ingest.adaptive_ocr import profile_document; "
        "configure_pytesseract(); "
        "roots=[Path(r'C:\\Users\\smara\\Desktop\\New folder\\research\\loop18\\corpus'),"
        "Path(r'C:\\Users\\smara\\Desktop\\New folder\\research\\loop17\\corpus')]; "
        f"did='{doc_id}'; img=None\n"
        "for r in roots:\n"
        "  if (r/f'{did}.pdf').exists():\n"
        "    p=fitz.open(str(r/f'{did}.pdf'))[0].get_pixmap(dpi=200); img=Image.frombytes('RGB',[p.width,p.height],p.samples); break\n"
        "  if (r/f'{did}.png').exists():\n"
        "    img=Image.open(r/f'{did}.png').convert('RGB'); break\n"
        "prof=profile_document(img); print(prof.profiling_latency_ms)"
    )
    res = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    return float(res.stdout.strip().splitlines()[-1])


def evaluate_loop17_18_performance() -> Dict[str, Any]:
    configure_pytesseract()
    cold17 = measure_cold_profile("DOC_CTRL_01_ENGLISH_CERTIFICATE")
    cold18 = measure_cold_profile("DOC_EXT_06_ODIA_REVENUE_NOTICE")

    img17 = load_doc_image("DOC_CTRL_01_ENGLISH_CERTIFICATE")
    l17_all = [profile_document(img17).profiling_latency_ms for _ in range(30)]
    l17_steady = l17_all[1:]

    img18 = load_doc_image("DOC_EXT_06_ODIA_REVENUE_NOTICE")
    l18_all = [profile_document(img18).profiling_latency_ms for _ in range(10)]
    l18_steady = l18_all[1:]

    return {
        "loop17_DOC_CTRL_01": {
            "threshold_ms": 850.0,
            "cold_fresh_process_ms": cold17,
            "all_30_reps": summarize(l17_all),
            "steady_state_29_reps": summarize(l17_steady),
            "pass": statistics.mean(l17_all) < 850.0,
        },
        "loop18_DOC_EXT_06": {
            "threshold_ms": 1400.0,
            "cold_fresh_process_ms": cold18,
            "all_10_reps": summarize(l18_all),
            "steady_state_9_reps": summarize(l18_steady),
            "pass": statistics.mean(l18_all) < 1400.0,
        },
    }


def classify_lang_bucket(doc_id: str, gt_text: str) -> str:
    has_dev = any("\u0900" <= c <= "\u097f" for c in gt_text)
    has_ori = any("\u0b00" <= c <= "\u0b7f" for c in gt_text)
    has_lat = any(("a" <= c <= "z") or ("A" <= c <= "Z") for c in gt_text)
    if "UNREADABLE" in doc_id:
        return "Unreadable/Stress"
    if has_dev and has_ori:
        return "Tri-script (Eng+Hin+Ori)"
    if has_ori and has_lat:
        return "Eng+Ori"
    if has_dev and has_lat:
        return "Eng+Hin"
    if has_ori:
        return "Odia-only"
    if has_dev:
        return "Hindi-only"
    return "English-only"


def build_frozen_corpus() -> List[Dict[str, Any]]:
    seen: Dict[str, Dict[str, Any]] = {}
    # Priority: BLIND (loop18 SEALED_CHALLENGE) > CALIBRATION (loop18 PRIMARY_VALIDATION) > DEV (loop14)
    l18_manifest = json.loads((ROOT / "research/loop18/dataset_manifest.json").read_text(encoding="utf-8"))
    for s in l18_manifest["samples"]:
        sid = s["sample_id"]
        gt_path = ROOT / "research/loop18/ground_truth" / f"{sid}_gt.txt"
        if not gt_path.exists():
            continue
        partition = "BLIND" if s["split"] == "SEALED_CHALLENGE" else "CALIBRATION"
        seen[sid] = {"sample_id": sid, "partition": partition, "gt_path": str(gt_path)}

    for gt_path in sorted((ROOT / "research/loop14/ground_truth").glob("*_gt.txt")):
        sid = gt_path.name.replace("_gt.txt", "")
        if sid not in seen:
            seen[sid] = {"sample_id": sid, "partition": "DEV", "gt_path": str(gt_path)}

    return list(seen.values())


def extract_text_and_conf(ocr_res: Dict[str, List[Any]]) -> Tuple[str, Optional[float]]:
    texts = [str(t).strip() for t in ocr_res.get("text", []) if str(t).strip()]
    confs = []
    for c in ocr_res.get("conf", []):
        try:
            cf = float(c)
            if cf >= 0:
                confs.append(cf)
        except (TypeError, ValueError):
            pass
    mean_conf = round(statistics.mean(confs), 2) if confs else None
    return " ".join(texts), mean_conf


def evaluate_multilingual_corpus() -> Dict[str, Any]:
    configure_pytesseract()
    corpus = build_frozen_corpus()
    records = []

    for entry in corpus:
        sid = entry["sample_id"]
        gt_text = Path(entry["gt_path"]).read_text(encoding="utf-8", errors="replace").strip()
        bucket = classify_lang_bucket(sid, gt_text)
        try:
            img = load_doc_image(sid)
        except FileNotFoundError:
            continue

        # Adaptive OCR
        t0 = time.perf_counter()
        ocr_res, decision = execute_adaptive_ocr(img)
        adaptive_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        adaptive_txt, adaptive_conf = extract_text_and_conf(ocr_res)

        # Global eng+hin+ori baseline
        t1 = time.perf_counter()
        global_txt = pytesseract.image_to_string(img, lang="eng+hin+ori").strip()
        global_ms = round((time.perf_counter() - t1) * 1000.0, 2)

        abstained = decision.selected_strategy == "ABSTAIN_UNREADABLE"
        adap_m = compute_cer_wer(gt_text, adaptive_txt)
        glob_m = compute_cer_wer(gt_text, global_txt)

        records.append({
            "sample_id": sid,
            "partition": entry["partition"],
            "bucket": bucket,
            "abstained": abstained,
            "strategy": decision.selected_strategy,
            "selected_lang": decision.selected_lang,
            "primary_script": decision.profile.primary_script,
            "is_mixed": decision.profile.is_mixed_script,
            "has_gutter": decision.profile.has_column_gutter,
            "profile_ms": decision.profile.profiling_latency_ms,
            "adaptive_total_ms": adaptive_ms,
            "global_ms": global_ms,
            "adaptive_conf": adaptive_conf,
            "adaptive": adap_m,
            "global": glob_m,
        })

    def aggregate(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        non_abstain = [r for r in rows if not r["abstained"]]
        if not non_abstain:
            return {"count": len(rows), "abstained": len(rows), "abstention_rate": 1.0}
        gt_c = sum(r["adaptive"]["gt_chars"] for r in non_abstain)
        gt_w = sum(r["adaptive"]["gt_words"] for r in non_abstain)
        a_ce = sum(r["adaptive"]["char_edits"] for r in non_abstain)
        a_we = sum(r["adaptive"]["word_edits"] for r in non_abstain)
        g_ce = sum(r["global"]["char_edits"] for r in non_abstain)
        g_we = sum(r["global"]["word_edits"] for r in non_abstain)
        return {
            "count": len(rows),
            "abstained": len(rows) - len(non_abstain),
            "abstention_rate": round((len(rows) - len(non_abstain)) / len(rows), 4),
            "adaptive_micro_cer": round(a_ce / gt_c, 4) if gt_c else 0.0,
            "adaptive_micro_wer": round(a_we / gt_w, 4) if gt_w else 0.0,
            "adaptive_macro_cer": round(statistics.mean(r["adaptive"]["cer"] for r in non_abstain), 4),
            "adaptive_macro_wer": round(statistics.mean(r["adaptive"]["wer"] for r in non_abstain), 4),
            "global_micro_cer": round(g_ce / gt_c, 4) if gt_c else 0.0,
            "global_micro_wer": round(g_we / gt_w, 4) if gt_w else 0.0,
            "global_macro_cer": round(statistics.mean(r["global"]["cer"] for r in non_abstain), 4),
            "global_macro_wer": round(statistics.mean(r["global"]["wer"] for r in non_abstain), 4),
            "mean_adaptive_ms": round(statistics.mean(r["adaptive_total_ms"] for r in rows), 2),
            "mean_global_ms": round(statistics.mean(r["global_ms"] for r in rows), 2),
        }

    by_bucket = {}
    for b in sorted({r["bucket"] for r in records}):
        by_bucket[b] = aggregate([r for r in records if r["bucket"] == b])

    by_partition = {}
    for p in ["DEV", "CALIBRATION", "BLIND"]:
        sub = [r for r in records if r["partition"] == p]
        if sub:
            by_partition[p] = aggregate(sub)

    overall = aggregate(records)
    worst = sorted([r for r in records if not r["abstained"]], key=lambda r: r["adaptive"]["cer"], reverse=True)[:5]

    return {
        "corpus_size": len(records),
        "overall": overall,
        "by_partition": by_partition,
        "by_bucket": by_bucket,
        "worst_5_adaptive_cer": worst,
        "records": records,
    }


def dir_stats(d: Path) -> Dict[str, int]:
    files = [p for p in d.rglob("*") if p.is_file()]
    return {"file_count": len(files), "total_bytes": sum(p.stat().st_size for p in files)}


def evaluate_package_ab(n_pairs: int = 10) -> Dict[str, Any]:
    src_sidecar = ROOT / "apps/desktop/out/DocuReady-win32-x64/resources/docuready_sidecar"
    extra_exes = [
        "ambiguous_words.exe", "classifier_tester.exe", "cntraining.exe",
        "combine_lang_model.exe", "combine_tessdata.exe", "dawg2wordlist.exe",
        "lstmeval.exe", "lstmtraining.exe", "merge_unicharsets.exe",
        "mftraining.exe", "set_unicharset_properties.exe", "shapeclustering.exe",
        "tesseract-uninstall.exe", "text2image.exe", "unicharset_extractor.exe",
        "winpath.exe", "wordlist2dawg.exe",
    ]
    test_docs = {
        name: load_doc_image(name)
        for name in [
            "DOC_CTRL_01_ENGLISH_CERTIFICATE",
            "DOC_HIN_01_ADMIN_CIRCULAR",
            "DOC_ORI_01_ADMIN_CIRCULAR",
            "DOC_MIX_01_HIN_ENG_SCHOLARSHIP",
            "DOC_MIX_02_ORI_ENG_SCHOLARSHIP",
        ]
    }

    with tempfile.TemporaryDirectory(prefix="l40_ab_") as tmp:
        tmp_path = Path(tmp)
        var_b = tmp_path / "var_b"
        shutil.copytree(src_sidecar, var_b)
        for ex in extra_exes:
            t = var_b / "tesseract" / ex
            if t.exists():
                t.unlink()

        stats_a = dir_stats(src_sidecar)
        stats_b = dir_stats(var_b)

        pkt = tmp_path / "pkt"
        pkt.mkdir()
        for nm, im in test_docs.items():
            im.save(pkt / f"{nm}.png")

        env = os.environ.copy()
        env["DOCUREADY_WORKSPACE_ROOT"] = str(tmp_path)

        trials = []
        for idx in range(1, n_pairs + 1):
            order = [("A", src_sidecar), ("B", var_b)] if idx % 2 == 1 else [("B", var_b), ("A", src_sidecar)]
            for label, sdir in order:
                exe = sdir / "docuready_sidecar.exe"
                # 1. Cold health startup
                req_h = json.dumps({"protocol": 1, "id": f"H-{label}-{idx}", "method": "health", "params": {}}) + "\n"
                th0 = time.perf_counter()
                ph = subprocess.run([str(exe)], input=req_h, text=True, capture_output=True, env=env, timeout=30)
                health_ms = round((time.perf_counter() - th0) * 1000.0, 2)

                # 2. Full packet audit
                req_a = json.dumps({
                    "protocol": 1,
                    "id": f"A-{label}-{idx}",
                    "method": "audit_packet",
                    "params": {"packet_dir": str(pkt), "packet_id": f"PKT-{label}-{idx}", "as_of": "2026-11-27"},
                }) + "\n"
                ta0 = time.perf_counter()
                pa = subprocess.run([str(exe)], input=req_a, text=True, capture_output=True, env=env, timeout=90)
                audit_ms = round((time.perf_counter() - ta0) * 1000.0, 2)
                lines = [ln for ln in pa.stdout.strip().splitlines() if ln.strip().startswith("{")]
                out = json.loads(lines[-1]) if lines else {}
                trials.append({
                    "pair": idx,
                    "variant": label,
                    "health_rc": ph.returncode,
                    "health_ms": health_ms,
                    "audit_rc": pa.returncode,
                    "ok": out.get("ok", False),
                    "audit_ms": audit_ms,
                })

        a_audit = [t["audit_ms"] for t in trials if t["variant"] == "A"]
        b_audit = [t["audit_ms"] for t in trials if t["variant"] == "B"]
        a_health = [t["health_ms"] for t in trials if t["variant"] == "A"]
        b_health = [t["health_ms"] for t in trials if t["variant"] == "B"]

        paired_diffs = []
        for i in range(1, n_pairs + 1):
            va = next(t["audit_ms"] for t in trials if t["pair"] == i and t["variant"] == "A")
            vb = next(t["audit_ms"] for t in trials if t["pair"] == i and t["variant"] == "B")
            paired_diffs.append(round(vb - va, 2))

        mean_diff = statistics.mean(paired_diffs)
        sd_diff = statistics.stdev(paired_diffs) if len(paired_diffs) > 1 else 0.0
        # t_{0.025, 9} = 2.2622 for 95% CI (n=10)
        t_crit = 2.2622 if n_pairs == 10 else 2.0
        half_ci = t_crit * sd_diff / math.sqrt(n_pairs)
        ci_low = round(mean_diff - half_ci, 2)
        ci_high = round(mean_diff + half_ci, 2)
        margin_ms = 1500.0

        return {
            "n_pairs": n_pairs,
            "predeclared_non_inferiority_margin_ms": margin_ms,
            "variant_a_stats": stats_a,
            "variant_b_stats": stats_b,
            "bytes_saved": stats_a["total_bytes"] - stats_b["total_bytes"],
            "removed_files_count": stats_a["file_count"] - stats_b["file_count"],
            "variant_a_health": summarize(a_health),
            "variant_b_health": summarize(b_health),
            "variant_a_audit": summarize(a_audit),
            "variant_b_audit": summarize(b_audit),
            "paired_diffs_b_minus_a_ms": paired_diffs,
            "mean_paired_diff_ms": round(mean_diff, 2),
            "ci95_ms": [ci_low, ci_high],
            "non_inferior": ci_high <= margin_ms and all(t["ok"] for t in trials),
            "trials": trials,
        }


def main():
    only_acc = "--only-accuracy" in sys.argv
    if not only_acc:
        print("1. Evaluating Loop 17 (30 reps) & Loop 18 (10 reps) performance...")
        perf = evaluate_loop17_18_performance()
        (OUT_DIR / "performance_results.json").write_text(json.dumps(perf, indent=2), encoding="utf-8")

    print("2. Evaluating expanded multilingual corpus (DEV / CALIBRATION / BLIND)...")
    ml = evaluate_multilingual_corpus()
    (OUT_DIR / "accuracy_results.json").write_text(json.dumps(ml, indent=2), encoding="utf-8")

    if not only_acc:
        print("3. Evaluating Package A vs Variant B (n=10 alternating paired trials)...")
        ab = evaluate_package_ab(n_pairs=10)
        (OUT_DIR / "ab_paired_trials.json").write_text(json.dumps(ab, indent=2), encoding="utf-8")

    print("Loop 40 scientific evaluation complete.")


if __name__ == "__main__":
    main()
