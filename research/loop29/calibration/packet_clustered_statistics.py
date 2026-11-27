"""
Packet-Clustered Statistical Reliability & Uncertainty Estimation for Loop 29.
Performs clustered block bootstrap (resampling whole packets with replacement, B=2000)
to produce defensible 95% confidence intervals accounting for within-packet claim correlation.
"""

import json
import math
import os
import random
import sys
from typing import Dict, Any, List

sys.path.insert(0, ".")
from src.docuready.evidence.cross_document import (
    DocumentIdentity, EntityIdentity, FieldClaim,
    verify_cross_document_packet_claim, normalize_claim_value
)

with open("research/loop28/corpus/cross_document_corpus.json", "r", encoding="utf-8") as f:
    corpus = json.load(f)

# Evaluate each packet and collect packet-level results
evaluated_packets = []
for pkt in corpus["packets"]:
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

    fields = list({c["field_name"] for c in pkt["claims"]})
    field_results = {}
    for f_name in fields:
        res = verify_cross_document_packet_claim(
            field_name=f_name,
            target_entity=target_entity,
            claims=claims,
            documents=doc_map,
            required_doc_types=pkt.get("required_doc_types", []),
            operating_threshold=70.0,
        )
        field_results[f_name] = res

    pkt_claims_eval = []
    has_verified = False
    has_false = False

    for c in pkt["claims"]:
        f_name = c["field_name"]
        res = field_results[f_name]
        supp_docs = res.supporting_doc_ids

        if res.outcome.value == "VERIFY":
            if c["doc_id"] in supp_docs:
                pred_outcome = "VERIFY"
            else:
                pred_outcome = "ENTITY_AMBIGUOUS"
        else:
            pred_outcome = res.outcome.value

        is_ver = (pred_outcome == "VERIFY")
        is_exact = False
        is_false = False

        if is_ver:
            has_verified = True
            norm_c = normalize_claim_value(c["claimed_value"], c["field_type"])
            norm_gt = normalize_claim_value(c.get("ground_truth"), c["field_type"]) if c.get("ground_truth") else ""
            if c["expected_outcome"] == "VERIFY" and norm_c == norm_gt:
                is_exact = True
            else:
                is_false = True
                has_false = True

        pkt_claims_eval.append({
            "field_name": f_name,
            "is_verified": is_ver,
            "is_exact": is_exact,
            "is_false": is_false,
        })

    evaluated_packets.append({
        "packet_id": pkt["packet_id"],
        "split": pkt["split"],
        "condition_code": pkt["condition_code"],
        "claims": pkt_claims_eval,
        "total_claims": len(pkt_claims_eval),
        "verified_count": sum(1 for c in pkt_claims_eval if c["is_verified"]),
        "exact_count": sum(1 for c in pkt_claims_eval if c["is_exact"]),
        "false_count": sum(1 for c in pkt_claims_eval if c["is_false"]),
        "has_verified_claim": has_verified,
        "has_false_verification": has_false,
        "is_all_abstained": not has_verified,
    })

def run_packet_bootstrap(packets: List[Dict[str, Any]], B: int = 2000, seed: int = 42):
    random.seed(seed)
    n = len(packets)
    if n == 0:
        return {}

    boot_claim_prec = []
    boot_claim_cov = []
    boot_pkt_cov = []
    boot_pkt_prec = []

    for _ in range(B):
        sample = [random.choice(packets) for _ in range(n)]
        tot_c = sum(p["total_claims"] for p in sample)
        ver_c = sum(p["verified_count"] for p in sample)
        ext_c = sum(p["exact_count"] for p in sample)
        fal_c = sum(p["false_count"] for p in sample)

        pkt_ver = sum(1 for p in sample if p["has_verified_claim"])
        pkt_fal = sum(1 for p in sample if p["has_false_verification"])

        claim_prec = (ext_c / ver_c * 100.0) if ver_c > 0 else 100.0
        claim_cov = (ver_c / tot_c * 100.0) if tot_c > 0 else 0.0
        pkt_cov = (pkt_ver / n * 100.0)
        pkt_prec = ((pkt_ver - pkt_fal) / pkt_ver * 100.0) if pkt_ver > 0 else 100.0

        boot_claim_prec.append(claim_prec)
        boot_claim_cov.append(claim_cov)
        boot_pkt_cov.append(pkt_cov)
        boot_pkt_prec.append(pkt_prec)

    boot_claim_prec.sort()
    boot_claim_cov.sort()
    boot_pkt_cov.sort()
    boot_pkt_prec.sort()

    low_idx = int(0.025 * B)
    high_idx = int(0.975 * B)

    return {
        "claim_precision_ci95": [round(boot_claim_prec[low_idx], 2), round(boot_claim_prec[high_idx], 2)],
        "claim_coverage_ci95": [round(boot_claim_cov[low_idx], 2), round(boot_claim_cov[high_idx], 2)],
        "packet_coverage_ci95": [round(boot_pkt_cov[low_idx], 2), round(boot_pkt_cov[high_idx], 2)],
        "packet_precision_ci95": [round(boot_pkt_prec[low_idx], 2), round(boot_pkt_prec[high_idx], 2)],
    }

# Compute statistics per partition and aggregate
splits = ["DEV", "CAL", "BLIND", "CHALL", "AGGREGATE"]
partition_results = {}

for s in splits:
    if s == "AGGREGATE":
        pkts = evaluated_packets
    else:
        pkts = [p for p in evaluated_packets if p["split"] == s]

    tot_pkts = len(pkts)
    tot_claims = sum(p["total_claims"] for p in pkts)
    ver_claims = sum(p["verified_count"] for p in pkts)
    ext_claims = sum(p["exact_count"] for p in pkts)
    fal_claims = sum(p["false_count"] for p in pkts)
    abs_claims = tot_claims - ver_claims

    pkts_with_ver = sum(1 for p in pkts if p["has_verified_claim"])
    pkts_with_fal = sum(1 for p in pkts if p["has_false_verification"])
    pkts_all_abs = sum(1 for p in pkts if p["is_all_abstained"])

    claim_prec = (ext_claims / ver_claims * 100.0) if ver_claims > 0 else 100.0
    claim_cov = (ver_claims / tot_claims * 100.0) if tot_claims > 0 else 0.0
    pkt_cov = (pkts_with_ver / tot_pkts * 100.0) if tot_pkts > 0 else 0.0
    pkt_fvr = (pkts_with_fal / tot_pkts * 100.0) if tot_pkts > 0 else 0.0

    boot = run_packet_bootstrap(pkts, B=2000)

    partition_results[s] = {
        "total_packets": tot_pkts,
        "packets_with_verified_claim": pkts_with_ver,
        "packets_with_false_verification": pkts_with_fal,
        "packets_all_abstained": pkts_all_abs,
        "packet_coverage_pct": round(pkt_cov, 2),
        "packet_false_verification_rate_pct": round(pkt_fvr, 2),
        "packet_coverage_ci95_clustered": boot.get("packet_coverage_ci95"),
        "packet_precision_ci95_clustered": boot.get("packet_precision_ci95"),
        "total_claims": tot_claims,
        "verified_claims": ver_claims,
        "exact_matches": ext_claims,
        "false_verifications": fal_claims,
        "abstentions": abs_claims,
        "claim_precision_pct": round(claim_prec, 2),
        "claim_coverage_pct": round(claim_cov, 2),
        "claim_precision_ci95_clustered": boot.get("claim_precision_ci95"),
        "claim_coverage_ci95_clustered": boot.get("claim_coverage_ci95"),
    }

print(f"{'Split':<10} | {'Pkts':<5} | {'PktCov':<8} | {'PktFVR':<8} | {'Claims':<6} | {'Ver':<4} | {'Exact':<5} | {'False':<5} | {'ClaimPrec [95% Clustered]':<26} | {'ClaimCov [95% Clustered]'}")
print("-" * 115)
for s, r in partition_results.items():
    p_ci = f"{r['claim_precision_pct']:.2f}% [{r['claim_precision_ci95_clustered'][0]}-{r['claim_precision_ci95_clustered'][1]}]"
    c_ci = f"{r['claim_coverage_pct']:.2f}% [{r['claim_coverage_ci95_clustered'][0]}-{r['claim_coverage_ci95_clustered'][1]}]"
    print(f"{s:<10} | {r['total_packets']:<5} | {r['packet_coverage_pct']:>6.2f}% | {r['packet_false_verification_rate_pct']:>6.2f}% | {r['total_claims']:<6} | {r['verified_claims']:<4} | {r['exact_matches']:<5} | {r['false_verifications']:<5} | {p_ci:<26} | {c_ci}")

out_stats_path = os.path.join("research", "loop29", "results", "packet_clustered_statistics.json")
with open(out_stats_path, "w", encoding="utf-8") as f:
    json.dump(partition_results, f, indent=2)
print(f"\nPacket-clustered statistics written to {out_stats_path}")
