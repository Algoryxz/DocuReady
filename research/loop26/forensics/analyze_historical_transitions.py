import json
from pathlib import Path

ledger_path = Path("research/loop26/forensics/historical_transition_ledger.json")
with open(ledger_path, "r", encoding="utf-8") as f:
    data = json.load(f)

print("=== 4 HISTORICAL TRANSITIONS (UNVERIFIED -> VERIFIED) ===")
promoted = []
other_transitions = []
for item in data["historical_transitions"]:
    l24 = item["loop24"]
    l25 = item["loop25"]
    if not l24["is_verified"] and l25["is_verified"]:
        promoted.append(item)
    else:
        other_transitions.append(item)

print(f"Total Promoted to Verified in Historical (Loops 20-23): {len(promoted)}")
for item in promoted:
    l24 = item["loop24"]
    l25 = item["loop25"]
    print(f"\nDocument: {item['doc_id']}")
    print(f"Field: {item['field_name']}")
    print(f"Expected: {item['expected']}")
    print(f"Loop 24: is_verified={l24['is_verified']}, status={l24['status']}, extracted='{l24['extracted']}'")
    print(f"Loop 25: is_verified={l25['is_verified']}, status={l25['status']}, extracted='{l25['extracted']}', conf={l25['confidence']}")
    print(f"Exact Match: {l25['is_exact']}")

print(f"\nOther Historical Transitions (abstention status refined): {len(other_transitions)}")
for item in other_transitions[:5]:
    l24 = item["loop24"]
    l25 = item["loop25"]
    print(f"Doc: {item['doc_id']} | Field: {item['field_name']} | L24: {l24['status']} -> L25: {l25['status']}")
