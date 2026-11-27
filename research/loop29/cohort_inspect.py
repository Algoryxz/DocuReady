import json

with open("research/loop26/dataset_manifest.json") as f:
    m26 = json.load(f)

with open("research/loop27/dataset_manifest.json") as f:
    m27 = json.load(f)

print("Loop 26 manifest keys:", list(m26.keys()))
if "cohorts" in m26:
    for c, data in m26["cohorts"].items():
        print(f"L26 Cohort {c}: docs={len(data.get('documents', []))}, fields={sum(len(d.get('critical_fields', [])) for d in data.get('documents', []))}")
elif "documents" in m26:
    print(f"L26 docs={len(m26['documents'])}")

print("\nLoop 27 manifest keys:", list(m27.keys()))
if "cohorts" in m27:
    for c, data in m27["cohorts"].items():
        print(f"L27 Cohort {c}: docs={len(data.get('documents', []))}, fields={sum(len(d.get('critical_fields', [])) for d in data.get('documents', []))}")
elif "documents" in m27:
    print(f"L27 docs={len(m27['documents'])}")
