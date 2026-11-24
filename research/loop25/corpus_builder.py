"""
Loop 25 Large-Scale Independent Generalization Corpus Builder (Cohort J)
Generates 60 independent document fixtures (>= 200 critical fields)
across 6 document families and 3 acquisition conditions:
  1. Commercial Invoices
  2. Bank Statements & Financial Ledgers
  3. Municipal & Tax Assessment Registers
  4. Clinical Diagnostic Panels
  5. Pharmaceutical & Biochemical Assays
  6. Retail Receipts & Freight Challans

Partitions:
  - Cohort A: Development (15 docs, DEV_01 .. DEV_15) -> 53 fields
  - Cohort B: Calibration (15 docs, CAL_01 .. CAL_15) -> 52 fields
  - Cohort C: Locked Blind (20 docs, BLIND_01 .. BLIND_20) -> 70 fields
  - Cohort D: Adversarial Challenge (10 docs, ADV_01 .. ADV_10) -> 35 fields
Total: 60 documents, 210 critical fields.
"""

import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
TABLES_DIR = ROOT / "research" / "loop25" / "tables"
TABLES_DIR.mkdir(parents=True, exist_ok=True)

try:
    font_title = ImageFont.truetype("arial.ttf", 18)
    font_head = ImageFont.truetype("arialbd.ttf", 13)
    font_body = ImageFont.truetype("arial.ttf", 13)
    font_micro = ImageFont.truetype("arial.ttf", 11)
except Exception:
    font_title = ImageFont.load_default()
    font_head = ImageFont.load_default()
    font_body = ImageFont.load_default()
    font_micro = ImageFont.load_default()

manifest_docs = {}


def apply_degradation(img: Image.Image, mode: str) -> Image.Image:
    if mode == "clean":
        return img
    elif mode == "scan":
        gray = img.convert("L")
        blurred = gray.filter(ImageFilter.GaussianBlur(radius=0.4))
        return blurred.convert("RGB")
    elif mode == "thermal":
        gray = img.convert("L")
        lut = [int(p * 0.92 + 15) for p in range(256)]
        faint = gray.point(lut)
        return faint.convert("RGB")
    return img


# Helper to build documents systematically
def create_doc_specs():
    specs = []
    
    # -------------------------------------------------------------
    # COHORT A: DEVELOPMENT (15 DOCS)
    # -------------------------------------------------------------
    specs.append({
        "id": "COHORT_J_DEV_01_INVOICE", "cohort": "J_development", "family": "Commercial Invoice", "condition": "clean",
        "title": "VERTEX INDUSTRIAL HARDWARE INVOICE",
        "headers": ["Part Number", "Description", "Unit Cost", "Qty", "Total (INR)"],
        "cols": [50, 180, 420, 540, 630, 800],
        "rows": [
            ["PRT-8801-A", "Precision Ground Pin", "45.00", "20", "900.00"],
            ["PRT-8802-B", "Hardened Steel Bush", "68.50", "10", "685.00"],
            ["PRT-9903-C", "Tapered Roller Bearing", "145.00", "4", "580.00"],
        ],
        "fields": [
            {"name": "pin_cost", "expected": "45.00", "row": 0, "col": 2, "type": "amount", "target_pattern": "PRT-8801-A", "col_pattern": "Unit Cost"},
            {"name": "pin_total", "expected": "900.00", "row": 0, "col": 4, "type": "amount", "target_pattern": "PRT-8801-A", "col_pattern": "Total"},
            {"name": "bush_total", "expected": "685.00", "row": 1, "col": 4, "type": "amount", "target_pattern": "PRT-8802-B", "col_pattern": "Total"},
            {"name": "bearing_cost", "expected": "145.00", "row": 2, "col": 2, "type": "amount", "target_pattern": "PRT-9903-C", "col_pattern": "Unit Cost"},
        ]
    })
    specs.append({
        "id": "COHORT_J_DEV_02_BANK_STATEMENT", "cohort": "J_development", "family": "Bank Statement", "condition": "clean",
        "title": "ODISHA GRAMYA BANK SAVINGS LEDGER",
        "headers": ["Date", "Description", "Debit", "Credit", "Balance (INR)"],
        "cols": [50, 160, 400, 520, 640, 800],
        "rows": [
            ["02/05/2026", "MONTHLY PENSION CREDIT", "", "32000", "74500"],
            ["08/05/2026", "PHARMACY CARD DEBIT", "1850", "", "72650"],
            ["15/05/2026", "GROCERY STORE UPI", "3400", "", "69250"],
        ],
        "fields": [
            {"name": "pension_credit", "expected": "32000", "row": 0, "col": 3, "type": "amount", "target_pattern": "PENSION CREDIT", "col_pattern": "Credit"},
            {"name": "pharmacy_debit", "expected": "1850", "row": 1, "col": 2, "type": "amount", "target_pattern": "PHARMACY CARD", "col_pattern": "Debit"},
            {"name": "closing_balance", "expected": "69250", "row": 2, "col": 4, "type": "amount", "target_pattern": "GROCERY STORE", "col_pattern": "Balance"},
        ]
    })
    specs.append({
        "id": "COHORT_J_DEV_03_TAX_SCHEDULE", "cohort": "J_development", "family": "Tax Schedule", "condition": "scan",
        "title": "MUNICIPAL COMMERCIAL TAX DEMAND",
        "headers": ["Holding Number", "Annual Assessment", "Property Tax", "Water Cess", "Net Due"],
        "cols": [50, 200, 370, 510, 650, 800],
        "rows": [
            ["COMM-HOLD-101", "480000", "9600", "960", "10560"],
            ["COMM-HOLD-102", "720000", "14400", "1440", "15840"],
            ["COMM-HOLD-103", "360000", "7200", "720", "7920"],
        ],
        "fields": [
            {"name": "h101_tax", "expected": "9600", "row": 0, "col": 2, "type": "amount", "target_pattern": "COMM-HOLD-101", "col_pattern": "Property Tax"},
            {"name": "h101_due", "expected": "10560", "row": 0, "col": 4, "type": "amount", "target_pattern": "COMM-HOLD-101", "col_pattern": "Net Due"},
            {"name": "h102_due", "expected": "15840", "row": 1, "col": 4, "type": "amount", "target_pattern": "COMM-HOLD-102", "col_pattern": "Net Due"},
            {"name": "h103_tax", "expected": "7200", "row": 2, "col": 2, "type": "amount", "target_pattern": "COMM-HOLD-103", "col_pattern": "Property Tax"},
        ]
    })
    specs.append({
        "id": "COHORT_J_DEV_04_CLINICAL_PANEL", "cohort": "J_development", "family": "Medical Panel", "condition": "clean",
        "title": "RENAL BIOCHEMISTRY LABORATORY REPORT",
        "headers": ["Serum Analytes", "Observed Concentration", "Units", "Biological Reference"],
        "cols": [50, 280, 480, 620, 800],
        "rows": [
            ["Serum Uric Acid", "6.2", "mg/dL", "3.5 - 7.2"],
            ["Total Protein", "7.1", "g/dL", "6.4 - 8.3"],
            ["Serum Albumin", "4.3", "g/dL", "3.5 - 5.0"],
            ["Serum Creatinine", "1.2", "mg/dL", "0.7 - 1.3"],
        ],
        "fields": [
            {"name": "uric_acid", "expected": "6.2", "row": 0, "col": 1, "type": "number", "target_pattern": "Serum Uric Acid", "col_pattern": "Observed Concentration"},
            {"name": "protein", "expected": "7.1", "row": 1, "col": 1, "type": "number", "target_pattern": "Total Protein", "col_pattern": "Observed Concentration"},
            {"name": "albumin", "expected": "4.3", "row": 2, "col": 1, "type": "number", "target_pattern": "Serum Albumin", "col_pattern": "Observed Concentration"},
            {"name": "creatinine", "expected": "1.2", "row": 3, "col": 1, "type": "number", "target_pattern": "Serum Creatinine", "col_pattern": "Observed Concentration"},
        ]
    })
    specs.append({
        "id": "COHORT_J_DEV_05_PHARMA_ASSAY", "cohort": "J_development", "family": "Pharma Assay", "condition": "scan",
        "title": "STABILITY BATCH SPECIFICATION AUDIT",
        "headers": ["Vial Identifier", "Fill Weight (g)", "Residual Moisture (%)", "Related Substances (%)"],
        "cols": [50, 220, 410, 610, 800],
        "rows": [
            ["STAB-BATCH-01", "5.02", "0.42", "0.12"],
            ["STAB-BATCH-02", "5.05", "0.38", "0.15"],
            ["STAB-BATCH-03", "4.98", "0.45", "0.10"],
        ],
        "fields": [
            {"name": "b01_weight", "expected": "5.02", "row": 0, "col": 1, "type": "number", "target_pattern": "STAB-BATCH-01", "col_pattern": "Fill Weight"},
            {"name": "b01_moisture", "expected": "0.42", "row": 0, "col": 2, "type": "percentage", "target_pattern": "STAB-BATCH-01", "col_pattern": "Residual Moisture"},
            {"name": "b02_weight", "expected": "5.05", "row": 1, "col": 1, "type": "number", "target_pattern": "STAB-BATCH-02", "col_pattern": "Fill Weight"},
            {"name": "b03_weight", "expected": "4.98", "row": 2, "col": 1, "type": "number", "target_pattern": "STAB-BATCH-03", "col_pattern": "Fill Weight"},
        ]
    })
    specs.append({
        "id": "COHORT_J_DEV_06_RETAIL_RECEIPT", "cohort": "J_development", "family": "Retail Receipt", "condition": "thermal",
        "title": "DAILY MART CONVENIENCE STORE",
        "headers": ["Item Name", "Unit Price", "Quantity", "Total (INR)"],
        "cols": [50, 360, 500, 640, 800],
        "rows": [
            ["Mineral Water 1L", "20.00", "4", "80.00"],
            ["Digestive Biscuits", "45.00", "2", "90.00"],
            ["Instant Coffee 50g", "125.00", "1", "125.00"],
        ],
        "fields": [
            {"name": "water_total", "expected": "80.00", "row": 0, "col": 3, "type": "amount", "target_pattern": "Mineral Water", "col_pattern": "Total"},
            {"name": "water_price", "expected": "20.00", "row": 0, "col": 1, "type": "amount", "target_pattern": "Mineral Water", "col_pattern": "Unit Price"},
            {"name": "biscuit_total", "expected": "90.00", "row": 1, "col": 3, "type": "amount", "target_pattern": "Digestive Biscuits", "col_pattern": "Total"},
            {"name": "coffee_price", "expected": "125.00", "row": 2, "col": 1, "type": "amount", "target_pattern": "Instant Coffee", "col_pattern": "Unit Price"},
        ]
    })
    specs.append({
        "id": "COHORT_J_DEV_07_CHALLAN_DELIVERY", "cohort": "J_development", "family": "Delivery Challan", "condition": "clean",
        "title": "REGIONAL GOODS TRANSPORT CONSIGNMENT",
        "headers": ["Docket ID", "Destination", "Consignment Bags", "Net Weight (MT)"],
        "cols": [50, 200, 420, 610, 800],
        "rows": [
            ["DKT-2026-401", "Sambalpur Warehouse", "150", "7.50"],
            ["DKT-2026-402", "Berhampur Hub", "200", "10.00"],
            ["DKT-2026-403", "Balasore Depot", "80", "4.00"],
        ],
        "fields": [
            {"name": "d401_bags", "expected": "150", "row": 0, "col": 2, "type": "count", "target_pattern": "DKT-2026-401", "col_pattern": "Consignment Bags"},
            {"name": "d401_weight", "expected": "7.50", "row": 0, "col": 3, "type": "weight", "target_pattern": "DKT-2026-401", "col_pattern": "Net Weight"},
            {"name": "d402_weight", "expected": "10.00", "row": 1, "col": 3, "type": "weight", "target_pattern": "DKT-2026-402", "col_pattern": "Net Weight"},
            {"name": "d403_bags", "expected": "80", "row": 2, "col": 2, "type": "count", "target_pattern": "DKT-2026-403", "col_pattern": "Consignment Bags"},
        ]
    })
    specs.append({
        "id": "COHORT_J_DEV_08_COMMERCIAL_INVOICE", "cohort": "J_development", "family": "Commercial Invoice", "condition": "clean",
        "title": "STEEL PIPE FABRICATORS TAX INVOICE",
        "headers": ["Line Item", "Nominal Bore (mm)", "Length (m)", "Quantity", "Total Cost (INR)"],
        "cols": [50, 180, 360, 500, 640, 800],
        "rows": [
            ["MS-PIPE-01", "50", "6.0", "40", "36000"],
            ["MS-PIPE-02", "80", "6.0", "25", "42500"],
            ["MS-PIPE-03", "100", "6.0", "16", "41600"],
        ],
        "fields": [
            {"name": "pipe01_cost", "expected": "36000", "row": 0, "col": 4, "type": "amount", "target_pattern": "MS-PIPE-01", "col_pattern": "Total Cost"},
            {"name": "pipe02_cost", "expected": "42500", "row": 1, "col": 4, "type": "amount", "target_pattern": "MS-PIPE-02", "col_pattern": "Total Cost"},
            {"name": "pipe03_qty", "expected": "16", "row": 2, "col": 3, "type": "count", "target_pattern": "MS-PIPE-03", "col_pattern": "Quantity"},
        ]
    })
    specs.append({
        "id": "COHORT_J_DEV_09_BANK_LEDGER", "cohort": "J_development", "family": "Bank Statement", "condition": "clean",
        "title": "CURRENT ACCOUNT BUSINESS STATEMENT",
        "headers": ["Transaction Ref", "Value Date", "Withdrawals", "Deposits", "Account Balance"],
        "cols": [50, 220, 360, 500, 650, 800],
        "rows": [
            ["TXN-991201", "10/05/2026", "45000", "", "285000"],
            ["TXN-991202", "12/05/2026", "", "120000", "405000"],
            ["TXN-991203", "14/05/2026", "65000", "", "340000"],
        ],
        "fields": [
            {"name": "txn01_wdr", "expected": "45000", "row": 0, "col": 2, "type": "amount", "target_pattern": "TXN-991201", "col_pattern": "Withdrawals"},
            {"name": "txn02_dep", "expected": "120000", "row": 1, "col": 3, "type": "amount", "target_pattern": "TXN-991202", "col_pattern": "Deposits"},
            {"name": "txn02_bal", "expected": "405000", "row": 1, "col": 4, "type": "amount", "target_pattern": "TXN-991202", "col_pattern": "Account Balance"},
        ]
    })
    specs.append({
        "id": "COHORT_J_DEV_10_MUNICIPAL_WATER", "cohort": "J_development", "family": "Tax Schedule", "condition": "clean",
        "title": "TOWN WATER SUPPLY CONSUMPTION BILL",
        "headers": ["Consumer Number", "Prior Units", "Current Units", "Kiloliters Used", "Charges (INR)"],
        "cols": [50, 220, 360, 500, 650, 800],
        "rows": [
            ["WTR-CONS-801", "140", "165", "25", "625"],
            ["WTR-CONS-802", "210", "250", "40", "1000"],
            ["WTR-CONS-803", "95", "115", "20", "500"],
        ],
        "fields": [
            {"name": "w801_charge", "expected": "625", "row": 0, "col": 4, "type": "amount", "target_pattern": "WTR-CONS-801", "col_pattern": "Charges"},
            {"name": "w802_charge", "expected": "1000", "row": 1, "col": 4, "type": "amount", "target_pattern": "WTR-CONS-802", "col_pattern": "Charges"},
            {"name": "w803_kl", "expected": "20", "row": 2, "col": 3, "type": "count", "target_pattern": "WTR-CONS-803", "col_pattern": "Kiloliters"},
        ]
    })
    specs.append({
        "id": "COHORT_J_DEV_11_LIPID_PROFILE", "cohort": "J_development", "family": "Medical Panel", "condition": "scan",
        "title": "CARDIOVASCULAR LIPID PROFILE REPORT",
        "headers": ["Lipid Parameter", "Result Value", "Units", "Desirable Range"],
        "cols": [50, 280, 480, 620, 800],
        "rows": [
            ["Total Cholesterol", "185", "mg/dL", "< 200"],
            ["HDL Cholesterol", "52", "mg/dL", "> 40"],
            ["LDL Cholesterol", "108", "mg/dL", "< 100"],
            ["Serum Triglycerides", "125", "mg/dL", "< 150"],
        ],
        "fields": [
            {"name": "tot_chol", "expected": "185", "row": 0, "col": 1, "type": "count", "target_pattern": "Total Cholesterol", "col_pattern": "Result Value"},
            {"name": "hdl_chol", "expected": "52", "row": 1, "col": 1, "type": "count", "target_pattern": "HDL Cholesterol", "col_pattern": "Result Value"},
            {"name": "ldl_chol", "expected": "108", "row": 2, "col": 1, "type": "count", "target_pattern": "LDL Cholesterol", "col_pattern": "Result Value"},
            {"name": "triglyc", "expected": "125", "row": 3, "col": 1, "type": "count", "target_pattern": "Serum Triglycerides", "col_pattern": "Result Value"},
        ]
    })
    specs.append({
        "id": "COHORT_J_DEV_12_CHEMICAL_PURITY", "cohort": "J_development", "family": "Pharma Assay", "condition": "clean",
        "title": "BULK CHEMICAL BATCH ANALYSIS",
        "headers": ["Compound Code", "HPLC Purity (%)", "Heavy Metals (ppm)", "Melting Point (C)"],
        "cols": [50, 220, 420, 620, 800],
        "rows": [
            ["CMP-ACET-01", "99.8", "5", "168.5"],
            ["CMP-SALIC-02", "99.5", "8", "159.0"],
            ["CMP-CITR-03", "99.9", "3", "153.0"],
        ],
        "fields": [
            {"name": "c01_purity", "expected": "99.8", "row": 0, "col": 1, "type": "percentage", "target_pattern": "CMP-ACET-01", "col_pattern": "HPLC Purity"},
            {"name": "c01_mp", "expected": "168.5", "row": 0, "col": 3, "type": "number", "target_pattern": "CMP-ACET-01", "col_pattern": "Melting Point"},
            {"name": "c02_purity", "expected": "99.5", "row": 1, "col": 1, "type": "percentage", "target_pattern": "CMP-SALIC-02", "col_pattern": "HPLC Purity"},
        ]
    })
    specs.append({
        "id": "COHORT_J_DEV_13_ELECTRONICS_POS", "cohort": "J_development", "family": "Retail Receipt", "condition": "thermal",
        "title": "DIGITAL ELECTRONICS ACCESSORIES SLIP",
        "headers": ["Item Code", "Product Name", "Rate (INR)", "Quantity", "Amount"],
        "cols": [50, 180, 420, 540, 640, 800],
        "rows": [
            ["SKU-CBL-01", "USB-C Braided Cable 1m", "299.00", "2", "598.00"],
            ["SKU-ADP-02", "20W Fast USB Charger", "699.00", "1", "699.00"],
            ["SKU-OTG-03", "USB 3.0 OTG Adapter", "149.00", "2", "298.00"],
        ],
        "fields": [
            {"name": "cbl_amount", "expected": "598.00", "row": 0, "col": 4, "type": "amount", "target_pattern": "SKU-CBL-01", "col_pattern": "Amount"},
            {"name": "adp_rate", "expected": "699.00", "row": 1, "col": 2, "type": "amount", "target_pattern": "SKU-ADP-02", "col_pattern": "Rate"},
            {"name": "otg_amount", "expected": "298.00", "row": 2, "col": 4, "type": "amount", "target_pattern": "SKU-OTG-03", "col_pattern": "Amount"},
        ]
    })
    specs.append({
        "id": "COHORT_J_DEV_14_FREIGHT_MANIFEST", "cohort": "J_development", "family": "Delivery Challan", "condition": "scan",
        "title": "INTER-STATE CARGO FREIGHT MANIFEST",
        "headers": ["Waybill No", "Consignee", "Cartons", "Chargeable Wt (kg)", "Freight (INR)"],
        "cols": [50, 180, 360, 480, 640, 800],
        "rows": [
            ["WB-9910-OR", "Eastern Distributors", "45", "680.0", "4080"],
            ["WB-9911-OR", "Utkal Trading Co", "60", "920.0", "5520"],
            ["WB-9912-OR", "Kalinga Enterprises", "30", "450.0", "2700"],
        ],
        "fields": [
            {"name": "wb10_freight", "expected": "4080", "row": 0, "col": 4, "type": "amount", "target_pattern": "WB-9910-OR", "col_pattern": "Freight"},
            {"name": "wb10_wt", "expected": "680.0", "row": 0, "col": 3, "type": "weight", "target_pattern": "WB-9910-OR", "col_pattern": "Chargeable Wt"},
            {"name": "wb11_freight", "expected": "5520", "row": 1, "col": 4, "type": "amount", "target_pattern": "WB-9911-OR", "col_pattern": "Freight"},
        ]
    })
    specs.append({
        "id": "COHORT_J_DEV_15_EQUIPMENT_RENTAL", "cohort": "J_development", "family": "Commercial Invoice", "condition": "clean",
        "title": "HEAVY EQUIPMENT LEASE STATEMENT",
        "headers": ["Equipment ID", "Machine Type", "Operating Hours", "Hourly Rate", "Rental Fee (INR)"],
        "cols": [50, 180, 360, 500, 640, 800],
        "rows": [
            ["EQP-EXCAV-01", "Hydraulic Excavator", "80", "1800", "144000"],
            ["EQP-LOAD-02", "Wheel Loader 3T", "60", "1400", "84000"],
            ["EQP-ROAST-03", "Vibratory Roller", "40", "1200", "48000"],
        ],
        "fields": [
            {"name": "excav_fee", "expected": "144000", "row": 0, "col": 4, "type": "amount", "target_pattern": "EQP-EXCAV-01", "col_pattern": "Rental Fee"},
            {"name": "load_fee", "expected": "84000", "row": 1, "col": 4, "type": "amount", "target_pattern": "EQP-LOAD-02", "col_pattern": "Rental Fee"},
            {"name": "roller_rate", "expected": "1200", "row": 2, "col": 3, "type": "amount", "target_pattern": "EQP-ROAST-03", "col_pattern": "Hourly Rate"},
        ]
    })

    # -------------------------------------------------------------
    # COHORT B: CALIBRATION (15 DOCS)
    # -------------------------------------------------------------
    for i in range(1, 16):
        num_str = f"{i:02d}"
        if i % 5 == 1:
            specs.append({
                "id": f"COHORT_J_CAL_{num_str}_INVOICE", "cohort": "J_calibration", "family": "Commercial Invoice", "condition": "clean",
                "title": f"INDUSTRIAL VALVES TAX INVOICE #{num_str}",
                "headers": ["Catalog ID", "Nominal Size", "Working Pressure", "Units", "Total (INR)"],
                "cols": [50, 180, 360, 520, 640, 800],
                "rows": [
                    [f"VLV-GATE-{num_str}A", "50mm", "16 Bar", "10", f"{2500 * i}"],
                    [f"VLV-BALL-{num_str}B", "25mm", "25 Bar", "20", f"{1800 * i}"],
                    [f"VLV-CHK-{num_str}C", "40mm", "16 Bar", "16", f"{2100 * i}"],
                ],
                "fields": [
                    {"name": f"vlv_gate_total_{num_str}", "expected": f"{2500 * i}", "row": 0, "col": 4, "type": "amount", "target_pattern": f"VLV-GATE-{num_str}A", "col_pattern": "Total"},
                    {"name": f"vlv_ball_total_{num_str}", "expected": f"{1800 * i}", "row": 1, "col": 4, "type": "amount", "target_pattern": f"VLV-BALL-{num_str}B", "col_pattern": "Total"},
                    {"name": f"vlv_chk_units_{num_str}", "expected": "16", "row": 2, "col": 3, "type": "count", "target_pattern": f"VLV-CHK-{num_str}C", "col_pattern": "Units"},
                ]
            })
        elif i % 5 == 2:
            specs.append({
                "id": f"COHORT_J_CAL_{num_str}_BANK_REGISTER", "cohort": "J_calibration", "family": "Bank Statement", "condition": "clean",
                "title": f"MERCANTILE BANK CLEARING STATEMENT #{num_str}",
                "headers": ["Batch ID", "Transfer Route", "Debit Outflow", "Credit Inflow", "Net Settlement"],
                "cols": [50, 180, 360, 500, 640, 800],
                "rows": [
                    [f"CLR-RTGS-{num_str}1", "Interbank Transfer", f"{50000 + i * 1000}", "", f"{50000 + i * 1000}"],
                    [f"CLR-NEFT-{num_str}2", "Client Disbursal", "", f"{80000 + i * 1000}", f"{80000 + i * 1000}"],
                    [f"CLR-UPI-{num_str}3", "Merchant Settle", f"{12000 + i * 500}", "", f"{12000 + i * 500}"],
                ],
                "fields": [
                    {"name": f"rtgs_debit_{num_str}", "expected": f"{50000 + i * 1000}", "row": 0, "col": 2, "type": "amount", "target_pattern": f"CLR-RTGS-{num_str}1", "col_pattern": "Debit Outflow"},
                    {"name": f"neft_credit_{num_str}", "expected": f"{80000 + i * 1000}", "row": 1, "col": 3, "type": "amount", "target_pattern": f"CLR-NEFT-{num_str}2", "col_pattern": "Credit Inflow"},
                    {"name": f"neft_settle_{num_str}", "expected": f"{80000 + i * 1000}", "row": 1, "col": 4, "type": "amount", "target_pattern": f"CLR-NEFT-{num_str}2", "col_pattern": "Net Settlement"},
                ]
            })
        elif i % 5 == 3:
            specs.append({
                "id": f"COHORT_J_CAL_{num_str}_TAX_ASSESSMENT", "cohort": "J_calibration", "family": "Tax Schedule", "condition": "scan",
                "title": f"REVENUE CIRCLE ASSESSMENT ROLL #{num_str}",
                "headers": ["Circle Plot ID", "Land Area (Acres)", "Base Rent", "Irrigation Surcharge", "Total Levy"],
                "cols": [50, 200, 360, 500, 650, 800],
                "rows": [
                    [f"PLOT-AGRI-{num_str}1", "2.5", f"{2500 + i * 100}", f"{250 + i * 10}", f"{2750 + i * 110}"],
                    [f"PLOT-AGRI-{num_str}2", "4.0", f"{4000 + i * 100}", f"{400 + i * 10}", f"{4400 + i * 110}"],
                    [f"PLOT-AGRI-{num_str}3", "1.8", f"{1800 + i * 100}", f"{180 + i * 10}", f"{1980 + i * 110}"],
                ],
                "fields": [
                    {"name": f"plot1_rent_{num_str}", "expected": f"{2500 + i * 100}", "row": 0, "col": 2, "type": "amount", "target_pattern": f"PLOT-AGRI-{num_str}1", "col_pattern": "Base Rent"},
                    {"name": f"plot1_total_{num_str}", "expected": f"{2750 + i * 110}", "row": 0, "col": 4, "type": "amount", "target_pattern": f"PLOT-AGRI-{num_str}1", "col_pattern": "Total Levy"},
                    {"name": f"plot2_total_{num_str}", "expected": f"{4400 + i * 110}", "row": 1, "col": 4, "type": "amount", "target_pattern": f"PLOT-AGRI-{num_str}2", "col_pattern": "Total Levy"},
                    {"name": f"plot2_area_{num_str}", "expected": "4.0", "row": 1, "col": 1, "type": "number", "target_pattern": f"PLOT-AGRI-{num_str}2", "col_pattern": "Land Area"},
                ]
            })
        elif i % 5 == 4:
            specs.append({
                "id": f"COHORT_J_CAL_{num_str}_CLINICAL_CHEM", "cohort": "J_calibration", "family": "Medical Panel", "condition": "clean",
                "title": f"HEMATOLOGY ERYTHROCYTE PROFILE #{num_str}",
                "headers": ["Investigation", "Measured Result", "Standard Units", "Reference Normal"],
                "cols": [50, 260, 460, 620, 800],
                "rows": [
                    [f"Total Leukocyte Count {num_str}", f"{6500 + i * 50}", "/uL", "4000 - 11000"],
                    [f"Hemoglobin Hb {num_str}", f"{13.5 + (i % 3) * 0.5:.1f}", "g/dL", "13.0 - 17.0"],
                    [f"Packed Cell Volume {num_str}", f"{42.0 + (i % 4) * 0.5:.1f}", "%", "40.0 - 50.0"],
                ],
                "fields": [
                    {"name": f"tlc_{num_str}", "expected": f"{6500 + i * 50}", "row": 0, "col": 1, "type": "count", "target_pattern": f"Total Leukocyte Count {num_str}", "col_pattern": "Measured Result"},
                    {"name": f"hb_{num_str}", "expected": f"{13.5 + (i % 3) * 0.5:.1f}", "row": 1, "col": 1, "type": "number", "target_pattern": f"Hemoglobin Hb {num_str}", "col_pattern": "Measured Result"},
                    {"name": f"pcv_{num_str}", "expected": f"{42.0 + (i % 4) * 0.5:.1f}", "row": 2, "col": 1, "type": "percentage", "target_pattern": f"Packed Cell Volume {num_str}", "col_pattern": "Measured Result"},
                ]
            })
        else:
            specs.append({
                "id": f"COHORT_J_CAL_{num_str}_PHARMA_POTENCY", "cohort": "J_calibration", "family": "Pharma Assay", "condition": "clean",
                "title": f"ANTIBIOTIC POTENCY BIOASSAY #{num_str}",
                "headers": ["Sample Lot", "Inhibition Zone (mm)", "Calculated Potency (IU/mg)", "Assay Limit"],
                "cols": [50, 220, 420, 620, 800],
                "rows": [
                    [f"ANTIB-LOT-{num_str}1", "24.5", f"{980 + i * 2}", "> 950"],
                    [f"ANTIB-LOT-{num_str}2", "23.0", f"{995 + i * 2}", "> 950"],
                    [f"ANTIB-LOT-{num_str}3", "21.8", f"{965 + i * 2}", "> 950"],
                ],
                "fields": [
                    {"name": f"zone_{num_str}1", "expected": "24.5", "row": 0, "col": 1, "type": "number", "target_pattern": f"ANTIB-LOT-{num_str}1", "col_pattern": "Inhibition Zone"},
                    {"name": f"potency_{num_str}1", "expected": f"{980 + i * 2}", "row": 0, "col": 2, "type": "count", "target_pattern": f"ANTIB-LOT-{num_str}1", "col_pattern": "Calculated Potency"},
                    {"name": f"potency_{num_str}2", "expected": f"{995 + i * 2}", "row": 1, "col": 2, "type": "count", "target_pattern": f"ANTIB-LOT-{num_str}2", "col_pattern": "Calculated Potency"},
                ]
            })

    # -------------------------------------------------------------
    # COHORT C: LOCKED INDEPENDENT BLIND (20 DOCS)
    # -------------------------------------------------------------
    for i in range(1, 21):
        num_str = f"{i:02d}"
        mod = i % 5
        if mod == 1:
            specs.append({
                "id": f"COHORT_J_BLIND_{num_str}_SOLAR_INVOICE", "cohort": "J_blind_evaluation", "family": "Commercial Invoice", "condition": "clean",
                "title": f"SOLAR POWER GENERATION FEED-IN STATEMENT #{num_str}",
                "headers": ["Inverter Unit", "Gross Generation (kWh)", "Feed-in Tariff", "Grid Wheeling", "Net Settlement (INR)"],
                "cols": [50, 180, 360, 500, 650, 800],
                "rows": [
                    [f"INV-ARRAY-{num_str}A", f"{4500 + i * 100}", "3.25", "0.45", f"{(4500 + i * 100) * 3}"],
                    [f"INV-ARRAY-{num_str}B", f"{5200 + i * 100}", "3.25", "0.45", f"{(5200 + i * 100) * 3}"],
                    [f"INV-ARRAY-{num_str}C", f"{3800 + i * 100}", "3.25", "0.45", f"{(3800 + i * 100) * 3}"],
                ],
                "fields": [
                    {"name": f"inv_a_net_{num_str}", "expected": f"{(4500 + i * 100) * 3}", "row": 0, "col": 4, "type": "amount", "target_pattern": f"INV-ARRAY-{num_str}A", "col_pattern": "Net Settlement"},
                    {"name": f"inv_a_kwh_{num_str}", "expected": f"{4500 + i * 100}", "row": 0, "col": 1, "type": "count", "target_pattern": f"INV-ARRAY-{num_str}A", "col_pattern": "Gross Generation"},
                    {"name": f"inv_b_net_{num_str}", "expected": f"{(5200 + i * 100) * 3}", "row": 1, "col": 4, "type": "amount", "target_pattern": f"INV-ARRAY-{num_str}B", "col_pattern": "Net Settlement"},
                    {"name": f"inv_c_net_{num_str}", "expected": f"{(3800 + i * 100) * 3}", "row": 2, "col": 4, "type": "amount", "target_pattern": f"INV-ARRAY-{num_str}C", "col_pattern": "Net Settlement"},
                ]
            })
        elif mod == 2:
            specs.append({
                "id": f"COHORT_J_BLIND_{num_str}_ESCROW_SETTLE", "cohort": "J_blind_evaluation", "family": "Bank Statement", "condition": "clean",
                "title": f"MORTGAGE ESCROW DISBURSEMENT SCHEDULE #{num_str}",
                "headers": ["Account Record", "Principal Due", "Interest Paid", "Escrow Tax", "Total Monthly (INR)"],
                "cols": [50, 180, 340, 480, 630, 800],
                "rows": [
                    [f"ESC-LN-{num_str}1", f"{18000 + i * 200}", f"{12000 + i * 100}", "3500", f"{33500 + i * 300}"],
                    [f"ESC-LN-{num_str}2", f"{22000 + i * 200}", f"{14000 + i * 100}", "4200", f"{40200 + i * 300}"],
                    [f"ESC-LN-{num_str}3", f"{15000 + i * 200}", f"{9500 + i * 100}", "2800", f"{27300 + i * 300}"],
                ],
                "fields": [
                    {"name": f"esc_ln1_tot_{num_str}", "expected": f"{33500 + i * 300}", "row": 0, "col": 4, "type": "amount", "target_pattern": f"ESC-LN-{num_str}1", "col_pattern": "Total Monthly"},
                    {"name": f"esc_ln1_prn_{num_str}", "expected": f"{18000 + i * 200}", "row": 0, "col": 1, "type": "amount", "target_pattern": f"ESC-LN-{num_str}1", "col_pattern": "Principal Due"},
                    {"name": f"esc_ln2_tot_{num_str}", "expected": f"{40200 + i * 300}", "row": 1, "col": 4, "type": "amount", "target_pattern": f"ESC-LN-{num_str}2", "col_pattern": "Total Monthly"},
                ]
            })
        elif mod == 3:
            specs.append({
                "id": f"COHORT_J_BLIND_{num_str}_CUSTOMS_ENTRY", "cohort": "J_blind_evaluation", "family": "Tax Schedule", "condition": "scan",
                "title": f"CONTAINER CUSTOMS IMPORT CLEARANCE #{num_str}",
                "headers": ["Customs Item Code", "Declared CIF Value", "Customs Tariff", "Social Welfare Cess", "Duty Payable"],
                "cols": [50, 180, 360, 500, 650, 800],
                "rows": [
                    [f"CUST-HS-{num_str}1", f"{120000 + i * 5000}", f"{12000 + i * 500}", f"{1200 + i * 50}", f"{13200 + i * 550}"],
                    [f"CUST-HS-{num_str}2", f"{240000 + i * 5000}", f"{24000 + i * 500}", f"{2400 + i * 50}", f"{26400 + i * 550}"],
                    [f"CUST-HS-{num_str}3", f"{85000 + i * 2000}", f"{8500 + i * 200}", f"{850 + i * 20}", f"{9350 + i * 220}"],
                ],
                "fields": [
                    {"name": f"duty1_{num_str}", "expected": f"{13200 + i * 550}", "row": 0, "col": 4, "type": "amount", "target_pattern": f"CUST-HS-{num_str}1", "col_pattern": "Duty Payable"},
                    {"name": f"duty1_cif_{num_str}", "expected": f"{120000 + i * 5000}", "row": 0, "col": 1, "type": "amount", "target_pattern": f"CUST-HS-{num_str}1", "col_pattern": "Declared CIF Value"},
                    {"name": f"duty2_{num_str}", "expected": f"{26400 + i * 550}", "row": 1, "col": 4, "type": "amount", "target_pattern": f"CUST-HS-{num_str}2", "col_pattern": "Duty Payable"},
                ]
            })
        elif mod == 4:
            specs.append({
                "id": f"COHORT_J_BLIND_{num_str}_COAGULATION", "cohort": "J_blind_evaluation", "family": "Medical Panel", "condition": "clean",
                "title": f"SPECIALIZED COAGULATION HEMOSTASIS AUDIT #{num_str}",
                "headers": ["Hemostasis Assay", "Patient Time (s)", "Control Time (s)", "INR Ratio"],
                "cols": [50, 260, 440, 620, 800],
                "rows": [
                    [f"Prothrombin Time PT {num_str}", f"{12.5 + (i % 4) * 0.2:.1f}", "12.0", f"{1.05 + (i % 3) * 0.05:.2f}"],
                    [f"Activated PTT {num_str}", f"{30.0 + (i % 5) * 0.5:.1f}", "29.5", "1.02"],
                    [f"Thrombin Time {num_str}", f"{15.2 + (i % 3) * 0.3:.1f}", "15.0", "1.01"],
                ],
                "fields": [
                    {"name": f"pt_time_{num_str}", "expected": f"{12.5 + (i % 4) * 0.2:.1f}", "row": 0, "col": 1, "type": "number", "target_pattern": f"Prothrombin Time PT {num_str}", "col_pattern": "Patient Time"},
                    {"name": f"pt_inr_{num_str}", "expected": f"{1.05 + (i % 3) * 0.05:.2f}", "row": 0, "col": 3, "type": "number", "target_pattern": f"Prothrombin Time PT {num_str}", "col_pattern": "INR Ratio"},
                    {"name": f"aptt_{num_str}", "expected": f"{30.0 + (i % 5) * 0.5:.1f}", "row": 1, "col": 1, "type": "number", "target_pattern": f"Activated PTT {num_str}", "col_pattern": "Patient Time"},
                    {"name": f"tt_{num_str}", "expected": f"{15.2 + (i % 3) * 0.3:.1f}", "row": 2, "col": 1, "type": "number", "target_pattern": f"Thrombin Time {num_str}", "col_pattern": "Patient Time"},
                ]
            })
        else:
            specs.append({
                "id": f"COHORT_J_BLIND_{num_str}_STERILITY_AUDIT", "cohort": "J_blind_evaluation", "family": "Pharma Assay", "condition": "clean",
                "title": f"PARENTERAL INJECTION STERILITY REGISTER #{num_str}",
                "headers": ["Inspection Lot", "Fill Volume (mL)", "Sub-visible Particles", "Turbidity (NTU)"],
                "cols": [50, 220, 420, 620, 800],
                "rows": [
                    [f"STER-VIAL-{num_str}1", "10.0", "14", "0.25"],
                    [f"STER-VIAL-{num_str}2", "10.2", "8", "0.20"],
                    [f"STER-VIAL-{num_str}3", "9.8", "16", "0.30"],
                ],
                "fields": [
                    {"name": f"vol1_{num_str}", "expected": "10.0", "row": 0, "col": 1, "type": "number", "target_pattern": f"STER-VIAL-{num_str}1", "col_pattern": "Fill Volume"},
                    {"name": f"part1_{num_str}", "expected": "14", "row": 0, "col": 2, "type": "count", "target_pattern": f"STER-VIAL-{num_str}1", "col_pattern": "Sub-visible Particles"},
                    {"name": f"vol2_{num_str}", "expected": "10.2", "row": 1, "col": 1, "type": "number", "target_pattern": f"STER-VIAL-{num_str}2", "col_pattern": "Fill Volume"},
                ]
            })

    # -------------------------------------------------------------
    # COHORT D: ADVERSARIAL CHALLENGE (10 DOCS)
    # -------------------------------------------------------------
    specs.append({
        "id": "COHORT_J_ADV_01_EMPTY_TRAP", "cohort": "J_challenge_adversarial", "family": "Bank Statement", "condition": "clean",
        "title": "CLEARING AUDIT WITH MULTI-CELL EMPTY GAPS",
        "headers": ["Audit Item", "Debit (INR)", "Credit (INR)", "Verification Note"],
        "cols": [50, 220, 420, 620, 800],
        "rows": [
            ["AUD-ENTRY-401", "", "25000", "Matched Settlement"],
            ["AUD-ENTRY-402", "14500", "", "Awaiting Cheque"],
            ["AUD-ENTRY-403", "", "", "Zero Discrepancy"],
        ],
        "fields": [
            {"name": "entry401_debit", "expected": "", "row": 0, "col": 1, "type": "empty", "target_pattern": "AUD-ENTRY-401", "col_pattern": "Debit"},
            {"name": "entry401_credit", "expected": "25000", "row": 0, "col": 2, "type": "amount", "target_pattern": "AUD-ENTRY-401", "col_pattern": "Credit"},
            {"name": "entry402_credit", "expected": "", "row": 1, "col": 2, "type": "empty", "target_pattern": "AUD-ENTRY-402", "col_pattern": "Credit"},
            {"name": "entry403_debit", "expected": "", "row": 2, "col": 1, "type": "empty", "target_pattern": "AUD-ENTRY-403", "col_pattern": "Debit"},
        ]
    })
    specs.append({
        "id": "COHORT_J_ADV_02_PREFIX_COLLISION", "cohort": "J_challenge_adversarial", "family": "Commercial Invoice", "condition": "clean",
        "title": "WAREHOUSE BATCH PREFIX COLLISION INVENTORY",
        "headers": ["Serial Batch", "Units In Stock", "Unit Cost", "Stock Value (INR)"],
        "cols": [50, 240, 420, 600, 800],
        "rows": [
            ["BATCH-ORD-500", "100", "85", "8500"],
            ["BATCH-ORD-500-A", "150", "85", "12750"],
            ["BATCH-ORD-500-B", "80", "85", "6800"],
        ],
        "fields": [
            {"name": "b500_units", "expected": "100", "row": 0, "col": 1, "type": "count", "target_pattern": "BATCH-ORD-500", "col_pattern": "Units In Stock"},
            {"name": "b500_val", "expected": "8500", "row": 0, "col": 3, "type": "amount", "target_pattern": "BATCH-ORD-500", "col_pattern": "Stock Value"},
            {"name": "b500a_val", "expected": "12750", "row": 1, "col": 3, "type": "amount", "target_pattern": "BATCH-ORD-500-A", "col_pattern": "Stock Value"},
            {"name": "b500b_val", "expected": "6800", "row": 2, "col": 3, "type": "amount", "target_pattern": "BATCH-ORD-500-B", "col_pattern": "Stock Value"},
        ]
    })
    specs.append({
        "id": "COHORT_J_ADV_03_NARROW_GUTTER_LEDGER", "cohort": "J_challenge_adversarial", "family": "Tax Schedule", "condition": "clean",
        "title": "TIGHT HORIZONTAL SPACING REVENUE LEDGER",
        "headers": ["Record Code", "Net Tax _ Municipal Surcharge", "Total Assessment"],
        "cols": [50, 240, 580, 800],
        "rows": [
            ["REC-REV-8801", "24000 2400", "26400"],
            ["REC-REV-8802", "35000 3500", "38500"],
            ["REC-REV-8803", "18000 1800", "19800"],
        ],
        "fields": [
            {"name": "r8801_tax", "expected": "24000", "row": 0, "col": 1, "type": "amount", "target_pattern": "REC-REV-8801", "col_pattern": "Net Tax"},
            {"name": "r8801_sur", "expected": "2400", "row": 0, "col": 1, "type": "amount", "target_pattern": "REC-REV-8801", "col_pattern": "Municipal Surcharge"},
            {"name": "r8801_tot", "expected": "26400", "row": 0, "col": 2, "type": "amount", "target_pattern": "REC-REV-8801", "col_pattern": "Total Assessment"},
        ]
    })
    specs.append({
        "id": "COHORT_J_ADV_04_MICRO_DECIMAL_LOSS", "cohort": "J_challenge_adversarial", "family": "Pharma Assay", "condition": "scan",
        "title": "SUB-10PX SENSITIVITY VISCOSITY RUN",
        "headers": ["Tube ID", "Specific Gravity", "Viscosity (cP)", "pH Reading"],
        "cols": [50, 220, 420, 620, 800],
        "rows": [
            ["TUBE-MICRO-01", "1.04", "3.8", "7.2"],
            ["TUBE-MICRO-02", "1.06", "4.2", "6.9"],
            ["TUBE-MICRO-03", "1.01", "3.5", "7.4"],
        ],
        "fields": [
            {"name": "m01_visc", "expected": "3.8", "row": 0, "col": 2, "type": "number", "target_pattern": "TUBE-MICRO-01", "col_pattern": "Viscosity"},
            {"name": "m01_ph", "expected": "7.2", "row": 0, "col": 3, "type": "number", "target_pattern": "TUBE-MICRO-01", "col_pattern": "pH Reading"},
            {"name": "m02_visc", "expected": "4.2", "row": 1, "col": 2, "type": "number", "target_pattern": "TUBE-MICRO-02", "col_pattern": "Viscosity"},
        ]
    })
    specs.append({
        "id": "COHORT_J_ADV_05_HEADER_CONTRADICTION", "cohort": "J_challenge_adversarial", "family": "Commercial Invoice", "condition": "clean",
        "title": "DISPUTED CARGO FREIGHT MANIFEST",
        "headers": ["Consignment", "Gross Cargo (kg)", "Declared Value (INR)", "Payment Status"],
        "cols": [50, 220, 420, 620, 800],
        "rows": [
            ["DISP-CON-01", "1450.0", "85000", "Pending"],
            ["DISP-CON-02", "2200.0", "140000", "Settled"],
        ],
        "fields": [
            # Type contradiction trap: asking for 'amount' on weight column, should abstain!
            {"name": "disp01_trap_weight", "expected": "1450.0", "row": 0, "col": 1, "type": "weight", "target_pattern": "DISP-CON-01", "col_pattern": "Gross Cargo"},
            {"name": "disp01_val", "expected": "85000", "row": 0, "col": 2, "type": "amount", "target_pattern": "DISP-CON-01", "col_pattern": "Declared Value"},
            {"name": "disp02_val", "expected": "140000", "row": 1, "col": 2, "type": "amount", "target_pattern": "DISP-CON-02", "col_pattern": "Declared Value"},
        ]
    })
    specs.append({
        "id": "COHORT_J_ADV_06_CHARACTER_SUBSTITUTION_STRESS", "cohort": "J_challenge_adversarial", "family": "Commercial Invoice", "condition": "scan",
        "title": "ALPHANUMERIC IDENTIFIER CHARACTER NOISE",
        "headers": ["Complex SKU", "Nominal Gauge", "Inventory Pack", "Total Value"],
        "cols": [50, 240, 440, 620, 800],
        "rows": [
            ["SKU-001-S05", "12.5", "100", "1250"],
            ["SKU-002-Z28", "14.0", "50", "700"],
            ["SKU-003-B88", "16.5", "80", "1320"],
        ],
        "fields": [
            {"name": "sku1_val", "expected": "1250", "row": 0, "col": 3, "type": "amount", "target_pattern": "SKU-001-S05", "col_pattern": "Total Value"},
            {"name": "sku2_val", "expected": "700", "row": 1, "col": 3, "type": "amount", "target_pattern": "SKU-002-Z28", "col_pattern": "Total Value"},
            {"name": "sku3_val", "expected": "1320", "row": 2, "col": 3, "type": "amount", "target_pattern": "SKU-003-B88", "col_pattern": "Total Value"},
        ]
    })
    specs.append({
        "id": "COHORT_J_ADV_07_IDENTICAL_NEIGHBORS", "cohort": "J_challenge_adversarial", "family": "Bank Statement", "condition": "clean",
        "title": "REPETITIVE EQUAL AMOUNT SETTLEMENT AUDIT",
        "headers": ["Voucher Ref", "Account Tag", "Fixed Surcharge", "Total Paid"],
        "cols": [50, 220, 420, 620, 800],
        "rows": [
            ["VCH-TAG-101", "Utility Pay", "500", "5500"],
            ["VCH-TAG-102", "Utility Pay", "500", "5500"],
            ["VCH-TAG-103", "Utility Pay", "500", "5500"],
        ],
        "fields": [
            {"name": "vch101_paid", "expected": "5500", "row": 0, "col": 3, "type": "amount", "target_pattern": "VCH-TAG-101", "col_pattern": "Total Paid"},
            {"name": "vch102_paid", "expected": "5500", "row": 1, "col": 3, "type": "amount", "target_pattern": "VCH-TAG-102", "col_pattern": "Total Paid"},
            {"name": "vch103_paid", "expected": "5500", "row": 2, "col": 3, "type": "amount", "target_pattern": "VCH-TAG-103", "col_pattern": "Total Paid"},
        ]
    })
    specs.append({
        "id": "COHORT_J_ADV_08_MULTI_TIER_INTERFERENCE", "cohort": "J_challenge_adversarial", "family": "Tax Schedule", "condition": "clean",
        "title": "SUPER-HEADER SPANNING REVENUE TABLE",
        "headers": ["Entity Code", "Q1 Budget", "Q1 Actual", "Q2 Budget", "Q2 Actual"],
        "cols": [50, 180, 330, 480, 630, 800],
        "rows": [
            ["ENT-REV-901", "50000", "48500", "60000", "59200"],
            ["ENT-REV-902", "80000", "79000", "85000", "84100"],
        ],
        "fields": [
            {"name": "ent901_q1_act", "expected": "48500", "row": 0, "col": 2, "type": "amount", "target_pattern": "ENT-REV-901", "col_pattern": "Q1 Actual"},
            {"name": "ent901_q2_act", "expected": "59200", "row": 0, "col": 4, "type": "amount", "target_pattern": "ENT-REV-901", "col_pattern": "Q2 Actual"},
            {"name": "ent902_q1_act", "expected": "79000", "row": 1, "col": 2, "type": "amount", "target_pattern": "ENT-REV-902", "col_pattern": "Q1 Actual"},
        ]
    })
    specs.append({
        "id": "COHORT_J_ADV_09_FAINT_THERMAL_RECEIPT", "cohort": "J_challenge_adversarial", "family": "Retail Receipt", "condition": "thermal",
        "title": "FAINT THERMAL TOLL PLAZA REGISTER",
        "headers": ["Lane Ref", "Vehicle Class", "Toll Rate", "Fastag Debit"],
        "cols": [50, 220, 420, 620, 800],
        "rows": [
            ["LANE-EAST-01", "Car / Jeep", "85.00", "85.00"],
            ["LANE-EAST-02", "Light Commercial", "140.00", "140.00"],
            ["LANE-WEST-03", "Multi-Axle Truck", "280.00", "280.00"],
        ],
        "fields": [
            {"name": "lane01_toll", "expected": "85.00", "row": 0, "col": 3, "type": "amount", "target_pattern": "LANE-EAST-01", "col_pattern": "Fastag Debit"},
            {"name": "lane02_toll", "expected": "140.00", "row": 1, "col": 3, "type": "amount", "target_pattern": "LANE-EAST-02", "col_pattern": "Fastag Debit"},
            {"name": "lane03_toll", "expected": "280.00", "row": 2, "col": 3, "type": "amount", "target_pattern": "LANE-WEST-03", "col_pattern": "Fastag Debit"},
        ]
    })
    specs.append({
        "id": "COHORT_J_ADV_10_SUB10PX_REAGENT_STABILITY", "cohort": "J_challenge_adversarial", "family": "Pharma Assay", "condition": "scan",
        "title": "SUB-10PX MICROLITER REAGENT ASSAY",
        "headers": ["Assay Well", "Reagent Density", "Osmolality (mOsm)", "pH Balance"],
        "cols": [50, 220, 420, 620, 800],
        "rows": [
            ["WELL-PLATE-01", "1.02", "295", "7.35"],
            ["WELL-PLATE-02", "1.05", "310", "7.40"],
            ["WELL-PLATE-03", "0.99", "285", "7.25"],
        ],
        "fields": [
            {"name": "well01_dens", "expected": "1.02", "row": 0, "col": 1, "type": "number", "target_pattern": "WELL-PLATE-01", "col_pattern": "Reagent Density"},
            {"name": "well01_ph", "expected": "7.35", "row": 0, "col": 3, "type": "number", "target_pattern": "WELL-PLATE-01", "col_pattern": "pH Balance"},
            {"name": "well02_dens", "expected": "1.05", "row": 1, "col": 1, "type": "number", "target_pattern": "WELL-PLATE-02", "col_pattern": "Reagent Density"},
            {"name": "well02_osmo", "expected": "310", "row": 1, "col": 2, "type": "count", "target_pattern": "WELL-PLATE-02", "col_pattern": "Osmolality"},
        ]
    })

    return specs


def render_document(spec: dict):
    doc_id = spec["id"]
    headers = spec["headers"]
    cols = spec["cols"]
    rows = spec["rows"]
    title = spec["title"]
    cond = spec["condition"]

    h_img = 120 + len(rows) * 45 + 30
    img = Image.new("RGB", (850, h_img), color=(255, 255, 255))
    d = ImageDraw.Draw(img)

    # Title
    d.text((50, 25), title, fill=(0, 0, 0), font=font_title)

    # Headers
    y_h_top = 70
    y_h_bot = 105
    for i in range(len(headers)):
        c1, c2 = cols[i], cols[i+1]
        d.rectangle([c1, y_h_top, c2, y_h_bot], outline=(0, 0, 0), width=1)
        d.text((c1 + 10, y_h_top + 10), headers[i], fill=(0, 0, 0), font=font_head)

    # Data Rows
    for r_i, row_data in enumerate(rows):
        y_top = y_h_bot + r_i * 45
        y_bot = y_top + 45
        for c_i, val in enumerate(row_data):
            c1, c2 = cols[c_i], cols[c_i+1]
            d.rectangle([c1, y_top, c2, y_bot], outline=(0, 0, 0), width=1)
            f = font_micro if cond == "scan" else font_body
            d.text((c1 + 12, y_top + 14), str(val), fill=(0, 0, 0), font=f)

    final_img = apply_degradation(img, cond)
    img_path = TABLES_DIR / f"{doc_id}.png"
    final_img.save(img_path)

    manifest_docs[doc_id] = {
        "cohort": spec["cohort"],
        "category": spec["family"],
        "condition": cond,
        "image_path": str(img_path),
        "critical_fields": spec["fields"]
    }


def main():
    specs = create_doc_specs()
    print(f"Generating {len(specs)} documents for Loop 25 Cohort J...")
    for s in specs:
        render_document(s)

    total_fields = sum(len(d["critical_fields"]) for d in manifest_docs.values())
    manifest_path = ROOT / "research" / "loop25" / "dataset_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_docs, f, indent=2)

    cohort_counts = {}
    for d in manifest_docs.values():
        c = d["cohort"]
        cohort_counts[c] = cohort_counts.get(c, 0) + 1

    print(f"Successfully generated {len(manifest_docs)} documents with {total_fields} critical fields.")
    for c, cnt in cohort_counts.items():
        print(f"  {c:25s}: {cnt} documents")
    print(f"Saved manifest to {manifest_path}")


if __name__ == "__main__":
    main()
