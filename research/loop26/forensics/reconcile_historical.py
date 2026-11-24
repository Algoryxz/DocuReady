import json
from pathlib import Path

b24_path = Path("research/loop24/results/benchmark_results.json")
b25_path = Path("research/loop25/results/benchmark_results.json")

with open(b24_path, "r", encoding="utf-8") as f:
    b24 = json.load(f)
with open(b25_path, "r", encoding="utf-8") as f:
    b25 = json.load(f)

docs24 = b24.get("per_document", {})
docs25 = b25.get("per_document", {})

fields24 = {}
for doc_id, doc_data in docs24.items():
    cohort = doc_data.get("cohort", "")
    for field in doc_data.get("fields", []):
        key = f"{doc_id}::{field['field_name']}"
        fields24[key] = {**field, "doc_id": doc_id, "cohort": cohort}

fields25 = {}
for doc_id, doc_data in docs25.items():
    cohort = doc_data.get("cohort", "")
    for field in doc_data.get("fields", []):
        key = f"{doc_id}::{field['field_name']}"
        fields25[key] = {**field, "doc_id": doc_id, "cohort": cohort}

print(f"Total fields in Loop 24 benchmark: {len(fields24)}")
print(f"Total fields in Loop 25 benchmark: {len(fields25)}")

# Historical fields are those from Loops 20-23
historical_keys = [k for k, v in fields24.items() if "COHORT_I" not in v["cohort"] and "COHORT_J" not in v["cohort"]]
print(f"Historical (Loops 20-23) fields: {len(historical_keys)}")

transitions = []
for k in historical_keys:
    if k in fields25:
        f24 = fields24[k]
        f25 = fields25[k]
        v24 = f24.get("is_verified")
        v25 = f25.get("is_verified")
        if v24 != v25 or f24.get("status") != f25.get("status"):
            transitions.append((k, f24, f25))

print(f"\nChanged historical field decisions: {len(transitions)}")
for k, f24, f25 in transitions:
    print(f"\n--- Field: {k} (Cohort: {f24['cohort']}) ---")
    print(f"  Loop 24: verified={f24.get('is_verified')}, status={f24.get('status')}, extracted='{f24.get('extracted')}', conf={f24.get('confidence')}, reason={f24.get('reason')}")
    print(f"  Loop 25: verified={f25.get('is_verified')}, status={f25.get('status')}, extracted='{f25.get('extracted')}', conf={f25.get('confidence')}, reason={f25.get('reason')}")
    print(f"  Expected: '{f24.get('expected')}'")

# Also check Cohort I transitions
cohort_i_transitions = []
for k, f24 in fields24.items():
    if "COHORT_I" in f24["cohort"] and k in fields25:
        f25 = fields25[k]
        if f24.get("is_verified") != f25.get("is_verified"):
            cohort_i_transitions.append((k, f24, f25))
print(f"\nCohort I transitions (verified status changed): {len(cohort_i_transitions)}")

# Save transition ledger
out_path = Path("research/loop26/forensics/historical_transition_ledger.json")
out_path.parent.mkdir(parents=True, exist_ok=True)
with open(out_path, "w", encoding="utf-8") as f:
    json.dump({
        "historical_transitions": [
            {
                "field_key": k,
                "doc_id": f24["doc_id"],
                "field_name": f24["field_name"],
                "cohort": f24["cohort"],
                "expected": f24.get("expected"),
                "loop24": f24,
                "loop25": f25,
            }
            for k, f24, f25 in transitions
        ],
        "cohort_i_transitions": [
            {
                "field_key": k,
                "doc_id": f24["doc_id"],
                "field_name": f24["field_name"],
                "cohort": f24["cohort"],
                "expected": f24.get("expected"),
                "loop24": f24,
                "loop25": f25,
            }
            for k, f24, f25 in cohort_i_transitions
        ]
    }, f, indent=2)

print(f"Saved detailed transition ledger to {out_path}")
