import json

with open("research/loop26/results/benchmark_results.json", "r", encoding="utf-8") as f:
    bench = json.load(f)

d = bench["per_document"]
mismatches = []
for doc_id, doc_info in d.items():
    if "COHORT_K" in doc_id:
        for f in doc_info["fields"]:
            if f.get("is_verified") and not f.get("is_exact"):
                mismatches.append({
                    "doc_id": doc_id,
                    "field_name": f["field_name"],
                    "expected": f["expected"],
                    "extracted": f["extracted"],
                    "conf": f["confidence"],
                    "status": f["status"],
                    "reason": f["reason"],
                })

print(f"Total Cohort K false verifications: {len(mismatches)}")
for m in mismatches[:15]:
    print(f"\nDoc: {m['doc_id']} | Field: {m['field_name']}")
    print(f"  Expected: '{m['expected']}'")
    print(f"  Extracted: '{m['extracted']}' (conf={m['conf']})")
    print(f"  Reason: {m['reason']}")
