"""
Loop 22 Synthetic Corpus Builder
Generates Cohort G (Evidence Association & Risk-Calibrated Abstention):
1. ASSOC_01_NEIGHBORING_COLUMN_TRAP (adjacent numeric columns with similar format)
2. ASSOC_02_REPEATED_TRANSACTION_ID (repeated ID across multiple sections)
3. ASSOC_03_GUTTER_BLEED_SPLIT_CELL (tight gutter causing concatenated numeric tokens)
4. ASSOC_04_LOW_CONFIDENCE_GARBLE (degraded scan causing low confidence garble)
5. ASSOC_05_CONTEXTUAL_CURRENCY_MISMATCH (type/unit mismatch across semantic columns)
6. ASSOC_06_CROSS_DOC_DISAGREEMENT (voucher with conflicting evidence across records)
"""

import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
TABLES_DIR = ROOT / "research" / "loop22" / "tables"
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
# 1. ASSOC_01: NEIGHBORING COLUMN TRAP
# Columns: Item Description | Base Cost (INR) | Clearance Surcharge (INR) | Net Amount (INR)
# ----------------------------------------------------------------------
img1 = Image.new("RGB", (900, 420), color=(255, 255, 255))
d1 = ImageDraw.Draw(img1)
d1.text((260, 25), "WAREHOUSE CLEARANCE AUDIT REGISTER", fill=(0, 0, 0), font=font_title)

cols1 = [50, 280, 460, 680, 850]
h1_labels = ["Item Description", "Base Cost (INR)", "Clearance Surcharge (INR)", "Net Amount (INR)"]
for i in range(4):
    d1.rectangle([cols1[i], 80, cols1[i+1], 120], outline=(0, 0, 0), width=1)
    d1.text((cols1[i] + 10, 92), h1_labels[i], fill=(0, 0, 0), font=font_head)

rows1 = [
    ["Turbine Bearings Batch A", "25000", "2500", "27500"],
    ["Hydraulic Actuators H-2", "48000", "4800", "52800"],
    ["Control Valve Assemblies", "36000", "3600", "39600"],
    ["Pressure Transmitters P-9", "18000", "1800", "19800"],
]
for r_i, row_data in enumerate(rows1):
    y_top = 120 + r_i * 45
    for c_i, val in enumerate(row_data):
        d1.rectangle([cols1[c_i], y_top, cols1[c_i+1], y_top + 45], outline=(0, 0, 0), width=1)
        d1.text((cols1[c_i] + 10, y_top + 14), val, fill=(0, 0, 0), font=font_body)

img1_path = TABLES_DIR / "ASSOC_01_NEIGHBORING_COLUMN_TRAP.png"
img1.save(img1_path)

manifest_docs["ASSOC_01_NEIGHBORING_COLUMN_TRAP"] = {
    "cohort": "G_evidence_association",
    "category": "neighboring_column_trap",
    "image_path": str(img1_path.relative_to(ROOT)).replace("\\", "/"),
    "critical_fields": [
        {
            "name": "turbine_clearance_surcharge",
            "expected": "2500",
            "row": 0,
            "col": 2,
            "type": "amount",
            "target_pattern": "Turbine Bearings Batch A",
            "col_pattern": "Clearance Surcharge"
        },
        {
            "name": "actuator_base_cost",
            "expected": "48000",
            "row": 1,
            "col": 1,
            "type": "amount",
            "target_pattern": "Hydraulic Actuators H-2",
            "col_pattern": "Base Cost"
        }
    ]
}

# ----------------------------------------------------------------------
# 2. ASSOC_02: REPEATED TRANSACTION ID
# Multi-section financial ledger where TXN-9092 appears in Disputed vs Settled
# ----------------------------------------------------------------------
img2 = Image.new("RGB", (900, 480), color=(255, 255, 255))
d2 = ImageDraw.Draw(img2)
d2.text((270, 20), "MERCHANT SETTLEMENT RECONCILIATION", fill=(0, 0, 0), font=font_title)

# Section 1: AUDIT DISPUTED CLAIMS
d2.text((50, 70), "SECTION 1: DISPUTED / ESCALATED TRANSACTIONS", fill=(180, 0, 0), font=font_head)
cols2 = [50, 230, 450, 650, 850]
h2_labels = ["Reference ID", "Merchant Name", "Dispute Code", "Withheld Amount (INR)"]
for i in range(4):
    d2.rectangle([cols2[i], 95, cols2[i+1], 130], outline=(0, 0, 0), width=1)
    d2.text((cols2[i] + 10, 105), h2_labels[i], fill=(0, 0, 0), font=font_head)

r2_sec1 = [
    ["TXN-9092", "Kalinga Logistics Pvt", "ERR-DISPUTE-77", "14500"],
    ["TXN-9098", "Mahanadi Traders Ltd", "ERR-DUPLICATE-12", "8200"],
]
for r_i, row_data in enumerate(r2_sec1):
    y_top = 130 + r_i * 35
    for c_i, val in enumerate(row_data):
        d2.rectangle([cols2[c_i], y_top, cols2[c_i+1], y_top + 35], outline=(0, 0, 0), width=1)
        d2.text((cols2[c_i] + 10, y_top + 10), val, fill=(0, 0, 0), font=font_body)

# Section 2: SETTLED CLAIMS
d2.text((50, 225), "SECTION 2: FINAL SETTLED TRANSACTIONS", fill=(0, 120, 0), font=font_head)
h2_labels_sec2 = ["Reference ID", "Merchant Name", "Settlement Batch", "Released Amount (INR)"]
for i in range(4):
    d2.rectangle([cols2[i], 250, cols2[i+1], 285], outline=(0, 0, 0), width=1)
    d2.text((cols2[i] + 10, 260), h2_labels_sec2[i], fill=(0, 0, 0), font=font_head)

r2_sec2 = [
    ["TXN-9092", "Kalinga Logistics Pvt", "BATCH-NOV-04", "89000"],
    ["TXN-9104", "Utkal Petrochemicals", "BATCH-NOV-05", "112000"],
]
for r_i, row_data in enumerate(r2_sec2):
    y_top = 285 + r_i * 35
    for c_i, val in enumerate(row_data):
        d2.rectangle([cols2[c_i], y_top, cols2[c_i+1], y_top + 35], outline=(0, 0, 0), width=1)
        d2.text((cols2[c_i] + 10, y_top + 10), val, fill=(0, 0, 0), font=font_body)

img2_path = TABLES_DIR / "ASSOC_02_REPEATED_TRANSACTION_ID.png"
img2.save(img2_path)

manifest_docs["ASSOC_02_REPEATED_TRANSACTION_ID"] = {
    "cohort": "G_evidence_association",
    "category": "repeated_transaction_id",
    "image_path": str(img2_path.relative_to(ROOT)).replace("\\", "/"),
    "critical_fields": [
        {
            "name": "txn_9092_withheld_amount",
            "expected": "14500",
            "row": 0,
            "col": 3,
            "type": "amount",
            "target_pattern": "TXN-9092",
            "col_pattern": "Withheld"
        },
        {
            "name": "txn_9104_released_amount",
            "expected": "112000",
            "row": 3,
            "col": 3,
            "type": "amount",
            "target_pattern": "TXN-9104",
            "col_pattern": "Released"
        }
    ]
}

# ----------------------------------------------------------------------
# 3. ASSOC_03: GUTTER BLEED SPLIT CELL (Borderless table with tight gutter)
# Columns: Holding Ref | Tax Assessed (INR) | Surcharge Penalty (INR) | Net Due (INR)
# Tax Assessed and Surcharge Penalty have tight gutter (8px), causing merge
# ----------------------------------------------------------------------
img3 = Image.new("RGB", (900, 380), color=(255, 255, 255))
d3 = ImageDraw.Draw(img3)
d3.text((280, 25), "MUNICIPAL ASSESSMENT SCHEDULE", fill=(0, 0, 0), font=font_title)

# Borderless columns with tight gutter between Col 1 and Col 2
c3_0 = 60
c3_1 = 280
c3_2 = 420  # Only ~100px width
c3_3 = 680

d3.text((c3_0, 80), "Property ID & Owner", fill=(0, 0, 0), font=font_head)
d3.text((c3_1, 80), "Base Tax (INR)", fill=(0, 0, 0), font=font_head)
d3.text((c3_2, 80), "Penalty (INR)", fill=(0, 0, 0), font=font_head)
d3.text((c3_3, 80), "Total Payable (INR)", fill=(0, 0, 0), font=font_head)

rows3 = [
    ("PID-401 Binodini Mohanty", "85000", "8500", "93500"),
    ("PID-402 Chandrasekhar Kar", "64000", "6400", "70400"),
    ("PID-403 Damodar Senapati", "42000", "4200", "46200"),
]
for r_i, (p_id, t_base, t_pen, t_tot) in enumerate(rows3):
    y_pos = 130 + r_i * 45
    d3.text((c3_0, y_pos), p_id, fill=(0, 0, 0), font=font_body)
    # Draw base tax and penalty closely spaced (tight 8px gap)
    d3.text((c3_1, y_pos), t_base, fill=(0, 0, 0), font=font_body)
    d3.text((c3_1 + 65, y_pos), t_pen, fill=(0, 0, 0), font=font_body)
    d3.text((c3_3, y_pos), t_tot, fill=(0, 0, 0), font=font_body)

img3_path = TABLES_DIR / "ASSOC_03_GUTTER_BLEED_SPLIT_CELL.png"
img3.save(img3_path)

manifest_docs["ASSOC_03_GUTTER_BLEED_SPLIT_CELL"] = {
    "cohort": "G_evidence_association",
    "category": "gutter_bleed_split_cell",
    "image_path": str(img3_path.relative_to(ROOT)).replace("\\", "/"),
    "critical_fields": [
        {
            "name": "binodini_base_tax",
            "expected": "85000",
            "row": 0,
            "col": 1,
            "type": "amount",
            "target_pattern": "Binodini Mohanty",
            "col_pattern": "Base Tax",
            "trap_note": "Tight gutter may bleed '85000 8500' - must abstain if multi-token"
        },
        {
            "name": "damodar_total_payable",
            "expected": "46200",
            "row": 2,
            "col": 2,
            "type": "amount",
            "target_pattern": "Damodar Senapati",
            "col_pattern": "Total Payable"
        }
    ]
}

# ----------------------------------------------------------------------
# 4. ASSOC_04: LOW CONFIDENCE GARBLE
# Degraded print causing Tesseract to produce garble with low confidence
# ----------------------------------------------------------------------
img4 = Image.new("RGB", (900, 380), color=(255, 255, 255))
d4 = ImageDraw.Draw(img4)
d4.text((260, 25), "REGULATORY COMPLIANCE AUDIT VOUCHER", fill=(0, 0, 0), font=font_title)

cols4 = [60, 280, 480, 680, 850]
h4_labels = ["Inspection Item", "Mandatory Norm", "Recorded Level", "Compliance Status"]
for i in range(4):
    d4.rectangle([cols4[i], 80, cols4[i+1], 120], outline=(0, 0, 0), width=1)
    d4.text((cols4[i] + 10, 92), h4_labels[i], fill=(0, 0, 0), font=font_head)

# Row 1 is normal
d4.rectangle([cols4[0], 120, cols4[1], 165], outline=(0, 0, 0), width=1)
d4.text((cols4[0] + 10, 134), "Boiler Emission Index", fill=(0, 0, 0), font=font_body)
d4.rectangle([cols4[1], 120, cols4[2], 165], outline=(0, 0, 0), width=1)
d4.text((cols4[1] + 10, 134), "<= 50 mg/Nm3", fill=(0, 0, 0), font=font_body)
d4.rectangle([cols4[2], 120, cols4[3], 165], outline=(0, 0, 0), width=1)
d4.text((cols4[2] + 10, 134), "38.5 mg/Nm3", fill=(0, 0, 0), font=font_body)
d4.rectangle([cols4[3], 120, cols4[4], 165], outline=(0, 0, 0), width=1)
d4.text((cols4[3] + 10, 134), "PASS", fill=(0, 0, 0), font=font_body)

# Row 2 has severe noise in compliance status
d4.rectangle([cols4[0], 165, cols4[1], 210], outline=(0, 0, 0), width=1)
d4.text((cols4[0] + 10, 179), "Effluent pH Buffer", fill=(0, 0, 0), font=font_body)
d4.rectangle([cols4[1], 165, cols4[2], 210], outline=(0, 0, 0), width=1)
d4.text((cols4[1] + 10, 179), "6.5 - 8.5 pH", fill=(0, 0, 0), font=font_body)
d4.rectangle([cols4[2], 165, cols4[3], 210], outline=(0, 0, 0), width=1)
d4.text((cols4[2] + 10, 179), "7.2 pH", fill=(0, 0, 0), font=font_body)
d4.rectangle([cols4[3], 165, cols4[4], 210], outline=(0, 0, 0), width=1)

# Draw garbled degraded glyphs in Status cell
d4.text((cols4[3] + 10, 179), "~{fe}§", fill=(120, 120, 120), font=font_body)
# Add small random noise speckles in this cell
import random
rng = random.Random(42)
for _ in range(50):
    nx = rng.randint(cols4[3] + 5, cols4[4] - 5)
    ny = rng.randint(170, 205)
    d4.point((nx, ny), fill=(100, 100, 100))

img4_path = TABLES_DIR / "ASSOC_04_LOW_CONFIDENCE_GARBLE.png"
img4.save(img4_path)

manifest_docs["ASSOC_04_LOW_CONFIDENCE_GARBLE"] = {
    "cohort": "G_evidence_association",
    "category": "low_confidence_garble",
    "image_path": str(img4_path.relative_to(ROOT)).replace("\\", "/"),
    "critical_fields": [
        {
            "name": "boiler_emission_level",
            "expected": "38.5 mg/Nm3",
            "row": 0,
            "col": 2,
            "type": "text",
            "target_pattern": "Boiler Emission Index",
            "col_pattern": "Recorded Level"
        },
        {
            "name": "effluent_compliance_status",
            "expected": "PASS",
            "row": 1,
            "col": 3,
            "type": "code",
            "target_pattern": "Effluent pH Buffer",
            "col_pattern": "Compliance Status",
            "trap_note": "Degraded scan garble - must abstain on low confidence or syntax characters"
        }
    ]
}

# ----------------------------------------------------------------------
# 5. ASSOC_05: CONTEXTUAL CURRENCY MISMATCH
# Equipment table: Unit Model | Power Rating (kW) | Operational Efficiency (%) | Asset Valuation (INR)
# ----------------------------------------------------------------------
img5 = Image.new("RGB", (900, 380), color=(255, 255, 255))
d5 = ImageDraw.Draw(img5)
d5.text((270, 25), "HEAVY MACHINERY TECHNICAL INVENTORY", fill=(0, 0, 0), font=font_title)

cols5 = [50, 260, 440, 640, 850]
h5_labels = ["Equipment Model", "Power Rating (kW)", "Efficiency Rating (%)", "Asset Valuation (INR)"]
for i in range(4):
    d5.rectangle([cols5[i], 80, cols5[i+1], 120], outline=(0, 0, 0), width=1)
    d5.text((cols5[i] + 10, 92), h5_labels[i], fill=(0, 0, 0), font=font_head)

rows5 = [
    ["Centrifugal Compressor CC-9", "450 kW", "94.5%", "1450000"],
    ["Rotary Kiln Drive RKD-2", "820 kW", "89.2%", "2800000"],
    ["Slurry Pump Unit SP-14", "160 kW", "91.8%", "680000"],
]
for r_i, row_data in enumerate(rows5):
    y_top = 120 + r_i * 45
    for c_i, val in enumerate(row_data):
        d5.rectangle([cols5[c_i], y_top, cols5[c_i+1], y_top + 45], outline=(0, 0, 0), width=1)
        d5.text((cols5[c_i] + 10, y_top + 14), val, fill=(0, 0, 0), font=font_body)

img5_path = TABLES_DIR / "ASSOC_05_CONTEXTUAL_CURRENCY_MISMATCH.png"
img5.save(img5_path)

manifest_docs["ASSOC_05_CONTEXTUAL_CURRENCY_MISMATCH"] = {
    "cohort": "G_evidence_association",
    "category": "contextual_type_mismatch",
    "image_path": str(img5_path.relative_to(ROOT)).replace("\\", "/"),
    "critical_fields": [
        {
            "name": "compressor_efficiency",
            "expected": "94.5%",
            "row": 0,
            "col": 2,
            "type": "percentage",
            "target_pattern": "Centrifugal Compressor CC-9",
            "col_pattern": "Efficiency"
        },
        {
            "name": "rotary_kiln_power",
            "expected": "820 kW",
            "row": 1,
            "col": 1,
            "type": "unit",
            "target_pattern": "Rotary Kiln Drive RKD-2",
            "col_pattern": "Power"
        }
    ]
}

# ----------------------------------------------------------------------
# 6. ASSOC_06: CROSS-DOC DISAGREEMENT
# Ledger where audit voucher has contradictory lines
# ----------------------------------------------------------------------
img6 = Image.new("RGB", (900, 420), color=(255, 255, 255))
d6 = ImageDraw.Draw(img6)
d6.text((250, 25), "VENDOR BILLING CONFLICT AUDIT RECORD", fill=(0, 0, 0), font=font_title)

cols6 = [50, 250, 450, 650, 850]
h6_labels = ["Vendor ID", "Original Invoice (INR)", "Debit Memo Adjustment (INR)", "Reconciled Status"]
for i in range(4):
    d6.rectangle([cols6[i], 80, cols6[i+1], 120], outline=(0, 0, 0), width=1)
    d6.text((cols6[i] + 10, 92), h6_labels[i], fill=(0, 0, 0), font=font_head)

rows6 = [
    ["V-101 Sunflag Steel", "58000", "-6000", "DISPUTED"],
    ["V-102 Balasore Alloys", "94000", "-12000", "APPROVED"],
    ["V-103 Paradeep Phosphates", "125000", "0", "VERIFIED"],
]
for r_i, row_data in enumerate(rows6):
    y_top = 120 + r_i * 45
    for c_i, val in enumerate(row_data):
        d6.rectangle([cols6[c_i], y_top, cols6[c_i+1], y_top + 45], outline=(0, 0, 0), width=1)
        d6.text((cols6[c_i] + 10, y_top + 14), val, fill=(0, 0, 0), font=font_body)

img6_path = TABLES_DIR / "ASSOC_06_CROSS_DOC_DISAGREEMENT.png"
img6.save(img6_path)

manifest_docs["ASSOC_06_CROSS_DOC_DISAGREEMENT"] = {
    "cohort": "G_evidence_association",
    "category": "cross_doc_disagreement",
    "image_path": str(img6_path.relative_to(ROOT)).replace("\\", "/"),
    "critical_fields": [
        {
            "name": "sunflag_invoice_amount",
            "expected": "58000",
            "row": 0,
            "col": 1,
            "type": "amount",
            "target_pattern": "Sunflag Steel",
            "col_pattern": "Original Invoice"
        },
        {
            "name": "balasore_debit_adjustment",
            "expected": "-12000",
            "row": 1,
            "col": 2,
            "type": "amount",
            "target_pattern": "Balasore Alloys",
            "col_pattern": "Debit Memo"
        }
    ]
}

# Save manifest
manifest_file = ROOT / "research" / "loop22" / "dataset_manifest.json"
manifest_content = {
    "loop": 22,
    "suite": "Evidence Association & Risk-Calibrated Abstention",
    "documents": manifest_docs
}
with open(manifest_file, "w", encoding="utf-8") as f:
    json.dump(manifest_content, f, indent=2)

print(f"Generated {len(manifest_docs)} fixtures in {TABLES_DIR}")
print(f"Manifest written to {manifest_file}")
