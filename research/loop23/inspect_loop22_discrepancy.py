import json

with open("research/loop22/results/benchmark_results.json", "r", encoding="utf-8") as f:
    data = json.load(f)

summary = data["summary"]
per_cohort = data["per_cohort"]

print("=== SUMMARY IN JSON ===")
for k, v in summary.items():
    if not isinstance(v, (dict, list)):
        print(f"  {k}: {v}")

print("\n=== PER-COHORT DATA IN JSON ===")
sum_docs = sum(c["total_docs"] for c in per_cohort.values())
sum_fields = sum(c["total_fields"] for c in per_cohort.values())
sum_sem = sum(c["sem_passes"] for c in per_cohort.values())
sum_fv = sum(c["false_verifications"] for c in per_cohort.values())
sum_abst = sum(c["abstentions"] for c in per_cohort.values())
sum_verif = sum(c["verified_claims"] for c in per_cohort.values())

print(f"sum_docs:   {sum_docs}")
print(f"sum_fields: {sum_fields}")
print(f"sum_verif:  {sum_verif}")
print(f"sum_sem:    {sum_sem}")
print(f"sum_fv:     {sum_fv}")
print(f"sum_abst:   {sum_abst}")

for name, c in per_cohort.items():
    print(f"  {name:<26}: docs={c['total_docs']} fields={c['total_fields']} verif={c['verified_claims']} sem={c['sem_passes']} fv={c['false_verifications']} abst={c['abstentions']}")

print("\n=== PER-FIELD BREAKDOWN ACROSS ALL DOCUMENTS ===")
actual_verif = 0
actual_exact = 0
actual_fv = 0
actual_abst = 0
empty_correct = 0

for doc_id, doc in data["per_document"].items():
    for fn, fld in doc["fields"].items():
        is_verif = fld.get("is_verified", False)
        is_fv = fld.get("is_false_verification", False)
        is_abst = fld.get("is_abstained", False)
        status = fld.get("status", "")
        exp = fld.get("expected", "")
        
        if is_verif:
            actual_verif += 1
            if is_fv:
                actual_fv += 1
            else:
                actual_exact += 1
        if is_abst:
            actual_abst += 1
        if status == "PASS_EMPTY_CORRECT":
            empty_correct += 1

print(f"Actual verified: {actual_verif}")
print(f"  - Exact verified: {actual_exact}")
print(f"  - False verified: {actual_fv}")
print(f"Actual abstained: {actual_abst}")
print(f"PASS_EMPTY_CORRECT count: {empty_correct}")
print(f"Total fields accounted: {actual_verif + actual_abst}")
