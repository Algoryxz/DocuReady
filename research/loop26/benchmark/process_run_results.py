import json
from pathlib import Path
import numpy as np
import math

res_dir = Path("research/loop26/results")
with open(res_dir / "benchmark_run1.json", "r", encoding="utf-8") as f:
    run1 = json.load(f)

per_cohort = run1["per_cohort"]

def compute_wilson_ci(k: int, n: int) -> list:
    if n == 0:
        return [0.0, 1.0]
    z = 1.959964
    p = k / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    spread = z * math.sqrt((p * (1 - p) + z**2 / (4 * n)) / n) / denom
    return [round(max(0.0, center - spread), 4), round(min(1.0, center + spread), 4)]

def summarize_cohort_group(match_fn):
    tot_fields = sum(v["total_fields"] for k, v in per_cohort.items() if match_fn(k))
    v_claims = sum(v["verified_claims"] for k, v in per_cohort.items() if match_fn(k))
    e_matches = sum(v["exact_matches"] for k, v in per_cohort.items() if match_fn(k))
    f_verifs = sum(v["false_verifications"] for k, v in per_cohort.items() if match_fn(k))
    absts = sum(v["abstentions"] for k, v in per_cohort.items() if match_fn(k))

    prec = round((e_matches / v_claims * 100.0) if v_claims > 0 else 100.0, 2)
    cov = round((v_claims / tot_fields * 100.0) if tot_fields > 0 else 0.0, 2)
    fvr = round((f_verifs / v_claims * 100.0) if v_claims > 0 else 0.0, 2)
    upper_risk = round(3.0 / v_claims, 4) if f_verifs == 0 and v_claims > 0 else (round(f_verifs / v_claims, 4) if v_claims > 0 else 0.0)

    return {
        "total_fields": tot_fields,
        "verified_claims": v_claims,
        "exact_matches": e_matches,
        "false_verifications": f_verifs,
        "abstentions": absts,
        "precision": prec,
        "precision_ci_95": compute_wilson_ci(e_matches, v_claims),
        "coverage": cov,
        "coverage_ci_95": compute_wilson_ci(v_claims, tot_fields),
        "false_verification_rate": fvr,
        "upper_risk_bound_95": upper_risk,
    }

k_sum = summarize_cohort_group(lambda k: k.startswith("Cohort_K"))
j_sum = summarize_cohort_group(lambda k: k.startswith("J_"))
i_sum = summarize_cohort_group(lambda k: k.startswith("I_"))
hist_sum = summarize_cohort_group(lambda k: not k.startswith("Cohort_K") and not k.startswith("J_") and not k.startswith("I_"))

run1["cohort_k_summary"] = {**run1["cohort_k_summary"], **k_sum}
run1["cohort_j_summary"] = {**run1["cohort_j_summary"], **j_sum}
run1["cohort_i_summary"] = {**run1["cohort_i_summary"], **i_sum}
run1["historical_summary"] = hist_sum

# Per-split breakdown for Cohort K
k_dev = summarize_cohort_group(lambda k: k == "Cohort_K_DEV")
k_cal = summarize_cohort_group(lambda k: k == "Cohort_K_CAL")
k_blind = summarize_cohort_group(lambda k: k == "Cohort_K_BLIND")
k_chall = summarize_cohort_group(lambda k: k == "Cohort_K_CHALL")
run1["cohort_k_splits"] = {
    "DEV": k_dev,
    "CAL": k_cal,
    "BLIND": k_blind,
    "CHALL": k_chall,
}

with open(res_dir / "benchmark_results.json", "w", encoding="utf-8") as f:
    json.dump(run1, f, indent=2)

print("=== RECONCILED LOOP 26 SCOREBOARD ===")
print("Cohort K (Independent Public, 60 docs):", k_sum)
print("  - DEV (15 docs):", k_dev["verified_claims"], "/", k_dev["total_fields"], f"({k_dev['coverage']}%)", f"prec={k_dev['precision']}%", f"false={k_dev['false_verifications']}")
print("  - CAL (15 docs):", k_cal["verified_claims"], "/", k_cal["total_fields"], f"({k_cal['coverage']}%)", f"prec={k_cal['precision']}%", f"false={k_cal['false_verifications']}")
print("  - BLIND (20 docs):", k_blind["verified_claims"], "/", k_blind["total_fields"], f"({k_blind['coverage']}%)", f"prec={k_blind['precision']}%", f"false={k_blind['false_verifications']}")
print("  - CHALL (10 docs):", k_chall["verified_claims"], "/", k_chall["total_fields"], f"({k_chall['coverage']}%)", f"prec={k_chall['precision']}%", f"false={k_chall['false_verifications']}")
print("\nCohort J (Loop 25 Synthetic, 60 docs):", j_sum)
print("Cohort I (Loop 24 Blind, 30 docs):", i_sum)
print("Historical (Loops 20-23, 52 docs):", hist_sum)
comb = run1["combined_summary"]
print(f"\nCombined Benchmark (202 docs, 723 fields): {comb['total_fields']} fields, {comb['verified_claims']} verified, {comb['exact_matches']} exact, {comb['false_verifications']} false, {comb['precision']}% prec, {comb['coverage']}% cov")
