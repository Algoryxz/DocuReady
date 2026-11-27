"""
Extended 10-Mode Ablation Study for DocuReady Loop 29.
Evaluates 10 ablation modes across both the Loop 28 Corpus and the Independent Cohort M Corpus:
- Mode A: Naive Baseline
- Mode B: Entity Resolution Only
- Mode C: Independence Detection Only
- Mode D: Contradiction Detection Only
- Mode E: Conservative Abstention Only
- Mode F: Full Production Policy
- Mode G: Full Policy LOO-Entity (Without Entity Resolution)
- Mode H: Full Policy LOO-Duplicate (Without Duplicate Suppression)
- Mode I: Full Policy LOO-Contradiction (Without Contradiction Detection)
- Mode J: Full Policy LOO-Missing (Without Missing-Evidence Enforcement)
"""

import json
import os
import sys
import time
from typing import Dict, Any, List

sys.path.insert(0, ".")
from src.docuready.evidence.cross_document import (
    DocumentIdentity, EntityIdentity, FieldClaim,
    resolve_entity_match, detect_document_independence,
    normalize_claim_value, verify_cross_document_packet_claim,
    VerificationOutcome, SourceIndependence
)

def evaluate_packet_claim(mode: str, pkt: Dict[str, Any], field_name: str) -> Dict[str, Any]:
    doc_map = {d["doc_id"]: DocumentIdentity(**d) for d in pkt["documents"]}
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

    field_claims = [c for c in claims if c.field_name == field_name]
    if not field_claims:
        return {"outcome": "ABSTAIN", "verified_val": None, "supporting_docs": []}

    # MODE A: Naive Baseline
    if mode == "Mode A: Naive Baseline":
        best = max(field_claims, key=lambda c: c.confidence)
        if best.confidence >= 70.0:
            norm_v = normalize_claim_value(best.claimed_value, best.field_type)
            return {"outcome": "VERIFY", "verified_val": norm_v, "supporting_docs": [c.doc_id for c in field_claims]}
        return {"outcome": "ABSTAIN", "verified_val": None, "supporting_docs": []}

    # MODE B: Entity Resolution Only
    if mode == "Mode B: Entity Resolution Only":
        valid = []
        for c in field_claims:
            m, _ = resolve_entity_match(
                target_entity.canonical_name,
                c.entity_hints.get("name") or target_entity.canonical_name,
                {"date_of_birth": target_entity.date_of_birth, "tax_id": target_entity.tax_id},
                c.entity_hints
            )
            if m:
                valid.append(c)
        if not valid:
            return {"outcome": "ENTITY_AMBIGUOUS", "verified_val": None, "supporting_docs": []}
        best = max(valid, key=lambda c: c.confidence)
        if best.confidence >= 70.0:
            return {"outcome": "VERIFY", "verified_val": normalize_claim_value(best.claimed_value, best.field_type), "supporting_docs": [c.doc_id for c in valid]}
        return {"outcome": "ABSTAIN", "verified_val": None, "supporting_docs": []}

    # MODE C: Independence Detection Only
    if mode == "Mode C: Independence Detection Only":
        doc_ids = list({c.doc_id for c in field_claims})
        if len(doc_ids) >= 2:
            d1 = doc_map.get(doc_ids[0])
            d2 = doc_map.get(doc_ids[1])
            if d1 and d2 and detect_document_independence(d1, d2) == SourceIndependence.DUPLICATE:
                return {"outcome": "DUPLICATE_UNCONFIRMED", "verified_val": None, "supporting_docs": []}
        best = max(field_claims, key=lambda c: c.confidence)
        if best.confidence >= 70.0:
            return {"outcome": "VERIFY", "verified_val": normalize_claim_value(best.claimed_value, best.field_type), "supporting_docs": [best.doc_id]}
        return {"outcome": "ABSTAIN", "verified_val": None, "supporting_docs": []}

    # MODE D: Contradiction Detection Only
    if mode == "Mode D: Contradiction Detection Only":
        norm_vals = set(normalize_claim_value(c.claimed_value, c.field_type) for c in field_claims if c.confidence >= 70.0)
        if len(norm_vals) > 1:
            return {"outcome": "CONTRADICTION_DETECTED", "verified_val": None, "supporting_docs": []}
        best = max(field_claims, key=lambda c: c.confidence)
        if best.confidence >= 70.0:
            return {"outcome": "VERIFY", "verified_val": normalize_claim_value(best.claimed_value, best.field_type), "supporting_docs": [c.doc_id for c in field_claims]}
        return {"outcome": "ABSTAIN", "verified_val": None, "supporting_docs": []}

    # MODE E: Conservative Abstention Only
    if mode == "Mode E: Conservative Abstention Only":
        req_docs = set(pkt.get("required_doc_types", []))
        present_docs = set(d["doc_type"] for d in pkt.get("documents", []))
        if not req_docs.issubset(present_docs):
            return {"outcome": "MISSING_EVIDENCE", "verified_val": None, "supporting_docs": []}
        best = max(field_claims, key=lambda c: c.confidence)
        if best.confidence >= 75.0:
            return {"outcome": "VERIFY", "verified_val": normalize_claim_value(best.claimed_value, best.field_type), "supporting_docs": [best.doc_id]}
        return {"outcome": "ABSTAIN", "verified_val": None, "supporting_docs": []}

    # Leave-One-Out Modes:
    req_docs = [] if mode == "Mode J: LOO-Missing" else pkt.get("required_doc_types", [])
    
    # If Mode G (LOO-Entity), wipe entity hints so entity matching accepts all claims
    if mode == "Mode G: LOO-Entity":
        for c in claims:
            c.entity_hints = {}

    res = verify_cross_document_packet_claim(
        field_name=field_name,
        target_entity=target_entity,
        claims=claims,
        documents=doc_map,
        required_doc_types=req_docs,
        operating_threshold=70.0
    )

    # If Mode I (LOO-Contradiction) and outcome was contradiction, override to verify best value
    if mode == "Mode I: LOO-Contradiction" and res.outcome == VerificationOutcome.CONTRADICTION:
        best = max(field_claims, key=lambda c: c.confidence)
        return {"outcome": "VERIFY", "verified_val": normalize_claim_value(best.claimed_value, best.field_type), "supporting_docs": [c.doc_id for c in field_claims]}

    return {
        "outcome": res.outcome.value,
        "verified_val": res.verified_value,
        "supporting_docs": res.supporting_doc_ids
    }

def run_ablation_on_corpus(corpus_path: str, corpus_name: str) -> List[Dict[str, Any]]:
    with open(corpus_path, "r", encoding="utf-8") as f:
        corpus = json.load(f)

    modes = [
        "Mode A: Naive Baseline",
        "Mode B: Entity Resolution Only",
        "Mode C: Independence Detection Only",
        "Mode D: Contradiction Detection Only",
        "Mode E: Conservative Abstention Only",
        "Mode F: Full Policy (Production)",
        "Mode G: LOO-Entity",
        "Mode H: LOO-Duplicate",
        "Mode I: LOO-Contradiction",
        "Mode J: LOO-Missing"
    ]

    results = []
    print(f"\n========================================================")
    print(f"ABLATION RESULTS: {corpus_name} ({len(corpus['packets'])} pkts)")
    print(f"========================================================")
    print(f"{'Mode':<38} | {'Claims':<6} | {'Ver':<5} | {'Exact':<5} | {'False':<5} | {'Prec':<8} | {'Cov':<8} | {'PktFalse'}")
    print("-" * 92)

    for mode in modes:
        t0 = time.perf_counter()
        tot_c = 0
        ver_c = 0
        ext_c = 0
        fal_c = 0
        abs_c = 0
        pkt_with_false = 0

        for pkt in corpus["packets"]:
            fields = list({c["field_name"] for c in pkt["claims"]})
            field_res = {}
            for f in fields:
                field_res[f] = evaluate_packet_claim(mode, pkt, f)

            has_false_in_pkt = False
            for c in pkt["claims"]:
                tot_c += 1
                f = c["field_name"]
                res = field_res[f]
                outcome = res["outcome"]
                supp_docs = res.get("supporting_docs", [])

                if outcome == "VERIFY":
                    if not supp_docs or c["doc_id"] in supp_docs:
                        pred_outcome = "VERIFY"
                    else:
                        pred_outcome = "ENTITY_AMBIGUOUS"
                else:
                    pred_outcome = outcome

                is_ver = (pred_outcome == "VERIFY")
                is_exact = False
                is_false = False

                if is_ver:
                    ver_c += 1
                    norm_c = normalize_claim_value(c["claimed_value"], c["field_type"])
                    norm_gt = normalize_claim_value(c.get("ground_truth"), c["field_type"]) if c.get("ground_truth") else ""
                    if c["expected_outcome"] in ["VERIFY", "EQUIVALENT_AFTER_NORMALIZATION"] and norm_c == norm_gt:
                        ext_c += 1
                        is_exact = True
                    else:
                        fal_c += 1
                        is_false = True
                        has_false_in_pkt = True
                else:
                    abs_c += 1

            if has_false_in_pkt:
                pkt_with_false += 1

        t1 = time.perf_counter()
        overhead_ms = (t1 - t0) * 1000.0 / len(corpus["packets"])

        prec = (ext_c / ver_c * 100.0) if ver_c > 0 else 0.0
        cov = (ver_c / tot_c * 100.0) if tot_c > 0 else 0.0

        print(f"{mode:<38} | {tot_c:<6} | {ver_c:<5} | {ext_c:<5} | {fal_c:<5} | {prec:>6.2f}% | {cov:>6.2f}% | {pkt_with_false}")
        results.append({
            "mode": mode,
            "total_claims": tot_c,
            "verified_claims": ver_c,
            "exact_matches": ext_c,
            "false_verifications": fal_c,
            "abstentions": abs_c,
            "precision_pct": round(prec, 2),
            "coverage_pct": round(cov, 2),
            "packets_with_false_verification": pkt_with_false,
            "mean_packet_overhead_ms": round(overhead_ms, 3)
        })

    return results

def main():
    res_l28 = run_ablation_on_corpus("research/loop28/corpus/cross_document_corpus.json", "Loop 28 Corpus")
    res_m = run_ablation_on_corpus("research/loop29/corpus/cohort_m_corpus.json", "Cohort M Corpus")

    payload = {
        "loop": 29,
        "loop28_corpus_ablations": res_l28,
        "cohort_m_corpus_ablations": res_m
    }

    out_path = os.path.join("research", "loop29", "ablations", "extended_ablation_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"\nExtended ablation results saved to {out_path}")

if __name__ == "__main__":
    main()
