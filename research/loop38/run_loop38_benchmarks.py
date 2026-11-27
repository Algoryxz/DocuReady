"""
Loop 38 Multilingual OCR Routing & Packaged Variant A vs B Qualification Runner.
Measures:
1. 7 language combinations (eng, hin, ori, eng+hin, eng+ori, hin+ori, eng+hin+ori) latencies.
2. Routing strategy comparison (Global eng+hin+ori vs Adaptive vs Region-aware) on Loop 14/18 docs.
3. Packaged Variant A (Original) vs Variant B (Minimized -63.41 MB) end-to-end OCR & audit_packet parity.
"""

import json
import math
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
from docuready.ingest.region_ocr import ocr_page_by_regions
from tests.test_loop17_adaptive_efficiency import _load_page_image

OUT_DIR = ROOT / "research" / "loop38"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def percentile(vals, p):
    s = sorted(vals)
    return s[min(len(s) - 1, max(0, int(math.ceil(p * len(s))) - 1))]


def stats_summary(vals):
    return {
        "n": len(vals),
        "mean_ms": round(statistics.mean(vals), 2),
        "median_ms": round(statistics.median(vals), 2),
        "p95_ms": round(percentile(vals, 0.95), 2),
        "stdev_ms": round(statistics.stdev(vals), 2) if len(vals) > 1 else 0.0,
        "min_ms": round(min(vals), 2),
        "max_ms": round(max(vals), 2),
    }


def benchmark_7_lang_combos():
    configure_pytesseract()
    img = _load_page_image("DOC_CTRL_01_ENGLISH_CERTIFICATE")
    combos = ["eng", "hin", "ori", "eng+hin", "eng+ori", "hin+ori", "eng+hin+ori"]
    results = {}
    for lang in combos:
        times = []
        # 10 reps per combo (30 reps on eng and eng+hin+ori)
        reps = 30 if lang in ("eng", "eng+hin+ori") else 10
        for _ in range(reps):
            t0 = time.perf_counter()
            _ = pytesseract.image_to_data(img, lang=lang, output_type=pytesseract.Output.DICT, timeout=15)
            times.append((time.perf_counter() - t0) * 1000.0)
        results[lang] = stats_summary(times)
    return results


def benchmark_routing_strategies():
    configure_pytesseract()
    docs = [
        ("DOC_CTRL_01_ENGLISH_CERTIFICATE", "eng"),
        ("DOC_HIN_01_ADMIN_CIRCULAR", "hin"),
        ("DOC_ORI_01_ADMIN_CIRCULAR", "ori"),
        ("DOC_MIX_01_HIN_ENG_SCHOLARSHIP", "eng+hin"),
        ("DOC_MIX_02_ORI_ENG_SCHOLARSHIP", "eng+ori"),
    ]
    rows = []
    for doc_id, expected_script_group in docs:
        try:
            img = _load_page_image(doc_id)
        except Exception:
            continue

        # 1. Global eng+hin+ori
        t0 = time.perf_counter()
        d_glob = pytesseract.image_to_data(img, lang="eng+hin+ori", output_type=pytesseract.Output.DICT, timeout=15)
        t_glob = (time.perf_counter() - t0) * 1000.0
        w_glob = len([w for w, c in zip(d_glob["text"], d_glob["conf"]) if str(w).strip() and float(c) >= 0])

        # 2. Adaptive OCR
        d_adap, dec = execute_adaptive_ocr(img)
        w_adap = len([w for w, c in zip(d_adap["text"], d_adap["conf"]) if str(w).strip() and float(c) >= 0])

        # 3. Region-aware OCR
        t1 = time.perf_counter()
        d_reg = ocr_page_by_regions(img)
        t_reg = (time.perf_counter() - t1) * 1000.0
        w_reg = len([w for w, c in zip(d_reg["text"], d_reg["conf"]) if str(w).strip() and float(c) >= 0])

        rows.append({
            "doc_id": doc_id,
            "expected_group": expected_script_group,
            "global_3lang_ms": round(t_glob, 2),
            "global_3lang_words": w_glob,
            "adaptive_strategy": dec.selected_strategy,
            "adaptive_lang": dec.selected_lang,
            "adaptive_ms": dec.total_latency_ms,
            "adaptive_words": w_adap,
            "region_ms": round(t_reg, 2),
            "region_words": w_reg,
            "fallback_triggered": dec.fallback_triggered,
        })
    return rows


def qualify_variant_a_vs_b():
    src_sidecar = ROOT / "apps/desktop/out/DocuReady-win32-x64/resources/docuready_sidecar"
    extra_exes = [
        "ambiguous_words.exe", "classifier_tester.exe", "cntraining.exe",
        "combine_lang_model.exe", "combine_tessdata.exe", "dawg2wordlist.exe",
        "lstmeval.exe", "lstmtraining.exe", "merge_unicharsets.exe",
        "mftraining.exe", "set_unicharset_properties.exe", "shapeclustering.exe",
        "tesseract-uninstall.exe", "text2image.exe", "unicharset_extractor.exe",
        "winpath.exe", "wordlist2dawg.exe"
    ]

    # Sample synthetic/public docs to test real OCR inside both packaged sidecars
    test_docs = {}
    for name in ["DOC_CTRL_01_ENGLISH_CERTIFICATE", "DOC_HIN_01_ADMIN_CIRCULAR", "DOC_ORI_01_ADMIN_CIRCULAR", "DOC_MIX_01_HIN_ENG_SCHOLARSHIP", "DOC_MIX_02_ORI_ENG_SCHOLARSHIP"]:
        try:
            test_docs[name] = _load_page_image(name)
        except Exception:
            pass

    def run_variant_checks(sidecar_dir: Path, label: str):
        exe = sidecar_dir / "docuready_sidecar.exe"
        # Health
        req_h = json.dumps({"protocol": 1, "id": f"{label}-h", "method": "health", "params": {}}) + "\n"
        t0 = time.perf_counter()
        p_h = subprocess.run([str(exe)], input=req_h, text=True, capture_output=True, timeout=20)
        h_ms = round((time.perf_counter() - t0) * 1000.0, 2)

        # Real audit_packet on a temp workspace with PNGs of English, Hindi, Odia, Mixed
        with tempfile.TemporaryDirectory(prefix=f"l38_{label}_") as wtmp:
            wp = Path(wtmp)
            pkt = wp / "pkt_multilang"
            pkt.mkdir()
            for doc_name, im in test_docs.items():
                im.save(pkt / f"{doc_name}.png")
            req_a = json.dumps({
                "protocol": 1, "id": f"{label}-audit", "method": "audit_packet",
                "params": {"packet_dir": str(pkt), "packet_id": f"PKT-{label}", "as_of": "2026-11-13"}
            }) + "\n"
            import os
            env = os.environ.copy()
            env["DOCUREADY_WORKSPACE_ROOT"] = str(wp)
            t1 = time.perf_counter()
            p_a = subprocess.run([str(exe)], input=req_a, text=True, capture_output=True, env=env, timeout=60)
            a_ms = round((time.perf_counter() - t1) * 1000.0, 2)
            lines = [ln for ln in p_a.stdout.strip().splitlines() if ln.strip().startswith("{")]
            audit_json = json.loads(lines[-1]) if lines else {}

        return {
            "variant": label,
            "size_bytes": sum(f.stat().st_size for f in sidecar_dir.rglob("*") if f.is_file()),
            "health_rc": p_h.returncode,
            "health_ms": h_ms,
            "audit_rc": p_a.returncode,
            "audit_ok": audit_json.get("ok", False),
            "audit_ms": a_ms,
            "readiness_score": audit_json.get("result", {}).get("readiness_score"),
            "finding_count": len(audit_json.get("result", {}).get("findings", [])),
        }

    res_a = run_variant_checks(src_sidecar, "Variant_A_Original")
    with tempfile.TemporaryDirectory(prefix="l38_var_b_") as tmp:
        var_b_dir = Path(tmp) / "docuready_sidecar"
        shutil.copytree(src_sidecar, var_b_dir)
        for ex in extra_exes:
            t = var_b_dir / "tesseract" / ex
            if t.exists():
                t.unlink()
        res_b = run_variant_checks(var_b_dir, "Variant_B_Minimized")

    return {"variant_a": res_a, "variant_b": res_b, "size_saved_bytes": res_a["size_bytes"] - res_b["size_bytes"]}


def main():
    print("1. Benchmarking 7 language combos...")
    lang_bench = benchmark_7_lang_combos()
    with open(OUT_DIR / "ocr_performance_results.json", "w", encoding="utf-8") as f:
        json.dump(lang_bench, f, indent=2)

    print("2. Benchmarking routing strategies across multilingual docs...")
    routing_rows = benchmark_routing_strategies()
    with open(OUT_DIR / "routing_strategies.json", "w", encoding="utf-8") as f:
        json.dump({"strategies": routing_rows}, f, indent=2)

    print("3. Qualifying Packaged Variant A vs Variant B...")
    pkg_comp = qualify_variant_a_vs_b()
    with open(OUT_DIR / "package_comparison.json", "w", encoding="utf-8") as f:
        json.dump(pkg_comp, f, indent=2)

    print("Loop 38 benchmark runner complete.")


if __name__ == "__main__":
    main()
