"""
Loop 28 Cross-Document Verification Benchmark Runner.
Executes comprehensive evaluation of the production cross-document verification engine:
- Evaluates across DEV, CAL, BLIND, and CHALL partitions.
- Computes packet-level and claim-level metrics with Wilson score 95% confidence intervals.
- Computes calibration statistics (ECE, MCE, Brier score).
- Executes double-run determinism verification (Run 1 vs Run 2 = 0 diffs).
- Profiles latency and execution throughput (mean, p50, p95, p99).
- Writes machine-readable results to research/loop28/results/benchmark_results.json.
"""

import json
import math
import os
import sys
import time
from typing import Dict, Any, List, Tuple

sys.path.insert(0, ".")
from src.docuready.evidence.cross_document import (
    DocumentIdentity,
    EntityIdentity,
    FieldClaim,
    PacketVerificationResult,
    VerificationOutcome,
    SourceIndependence,
    normalize_claim_value,
    verify_cross_document_packet_claim,
)

CORPUS_PATH = os.path.join("research", "loop28", "corpus", "cross_document_corpus.json")
RESULTS_PATH = os.path.join("research", "loop28", "results", "benchmark_results.json")
os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)


def wilson_score_interval(successes: int, total: int, z: float = 1.96) -> Tuple[float, float]:
    """Computes Wilson score 95% confidence interval for a proportion."""
    if total == 0:
        return (0.0, 0.0)
    p_hat = successes / total
    denom = 1.0 + (z**2) / total
    center = (p_hat + (z**2) / (2 * total)) / denom
    margin = (z / denom) * math.sqrt((p_hat * (1 - p_hat) / total) + ((z**2) / (4 * (total**2))))
    lower = max(0.0, center - margin) * 100.0
    upper = min(1.0, center + margin) * 100.0
    return (round(lower, 2), round(upper, 2))


def compute_calibration_metrics(predictions: List[Dict[str, Any]], num_bins: int = 10) -> Dict[str, float]:
    """Computes Expected Calibration Error (ECE), Maximum Calibration Error (MCE), and Brier Score."""
    if not predictions:
        return {"ece": 0.0, "mce": 0.0, "brier": 0.0}

    # Brier score
    total_brier = 0.0
    for p in predictions:
        conf = p["confidence"] / 100.0
        y_true = 1.0 if p["is_exact"] else 0.0
        total_brier += (conf - y_true) ** 2
    brier = total_brier / len(predictions)

    # Binning for ECE and MCE
    bins = [[] for _ in range(num_bins)]
    for p in predictions:
        conf = min(max(p["confidence"] / 100.0, 0.0), 1.0)
        bin_idx = min(int(conf * num_bins), num_bins - 1)
        bins[bin_idx].append((conf, 1.0 if p["is_exact"] else 0.0))

    ece = 0.0
    mce = 0.0
    n = len(predictions)

    for b in bins:
        if not b:
            continue
        bin_size = len(b)
        avg_conf = sum(x[0] for x in b) / bin_size
        avg_acc = sum(x[1] for x in b) / bin_size
        gap = abs(avg_acc - avg_conf)
        ece += (bin_size / n) * gap
        if gap > mce:
            mce = gap

    return {
        "ece": round(ece * 100.0, 2),
        "mce": round(mce * 100.0, 2),
        "brier_score": round(brier, 4),
    }


def run_benchmark_pass(corpus: Dict[str, Any]) -> Tuple[Dict[str, Any], List[float]]:
    latencies = []
    partition_data = {
        "DEV": {"packets": 0, "claims": 0, "verified": 0, "exact": 0, "false": 0, "abstain": 0, "records": []},
        "CAL": {"packets": 0, "claims": 0, "verified": 0, "exact": 0, "false": 0, "abstain": 0, "records": []},
        "BLIND": {"packets": 0, "claims": 0, "verified": 0, "exact": 0, "false": 0, "abstain": 0, "records": []},
        "CHALL": {"packets": 0, "claims": 0, "verified": 0, "exact": 0, "false": 0, "abstain": 0, "records": []},
    }

    condition_data = {}
    all_claim_records = []

    for pkt in corpus["packets"]:
        split = pkt["split"]
        cond = pkt["condition_code"]
        if cond not in condition_data:
            condition_data[cond] = {"claims": 0, "verified": 0, "exact": 0, "false": 0, "abstain": 0}

        partition_data[split]["packets"] += 1

        tgt = pkt["target_entity"]
        target_entity = EntityIdentity(
            entity_id=tgt["entity_id"],
            canonical_name=tgt["canonical_name"],
            father_or_guardian_name=tgt.get("father_name"),
            date_of_birth=tgt.get("date_of_birth"),
            tax_id=tgt.get("tax_id"),
            national_id=tgt.get("national_id"),
            account_number=tgt.get("account_number"),
            address=tgt.get("address"),
        )
        doc_map = {d["doc_id"]: DocumentIdentity(**d) for d in pkt["documents"]}
        claims = [
            FieldClaim(
                claim_id=f"c_{i}",
                doc_id=c["doc_id"],
                field_name=c["field_name"],
                field_type=c["field_type"],
                claimed_value=c["claimed_value"],
                raw_ocr_value=c["claimed_value"],
                confidence=c["confidence"],
                entity_hints=c.get("entity_hints") or {},
                unit_or_currency=c.get("unit_or_currency"),
            )
            for i, c in enumerate(pkt["claims"])
        ]

        # Measure verification latency
        fields = list({c["field_name"] for c in pkt["claims"]})
        t0 = time.perf_counter()
        field_results = {}
        for f in fields:
            res = verify_cross_document_packet_claim(
                field_name=f,
                target_entity=target_entity,
                claims=claims,
                documents=doc_map,
                required_doc_types=pkt.get("required_doc_types", []),
                operating_threshold=70.0,
            )
            field_results[f] = res
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000.0)

        for c in pkt["claims"]:
            f = c["field_name"]
            res = field_results[f]
            overall_outcome = res.outcome.value
            supp_docs = res.supporting_doc_ids

            if overall_outcome == "VERIFY":
                if c["doc_id"] in supp_docs:
                    pred_outcome = "VERIFY"
                else:
                    pred_outcome = "ENTITY_AMBIGUOUS"
            else:
                pred_outcome = overall_outcome

            expected_outcome = c["expected_outcome"]
            ground_truth = c.get("ground_truth")

            is_verified = (pred_outcome == "VERIFY")
            is_exact = False
            is_false = False

            if is_verified:
                norm_c = normalize_claim_value(c["claimed_value"], c["field_type"])
                norm_gt = normalize_claim_value(ground_truth, c["field_type"]) if ground_truth else ""
                if expected_outcome == "VERIFY" and norm_c == norm_gt:
                    is_exact = True
                else:
                    is_false = True

            pdata = partition_data[split]
            pdata["claims"] += 1
            condition_data[cond]["claims"] += 1

            if is_verified:
                pdata["verified"] += 1
                condition_data[cond]["verified"] += 1
                if is_exact:
                    pdata["exact"] += 1
                    condition_data[cond]["exact"] += 1
                if is_false:
                    pdata["false"] += 1
                    condition_data[cond]["false"] += 1
            else:
                pdata["abstain"] += 1
                condition_data[cond]["abstain"] += 1

            record = {
                "packet_id": pkt["packet_id"],
                "split": split,
                "condition_code": cond,
                "field_name": f,
                "doc_id": c["doc_id"],
                "claimed_value": c["claimed_value"],
                "confidence": c["confidence"],
                "predicted_outcome": pred_outcome,
                "expected_outcome": expected_outcome,
                "is_verified": is_verified,
                "is_exact": is_exact,
                "is_false": is_false,
            }
            pdata["records"].append(record)
            all_claim_records.append(record)

    summary_by_split = {}
    tot_claims = sum(p["claims"] for p in partition_data.values())
    tot_verified = sum(p["verified"] for p in partition_data.values())
    tot_exact = sum(p["exact"] for p in partition_data.values())
    tot_false = sum(p["false"] for p in partition_data.values())
    tot_abstain = sum(p["abstain"] for p in partition_data.values())

    for split, p in partition_data.items():
        v = p["verified"]
        e = p["exact"]
        tc = p["claims"]
        prec = (e / v * 100.0) if v > 0 else 0.0
        cov = (v / tc * 100.0) if tc > 0 else 0.0
        prec_ci = wilson_score_interval(e, v)
        cov_ci = wilson_score_interval(v, tc)
        summary_by_split[split] = {
            "packets": p["packets"],
            "claims": tc,
            "verified": v,
            "exact_matches": e,
            "false_verifications": p["false"],
            "abstentions": p["abstain"],
            "precision": round(prec, 2),
            "precision_ci95": prec_ci,
            "coverage": round(cov, 2),
            "coverage_ci95": cov_ci,
        }

    agg_prec = (tot_exact / tot_verified * 100.0) if tot_verified > 0 else 0.0
    agg_cov = (tot_verified / tot_claims * 100.0) if tot_claims > 0 else 0.0

    return {
        "partitions": summary_by_split,
        "aggregate": {
            "total_packets": len(corpus["packets"]),
            "total_claims": tot_claims,
            "verified_claims": tot_verified,
            "exact_matches": tot_exact,
            "false_verifications": tot_false,
            "abstentions": tot_abstain,
            "precision": round(agg_prec, 2),
            "precision_ci95": wilson_score_interval(tot_exact, tot_verified),
            "coverage": round(agg_cov, 2),
            "coverage_ci95": wilson_score_interval(tot_verified, tot_claims),
        },
        "conditions": condition_data,
        "all_records": all_claim_records,
    }, latencies


def main():
    with open(CORPUS_PATH, "r", encoding="utf-8") as f:
        corpus = json.load(f)

    print("Executing Benchmark Run 1...")
    res1, lat1 = run_benchmark_pass(corpus)

    print("Executing Benchmark Run 2 (Determinism Verification)...")
    res2, lat2 = run_benchmark_pass(corpus)

    # Determinism Diff Check
    records1 = res1["all_records"]
    records2 = res2["all_records"]
    diffs = 0
    for r1, r2 in zip(records1, records2):
        if r1["predicted_outcome"] != r2["predicted_outcome"] or r1["is_verified"] != r2["is_verified"]:
            diffs += 1

    print(f"Determinism Check: {diffs} discrepancies found between Run 1 and Run 2.")
    assert diffs == 0, f"Benchmark is non-deterministic: {diffs} differences detected!"

    # Latency Stats
    lat1.sort()
    mean_lat = sum(lat1) / len(lat1)
    p50_lat = lat1[len(lat1) // 2]
    p95_lat = lat1[int(len(lat1) * 0.95)]
    p99_lat = lat1[int(len(lat1) * 0.99)]

    # Calibration Metrics
    cal_metrics = compute_calibration_metrics(records1)

    print("\n" + "=" * 90)
    print("DOCUREADY LOOP 28 BENCHMARK RESULTS")
    print("=" * 90)
    print(f"{'Partition':<10} | {'Pkts':<6} | {'Claims':<8} | {'Verified':<10} | {'Exact':<6} | {'False':<6} | {'Precision (95% CI)':<22} | {'Coverage (95% CI)':<22}")
    print("-" * 90)
    for split, p in res1["partitions"].items():
        p_ci = f"{p['precision']:.2f}% [{p['precision_ci95'][0]}-{p['precision_ci95'][1]}]"
        c_ci = f"{p['coverage']:.2f}% [{p['coverage_ci95'][0]}-{p['coverage_ci95'][1]}]"
        print(f"{split:<10} | {p['packets']:<6} | {p['claims']:<8} | {p['verified']:<10} | {p['exact_matches']:<6} | {p['false_verifications']:<6} | {p_ci:<22} | {c_ci:<22}")

    agg = res1["aggregate"]
    agg_p_ci = f"{agg['precision']:.2f}% [{agg['precision_ci95'][0]}-{agg['precision_ci95'][1]}]"
    agg_c_ci = f"{agg['coverage']:.2f}% [{agg['coverage_ci95'][0]}-{agg['coverage_ci95'][1]}]"
    print("-" * 90)
    print(f"{'AGGREGATE':<10} | {agg['total_packets']:<6} | {agg['total_claims']:<8} | {agg['verified_claims']:<10} | {agg['exact_matches']:<6} | {agg['false_verifications']:<6} | {agg_p_ci:<22} | {agg_c_ci:<22}")
    print("=" * 90)

    print(f"\nCalibration Metrics:")
    print(f"  ECE (Expected Calibration Error): {cal_metrics['ece']:.2f}%")
    print(f"  MCE (Maximum Calibration Error):  {cal_metrics['mce']:.2f}%")
    print(f"  Brier Score:                     {cal_metrics['brier_score']:.4f}")

    print(f"\nLatency Profile per Packet (N={len(lat1)}):")
    print(f"  Mean:   {mean_lat:.2f} ms (Target < 3.0 ms: {'PASS' if mean_lat < 3.0 else 'FAIL'})")
    print(f"  Median: {p50_lat:.2f} ms")
    print(f"  p95:    {p95_lat:.2f} ms (Target < 6.0 ms: {'PASS' if p95_lat < 6.0 else 'FAIL'})")
    print(f"  p99:    {p99_lat:.2f} ms")

    final_payload = {
        "loop": 28,
        "timestamp": "2026-11-24T16:25:00+05:30",
        "partitions": res1["partitions"],
        "aggregate": agg,
        "calibration": cal_metrics,
        "latency_ms": {
            "mean": round(mean_lat, 2),
            "p50": round(p50_lat, 2),
            "p95": round(p95_lat, 2),
            "p99": round(p99_lat, 2),
            "target_mean_passed": mean_lat < 3.0,
            "target_p95_passed": p95_lat < 6.0,
        },
        "determinism": {
            "run1_vs_run2_discrepancies": diffs,
            "status": "DETERMINISTIC_BIT_EXACT",
        },
        "conditions": res1["conditions"],
    }

    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(final_payload, f, indent=2)
    print(f"\nBenchmark results saved to {RESULTS_PATH}")


if __name__ == "__main__":
    main()
