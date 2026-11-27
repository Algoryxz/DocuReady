"""
Loop 21 Synthetic Corpus Builder
Generates dedicated stress fixtures for:
1. Hierarchical Multi-Tier Column Headers (HIER_01, HIER_02, HIER_03)
2. Low-Resolution Decimal Point Integrity (DEC_01, DEC_02, DEC_03)
"""

import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
TABLES_DIR = ROOT / "research" / "loop21" / "tables"
TABLES_DIR.mkdir(parents=True, exist_ok=True)

try:
    font_title = ImageFont.truetype("arial.ttf", 20)
    font_head = ImageFont.truetype("arialbd.ttf", 14)
    font_body = ImageFont.truetype("arial.ttf", 12)
    font_small = ImageFont.truetype("arial.ttf", 11)
except Exception:
    font_title = ImageFont.load_default()
    font_head = ImageFont.load_default()
    font_body = ImageFont.load_default()
    font_small = ImageFont.load_default()

manifest_docs = {}

# ----------------------------------------------------------------------
# 1. HIER_01: QUARTERLY PERFORMANCE REPORT (2-Tier Header)
# Parent headers: FY 2025-26 Targets, FY 2025-26 Actuals
# Child headers: Division | Budget | Revenue | Budget | Revenue
# ----------------------------------------------------------------------
img1 = Image.new("RGB", (900, 450), color=(255, 255, 255))
d1 = ImageDraw.Draw(img1)
d1.text((250, 25), "QUARTERLY PERFORMANCE AUDIT REPORT", fill=(0, 0, 0), font=font_title)

# Tier 1 super-headers
d1.rectangle([50, 70, 210, 110], outline=(0, 0, 0), width=1)
d1.text((60, 82), "DIVISION", fill=(0, 0, 0), font=font_head)

d1.rectangle([210, 70, 550, 110], outline=(0, 0, 0), width=1)
d1.text((310, 82), "PLANNED TARGETS", fill=(0, 0, 0), font=font_head)

d1.rectangle([550, 70, 850, 110], outline=(0, 0, 0), width=1)
d1.text((650, 82), "ACHIEVED METRICS", fill=(0, 0, 0), font=font_head)

# Tier 2 child headers
cols1 = [50, 210, 380, 550, 700, 850]
h2_labels = ["Division Name", "Target Capex", "Target Opex", "Actual Capex", "Actual Opex"]
for i in range(5):
    d1.rectangle([cols1[i], 110, cols1[i+1], 150], outline=(0, 0, 0), width=1)
    d1.text((cols1[i] + 10, 122), h2_labels[i], fill=(0, 0, 0), font=font_head)

# Data rows
rows1 = [
    ["Agriculture", "150000", "45000", "148000", "42500"],
    ["Public Works", "320000", "95000", "310000", "91000"],
    ["Health Mission", "210000", "65000", "205000", "64200"],
]
for r_i, row in enumerate(rows1):
    y_top = 150 + r_i * 40
    y_bot = y_top + 40
    for c_i, val in enumerate(row):
        d1.rectangle([cols1[c_i], y_top, cols1[c_i+1], y_bot], outline=(128, 128, 128), width=1)
        d1.text((cols1[c_i] + 12, y_top + 12), val, fill=(0, 0, 0), font=font_body)

p1 = TABLES_DIR / "HIER_01_QUARTERLY_PERFORMANCE.png"
img1.save(p1)

manifest_docs["HIER_01_QUARTERLY_PERFORMANCE"] = {
    "cohort": "E_hierarchical_headers",
    "category": "Hierarchical Multi-Tier",
    "critical_fields": [
        {"name": "agri_actual_capex", "expected": "148000", "row": 0, "col": 3, "type": "amount", "target_pattern": "Agriculture", "col_pattern": "Actual Capex"},
        {"name": "health_target_opex", "expected": "65000", "row": 2, "col": 2, "type": "amount", "target_pattern": "Health Mission", "col_pattern": "Target Opex"},
    ]
}

# ----------------------------------------------------------------------
# 2. HIER_02: HEALTH IMMUNIZATION SUMMARY (2-Tier Header)
# Parent: District | Urban Centers | Rural Blocks
# Child: District | Target | Vaccinated | Target | Vaccinated
# ----------------------------------------------------------------------
img2 = Image.new("RGB", (900, 450), color=(255, 255, 255))
d2 = ImageDraw.Draw(img2)
d2.text((280, 25), "CHILD IMMUNIZATION CAMPAIGN SUMMARY", fill=(0, 0, 0), font=font_title)

d2.rectangle([50, 70, 210, 110], outline=(0, 0, 0), width=1)
d2.text((80, 82), "ADMINISTRATION", fill=(0, 0, 0), font=font_head)

d2.rectangle([210, 70, 530, 110], outline=(0, 0, 0), width=1)
d2.text((310, 82), "URBAN SECTOR", fill=(0, 0, 0), font=font_head)

d2.rectangle([530, 70, 850, 110], outline=(0, 0, 0), width=1)
d2.text((630, 82), "RURAL SECTOR", fill=(0, 0, 0), font=font_head)

cols2 = [50, 210, 370, 530, 690, 850]
h2_labels_2 = ["District", "Urban Target", "Urban Given", "Rural Target", "Rural Given"]
for i in range(5):
    d2.rectangle([cols2[i], 110, cols2[i+1], 150], outline=(0, 0, 0), width=1)
    d2.text((cols2[i] + 10, 122), h2_labels_2[i], fill=(0, 0, 0), font=font_head)

rows2 = [
    ["Khordha", "12500", "11800", "28000", "26500"],
    ["Cuttack", "14000", "13200", "31000", "29800"],
    ["Ganjam", "9500", "9100", "35000", "33500"],
]
for r_i, row in enumerate(rows2):
    y_top = 150 + r_i * 40
    y_bot = y_top + 40
    for c_i, val in enumerate(row):
        d2.rectangle([cols2[c_i], y_top, cols2[c_i+1], y_bot], outline=(128, 128, 128), width=1)
        d2.text((cols2[c_i] + 12, y_top + 12), val, fill=(0, 0, 0), font=font_body)

p2 = TABLES_DIR / "HIER_02_HEALTH_IMMUNIZATION.png"
img2.save(p2)

manifest_docs["HIER_02_HEALTH_IMMUNIZATION"] = {
    "cohort": "E_hierarchical_headers",
    "category": "Hierarchical Multi-Tier",
    "critical_fields": [
        {"name": "khordha_rural_given", "expected": "26500", "row": 0, "col": 4, "type": "count", "target_pattern": "Khordha", "col_pattern": "Rural Given"},
        {"name": "cuttack_urban_given", "expected": "13200", "row": 1, "col": 2, "type": "count", "target_pattern": "Cuttack", "col_pattern": "Urban Given"},
    ]
}

# ----------------------------------------------------------------------
# 3. HIER_03: MUNICIPAL TAX REVENUE (2-Tier Header)
# Parent: Zone | Commercial Properties | Residential Properties
# Child: Zone | Assessed | Collected | Assessed | Collected
# ----------------------------------------------------------------------
img3 = Image.new("RGB", (900, 450), color=(255, 255, 255))
d3 = ImageDraw.Draw(img3)
d3.text((290, 25), "MUNICIPAL PROPERTY TAX REGISTER", fill=(0, 0, 0), font=font_title)

d3.rectangle([50, 70, 210, 110], outline=(0, 0, 0), width=1)
d3.text((90, 82), "JURISDICTION", fill=(0, 0, 0), font=font_head)

d3.rectangle([210, 70, 530, 110], outline=(0, 0, 0), width=1)
d3.text((290, 82), "COMMERCIAL REVENUE", fill=(0, 0, 0), font=font_head)

d3.rectangle([530, 70, 850, 110], outline=(0, 0, 0), width=1)
d3.text((610, 82), "RESIDENTIAL REVENUE", fill=(0, 0, 0), font=font_head)

cols3 = [50, 210, 370, 530, 690, 850]
h2_labels_3 = ["Ward Zone", "Comm Assessed", "Comm Coll", "Res Assessed", "Res Coll"]
for i in range(5):
    d3.rectangle([cols3[i], 110, cols3[i+1], 150], outline=(0, 0, 0), width=1)
    d3.text((cols3[i] + 10, 122), h2_labels_3[i], fill=(0, 0, 0), font=font_head)

rows3 = [
    ["Zone North", "850000", "810000", "420000", "395000"],
    ["Zone Central", "1200000", "1150000", "650000", "620000"],
    ["Zone South", "680000", "640000", "380000", "365000"],
]
for r_i, row in enumerate(rows3):
    y_top = 150 + r_i * 40
    y_bot = y_top + 40
    for c_i, val in enumerate(row):
        d3.rectangle([cols3[c_i], y_top, cols3[c_i+1], y_bot], outline=(128, 128, 128), width=1)
        d3.text((cols3[c_i] + 12, y_top + 12), val, fill=(0, 0, 0), font=font_body)

p3 = TABLES_DIR / "HIER_03_TAX_REVENUE.png"
img3.save(p3)

manifest_docs["HIER_03_TAX_REVENUE"] = {
    "cohort": "E_hierarchical_headers",
    "category": "Hierarchical Multi-Tier",
    "critical_fields": [
        {"name": "central_comm_coll", "expected": "1150000", "row": 1, "col": 2, "type": "amount", "target_pattern": "Zone Central", "col_pattern": "Comm Coll"},
        {"name": "north_res_coll", "expected": "395000", "row": 0, "col": 4, "type": "amount", "target_pattern": "Zone North", "col_pattern": "Res Coll"},
    ]
}

# ----------------------------------------------------------------------
# 4. DEC_01: CLINICAL BIOCHEMISTRY PROFILE (Decimal Dots at 11-12px Font)
# Tests fine decimal dots in clinical measurements (e.g. 4.2, 0.8, 1.25)
# ----------------------------------------------------------------------
img4 = Image.new("RGB", (850, 480), color=(255, 255, 255))
d4 = ImageDraw.Draw(img4)
d4.text((250, 25), "REGIONAL DIAGNOSTIC BIOCHEMISTRY REPORT", fill=(0, 0, 0), font=font_title)

cols4 = [50, 280, 420, 560, 800]
h_labels_4 = ["Investigation", "Observed Value", "Units", "Biological Reference"]
for i in range(4):
    d4.rectangle([cols4[i], 70, cols4[i+1], 110], outline=(0, 0, 0), width=1)
    d4.text((cols4[i] + 10, 82), h_labels_4[i], fill=(0, 0, 0), font=font_head)

rows4 = [
    ["Serum Albumin", "4.2", "g/dL", "3.5 - 5.0"],
    ["Total Bilirubin", "0.8", "mg/dL", "0.2 - 1.2"],
    ["Serum Creatinine", "1.25", "mg/dL", "0.7 - 1.3"],
    ["Blood Urea Nitrogen", "24", "mg/dL", "7.0 - 20.0"],
    ["Serum Uric Acid", "6.4", "mg/dL", "3.4 - 7.0"],
]
for r_i, row in enumerate(rows4):
    y_top = 110 + r_i * 38
    y_bot = y_top + 38
    for c_i, val in enumerate(row):
        d4.rectangle([cols4[c_i], y_top, cols4[c_i+1], y_bot], outline=(128, 128, 128), width=1)
        d4.text((cols4[c_i] + 12, y_top + 10), val, fill=(0, 0, 0), font=font_small)

p4 = TABLES_DIR / "DEC_01_BIOCHEMISTRY_REPORT.png"
img4.save(p4)

manifest_docs["DEC_01_BIOCHEMISTRY_REPORT"] = {
    "cohort": "F_decimal_integrity",
    "category": "Decimal Integrity",
    "critical_fields": [
        {"name": "serum_albumin", "expected": "4.2", "row": 0, "col": 1, "type": "number", "target_pattern": "Serum Albumin"},
        {"name": "total_bilirubin", "expected": "0.8", "row": 1, "col": 1, "type": "number", "target_pattern": "Total Bilirubin"},
        {"name": "serum_creatinine", "expected": "1.25", "row": 2, "col": 1, "type": "number", "target_pattern": "Serum Creatinine"},
        {"name": "blood_urea", "expected": "24", "row": 3, "col": 1, "type": "number", "target_pattern": "Blood Urea Nitrogen"},
    ]
}

# ----------------------------------------------------------------------
# 5. DEC_02: COMMODITY TRADING DAILY RATES (Decimal Dots & Integers Mixed)
# Tests currency and rates with varying decimals (e.g. 84.15, 91.20, 108.5, 520)
# ----------------------------------------------------------------------
img5 = Image.new("RGB", (850, 480), color=(255, 255, 255))
d5 = ImageDraw.Draw(img5)
d5.text((270, 25), "DAILY COMMODITY SETTLEMENT BULLETIN", fill=(0, 0, 0), font=font_title)

cols5 = [50, 280, 420, 560, 800]
h_labels_5 = ["Commodity Code", "Opening Price", "Settlement Price", "Trading Volume"]
for i in range(4):
    d5.rectangle([cols5[i], 70, cols5[i+1], 110], outline=(0, 0, 0), width=1)
    d5.text((cols5[i] + 10, 82), h_labels_5[i], fill=(0, 0, 0), font=font_head)

rows5 = [
    ["Mustard Seed", "54.50", "56.25", "1200"],
    ["Soybean Grain", "42.80", "43.10", "2500"],
    ["Chana Whole", "68.5", "69.0", "1850"],
    ["Turmeric Polished", "135.25", "138.50", "940"],
    ["Barley Feed", "21.4", "22.0", "3100"],
]
for r_i, row in enumerate(rows5):
    y_top = 110 + r_i * 38
    y_bot = y_top + 38
    for c_i, val in enumerate(row):
        d5.rectangle([cols5[c_i], y_top, cols5[c_i+1], y_bot], outline=(128, 128, 128), width=1)
        d5.text((cols5[c_i] + 12, y_top + 10), val, fill=(0, 0, 0), font=font_small)

p5 = TABLES_DIR / "DEC_02_COMMODITY_RATES.png"
img5.save(p5)

manifest_docs["DEC_02_COMMODITY_RATES"] = {
    "cohort": "F_decimal_integrity",
    "category": "Decimal Integrity",
    "critical_fields": [
        {"name": "mustard_settlement", "expected": "56.25", "row": 0, "col": 2, "type": "number", "target_pattern": "Mustard Seed"},
        {"name": "chana_opening", "expected": "68.5", "row": 2, "col": 1, "type": "number", "target_pattern": "Chana Whole"},
        {"name": "turmeric_settlement", "expected": "138.50", "row": 3, "col": 2, "type": "number", "target_pattern": "Turmeric Polished"},
        {"name": "barley_volume", "expected": "3100", "row": 4, "col": 3, "type": "count", "target_pattern": "Barley Feed"},
    ]
}

# ----------------------------------------------------------------------
# 6. DEC_03: PHARMACEUTICAL QUALITY DOSAGE (Small Dosage Decimals)
# Tests 0.25, 0.5, 2.5, 10, 50
# ----------------------------------------------------------------------
img6 = Image.new("RGB", (850, 480), color=(255, 255, 255))
d6 = ImageDraw.Draw(img6)
d6.text((260, 25), "PHARMACEUTICAL DOSAGE STRENGTH AUDIT", fill=(0, 0, 0), font=font_title)

cols6 = [50, 280, 420, 560, 800]
h_labels_6 = ["Formulation", "Active Strength", "Batch Size", "Assay Percentage"]
for i in range(4):
    d6.rectangle([cols6[i], 70, cols6[i+1], 110], outline=(0, 0, 0), width=1)
    d6.text((cols6[i] + 10, 82), h_labels_6[i], fill=(0, 0, 0), font=font_head)

rows6 = [
    ["Levothyroxine Tab", "0.25", "100000", "99.4"],
    ["Clonazepam Tab", "0.5", "50000", "98.8"],
    ["Amlodipine Besylate", "2.5", "75000", "99.1"],
    ["Metformin HCl", "500", "120000", "99.7"],
    ["Atorvastatin Calcium", "10", "80000", "98.5"],
]
for r_i, row in enumerate(rows6):
    y_top = 110 + r_i * 38
    y_bot = y_top + 38
    for c_i, val in enumerate(row):
        d6.rectangle([cols6[c_i], y_top, cols6[c_i+1], y_bot], outline=(128, 128, 128), width=1)
        d6.text((cols6[c_i] + 12, y_top + 10), val, fill=(0, 0, 0), font=font_small)

p6 = TABLES_DIR / "DEC_03_PHARMA_DOSAGE.png"
img6.save(p6)

manifest_docs["DEC_03_PHARMA_DOSAGE"] = {
    "cohort": "F_decimal_integrity",
    "category": "Decimal Integrity",
    "critical_fields": [
        {"name": "levo_strength", "expected": "0.25", "row": 0, "col": 1, "type": "number", "target_pattern": "Levothyroxine Tab"},
        {"name": "clonazepam_strength", "expected": "0.5", "row": 1, "col": 1, "type": "number", "target_pattern": "Clonazepam Tab"},
        {"name": "amlodipine_strength", "expected": "2.5", "row": 2, "col": 1, "type": "number", "target_pattern": "Amlodipine Besylate"},
        {"name": "metformin_strength", "expected": "500", "row": 3, "col": 1, "type": "number", "target_pattern": "Metformin HCl"},
    ]
}

# Save manifest
manifest_out = {
    "benchmark_name": "Loop 21 Dedicated Stress Cohorts",
    "total_documents": len(manifest_docs),
    "cohorts": ["E_hierarchical_headers", "F_decimal_integrity"],
    "documents": manifest_docs,
}

manifest_path = ROOT / "research" / "loop21" / "dataset_manifest.json"
with open(manifest_path, "w", encoding="utf-8") as f:
    json.dump(manifest_out, f, indent=2)

print(f"Loop 21 corpus generated: {len(manifest_docs)} fixtures saved to {TABLES_DIR}")
