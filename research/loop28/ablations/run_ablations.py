"""
Cross-Document Ablation Runner for Loop 28.
Evaluates 6 ablation modes across the 36-packet (92 claims) corpus:
- Mode A: Naive Baseline (Loop 27 single-doc / naive confidence thresholding: no entity resolution, no independence detection, no contradiction check)
- Mode B: Entity Resolution Only (filters to entity-matching claims, but no duplicate check or contradiction check)
- Mode C: Evidence Independence Only (deduplicates documents, but naive entity/contradiction)
- Mode D: Contradiction Detection Only (checks value agreement, but naive entity/independence)
- Mode E: Conservative Abstention Only (checks required documents and elevated threshold, but naive cross-doc logic)
- Mode F: Full Cross-Document Policy (All modules enabled: Entity + Independence + Contradiction + Missing Evidence + Calibrated Abstention)
"""

import json
import os
import sys
from typing import Dict, Any, List

sys.path.insert(0, ".")
from src.docuready.evidence.cross_document import (
    DocumentIdentity,
    EntityIdentity,
    FieldClaim,
    PacketVerificationResult,
    VerificationOutcome,
    SourceIndependence,
    resolve_entity_match,
    detect_document_independence,
    normalize_claim_value,
    verify_cross_document_packet_claim,
)

CORPUS_PATH = os.path.join("research", "loop28", "corpus", "cross_document_corpus.json")
OUTPUT_PATH = os.path.join("research", "loop28", "ablations", "ablation_results.json")

def load_corpus() -> Dict[str, Any]:
    with open(CORPUS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def run_mode_a(packet: Dict[str, Any], field_name: str) -> Dict[str, Any]:
    """Mode A: Naive baseline. If any claim has conf >= 70, blindly verify the highest-confidence claim."""
    field_claims = [c for c in packet["claims"] if c["field_name"] == field_name]
    if not field_claims:
        return {"outcome": "ABSTAIN", "verified_val": None}
    best = max(field_claims, key=lambda c: c["confidence"])
    if best["confidence"] >= 70.0:
        norm_v = normalize_claim_value(best["claimed_value"], best["field_type"])
        return {"outcome": "VERIFY", "verified_val": norm_v}
    return {"outcome": "ABSTAIN", "verified_val": None}

def run_mode_b(packet: Dict[str, Any], field_name: str) -> Dict[str, Any]:
    """Mode B: Entity matching only. Filters to claims matching target entity; if any conf >= 70, verifies without checking contradiction or duplicate."""
    field_claims = [c for c in packet["claims"] if c["field_name"] == field_name]
    if not field_claims:
        return {"outcome": "ABSTAIN", "verified_val": None}
    
    tgt = packet["target_entity"]
    valid_claims = []
    for c in field_claims:
        e_hints = c.get("entity_hints") or {}
        c_name = e_hints.get("name") or e_hints.get("applicant_name") or tgt["canonical_name"]
        match, _ = resolve_entity_match(
            e1_name=tgt["canonical_name"],
            e2_name=c_name,
            e1_hints={
                "tax_id": tgt.get("tax_id"),
                "national_id": tgt.get("national_id"),
                "date_of_birth": tgt.get("date_of_birth"),
                "father_name": tgt.get("father_name"),
                "address": tgt.get("address"),
            },
            e2_hints=e_hints,
        )
        if match:
            valid_claims.append(c)
            
    if not valid_claims:
        return {"outcome": "ENTITY_AMBIGUOUS", "verified_val": None}
    
    best = max(valid_claims, key=lambda c: c["confidence"])
    if best["confidence"] >= 70.0:
        norm_v = normalize_claim_value(best["claimed_value"], best["field_type"])
        return {"outcome": "VERIFY", "verified_val": norm_v}
    return {"outcome": "ABSTAIN", "verified_val": None}

def run_mode_c(packet: Dict[str, Any], field_name: str) -> Dict[str, Any]:
    """Mode C: Evidence Independence only. Filters duplicate documents, then naively verifies best claim."""
    field_claims = [c for c in packet["claims"] if c["field_name"] == field_name]
    if not field_claims:
        return {"outcome": "ABSTAIN", "verified_val": None}
    
    doc_map = {d["doc_id"]: DocumentIdentity(**d) for d in packet["documents"]}
    # Check if all claims come from duplicate documents
    doc_ids = list({c["doc_id"] for c in field_claims})
    if len(doc_ids) >= 2:
        d1 = doc_map.get(doc_ids[0])
        d2 = doc_map.get(doc_ids[1])
        if d1 and d2:
            indep = detect_document_independence(d1, d2)
            if indep == SourceIndependence.DUPLICATE:
                return {"outcome": "DUPLICATE_UNCONFIRMED", "verified_val": None}
                
    best = max(field_claims, key=lambda c: c["confidence"])
    if best["confidence"] >= 70.0:
        norm_v = normalize_claim_value(best["claimed_value"], best["field_type"])
        return {"outcome": "VERIFY", "verified_val": norm_v}
    return {"outcome": "ABSTAIN", "verified_val": None}

def run_mode_d(packet: Dict[str, Any], field_name: str) -> Dict[str, Any]:
    """Mode D: Contradiction Detection only. Checks value harmony across all claims without entity or independence check."""
    field_claims = [c for c in packet["claims"] if c["field_name"] == field_name]
    if not field_claims:
        return {"outcome": "ABSTAIN", "verified_val": None}
        
    norm_vals = set(normalize_claim_value(c["claimed_value"], c["field_type"]) for c in field_claims if c["confidence"] >= 70.0)
    if len(norm_vals) > 1:
        return {"outcome": "CONTRADICTION_DETECTED", "verified_val": None}
        
    best = max(field_claims, key=lambda c: c["confidence"])
    if best["confidence"] >= 70.0:
        norm_v = normalize_claim_value(best["claimed_value"], best["field_type"])
        return {"outcome": "VERIFY", "verified_val": norm_v}
    return {"outcome": "ABSTAIN", "verified_val": None}

def run_mode_e(packet: Dict[str, Any], field_name: str) -> Dict[str, Any]:
    """Mode E: Conservative Abstention only. Checks mandatory documents and elevated threshold (75.0%)."""
    req_docs = set(packet.get("required_doc_types", []))
    present_docs = set(d["doc_type"] for d in packet.get("documents", []))
    if not req_docs.issubset(present_docs):
        return {"outcome": "MISSING_EVIDENCE", "verified_val": None}
        
    field_claims = [c for c in packet["claims"] if c["field_name"] == field_name]
    if not field_claims:
        return {"outcome": "ABSTAIN", "verified_val": None}
        
    best = max(field_claims, key=lambda c: c["confidence"])
    if best["confidence"] >= 75.0:
        norm_v = normalize_claim_value(best["claimed_value"], best["field_type"])
        return {"outcome": "VERIFY", "verified_val": norm_v}
    return {"outcome": "ABSTAIN", "verified_val": None}

def run_mode_f(packet: Dict[str, Any], field_name: str) -> Dict[str, Any]:
    """Mode F: Full Policy (Production Engine)."""
    tgt = packet["target_entity"]
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
    doc_map = {d["doc_id"]: DocumentIdentity(**d) for d in packet["documents"]}
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
        for i, c in enumerate(packet["claims"])
    ]
    
    res = verify_cross_document_packet_claim(
        field_name=field_name,
        target_entity=target_entity,
        claims=claims,
        documents=doc_map,
        required_doc_types=packet.get("required_doc_types", []),
        operating_threshold=70.0,
    )
    return {
        "outcome": res.outcome.value,
        "verified_val": res.verified_value,
        "supporting_doc_ids": res.supporting_doc_ids,
    }

def evaluate_mode(mode_name: str, runner_func, corpus: Dict[str, Any]) -> Dict[str, Any]:
    total_claims = 0
    verified = 0
    exact = 0
    false_verifications = 0
    abstentions = 0
    contradictions = 0
    entity_mismatches = 0
    duplicates = 0
    missing = 0

    per_claim_records = []

    for pkt in corpus["packets"]:
        # Group claims by field_name to simulate per-field verification across the packet
        fields = list({c["field_name"] for c in pkt["claims"]})
        field_eval = {}
        for f in fields:
            field_eval[f] = runner_func(pkt, f)

        for c in pkt["claims"]:
            total_claims += 1
            f = c["field_name"]
            res = field_eval[f]
            overall_outcome = res["outcome"]
            supporting_docs = res.get("supporting_doc_ids")

            # Determine claim-specific outcome
            if overall_outcome == "VERIFY":
                if supporting_docs is None or c["doc_id"] in supporting_docs:
                    pred_outcome = "VERIFY"
                else:
                    pred_outcome = "ENTITY_AMBIGUOUS"
            else:
                pred_outcome = overall_outcome

            pred_val = res["verified_val"]
            expected_outcome = c["expected_outcome"]
            ground_truth = c.get("ground_truth")

            is_verified = (pred_outcome == "VERIFY")
            is_exact = False
            is_false = False

            if is_verified:
                verified += 1
                norm_c = normalize_claim_value(c["claimed_value"], c["field_type"])
                norm_gt = normalize_claim_value(ground_truth, c["field_type"]) if ground_truth else ""
                if expected_outcome == "VERIFY" and norm_c == norm_gt:
                    exact += 1
                    is_exact = True
                else:
                    false_verifications += 1
                    is_false = True
            else:
                abstentions += 1
                if pred_outcome == "CONTRADICTION_DETECTED":
                    contradictions += 1
                elif pred_outcome == "ENTITY_AMBIGUOUS":
                    entity_mismatches += 1
                elif pred_outcome == "DUPLICATE_UNCONFIRMED":
                    duplicates += 1
                elif pred_outcome == "MISSING_EVIDENCE":
                    missing += 1

            per_claim_records.append({
                "packet_id": pkt["packet_id"],
                "split": pkt["split"],
                "condition_code": pkt["condition_code"],
                "field_name": f,
                "claimed_value": c["claimed_value"],
                "predicted_outcome": pred_outcome,
                "expected_outcome": expected_outcome,
                "is_verified": is_verified,
                "is_exact": is_exact,
                "is_false": is_false,
            })

    precision = (exact / verified * 100.0) if verified > 0 else 0.0
    coverage = (verified / total_claims * 100.0) if total_claims > 0 else 0.0

    return {
        "mode": mode_name,
        "total_claims": total_claims,
        "verified_claims": verified,
        "exact_matches": exact,
        "false_verifications": false_verifications,
        "abstentions": abstentions,
        "contradiction_detections": contradictions,
        "entity_mismatches": entity_mismatches,
        "duplicates_suppressed": duplicates,
        "missing_evidence": missing,
        "precision": round(precision, 2),
        "coverage": round(coverage, 2),
    }

def main():
    corpus = load_corpus()
    modes = [
        ("Mode A: Naive Baseline", run_mode_a),
        ("Mode B: Entity Resolution Only", run_mode_b),
        ("Mode C: Independence Detection Only", run_mode_c),
        ("Mode D: Contradiction Detection Only", run_mode_d),
        ("Mode E: Conservative Abstention Only", run_mode_e),
        ("Mode F: Full Policy (Production)", run_mode_f),
    ]

    results = []
    print(f"{'Mode':<36} | {'Claims':<6} | {'Verified':<8} | {'Exact':<6} | {'False':<6} | {'Abstain':<8} | {'Precision':<10} | {'Coverage':<10}")
    print("-" * 102)
    for name, fn in modes:
        res = evaluate_mode(name, fn, corpus)
        results.append(res)
        print(f"{name:<36} | {res['total_claims']:<6} | {res['verified_claims']:<8} | {res['exact_matches']:<6} | {res['false_verifications']:<6} | {res['abstentions']:<8} | {res['precision']:>8.2f}% | {res['coverage']:>8.2f}%")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nAblation results saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
