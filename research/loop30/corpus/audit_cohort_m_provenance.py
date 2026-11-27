"""
Cohort M Provenance & Audit Tool for Loop 30.
Inspects all 30 packets and 103 claims in research/loop29/corpus/cohort_m_corpus.json,
verifies cryptographic hash, classifies synthetic attributes, and generates a structured audit report.
"""

import json
import hashlib
import os

def audit_cohort_m():
    corpus_path = "research/loop29/corpus/cohort_m_corpus.json"
    with open(corpus_path, "rb") as f:
        raw_bytes = f.read()
        sha256 = hashlib.sha256(raw_bytes).hexdigest()

    data = json.loads(raw_bytes.decode("utf-8"))
    packets = data.get("packets", [])
    
    expected_hash = "c33c7491bc78f769e856d1dcc476a42ba537eefefae87598bd693cc630280722"
    assert sha256 == expected_hash, f"Hash mismatch: {sha256} vs {expected_hash}"

    family_stats = {}
    outcome_stats = {}
    claim_count = 0
    document_count = 0

    for p in packets:
        fam = p.get("family", "Unknown")
        family_stats.setdefault(fam, {"packets": 0, "claims": 0, "documents": 0, "contradictions": 0})
        family_stats[fam]["packets"] += 1
        
        docs = p.get("documents", [])
        family_stats[fam]["documents"] += len(docs)
        document_count += len(docs)

        claims = p.get("claims", [])
        for c in claims:
            claim_count += 1
            family_stats[fam]["claims"] += 1
            out = c.get("expected_outcome", "UNKNOWN")
            outcome_stats[out] = outcome_stats.get(out, 0) + 1
            if "CONTRADICTION" in out:
                family_stats[fam]["contradictions"] += 1

    report = {
        "audit_version": "30.0.0",
        "corpus_name": "Cohort M (Cross-Document Generalization Suite)",
        "synthetic_classification": "SYNTHETIC_GENERATED_EVALUATION_SUITE",
        "real_world_scanned": False,
        "sha256": sha256,
        "file_size_bytes": len(raw_bytes),
        "total_packets": len(packets),
        "total_documents": document_count,
        "total_claims": claim_count,
        "family_breakdown": family_stats,
        "outcome_breakdown": outcome_stats
    }

    out_path = "research/loop30/corpus/cohort_m_provenance_audit.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"Cohort M Provenance Audit saved to {out_path}")
    print(f"Total Packets: {len(packets)}, Docs: {document_count}, Claims: {claim_count}")
    print("Outcome Breakdown:", outcome_stats)

if __name__ == "__main__":
    audit_cohort_m()
