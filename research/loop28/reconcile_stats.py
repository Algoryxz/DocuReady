import json

with open('research/loop27/results/benchmark_results.json', 'r', encoding='utf-8') as f:
    bench = json.load(f)

for c_name, c_data in bench['per_cohort'].items():
    print(f"{c_name:30}: fields={c_data['total_fields']:3d} V={c_data['verified_claims']:3d} E={c_data['exact_matches']:3d} F={c_data['false_verifications']:3d} A={c_data['abstentions']:3d}")

s = bench['summary']
print("\nAggregate:")
print(f"Total Docs  : {s['total_documents']}")
print(f"Total Fields: {s['total_critical_fields']}")
print(f"V={s['verified_claims']} E={s['exact_matches']} F={s['false_verifications']} A={s['abstentions']}")
