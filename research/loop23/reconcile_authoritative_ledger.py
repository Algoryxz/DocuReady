import json

with open("research/loop22/results/benchmark_results.json", "r", encoding="utf-8") as f:
    data = json.load(f)

per_doc = data["per_document"]
per_cohort_data = {}

for doc_id, doc in per_doc.items():
    cohort = doc["cohort"]
    if cohort not in per_cohort_data:
        per_cohort_data[cohort] = {
            "docs": 0,
            "fields": 0,
            "verified": 0,
            "exact_verified": 0,
            "false_verified": 0,
            "abstained": 0,
            "sem_passes": 0,
            "empty_correct": 0,
            "abstained_sem_passes": 0
        }
    
    st = per_cohort_data[cohort]
    st["docs"] += 1
    
    for fn, fld in doc["fields"].items():
        st["fields"] += 1
        is_verif = fld.get("is_verified", False)
        is_fv = fld.get("is_false_verification", False)
        is_abst = fld.get("is_abstained", False)
        is_sem = fld.get("sem_pass", False)
        status = fld.get("status", "")
        
        if is_sem:
            st["sem_passes"] += 1
        if status == "PASS_EMPTY_CORRECT":
            st["empty_correct"] += 1
            
        if is_verif:
            st["verified"] += 1
            if is_fv:
                st["false_verified"] += 1
            else:
                st["exact_verified"] += 1
        elif is_abst:
            st["abstained"] += 1
            if is_sem and status != "PASS_EMPTY_CORRECT":
                st["abstained_sem_passes"] += 1

print(f"{'Cohort':<26} | {'Docs':>4} | {'Fields':>6} | {'Verif':>5} | {'Exact':>5} | {'FV':>3} | {'Abst':>4} | {'SEM':>4} | {'Precision':>9} | {'Coverage':>8}")
print("-" * 92)

tot_docs = 0
tot_fields = 0
tot_verif = 0
tot_exact = 0
tot_fv = 0
tot_abst = 0
tot_sem = 0

for c_name, st in sorted(per_cohort_data.items()):
    prec = st["exact_verified"] / st["verified"] * 100 if st["verified"] > 0 else 0
    cov = st["verified"] / st["fields"] * 100 if st["fields"] > 0 else 0
    print(f"{c_name:<26} | {st['docs']:>4} | {st['fields']:>6} | {st['verified']:>5} | {st['exact_verified']:>5} | {st['false_verified']:>3} | {st['abstained']:>4} | {st['sem_passes']:>4} | {prec:>8.2f}% | {cov:>7.2f}%")
    tot_docs += st["docs"]
    tot_fields += st["fields"]
    tot_verif += st["verified"]
    tot_exact += st["exact_verified"]
    tot_fv += st["false_verified"]
    tot_abst += st["abstained"]
    tot_sem += st["sem_passes"]

print("-" * 92)
tot_prec = tot_exact / tot_verif * 100 if tot_verif > 0 else 0
tot_cov = tot_verif / tot_fields * 100 if tot_fields > 0 else 0
print(f"{'TOTAL':<26} | {tot_docs:>4} | {tot_fields:>6} | {tot_verif:>5} | {tot_exact:>5} | {tot_fv:>3} | {tot_abst:>4} | {tot_sem:>4} | {tot_prec:>8.2f}% | {tot_cov:>7.2f}%")
