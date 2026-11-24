import json
data = json.load(open('research/loop25/results/benchmark_results.json'))
print("Listing all false verifications:")
count = 0
for doc_id, doc in data['per_document'].items():
    for f in doc['fields']:
        if f['is_false_verification']:
            count += 1
            print(f"[{count}] {doc['cohort']} | {doc_id} | {f['field_name']}: got '{f['extracted']}', expected '{f['expected']}', conf: {f['confidence']}, rec: {f.get('row_recovery_method')}")
