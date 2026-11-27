import json

data = json.load(open("research/loop25/forensics/row_label_failure_audit.json"))
count = 0
for x in data:
    if x["failure_type"] in ["1_char_substitution", "2_char_deletion", "3_char_insertion"]:
        print(f"{x['document_id'][:28]:28s} | {x['field_name'][:18]:18s} | Expected: '{x['target_norm']}' vs OCR: '{x['actual_norm']}' ({x['failure_type']})")
        count += 1
        if count >= 20:
            break
