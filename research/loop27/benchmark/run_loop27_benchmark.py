"""
Loop 27 Comprehensive Benchmark Suite
Evaluates:
  1. Cohort L — New Independent Public Validation (45 docs, 120 fields):
     - DEV (10 docs, 26 fields)
     - CAL (10 docs, 26 fields)
     - BLIND (15 docs, 42 fields)
     - CHALL (10 docs, 26 fields)
  2. Cohort K — Loop 26 Independent Public Baseline (60 docs, 307 fields)
  3. Cohort J — Loop 25 Large-Scale Synthetic Corpus (60 docs, 201 fields)
  4. Cohort I — Loop 24 Blind Generalization Corpus (30 docs, 102 fields)
  5. Historical Loops 20-23 Corpus (52 docs, 113 fields)
Total Combined Benchmark: 247 documents, 843 critical fields.

Features:
  - Frozen operating policy T* = 70.0, T_fuzzy = 75.0
  - Conservative identifier verification & character ambiguity guards
  - Mutually exclusive outcome categories (Exact + False + Abstain = Total)
  - 12-category abstention taxonomy tracking
  - Table grid construction overhead & total document latency
  - Determinism verification (double-run comparison)
  - ECE, MCE, and Brier score calibration
  - Statistical confidence intervals (Wilson score & Clopper-Pearson / Rule-of-Three upper risk bounds)
"""

import json
import math
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple
from PIL import Image
import pytesseract
import numpy as np

from docuready.ingest.table_association import (
    build_table_grid,
    extract_cell_by_intersection,
    extract_field_by_spatial_association,
    FieldEvidence,
)
from docuready.ingest.identifier_validation import (
    validate_identifier_syntax_and_ambiguity,
    sanitize_identifier_token,
)

ROOT = Path(__file__).resolve().parents[3]
L20_DIR = ROOT / "research" / "loop20"
L21_DIR = ROOT / "research" / "loop21"
L22_DIR = ROOT / "research" / "loop22"
L23_DIR = ROOT / "research" / "loop23"
L24_DIR = ROOT / "research" / "loop24"
L25_DIR = ROOT / "research" / "loop25"
L26_DIR = ROOT / "research" / "loop26"
L27_DIR = ROOT / "research" / "loop27"
RESULTS_DIR = L27_DIR / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def configure_pytesseract():
    tess_path = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
    if tess_path.exists():
        pytesseract.pytesseract.tesseract_cmd = str(tess_path)


ABSTENTION_CATEGORIES = [
    "OCR uncertainty",
    "Spatial ambiguity",
    "Header ambiguity",
    "Multi-token bleed",
    "Decimal/integer ambiguity",
    "Identifier character ambiguity",
    "Identifier syntax violation",
    "Cross-doc conflict",
    "Missing evidence",
    "Confidence floor",
    "Unsupported font",
    "Ground-truth ambiguity",
    "Processing failure",
    "Other",
]


def classify_abstention_reason(reason: str, conf: float, conf_thresh: float) -> str:
    if not reason:
        return "Other"
    r = reason.lower()
    if "identifier character-level" in r or "o vs 0" in r or "confusable" in r or "glyph" in r:
        return "Identifier character ambiguity"
    if "ifsc code structural" in r or "invalid ifsc" in r or "pan structural" in r or "syntax violation" in r:
        return "Identifier syntax violation"
    if "missing" in r or "no candidate" in r or "not extracted" in r:
        return "Missing evidence"
    if "header" in r or "column" in r or "contradicts" in r:
        return "Header ambiguity"
    if "spatial" in r or "bounding-box" in r or "bleed" in r or "gutter" in r:
        return "Spatial ambiguity"
    if "multi-token" in r or "narrow" in r:
        return "Multi-token bleed"
    if "decimal" in r or "dot" in r or "integer" in r:
        return "Decimal/integer ambiguity"
    if "font" in r or "sub-10px" in r:
        return "Unsupported font"
    if "ground-truth" in r or "chronological horizon" in r:
        return "Ground-truth ambiguity"
    if "exception" in r or "failure" in r:
        return "Processing failure"
    if conf < conf_thresh or "confidence floor" in r or "confidence below" in r or "low ocr confidence" in r:
        return "Confidence floor"
    if "ocr uncertainty" in r or "recognition confidence" in r:
        return "OCR uncertainty"
    return "Other"


def evaluate_field_record(
    grid: Any,
    field_meta: Dict[str, Any],
    doc_id: str,
    img: Image.Image,
    conf_threshold: float,
) -> Dict[str, Any]:
    field_name = field_meta["name"]
    expected_val = str(field_meta["expected"]).strip()
    target_pattern = field_meta.get("target_pattern", field_name)
    col_pattern = field_meta.get("col_pattern")
    col_idx = field_meta.get("col")
    exp_row = field_meta.get("row")
    exp_col = field_meta.get("col")
    expected_type = field_meta.get("type", "text")

    if col_pattern is not None or col_idx is not None:
        evidence = extract_cell_by_intersection(
            grid=grid,
            field_name=field_name,
            row_pattern=target_pattern,
            col_pattern=col_pattern or "",
            col_idx=col_idx,
            expected_type=expected_type,
            doc_id=doc_id,
            image=img,
        )
    else:
        evidence = extract_field_by_spatial_association(
            grid=grid,
            field_name=field_name,
            target_pattern=target_pattern,
            expected_type=expected_type,
            doc_id=doc_id,
            image=img,
        )

    if evidence is None:
        return {
            "field_name": field_name,
            "expected": expected_val,
            "extracted": "",
            "confidence": 0.0,
            "is_verified": False,
            "is_exact": False,
            "is_false_verification": False,
            "is_abstained": True,
            "status": "ABSTAIN_NOT_EXTRACTED",
            "reason": "Missing evidence / no cell found",
            "abstention_category": "Missing evidence",
            "row": -1,
            "col": -1,
        }

    ext_val = evidence.value.strip()
    conf = float(evidence.confidence)

    norm_ext = sanitize_identifier_token(ext_val).replace("₹", "").replace("Rs.", "").replace("INR", "").replace(",", "").replace("$", "").strip()
    norm_exp = sanitize_identifier_token(expected_val).replace("₹", "").replace("Rs.", "").replace("INR", "").replace(",", "").replace("$", "").strip()

    row_match = (exp_row is None or evidence.row_idx == exp_row or evidence.row_idx == exp_row + 1)
    header_matched = bool(col_pattern and evidence.col_header and col_pattern.strip().upper() in evidence.col_header.upper())
    col_match = (exp_col is None or evidence.col_idx == exp_col or header_matched)

    should_abstain = False
    raw_reason = None

    if conf < conf_threshold:
        should_abstain = True
        raw_reason = f"Confidence floor ({conf:.1f}% < {conf_threshold}%)"
    elif evidence.verification_decision == "ABSTAIN" or evidence.is_ambiguous:
        should_abstain = True
        raw_reason = evidence.abstention_reason or "Evidence flagged ambiguous"

    if should_abstain:
        cat = classify_abstention_reason(raw_reason, conf, conf_threshold)
        return {
            "field_name": field_name,
            "expected": expected_val,
            "extracted": ext_val,
            "confidence": conf,
            "is_verified": False,
            "is_exact": (norm_ext == norm_exp and row_match and col_match),
            "is_false_verification": False,
            "is_abstained": True,
            "status": f"ABSTAIN_FILTERED ({raw_reason})",
            "reason": raw_reason,
            "abstention_category": cat,
            "row": evidence.row_idx,
            "col": evidence.col_idx,
            "row_recovery_method": evidence.provenance.get("row_recovery_method", "exact_match"),
        }

    is_exact = (norm_ext == norm_exp and row_match and col_match)
    is_false_verification = not is_exact

    return {
        "field_name": field_name,
        "expected": expected_val,
        "extracted": ext_val,
        "confidence": conf,
        "is_verified": True,
        "is_exact": is_exact,
        "is_false_verification": is_false_verification,
        "is_abstained": False,
        "status": "PASS_EXACT" if is_exact else "FAIL_MISMATCH",
        "reason": None if is_exact else f"Value mismatch (got '{ext_val}', expected '{expected_val}')",
        "abstention_category": None,
        "row": evidence.row_idx,
        "col": evidence.col_idx,
        "row_recovery_method": evidence.provenance.get("row_recovery_method", "exact_match"),
    }


def compute_calibration_metrics(field_results: List[Dict[str, Any]], num_bins: int = 10) -> Dict[str, float]:
    bins = [[] for _ in range(num_bins)]
    brier_sum = 0.0
    total_evaluated = len(field_results)

    for f in field_results:
        conf_norm = max(0.0, min(1.0, f["confidence"] / 100.0))
        y_true = 1.0 if f["is_exact"] else 0.0
        brier_sum += (conf_norm - y_true) ** 2
        bin_idx = min(num_bins - 1, int(conf_norm * num_bins))
        bins[bin_idx].append((conf_norm, y_true))

    ece = 0.0
    mce = 0.0
    for b in bins:
        if not b:
            continue
        n_b = len(b)
        mean_conf = sum(x[0] for x in b) / n_b
        mean_acc = sum(x[1] for x in b) / n_b
        gap = abs(mean_acc - mean_conf)
        ece += (n_b / total_evaluated) * gap
        mce = max(mce, gap)

    brier_score = brier_sum / total_evaluated if total_evaluated > 0 else 0.0
    return {
        "ece": round(ece, 4),
        "mce": round(mce, 4),
        "brier_score": round(brier_score, 4),
    }


def compute_wilson_ci(k: int, n: int, confidence: float = 0.95) -> Tuple[float, float]:
    if n == 0:
        return 0.0, 1.0
    z = 1.959964
    p = k / n
    denominator = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denominator
    spread = z * math.sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / denominator
    return round(max(0.0, center - spread), 4), round(min(1.0, center + spread), 4)


def compute_rule_of_three_upper_bound(n: int) -> float:
    return round(3.0 / n, 4) if n > 0 else 1.0


def run_benchmark(operating_threshold: float = 70.0) -> Dict[str, Any]:
    configure_pytesseract()

    # Load manifests
    with open(L27_DIR / "dataset_manifest.json", "r", encoding="utf-8") as f:
        l_manifest = json.load(f)
    with open(L26_DIR / "dataset_manifest.json", "r", encoding="utf-8") as f:
        k_manifest = json.load(f)
    with open(L25_DIR / "dataset_manifest.json", "r", encoding="utf-8") as f:
        j_manifest = json.load(f)
    with open(L24_DIR / "dataset_manifest.json", "r", encoding="utf-8") as f:
        i_manifest = json.load(f)
    with open(L23_DIR / "results" / "benchmark_results.json", "r", encoding="utf-8") as f:
        hist_bench = json.load(f)

    all_field_results = []
    per_doc_results = {}
    per_cohort_stats = {}

    def init_cohort_stat():
        return {
            "total_fields": 0,
            "verified_claims": 0,
            "exact_matches": 0,
            "false_verifications": 0,
            "abstentions": 0,
            "abstention_breakdown": {k: 0 for k in ABSTENTION_CATEGORIES},
            "table_overheads": [],
            "latencies": [],
            "field_records": [],
        }

    # 1. Evaluate Cohort L (45 docs, 120 fields)
    print("Evaluating Cohort L (45 New Independent Public Documents)...")
    for doc in l_manifest["documents"]:
        doc_id = doc["doc_id"]
        img_path = ROOT / doc["image_path"]
        cohort_name = f"Cohort_L_{doc['split']}"
        if cohort_name not in per_cohort_stats:
            per_cohort_stats[cohort_name] = init_cohort_stat()

        t0 = time.perf_counter()
        img = Image.open(img_path).convert("RGB")
        ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

        t_table_0 = time.perf_counter()
        grid = build_table_grid(ocr_data, page_width=img.width, page_height=img.height, image=img)
        t_table_1 = time.perf_counter()
        table_overhead_ms = (t_table_1 - t_table_0) * 1000.0

        doc_fields = []
        for cf in doc["critical_fields"]:
            f_meta = {
                "name": cf["field_name"],
                "expected": cf["expected_value"],
                "type": cf.get("expected_type", "text"),
                "target_pattern": cf.get("target_pattern", cf["field_name"]),
            }
            rec = evaluate_field_record(grid, f_meta, doc_id, img, operating_threshold)
            doc_fields.append(rec)
            all_field_results.append(rec)

            st = per_cohort_stats[cohort_name]
            st["total_fields"] += 1
            if rec["is_verified"]:
                st["verified_claims"] += 1
                if rec["is_exact"]:
                    st["exact_matches"] += 1
                else:
                    st["false_verifications"] += 1
            else:
                st["abstentions"] += 1
                cat = rec["abstention_category"]
                if cat in st["abstention_breakdown"]:
                    st["abstention_breakdown"][cat] += 1
            st["field_records"].append(rec)

        t1 = time.perf_counter()
        total_ms = (t1 - t0) * 1000.0

        per_cohort_stats[cohort_name]["table_overheads"].append(table_overhead_ms)
        per_cohort_stats[cohort_name]["latencies"].append(total_ms)

        per_doc_results[doc_id] = {
            "cohort": cohort_name,
            "overhead_ms": round(table_overhead_ms, 2),
            "total_ms": round(total_ms, 2),
            "fields": doc_fields,
        }

    # 2. Evaluate Cohort K (60 docs, 307 fields)
    print("Evaluating Cohort K (60 Independent Public Baseline Documents)...")
    for doc in k_manifest["documents"]:
        doc_id = doc["doc_id"]
        img_path = ROOT / doc["image_path"]
        cohort_name = f"Cohort_K_{doc['split']}"
        if cohort_name not in per_cohort_stats:
            per_cohort_stats[cohort_name] = init_cohort_stat()

        t0 = time.perf_counter()
        img = Image.open(img_path).convert("RGB")
        ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)

        t_table_0 = time.perf_counter()
        grid = build_table_grid(ocr_data, page_width=img.width, page_height=img.height, image=img)
        t_table_1 = time.perf_counter()
        table_overhead_ms = (t_table_1 - t_table_0) * 1000.0

        doc_fields = []
        for cf in doc["critical_fields"]:
            f_meta = {
                "name": cf["field_name"],
                "expected": cf["expected_value"],
                "type": cf.get("expected_type", "text"),
                "target_pattern": cf["field_name"],
            }
            rec = evaluate_field_record(grid, f_meta, doc_id, img, operating_threshold)
            doc_fields.append(rec)
            all_field_results.append(rec)

            st = per_cohort_stats[cohort_name]
            st["total_fields"] += 1
            if rec["is_verified"]:
                st["verified_claims"] += 1
                if rec["is_exact"]:
                    st["exact_matches"] += 1
                else:
                    st["false_verifications"] += 1
            else:
                st["abstentions"] += 1
                cat = rec["abstention_category"]
                if cat in st["abstention_breakdown"]:
                    st["abstention_breakdown"][cat] += 1
            st["field_records"].append(rec)

        t1 = time.perf_counter()
        total_ms = (t1 - t0) * 1000.0

        per_cohort_stats[cohort_name]["table_overheads"].append(table_overhead_ms)
        per_cohort_stats[cohort_name]["latencies"].append(total_ms)

        per_doc_results[doc_id] = {
            "cohort": cohort_name,
            "overhead_ms": round(table_overhead_ms, 2),
            "total_ms": round(total_ms, 2),
            "fields": doc_fields,
        }

    # Helper to normalize historical field records
    def normalize_hist_field(fld: Dict[str, Any]) -> Dict[str, Any]:
        is_ver = bool(fld.get("is_verified", False))
        is_ex = bool(fld.get("is_exact", (fld.get("status") == "PASS_SPATIAL_EXACT" or (is_ver and not fld.get("is_false_verification", False)))))
        is_fls = bool(fld.get("is_false_verification", False) or (is_ver and not is_ex))
        is_abs = bool(fld.get("is_abstained", not is_ver))
        return {
            "field_name": fld["field_name"],
            "expected": fld.get("expected", ""),
            "extracted": fld.get("extracted", fld.get("extracted_value", "")),
            "confidence": float(fld.get("confidence", 0.0)),
            "is_verified": is_ver,
            "is_exact": is_ex,
            "is_false_verification": is_fls,
            "is_abstained": is_abs,
            "status": fld.get("status", "UNKNOWN"),
            "reason": fld.get("reason", fld.get("abstention_reason", None)),
            "abstention_category": fld.get("abstention_category", "Other"),
            "row": fld.get("row", -1),
            "col": fld.get("col", -1),
        }

    # 3. Incorporate Cohort J (60 docs, 201 fields - synthetic large scale)
    print("Incorporate Cohort J (60 Synthetic Documents)...")
    cohort_j_name = "Cohort_J_Synthetic"
    per_cohort_stats[cohort_j_name] = init_cohort_stat()
    with open(L26_DIR / "results" / "benchmark_results.json", "r", encoding="utf-8") as f:
        l26_bench = json.load(f)
    for doc_id, doc_info in l26_bench["per_document"].items():
        if "COHORT_J" in doc_id:
            norm_fields = [normalize_hist_field(f) for f in doc_info["fields"]]
            per_doc_results[doc_id] = {
                "cohort": cohort_j_name,
                "overhead_ms": doc_info["overhead_ms"],
                "total_ms": doc_info["total_ms"],
                "fields": norm_fields,
            }
            per_cohort_stats[cohort_j_name]["table_overheads"].append(doc_info["overhead_ms"])
            per_cohort_stats[cohort_j_name]["latencies"].append(doc_info["total_ms"])
            for fld in norm_fields:
                all_field_results.append(fld)
                st = per_cohort_stats[cohort_j_name]
                st["total_fields"] += 1
                if fld["is_verified"]:
                    st["verified_claims"] += 1
                    if fld["is_exact"]:
                        st["exact_matches"] += 1
                    else:
                        st["false_verifications"] += 1
                else:
                    st["abstentions"] += 1
                    cat = fld.get("abstention_category", "Other")
                    if cat in st["abstention_breakdown"]:
                        st["abstention_breakdown"][cat] += 1
                st["field_records"].append(fld)

    # 4. Incorporate Cohort I (30 docs, 102 fields)
    print("Incorporate Cohort I (30 Blind Generalization Documents)...")
    cohort_i_name = "Cohort_I_Blind"
    per_cohort_stats[cohort_i_name] = init_cohort_stat()
    for doc_id, doc_info in l26_bench["per_document"].items():
        if "COHORT_I" in doc_id or "COHORT_H" in doc_id:
            norm_fields = [normalize_hist_field(f) for f in doc_info["fields"]]
            per_doc_results[doc_id] = {
                "cohort": cohort_i_name,
                "overhead_ms": doc_info["overhead_ms"],
                "total_ms": doc_info["total_ms"],
                "fields": norm_fields,
            }
            per_cohort_stats[cohort_i_name]["table_overheads"].append(doc_info["overhead_ms"])
            per_cohort_stats[cohort_i_name]["latencies"].append(doc_info["total_ms"])
            for fld in norm_fields:
                all_field_results.append(fld)
                st = per_cohort_stats[cohort_i_name]
                st["total_fields"] += 1
                if fld["is_verified"]:
                    st["verified_claims"] += 1
                    if fld["is_exact"]:
                        st["exact_matches"] += 1
                    else:
                        st["false_verifications"] += 1
                else:
                    st["abstentions"] += 1
                    cat = fld.get("abstention_category", "Other")
                    if cat in st["abstention_breakdown"]:
                        st["abstention_breakdown"][cat] += 1
                st["field_records"].append(fld)

    # 5. Incorporate Historical Loops 20-23 (52 docs, 113 fields)
    print("Incorporate Historical Loops 20-23 (52 Documents)...")
    hist_name = "Historical_Loops_20_23"
    per_cohort_stats[hist_name] = init_cohort_stat()
    for doc_id, doc_info in l26_bench["per_document"].items():
        if any(h in doc_id for h in ["VAL_", "CHALL_", "STRESS_", "DEC_", "GUTTER_"]) and not doc_id.startswith("COHORT_"):
            norm_fields = [normalize_hist_field(f) for f in doc_info["fields"]]
            per_doc_results[doc_id] = {
                "cohort": hist_name,
                "overhead_ms": doc_info["overhead_ms"],
                "total_ms": doc_info["total_ms"],
                "fields": norm_fields,
            }
            per_cohort_stats[hist_name]["table_overheads"].append(doc_info["overhead_ms"])
            per_cohort_stats[hist_name]["latencies"].append(doc_info["total_ms"])
            for fld in norm_fields:
                all_field_results.append(fld)
                st = per_cohort_stats[hist_name]
                st["total_fields"] += 1
                if fld["is_verified"]:
                    st["verified_claims"] += 1
                    if fld["is_exact"]:
                        st["exact_matches"] += 1
                    else:
                        st["false_verifications"] += 1
                else:
                    st["abstentions"] += 1
                    cat = fld.get("abstention_category", "Other")
                    if cat in st["abstention_breakdown"]:
                        st["abstention_breakdown"][cat] += 1
                st["field_records"].append(fld)

    # Aggregate summaries
    total_docs = len(per_doc_results)
    total_fields = len(all_field_results)
    total_verified = sum(1 for f in all_field_results if f["is_verified"])
    total_exact = sum(1 for f in all_field_results if f["is_verified"] and f["is_exact"])
    total_false = sum(1 for f in all_field_results if f["is_verified"] and not f["is_exact"])
    total_abstain = sum(1 for f in all_field_results if f["is_abstained"])

    precision = round((total_exact / total_verified) * 100, 2) if total_verified > 0 else 100.0
    fvr = round((total_false / total_verified) * 100, 2) if total_verified > 0 else 0.0
    coverage = round((total_verified / total_fields) * 100, 2)
    abstention_rate = round((total_abstain / total_fields) * 100, 2)

    all_overheads = [d["overhead_ms"] for d in per_doc_results.values()]
    all_latencies = [d["total_ms"] for d in per_doc_results.values()]

    mean_overhead = round(float(np.mean(all_overheads)), 2)
    p95_overhead = round(float(np.percentile(all_overheads, 95)), 2)
    mean_latency = round(float(np.mean(all_latencies)), 2)
    p95_latency = round(float(np.percentile(all_latencies, 95)), 2)

    calib = compute_calibration_metrics(all_field_results)
    prec_ci = compute_wilson_ci(total_exact, total_verified)
    fvr_ci = compute_wilson_ci(total_false, total_verified)
    rule_of_three_risk = compute_rule_of_three_upper_bound(total_verified)

    # Summarize per-cohort
    cohort_summaries = {}
    for c_name, c_st in per_cohort_stats.items():
        v = c_st["verified_claims"]
        e = c_st["exact_matches"]
        f_cnt = c_st["false_verifications"]
        tot = c_st["total_fields"]
        prec = round((e / v) * 100, 2) if v > 0 else 100.0
        cov = round((v / tot) * 100, 2) if tot > 0 else 0.0
        c_fvr = round((f_cnt / v) * 100, 2) if v > 0 else 0.0
        upper_bound = compute_rule_of_three_upper_bound(v) if f_cnt == 0 else compute_wilson_ci(f_cnt, v)[1] * 100.0

        cohort_summaries[c_name] = {
            "total_fields": tot,
            "verified_claims": v,
            "exact_matches": e,
            "false_verifications": f_cnt,
            "abstentions": c_st["abstentions"],
            "precision_pct": prec,
            "false_verification_rate_pct": c_fvr,
            "coverage_pct": cov,
            "upper_risk_bound_pct": round(upper_bound, 2),
            "mean_table_overhead_ms": round(float(np.mean(c_st["table_overheads"])), 2) if c_st["table_overheads"] else 0.0,
            "mean_latency_ms": round(float(np.mean(c_st["latencies"])), 2) if c_st["latencies"] else 0.0,
            "abstention_breakdown": c_st["abstention_breakdown"],
        }

    return {
        "benchmark_version": "27.0.0",
        "loop": 27,
        "operating_threshold": operating_threshold,
        "summary": {
            "total_documents": total_docs,
            "total_critical_fields": total_fields,
            "verified_claims": total_verified,
            "exact_matches": total_exact,
            "false_verifications": total_false,
            "abstentions": total_abstain,
            "verified_precision_pct": precision,
            "false_verification_rate_pct": fvr,
            "coverage_pct": coverage,
            "abstention_rate_pct": abstention_rate,
            "rule_of_three_upper_risk_bound_pct": round(rule_of_three_risk * 100, 2),
            "precision_95_wilson_ci": [round(prec_ci[0] * 100, 2), round(prec_ci[1] * 100, 2)],
            "fvr_95_wilson_ci": [round(fvr_ci[0] * 100, 2), round(fvr_ci[1] * 100, 2)],
            "mean_table_overhead_ms": mean_overhead,
            "p95_table_overhead_ms": p95_overhead,
            "mean_total_latency_ms": mean_latency,
            "p95_total_latency_ms": p95_latency,
            "calibration": calib,
        },
        "per_cohort": cohort_summaries,
        "per_document": per_doc_results,
    }


if __name__ == "__main__":
    print("Starting Loop 27 Double Benchmark Execution...")
    run1 = run_benchmark(70.0)
    with open(RESULTS_DIR / "benchmark_run1.json", "w", encoding="utf-8") as f:
        json.dump(run1, f, indent=2)

    print("Running Bit-Exact Verification Run 2...")
    run2 = run_benchmark(70.0)
    with open(RESULTS_DIR / "benchmark_run2.json", "w", encoding="utf-8") as f:
        json.dump(run2, f, indent=2)

    # Check determinism
    diffs = 0
    for doc_id in run1["per_document"]:
        f1 = run1["per_document"][doc_id]["fields"]
        f2 = run2["per_document"][doc_id]["fields"]
        for a, b in zip(f1, f2):
            if a["extracted"] != b["extracted"] or a["is_verified"] != b["is_verified"] or a["is_exact"] != b["is_exact"]:
                diffs += 1

    print(f"Determinism Check: {diffs} discrepancies between Run 1 and Run 2")
    with open(RESULTS_DIR / "benchmark_results.json", "w", encoding="utf-8") as f:
        json.dump(run1, f, indent=2)

    s = run1["summary"]
    print("\n================== LOOP 27 BENCHMARK SUMMARY ==================")
    print(f"Total Documents       : {s['total_documents']}")
    print(f"Total Critical Fields : {s['total_critical_fields']}")
    print(f"Verified Claims (V)   : {s['verified_claims']}")
    print(f"Exact Matches (E)     : {s['exact_matches']}")
    print(f"False Verifications (F): {s['false_verifications']}")
    print(f"Abstentions (A)       : {s['abstentions']}")
    print(f"Verified Precision    : {s['verified_precision_pct']}%")
    print(f"False Verification Rt : {s['false_verification_rate_pct']}%")
    print(f"Coverage              : {s['coverage_pct']}%")
    print(f"Abstention Rate       : {s['abstention_rate_pct']}%")
    print(f"Mean Table Overhead   : {s['mean_table_overhead_ms']} ms (p95: {s['p95_table_overhead_ms']} ms)")
    print(f"Mean Total Latency    : {s['mean_total_latency_ms']} ms (p95: {s['p95_total_latency_ms']} ms)")
    print(f"ECE                   : {s['calibration']['ece']}, MCE: {s['calibration']['mce']}, Brier: {s['calibration']['brier_score']}")
    print("===============================================================")
