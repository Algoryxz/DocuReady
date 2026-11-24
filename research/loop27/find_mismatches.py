import json

with open("research/loop27/results/benchmark_run1.json", "r", encoding="utf-8") as f:
    r = json.load(f)

count = 0
for doc_id, doc in r["per_document"].items():
    cohort = doc.get("cohort", "unknown")
    for f in doc["fields"]:
        if f.get("is_verified") and not f.get("is_exact"):
            count += 1
            print(f"[{count}] {doc_id} ({cohort}) | {f['field_name']}")
            print(f"    Extracted: '{f['extracted']}' (conf={f['confidence']})")
            print(f"    Expected : '{f['expected']}'")
            print(f"    Reason   : {f.get('reason')}")
print(f"Total false verifications: {count}")
