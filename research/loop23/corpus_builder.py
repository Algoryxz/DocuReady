"""
Loop 23 Synthetic Corpus Builder - Cohort H (Micro-Font & Narrow-Gutter Integrity)
Generates 6 dedicated blind evaluation fixtures:
1. COHORT_H_01_MICRO_CLINICAL_PANEL (Sub-10px font clinical chemistry)
2. COHORT_H_02_MICRO_DOSAGE_AUDIT (Sub-10px dosage and purity measurements)
3. COHORT_H_03_NARROW_GUTTER_LEDGER (Borderless financial ledger with tight 6-8px gutters)
4. COHORT_H_04_NARROW_GUTTER_INVOICE (Borderless invoice with adjacent price/qty/total)
5. COHORT_H_05_ADVERSARIAL_NARROW_EMPTY_TRAP (Empty cell adjacent to tight numeric column)
6. COHORT_H_06_ADVERSARIAL_MICRO_COLLISION (Repeated identifier collision in micro-font table)
"""

import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
TABLES_DIR = ROOT / "research" / "loop23" / "tables"
TABLES_DIR.mkdir(parents=True, exist_ok=True)

try:
    font_title = ImageFont.truetype("arial.ttf", 18)
    font_head = ImageFont.truetype("arialbd.ttf", 12)
    font_body = ImageFont.truetype("arial.ttf", 11)
    font_micro = ImageFont.truetype("arial.ttf", 10)
except Exception:
    font_title = ImageFont.load_default()
    font_head = ImageFont.load_default()
    font_body = ImageFont.load_default()
    font_micro = ImageFont.load_default()

manifest_docs = {}

# ----------------------------------------------------------------------
# 1. COHORT_H_01_MICRO_CLINICAL_PANEL
# ----------------------------------------------------------------------
img1 = Image.new("RGB", (850, 420), color=(255, 255, 255))
d1 = ImageDraw.Draw(img1)
d1.text((250, 20), "ADVANCED CLINICAL METABOLIC PANEL", fill=(0, 0, 0), font=font_title)

cols1 = [50, 280, 420, 560, 800]
h1 = ["Test Description", "Result", "Units", "Reference Range"]
for i in range(4):
    d1.rectangle([cols1[i], 60, cols1[i+1], 95], outline=(0, 0, 0), width=1)
    d1.text((cols1[i] + 10, 70), h1[i], fill=(0, 0, 0), font=font_head)

rows1 = [
    ["Hemoglobin A1c", "5.8", "%", "4.0 - 5.6"],
    ["Platelet Count", "240", "10^3/uL", "150 - 450"],
    ["Serum Potassium", "4.1", "mmol/L", "3.5 - 5.1"],
    ["Serum Sodium", "138", "mmol/L", "135 - 145"],
]
for r_i, row in enumerate(rows1):
    y_top = 95 + r_i * 35
    y_bot = y_top + 35
    for c_i, val in enumerate(row):
        d1.rectangle([cols1[c_i], y_top, cols1[c_i+1], y_bot], outline=(0, 0, 0), width=1)
        d1.text((cols1[c_i] + 12, y_top + 10), val, fill=(0, 0, 0), font=font_micro)

p1 = TABLES_DIR / "COHORT_H_01_MICRO_CLINICAL_PANEL.png"
img1.save(p1)

manifest_docs["COHORT_H_01_MICRO_CLINICAL_PANEL"] = {
    "cohort": "H_microfont_narrow_gutter",
    "category": "Micro-Font Clinical",
    "critical_fields": [
        {"name": "hba1c_result", "expected": "5.8", "row": 0, "col": 1, "type": "number", "target_pattern": "Hemoglobin A1c"},
        {"name": "platelet_count", "expected": "240", "row": 1, "col": 1, "type": "count", "target_pattern": "Platelet Count"},
        {"name": "potassium_result", "expected": "4.1", "row": 2, "col": 1, "type": "number", "target_pattern": "Serum Potassium"},
        {"name": "sodium_result", "expected": "138", "row": 3, "col": 1, "type": "number", "target_pattern": "Serum Sodium"},
    ]
}

# ----------------------------------------------------------------------
# 2. COHORT_H_02_MICRO_DOSAGE_AUDIT
# ----------------------------------------------------------------------
img2 = Image.new("RGB", (850, 420), color=(255, 255, 255))
d2 = ImageDraw.Draw(img2)
d2.text((260, 20), "PHARMACEUTICAL STRENGTH AUDIT", fill=(0, 0, 0), font=font_title)

cols2 = [50, 280, 420, 560, 800]
h2 = ["Product Code", "Active Strength", "Assay Purity", "Batch Units"]
for i in range(4):
    d2.rectangle([cols2[i], 60, cols2[i+1], 95], outline=(0, 0, 0), width=1)
    d2.text((cols2[i] + 10, 70), h2[i], fill=(0, 0, 0), font=font_head)

rows2 = [
    ["TAB-LORA-01", "0.75", "99.2", "4500"],
    ["TAB-DIAZ-02", "2.4", "98.7", "8000"],
    ["CAP-OMEP-03", "20", "99.5", "15000"],
]
for r_i, row in enumerate(rows2):
    y_top = 95 + r_i * 35
    y_bot = y_top + 35
    for c_i, val in enumerate(row):
        d2.rectangle([cols2[c_i], y_top, cols2[c_i+1], y_bot], outline=(0, 0, 0), width=1)
        d2.text((cols2[c_i] + 12, y_top + 10), val, fill=(0, 0, 0), font=font_micro)

p2 = TABLES_DIR / "COHORT_H_02_MICRO_DOSAGE_AUDIT.png"
img2.save(p2)

manifest_docs["COHORT_H_02_MICRO_DOSAGE_AUDIT"] = {
    "cohort": "H_microfont_narrow_gutter",
    "category": "Micro-Font Dosage",
    "critical_fields": [
        {"name": "lora_strength", "expected": "0.75", "row": 0, "col": 1, "type": "number", "target_pattern": "TAB-LORA-01"},
        {"name": "lora_purity", "expected": "99.2", "row": 0, "col": 2, "type": "percentage", "target_pattern": "TAB-LORA-01"},
        {"name": "diaz_strength", "expected": "2.4", "row": 1, "col": 1, "type": "number", "target_pattern": "TAB-DIAZ-02"},
        {"name": "omep_strength", "expected": "20", "row": 2, "col": 1, "type": "number", "target_pattern": "CAP-OMEP-03"},
    ]
}

# ----------------------------------------------------------------------
# 3. COHORT_H_03_NARROW_GUTTER_LEDGER (Borderless with tight gutters)
# ----------------------------------------------------------------------
img3 = Image.new("RGB", (850, 400), color=(255, 255, 255))
d3 = ImageDraw.Draw(img3)
d3.text((270, 25), "DAILY CLEARING SETTLEMENT LEDGER", fill=(0, 0, 0), font=font_title)

# Header (borderless layout, tight horizontal spacing)
d3.text((60, 80), "Account Entity", fill=(0, 0, 0), font=font_head)
d3.text((280, 80), "Debit (INR) _ Credit (INR)", fill=(0, 0, 0), font=font_head)
d3.text((680, 80), "Closing Balance (INR)", fill=(0, 0, 0), font=font_head)

rows3 = [
    ("ACC-101 Alpha Traders", "12500", "1250", "11250"),
    ("ACC-102 Beta Logistics", "34000", "3400", "30600"),
    ("ACC-103 Gamma Infotech", "56000", "5600", "50400"),
]
for r_i, (acc, deb, cred, bal) in enumerate(rows3):
    y = 130 + r_i * 45
    d3.text((60, y), acc, fill=(0, 0, 0), font=font_body)
    # Tight gutter between Debit and Credit (gap ~25px)
    d3.text((280, y), deb, fill=(0, 0, 0), font=font_body)
    d3.text((345, y), cred, fill=(0, 0, 0), font=font_body)
    d3.text((680, y), bal, fill=(0, 0, 0), font=font_body)

p3 = TABLES_DIR / "COHORT_H_03_NARROW_GUTTER_LEDGER.png"
img3.save(p3)

manifest_docs["COHORT_H_03_NARROW_GUTTER_LEDGER"] = {
    "cohort": "H_microfont_narrow_gutter",
    "category": "Narrow-Gutter Financial",
    "critical_fields": [
        {"name": "alpha_debit", "expected": "12500", "row": 0, "col": 1, "type": "amount", "target_pattern": "ACC-101", "col_pattern": "Debit"},
        {"name": "alpha_credit", "expected": "1250", "row": 0, "col": 1, "type": "amount", "target_pattern": "ACC-101", "col_pattern": "Credit"},
        {"name": "beta_closing", "expected": "30600", "row": 1, "col": 2, "type": "amount", "target_pattern": "ACC-102"},
    ]
}

# ----------------------------------------------------------------------
# 4. COHORT_H_04_NARROW_GUTTER_INVOICE (Borderless invoice)
# ----------------------------------------------------------------------
img4 = Image.new("RGB", (850, 400), color=(255, 255, 255))
d4 = ImageDraw.Draw(img4)
d4.text((280, 25), "COMMODITY SUPPLY BILL OF SUPPLY", fill=(0, 0, 0), font=font_title)

d4.text((60, 80), "Line Item", fill=(0, 0, 0), font=font_head)
d4.text((280, 80), "Rate (INR) _ Tax (INR)", fill=(0, 0, 0), font=font_head)
d4.text((680, 80), "Gross Total (INR)", fill=(0, 0, 0), font=font_head)

rows4 = [
    ("Wheat Flour Premium 50kg", "45.50", "2.25", "2387.50"),
    ("Refined Palm Oil 15L", "110.00", "5.50", "1732.50"),
    ("Sugar Crystal M-30 50kg", "38.20", "1.90", "2005.00"),
]
for r_i, (item, rate, tax, gross) in enumerate(rows4):
    y = 130 + r_i * 45
    d4.text((60, y), item, fill=(0, 0, 0), font=font_body)
    d4.text((280, y), rate, fill=(0, 0, 0), font=font_body)
    d4.text((345, y), tax, fill=(0, 0, 0), font=font_body)
    d4.text((680, y), gross, fill=(0, 0, 0), font=font_body)

p4 = TABLES_DIR / "COHORT_H_04_NARROW_GUTTER_INVOICE.png"
img4.save(p4)

manifest_docs["COHORT_H_04_NARROW_GUTTER_INVOICE"] = {
    "cohort": "H_microfont_narrow_gutter",
    "category": "Narrow-Gutter Commercial",
    "critical_fields": [
        {"name": "flour_rate", "expected": "45.50", "row": 0, "col": 1, "type": "amount", "target_pattern": "Wheat Flour", "col_pattern": "Rate"},
        {"name": "flour_tax", "expected": "2.25", "row": 0, "col": 1, "type": "amount", "target_pattern": "Wheat Flour", "col_pattern": "Tax"},
        {"name": "sugar_rate", "expected": "38.20", "row": 2, "col": 1, "type": "amount", "target_pattern": "Sugar Crystal", "col_pattern": "Rate"},
    ]
}

# ----------------------------------------------------------------------
# 5. COHORT_H_05_ADVERSARIAL_NARROW_EMPTY_TRAP
# ----------------------------------------------------------------------
img5 = Image.new("RGB", (850, 400), color=(255, 255, 255))
d5 = ImageDraw.Draw(img5)
d5.text((260, 25), "ARREARS ASSESSMENT SPECIAL SCHEDULE", fill=(0, 0, 0), font=font_title)

d5.text((60, 80), "Taxpayer Record", fill=(0, 0, 0), font=font_head)
d5.text((280, 80), "Penal Surcharge", fill=(0, 0, 0), font=font_head)
d5.text((500, 80), "Current Year Demand", fill=(0, 0, 0), font=font_head)

# Row 1: Penal Surcharge is EMPTY! Current Demand is 28000
d5.text((60, 140), "REC-701 Narayan Jena", fill=(0, 0, 0), font=font_body)
# Penal Surcharge is intentionally BLANK
d5.text((500, 140), "28000", fill=(0, 0, 0), font=font_body)

# Row 2: Has both
d5.text((60, 190), "REC-702 Bishnu Swain", fill=(0, 0, 0), font=font_body)
d5.text((280, 190), "4500", fill=(0, 0, 0), font=font_body)
d5.text((500, 190), "32000", fill=(0, 0, 0), font=font_body)

p5 = TABLES_DIR / "COHORT_H_05_ADVERSARIAL_NARROW_EMPTY_TRAP.png"
img5.save(p5)

manifest_docs["COHORT_H_05_ADVERSARIAL_NARROW_EMPTY_TRAP"] = {
    "cohort": "H_microfont_narrow_gutter",
    "category": "Adversarial Trap",
    "critical_fields": [
        {"name": "narayan_penal_empty", "expected": "", "row": 0, "col": 1, "type": "empty", "target_pattern": "REC-701", "is_trap": True},
        {"name": "narayan_current_demand", "expected": "28000", "row": 0, "col": 2, "type": "amount", "target_pattern": "REC-701"},
    ]
}

# ----------------------------------------------------------------------
# 6. COHORT_H_06_ADVERSARIAL_MICRO_COLLISION
# ----------------------------------------------------------------------
img6 = Image.new("RGB", (850, 420), color=(255, 255, 255))
d6 = ImageDraw.Draw(img6)
d6.text((240, 25), "BRANCH SETTLEMENT MULTI-RECORD AUDIT", fill=(0, 0, 0), font=font_title)

cols6 = [50, 260, 450, 650, 800]
h6 = ["Reference ID", "Branch Name", "Quarterly Volume", "Clearance Status"]
for i in range(4):
    d6.rectangle([cols6[i], 70, cols6[i+1], 105], outline=(0, 0, 0), width=1)
    d6.text((cols6[i] + 10, 80), h6[i], fill=(0, 0, 0), font=font_head)

rows6 = [
    ["ACC-901", "Cuttack Metro Branch", "14800", "CLEARED"],
    ["ACC-901", "Bhubaneswar South Branch", "26500", "PENDING"],  # Collision on ACC-901!
    ["ACC-902", "Puri Seaside Branch", "19200", "CLEARED"],
]
for r_i, row in enumerate(rows6):
    y_top = 105 + r_i * 40
    y_bot = y_top + 40
    for c_i, val in enumerate(row):
        d6.rectangle([cols6[c_i], y_top, cols6[c_i+1], y_bot], outline=(0, 0, 0), width=1)
        d6.text((cols6[c_i] + 12, y_top + 12), val, fill=(0, 0, 0), font=font_micro)

p6 = TABLES_DIR / "COHORT_H_06_ADVERSARIAL_MICRO_COLLISION.png"
img6.save(p6)

manifest_docs["COHORT_H_06_ADVERSARIAL_MICRO_COLLISION"] = {
    "cohort": "H_microfont_narrow_gutter",
    "category": "Adversarial Trap",
    "critical_fields": [
        # ACC-901 appears in row 0 and row 1: must abstain due to multi-row ambiguity!
        {"name": "acc_901_ambiguous_vol", "expected": "", "row": 0, "col": 2, "type": "empty", "target_pattern": "ACC-901", "is_trap": True},
        {"name": "acc_902_puri_vol", "expected": "19200", "row": 2, "col": 2, "type": "amount", "target_pattern": "ACC-902"},
    ]
}

manifest_out = {
    "benchmark_name": "Loop 23 Cohort H (Micro-Font & Narrow-Gutter Integrity)",
    "total_documents": len(manifest_docs),
    "cohorts": ["H_microfont_narrow_gutter"],
    "documents": manifest_docs,
}

manifest_path = ROOT / "research" / "loop23" / "dataset_manifest.json"
with open(manifest_path, "w", encoding="utf-8") as f:
    json.dump(manifest_out, f, indent=2)

print(f"Generated {len(manifest_docs)} documents for Cohort H in {TABLES_DIR}")
print(f"Manifest written to {manifest_path}")
