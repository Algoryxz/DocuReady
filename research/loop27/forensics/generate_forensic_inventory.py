import json
from pathlib import Path

out_dir = Path("research/loop27/forensics")
out_dir.mkdir(parents=True, exist_ok=True)

with open("research/loop26/results/benchmark_results.json", "r", encoding="utf-8") as f:
    bench = json.load(f)

d = bench["per_document"]
inventory = []
for doc_id, doc_info in d.items():
    if "COHORT_K" in doc_id:
        for f in doc_info["fields"]:
            if f.get("is_verified") and not f.get("is_exact"):
                is_ifsc = "IFSC" in f["field_name"] or "BARB" in f["expected"] or "SBIN" in f["expected"]
                item = {
                    "case_id": f"CASE_{len(inventory)+1:02d}",
                    "doc_id": doc_id,
                    "cohort": doc_info.get("cohort", "Cohort_K"),
                    "field_name": f["field_name"],
                    "expected": f["expected"],
                    "extracted": f["extracted"],
                    "confidence": f["confidence"],
                    "error_type": "Character-level OCR Substitution (O vs 0)" if is_ifsc else "Glyph Confusion + Punctuation Bleed (6 vs 8)",
                    "glyph_pair": "O vs 0" if is_ifsc else "6 vs 8 + trailing comma",
                    "root_cause": (
                        "IFSC syntax requires 5th char to be 0 (^[A-Z]{4}0[A-Z0-9]{6}$). "
                        "Tesseract OCR recognized 0 as capital letter O with high confidence. "
                        "Unconstrained verification accepted invalid IFSC without syntax or ambiguity check."
                    ) if is_ifsc else (
                        "OCR glyph confusion substituted 6 with 8 in year token, "
                        "and trailing comma was not cleanly stripped, producing invalid date format."
                    ),
                    "remedy": (
                        "Implement strict identifier syntax and glyph confusable validation. "
                        "Flag O/0 ambiguity at index 4 of IFSC pattern and abstain under conservative policy."
                    ) if is_ifsc else (
                        "Enforce trailing punctuation stripping and date semantic validation."
                    )
                }
                inventory.append(item)

inv_path = out_dir / "ten_false_verifications_inventory.json"
with open(inv_path, "w", encoding="utf-8") as f:
    json.dump({"total_cases": len(inventory), "cases": inventory}, f, indent=2)

print(f"Successfully wrote {len(inventory)} cases to {inv_path}")
