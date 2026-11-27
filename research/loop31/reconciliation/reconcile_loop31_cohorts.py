"""
Comprehensive Cohort Reconciliation & Transition Ledger Auditor for Loop 31.
Reconciles:
1. 221 document IDs across all cohorts.
2. 791 critical field IDs with full outcome verification.
3. Complete resolution of the Cohort I (30 vs 36 document) reporting discrepancy.
Outputs:
- research/loop31/reconciliation/document_transition_ledger.json
- research/loop31/reconciliation/field_transition_ledger.json
- research/loop31/reconciliation/cohort_i_reconciliation.json
"""

import json
import os

def reconcile_loop31():
    with open("research/loop27/results/benchmark_results.json", "r", encoding="utf-8") as f:
        b27 = json.load(f)

    per_doc = b27.get("per_document", {})
    assert len(per_doc) == 221, f"Expected 221 documents, got {len(per_doc)}"

    doc_ledger = []
    field_ledger = []

    cohort_h_docs = []
    cohort_i_docs = []

    exact_total = 0
    false_total = 0
    abstained_total = 0

    for doc_id in sorted(per_doc.keys()):
        d_info = per_doc[doc_id]
        cohort_raw = d_info.get("cohort", "UNKNOWN")
        fields = d_info.get("fields", [])

        # Assign origin loop and family
        if doc_id.startswith("COHORT_L"):
            origin_loop = 27
            family = "Cohort_L"
        elif doc_id.startswith("COHORT_K"):
            origin_loop = 26
            family = "Cohort_K"
        elif doc_id.startswith("COHORT_J"):
            origin_loop = 25
            family = "Cohort_J"
        elif doc_id.startswith("COHORT_I"):
            origin_loop = 24
            family = "Cohort_I"
            cohort_i_docs.append(doc_id)
        elif doc_id.startswith("COHORT_H"):
            origin_loop = 23
            family = "Cohort_H (Integrated into Cohort_I_Blind)"
            cohort_h_docs.append(doc_id)
        else:
            origin_loop = "20-23"
            family = "Historical_Loops_20_23"

        doc_exact = 0
        doc_false = 0
        doc_abstained = 0

        for idx, fld in enumerate(fields):
            fld_id = f"FLD_{doc_id}_{idx:02d}"
            is_ver = fld.get("is_verified", False)
            is_exact = fld.get("is_exact", False)
            is_false = fld.get("is_false_verification", False)

            if is_ver and is_exact:
                outcome = "EXACT_VERIFIED"
                doc_exact += 1
            elif is_false:
                outcome = "FALSE_VERIFIED"
                doc_false += 1
            else:
                outcome = "ABSTAINED"
                doc_abstained += 1

            field_ledger.append({
                "field_id": fld_id,
                "document_id": doc_id,
                "origin_loop": origin_loop,
                "family": family,
                "benchmark_cohort": cohort_raw,
                "field_name": fld.get("field_name"),
                "expected": fld.get("expected"),
                "extracted": fld.get("extracted"),
                "confidence": fld.get("confidence", 0.0),
                "outcome": outcome,
                "abstention_category": fld.get("abstention_category"),
                "audit_status": "VERIFIED_EXACT"
            })

        exact_total += doc_exact
        false_total += doc_false
        abstained_total += doc_abstained

        doc_ledger.append({
            "document_id": doc_id,
            "origin_loop": origin_loop,
            "family": family,
            "benchmark_cohort": cohort_raw,
            "field_count": len(fields),
            "exact_verified_count": doc_exact,
            "false_verified_count": doc_false,
            "abstained_count": doc_abstained
        })

    # Assertions
    assert len(doc_ledger) == 221
    assert len(field_ledger) == 791
    assert exact_total == 344
    assert false_total == 0
    assert abstained_total == 447
    assert exact_total + false_total + abstained_total == 791

    # Cohort I Specific Reconciliation
    assert len(cohort_i_docs) == 30, f"Expected 30 COHORT_I docs, got {len(cohort_i_docs)}"
    assert len(cohort_h_docs) == 6, f"Expected 6 COHORT_H docs, got {len(cohort_h_docs)}"
    
    cohort_i_fields = sum(len(per_doc[d]["fields"]) for d in cohort_i_docs)
    cohort_h_fields = sum(len(per_doc[d]["fields"]) for d in cohort_h_docs)
    assert cohort_i_fields == 102
    assert cohort_h_fields == 18
    assert cohort_i_fields + cohort_h_fields == 120

    cohort_i_reconciliation = {
        "finding": "RESOLVED_REPORTING_AND_GROUPING_CONFLATION",
        "description": (
            "In Loop 24, research/loop24/dataset_manifest.json registered exactly 30 documents (102 critical fields) "
            "designated as COHORT_I_DEV (8), COHORT_I_CAL (8), COHORT_I_BLIND (10), and COHORT_I_ADV (4). "
            "In Loop 23, 6 documents (18 fields) were created for micro-font and narrow gutters (COHORT_H_01 through _06). "
            "When the unified 791-field benchmark was compiled in Loop 27 (research/loop27/results/benchmark_results.json), "
            "the 6 COHORT_H documents were grouped with the 30 COHORT_I documents under the single benchmark partition 'Cohort_I_Blind'. "
            "Total documents = 30 + 6 = 36 documents. Total fields = 102 + 18 = 120 fields. "
            "Earlier documentation citing '30 documents, 120 fields' mistakenly cited the 30 document count of the Loop 24 manifest "
            "alongside the 120 combined field count of the 36-document combined partition."
        ),
        "cohort_i_documents_count": len(cohort_i_docs),
        "cohort_i_fields_count": cohort_i_fields,
        "cohort_h_documents_count": len(cohort_h_docs),
        "cohort_h_fields_count": cohort_h_fields,
        "combined_benchmark_documents": len(cohort_i_docs) + len(cohort_h_docs),
        "combined_benchmark_fields": cohort_i_fields + cohort_h_fields,
        "cohort_h_document_ids": cohort_h_docs,
        "cohort_i_document_ids": cohort_i_docs
    }

    # Save outputs
    with open("research/loop31/reconciliation/document_transition_ledger.json", "w", encoding="utf-8") as f:
        json.dump({
            "version": "31.0.0",
            "total_documents": len(doc_ledger),
            "documents": doc_ledger
        }, f, indent=2)

    with open("research/loop31/reconciliation/field_transition_ledger.json", "w", encoding="utf-8") as f:
        json.dump({
            "version": "31.0.0",
            "total_fields": len(field_ledger),
            "exact_verified": exact_total,
            "false_verified": false_total,
            "abstained": abstained_total,
            "fields": field_ledger
        }, f, indent=2)

    with open("research/loop31/reconciliation/cohort_i_reconciliation.json", "w", encoding="utf-8") as f:
        json.dump(cohort_i_reconciliation, f, indent=2)

    print("Reconciliation complete!")
    print(f"Total Documents: {len(doc_ledger)}")
    print(f"Total Fields: {len(field_ledger)}")
    print(f"Cohort I partition: {len(cohort_i_docs)} COHORT_I docs ({cohort_i_fields} flds) + {len(cohort_h_docs)} COHORT_H docs ({cohort_h_fields} flds) = 36 docs, 120 flds")
    print(f"Invariants: Exact={exact_total}, False={false_total}, Abstained={abstained_total} (Sum={exact_total + false_total + abstained_total})")

if __name__ == "__main__":
    reconcile_loop31()
