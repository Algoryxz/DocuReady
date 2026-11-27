import sys
sys.path.insert(0, ".")
import json
from research.loop27.ablations.run_ablations import evaluate_adversarial_fixture

with open('research/loop27/corpus/adversarial_identifier_corpus.json', 'r', encoding='utf-8') as f:
    corpus = json.load(f)

print(f"Total fixtures: {len(corpus['fixtures'])}")
false_cases = []
for fix in corpus['fixtures']:
    res = evaluate_adversarial_fixture(fix, 'FULL_POLICY')
    if res['is_false_verification']:
        false_cases.append((fix, res))

print(f"Residual false verifications under FULL_POLICY: {len(false_cases)}")
for fix, res in false_cases:
    print(f"\n--- {fix['fixture_id']} ---")
    print(f"Category: {fix.get('category')}")
    print(f"Field   : {fix['field_name']}")
    print(f"Input   : '{fix['input_text']}'")
    print(f"GT      : '{fix['ground_truth']}'")
    print(f"Perturb : {fix.get('adversarial_perturbation')}")
    print(f"Expected Decision: {fix.get('expected_policy_decision')}")
