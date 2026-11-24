import json

with open("research/loop23/results/benchmark_results.json", "r", encoding="utf-8") as f:
    d = json.load(f)

for doc_id, doc in d["per_document"].items():
    if doc["cohort"] == "H_microfont_narrow_gutter":
        print(f"\n=== {doc_id} ===")
        for fn, fld in doc["fields"].items():
            if fld["is_false_verification"]:
                print(f"  [FV] {fn}: expected='{fld['expected']}', got='{fld['extracted_value']}', status={fld['status']}, conf={fld['confidence']}")
            elif fld["is_verified"]:
                print(f"  [EXACT] {fn}: val='{fld['extracted_value']}', conf={fld['confidence']}")
            else:
                print(f"  [ABSTAIN] {fn}: val='{fld['extracted_value']}', reason={fld['abstention_reason']}")
