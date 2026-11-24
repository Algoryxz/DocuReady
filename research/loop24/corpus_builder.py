"""
Loop 24 Independent Generalization Corpus Builder - Cohort I
Generates 30 independent document fixtures (>= 100 critical fields)
across 6 document families and 3 rendering/acquisition conditions:
  1. Commercial Invoices
  2. Bank Statements
  3. Tax & Municipal Assessment Schedules
  4. Medical & Diagnostic Panels
  5. Pharmaceutical Quality & Strength Statements
  6. Retail Receipts & Delivery Challans

Partitions:
  - Cohort A (Development): 8 docs (DEV_01 .. DEV_08) -> 28 fields
  - Cohort B (Calibration): 8 docs (CAL_01 .. CAL_08) -> 28 fields
  - Cohort C (Locked Independent Blind): 10 docs (BLIND_01 .. BLIND_10) -> 35 fields
  - Cohort D (Challenge / Adversarial): 4 docs (ADV_01 .. ADV_04) -> 13 fields
Total: 30 documents, 104 critical fields.
"""

import json
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
TABLES_DIR = ROOT / "research" / "loop24" / "tables"
TABLES_DIR.mkdir(parents=True, exist_ok=True)

try:
    font_title = ImageFont.truetype("arial.ttf", 18)
    font_head = ImageFont.truetype("arialbd.ttf", 12)
    font_body = ImageFont.truetype("arial.ttf", 11)
    font_micro = ImageFont.truetype("arial.ttf", 10)
    font_mono = ImageFont.truetype("cour.ttf", 11)
except Exception:
    font_title = ImageFont.load_default()
    font_head = ImageFont.load_default()
    font_body = ImageFont.load_default()
    font_micro = ImageFont.load_default()
    font_mono = ImageFont.load_default()

manifest_docs = {}


def apply_degradation(img: Image.Image, mode: str) -> Image.Image:
    if mode == "clean":
        return img
    elif mode == "scan":
        # Slight blur and threshold noise mimicking 200dpi scanner
        gray = img.convert("L")
        blurred = gray.filter(ImageFilter.GaussianBlur(radius=0.4))
        return blurred.convert("RGB")
    elif mode == "thermal":
        # Thermal paper faint contrast
        gray = img.convert("L")
        lut = [int(p * 0.92 + 15) for p in range(256)]
        faint = gray.point(lut)
        return faint.convert("RGB")
    return img


# ======================================================================
# DEFINITION OF 30 DOCUMENTS ACROSS 6 FAMILIES
# ======================================================================

docs_spec = [
    # --- COHORT A: DEVELOPMENT (8 docs) ---
    {
        "id": "COHORT_I_DEV_01_INVOICE",
        "cohort": "I_development",
        "family": "Commercial Invoice",
        "condition": "clean",
        "title": "GLOBAL SUPPLY LOGISTICS INVOICE",
        "headers": ["Item Code", "Description", "Unit Price", "Qty", "Total (USD)"],
        "cols": [50, 160, 420, 540, 620, 800],
        "rows": [
            ["SKU-9901", "Industrial Ball Bearing", "24.50", "10", "245.00"],
            ["SKU-8820", "Polymer Drive Belt", "12.00", "5", "60.00"],
            ["SKU-7734", "Hydraulic Coupling", "45.80", "4", "183.20"],
        ],
        "fields": [
            {"name": "bearing_price", "expected": "24.50", "row": 0, "col": 2, "type": "amount", "target_pattern": "SKU-9901", "col_pattern": "Unit Price"},
            {"name": "bearing_total", "expected": "245.00", "row": 0, "col": 4, "type": "amount", "target_pattern": "SKU-9901", "col_pattern": "Total"},
            {"name": "belt_total", "expected": "60.00", "row": 1, "col": 4, "type": "amount", "target_pattern": "SKU-8820", "col_pattern": "Total"},
            {"name": "coupling_price", "expected": "45.80", "row": 2, "col": 2, "type": "amount", "target_pattern": "SKU-7734", "col_pattern": "Unit Price"},
        ]
    },
    {
        "id": "COHORT_I_DEV_02_BANK_STATEMENT",
        "cohort": "I_development",
        "family": "Bank Statement",
        "condition": "clean",
        "title": "CITY NATIONAL BANK - TRANSACTION REGISTER",
        "headers": ["Txn Date", "Reference", "Debit (INR)", "Credit (INR)", "Balance (INR)"],
        "cols": [50, 160, 380, 510, 640, 800],
        "rows": [
            ["12/04/2026", "SALARY CREDIT NEFT", "", "85000", "142500"],
            ["14/04/2026", "ATM CASH WITHDRAWAL", "5000", "", "137500"],
            ["18/04/2026", "ELECTRICITY BILL UPI", "2450", "", "135050"],
        ],
        "fields": [
            {"name": "salary_credit", "expected": "85000", "row": 0, "col": 3, "type": "amount", "target_pattern": "SALARY CREDIT", "col_pattern": "Credit"},
            {"name": "atm_debit", "expected": "5000", "row": 1, "col": 2, "type": "amount", "target_pattern": "ATM CASH", "col_pattern": "Debit"},
            {"name": "post_atm_balance", "expected": "137500", "row": 1, "col": 4, "type": "amount", "target_pattern": "ATM CASH", "col_pattern": "Balance"},
            {"name": "elec_debit", "expected": "2450", "row": 2, "col": 2, "type": "amount", "target_pattern": "ELECTRICITY BILL", "col_pattern": "Debit"},
        ]
    },
    {
        "id": "COHORT_I_DEV_03_TAX_SCHEDULE",
        "cohort": "I_development",
        "family": "Tax & Municipal Schedule",
        "condition": "clean",
        "title": "MUNICIPAL PROPERTY VALUATION NOTICE",
        "headers": ["Ward No", "Holding No", "Assessed Value", "Annual Tax", "Cess (10%)"],
        "cols": [50, 160, 310, 480, 640, 800],
        "rows": [
            ["WARD-14", "HOLD-8821", "650000", "13000", "1300"],
            ["WARD-14", "HOLD-8822", "820000", "16400", "1640"],
            ["WARD-15", "HOLD-9104", "450000", "9000", "900"],
        ],
        "fields": [
            {"name": "h8821_tax", "expected": "13000", "row": 0, "col": 3, "type": "amount", "target_pattern": "HOLD-8821", "col_pattern": "Annual Tax"},
            {"name": "h8821_cess", "expected": "1300", "row": 0, "col": 4, "type": "amount", "target_pattern": "HOLD-8821", "col_pattern": "Cess"},
            {"name": "h8822_value", "expected": "820000", "row": 1, "col": 2, "type": "amount", "target_pattern": "HOLD-8822", "col_pattern": "Assessed Value"},
            {"name": "h9104_tax", "expected": "9000", "row": 2, "col": 3, "type": "amount", "target_pattern": "HOLD-9104", "col_pattern": "Annual Tax"},
        ]
    },
    {
        "id": "COHORT_I_DEV_04_CLINICAL_PANEL",
        "cohort": "I_development",
        "family": "Medical & Diagnostic Panel",
        "condition": "scan",
        "title": "DIAGNOSTIC PATHOLOGY LABORATORY REPORT",
        "headers": ["Investigation", "Observed Value", "Standard Units", "Reference Range"],
        "cols": [50, 300, 460, 600, 800],
        "rows": [
            ["Serum Bilirubin Total", "0.9", "mg/dL", "0.2 - 1.2"],
            ["Serum Creatinine", "1.1", "mg/dL", "0.7 - 1.3"],
            ["Blood Urea Nitrogen", "16", "mg/dL", "7 - 20"],
            ["Fasting Plasma Glucose", "94", "mg/dL", "70 - 99"],
        ],
        "fields": [
            {"name": "bili_val", "expected": "0.9", "row": 0, "col": 1, "type": "number", "target_pattern": "Serum Bilirubin", "col_pattern": "Observed Value"},
            {"name": "creat_val", "expected": "1.1", "row": 1, "col": 1, "type": "number", "target_pattern": "Serum Creatinine", "col_pattern": "Observed Value"},
            {"name": "bun_val", "expected": "16", "row": 2, "col": 1, "type": "count", "target_pattern": "Blood Urea", "col_pattern": "Observed Value"},
            {"name": "fpg_val", "expected": "94", "row": 3, "col": 1, "type": "count", "target_pattern": "Fasting Plasma", "col_pattern": "Observed Value"},
        ]
    },
    {
        "id": "COHORT_I_DEV_05_PHARMA_ASSAY",
        "cohort": "I_development",
        "family": "Pharmaceutical Quality Statement",
        "condition": "clean",
        "title": "ACTIVE PHARMACEUTICAL INGREDIENT CERTIFICATE",
        "headers": ["Compound Name", "Batch Lot", "Assay Purity", "Moisture Content"],
        "cols": [50, 280, 460, 630, 800],
        "rows": [
            ["Paracetamol Micronized", "LOT-PC-401", "99.4", "0.35"],
            ["Ibuprofen Powder", "LOT-IB-102", "98.9", "0.20"],
            ["Metformin Hydrochloride", "LOT-MF-880", "99.7", "0.15"],
        ],
        "fields": [
            {"name": "para_purity", "expected": "99.4", "row": 0, "col": 2, "type": "percentage", "target_pattern": "Paracetamol Micronized", "col_pattern": "Assay Purity"},
            {"name": "para_moist", "expected": "0.35", "row": 0, "col": 3, "type": "number", "target_pattern": "Paracetamol Micronized", "col_pattern": "Moisture"},
            {"name": "ibu_purity", "expected": "98.9", "row": 1, "col": 2, "type": "percentage", "target_pattern": "Ibuprofen Powder", "col_pattern": "Assay Purity"},
        ]
    },
    {
        "id": "COHORT_I_DEV_06_RETAIL_RECEIPT",
        "cohort": "I_development",
        "family": "Retail Receipt",
        "condition": "thermal",
        "title": "METRO FRESH SUPERMARKET REGISTER",
        "headers": ["Product Name", "Rate (INR)", "Quantity", "Amount (INR)"],
        "cols": [50, 360, 500, 640, 800],
        "rows": [
            ["Whole Wheat Flour 5kg", "210.00", "2", "420.00"],
            ["Organic Brown Sugar 1kg", "75.00", "3", "225.00"],
            ["Virgin Olive Oil 500ml", "480.00", "1", "480.00"],
        ],
        "fields": [
            {"name": "flour_rate", "expected": "210.00", "row": 0, "col": 1, "type": "amount", "target_pattern": "Whole Wheat Flour", "col_pattern": "Rate"},
            {"name": "flour_total", "expected": "420.00", "row": 0, "col": 3, "type": "amount", "target_pattern": "Whole Wheat Flour", "col_pattern": "Amount"},
            {"name": "sugar_total", "expected": "225.00", "row": 1, "col": 3, "type": "amount", "target_pattern": "Organic Brown Sugar", "col_pattern": "Amount"},
        ]
    },
    {
        "id": "COHORT_I_DEV_07_CHALLAN_DELIVERY",
        "cohort": "I_development",
        "family": "Delivery Challan",
        "condition": "clean",
        "title": "INDUSTRIAL WAREHOUSE DELIVERY CHALLAN",
        "headers": ["Consignment No", "Destination City", "Packages", "Gross Weight (kg)"],
        "cols": [50, 240, 460, 600, 800],
        "rows": [
            ["CN-2026-081", "Bhubaneswar", "25", "1450.5"],
            ["CN-2026-082", "Cuttack", "10", "620.0"],
            ["CN-2026-083", "Rourkela", "40", "2180.0"],
        ],
        "fields": [
            {"name": "cn81_packages", "expected": "25", "row": 0, "col": 2, "type": "count", "target_pattern": "CN-2026-081", "col_pattern": "Packages"},
            {"name": "cn81_weight", "expected": "1450.5", "row": 0, "col": 3, "type": "weight", "target_pattern": "CN-2026-081", "col_pattern": "Gross Weight"},
            {"name": "cn82_weight", "expected": "620.0", "row": 1, "col": 3, "type": "weight", "target_pattern": "CN-2026-082", "col_pattern": "Gross Weight"},
        ]
    },
    {
        "id": "COHORT_I_DEV_08_ENERGY_AUDIT",
        "cohort": "I_development",
        "family": "Commercial Invoice",
        "condition": "scan",
        "title": "COMMERCIAL POWER CONSUMPTION LEDGER",
        "headers": ["Meter Serial", "Prior Reading", "Current Reading", "Units Billed"],
        "cols": [50, 220, 410, 610, 800],
        "rows": [
            ["MTR-8812-A", "14200", "15850", "1650"],
            ["MTR-8812-B", "21400", "23900", "2500"],
            ["MTR-8812-C", "8900", "9750", "850"],
        ],
        "fields": [
            {"name": "mtr_a_units", "expected": "1650", "row": 0, "col": 3, "type": "count", "target_pattern": "MTR-8812-A", "col_pattern": "Units Billed"},
            {"name": "mtr_b_units", "expected": "2500", "row": 1, "col": 3, "type": "count", "target_pattern": "MTR-8812-B", "col_pattern": "Units Billed"},
            {"name": "mtr_c_prior", "expected": "8900", "row": 2, "col": 1, "type": "count", "target_pattern": "MTR-8812-C", "col_pattern": "Prior Reading"},
        ]
    },

    # --- COHORT B: CALIBRATION (8 docs) ---
    {
        "id": "COHORT_I_CAL_01_FREIGHT_INVOICE",
        "cohort": "I_calibration",
        "family": "Commercial Invoice",
        "condition": "clean",
        "title": "PACIFIC OCEAN CARRIER BILL OF LADING",
        "headers": ["Container ID", "Cargo Class", "Handling Fee", "Insurance", "Net Ocean Freight"],
        "cols": [50, 200, 350, 490, 630, 800],
        "rows": [
            ["CONT-9941-X", "Machinery", "450", "120", "3200"],
            ["CONT-7720-Y", "Textiles", "300", "85", "2100"],
            ["CONT-5511-Z", "Chemicals", "600", "210", "4150"],
        ],
        "fields": [
            {"name": "cont_x_freight", "expected": "3200", "row": 0, "col": 4, "type": "amount", "target_pattern": "CONT-9941-X", "col_pattern": "Net Ocean Freight"},
            {"name": "cont_x_handling", "expected": "450", "row": 0, "col": 2, "type": "amount", "target_pattern": "CONT-9941-X", "col_pattern": "Handling Fee"},
            {"name": "cont_y_freight", "expected": "2100", "row": 1, "col": 4, "type": "amount", "target_pattern": "CONT-7720-Y", "col_pattern": "Net Ocean Freight"},
            {"name": "cont_z_insurance", "expected": "210", "row": 2, "col": 3, "type": "amount", "target_pattern": "CONT-5511-Z", "col_pattern": "Insurance"},
        ]
    },
    {
        "id": "COHORT_I_CAL_02_ESCROW_STATEMENT",
        "cohort": "I_calibration",
        "family": "Bank Statement",
        "condition": "clean",
        "title": "TRUST & ESCROW SETTLEMENT STATEMENT",
        "headers": ["Escrow Sub-Account", "Disbursement", "Retention (INR)", "Released Balance"],
        "cols": [50, 250, 430, 610, 800],
        "rows": [
            ["SUB-ESCROW-01", "250000", "25000", "225000"],
            ["SUB-ESCROW-02", "180000", "18000", "162000"],
            ["SUB-ESCROW-03", "400000", "40000", "360000"],
        ],
        "fields": [
            {"name": "escrow_01_ret", "expected": "25000", "row": 0, "col": 2, "type": "amount", "target_pattern": "SUB-ESCROW-01", "col_pattern": "Retention"},
            {"name": "escrow_01_bal", "expected": "225000", "row": 0, "col": 3, "type": "amount", "target_pattern": "SUB-ESCROW-01", "col_pattern": "Released Balance"},
            {"name": "escrow_02_bal", "expected": "162000", "row": 1, "col": 3, "type": "amount", "target_pattern": "SUB-ESCROW-02", "col_pattern": "Released Balance"},
            {"name": "escrow_03_disb", "expected": "400000", "row": 2, "col": 1, "type": "amount", "target_pattern": "SUB-ESCROW-03", "col_pattern": "Disbursement"},
        ]
    },
    {
        "id": "COHORT_I_CAL_03_CORPORATE_TAX",
        "cohort": "I_calibration",
        "family": "Tax & Municipal Schedule",
        "condition": "scan",
        "title": "ADVANCE TAX INSTALLMENT ASSESSMENT",
        "headers": ["Installment Due", "Gross Assessment", "TDS Credit", "Net Payable"],
        "cols": [50, 230, 430, 610, 800],
        "rows": [
            ["15-JUN-2026", "150000", "35000", "115000"],
            ["15-SEP-2026", "250000", "40000", "210000"],
            ["15-DEC-2026", "300000", "45000", "255000"],
        ],
        "fields": [
            {"name": "tax_jun_net", "expected": "115000", "row": 0, "col": 3, "type": "amount", "target_pattern": "15-JUN-2026", "col_pattern": "Net Payable"},
            {"name": "tax_jun_tds", "expected": "35000", "row": 0, "col": 2, "type": "amount", "target_pattern": "15-JUN-2026", "col_pattern": "TDS Credit"},
            {"name": "tax_sep_net", "expected": "210000", "row": 1, "col": 3, "type": "amount", "target_pattern": "15-SEP-2026", "col_pattern": "Net Payable"},
        ]
    },
    {
        "id": "COHORT_I_CAL_04_BLOOD_GAS",
        "cohort": "I_calibration",
        "family": "Medical & Diagnostic Panel",
        "condition": "clean",
        "title": "ARTERIAL BLOOD GAS EVALUATION REPORT",
        "headers": ["Parameter", "Measured Value", "Units", "Target Reference"],
        "cols": [50, 280, 460, 620, 800],
        "rows": [
            ["Arterial pH", "7.42", "pH units", "7.35 - 7.45"],
            ["pCO2 Partial Pressure", "38.5", "mmHg", "35.0 - 45.0"],
            ["pO2 Oxygen Tension", "94.2", "mmHg", "80.0 - 100.0"],
            ["Bicarbonate HCO3", "24.6", "mEq/L", "22.0 - 26.0"],
        ],
        "fields": [
            {"name": "ph_val", "expected": "7.42", "row": 0, "col": 1, "type": "number", "target_pattern": "Arterial pH", "col_pattern": "Measured Value"},
            {"name": "pco2_val", "expected": "38.5", "row": 1, "col": 1, "type": "number", "target_pattern": "pCO2 Partial", "col_pattern": "Measured Value"},
            {"name": "po2_val", "expected": "94.2", "row": 2, "col": 1, "type": "number", "target_pattern": "pO2 Oxygen", "col_pattern": "Measured Value"},
            {"name": "hco3_val", "expected": "24.6", "row": 3, "col": 1, "type": "number", "target_pattern": "Bicarbonate HCO3", "col_pattern": "Measured Value"},
        ]
    },
    {
        "id": "COHORT_I_CAL_05_DISSOLUTION_RATE",
        "cohort": "I_calibration",
        "family": "Pharmaceutical Quality Statement",
        "condition": "clean",
        "title": "TABLET DISSOLUTION & STABILITY PROFILE",
        "headers": ["Time Point", "Vessel 1 (%)", "Vessel 2 (%)", "Vessel 3 (%)", "Mean Release (%)"],
        "cols": [50, 200, 350, 500, 650, 800],
        "rows": [
            ["15 Minutes", "45.2", "44.8", "46.1", "45.4"],
            ["30 Minutes", "78.4", "77.9", "79.2", "78.5"],
            ["45 Minutes", "94.6", "95.1", "94.2", "94.6"],
        ],
        "fields": [
            {"name": "mean_15m", "expected": "45.4", "row": 0, "col": 4, "type": "percentage", "target_pattern": "15 Minutes", "col_pattern": "Mean Release"},
            {"name": "mean_30m", "expected": "78.5", "row": 1, "col": 4, "type": "percentage", "target_pattern": "30 Minutes", "col_pattern": "Mean Release"},
            {"name": "mean_45m", "expected": "94.6", "row": 2, "col": 4, "type": "percentage", "target_pattern": "45 Minutes", "col_pattern": "Mean Release"},
        ]
    },
    {
        "id": "COHORT_I_CAL_06_HARDWARE_POS",
        "cohort": "I_calibration",
        "family": "Retail Receipt",
        "condition": "thermal",
        "title": "BUILDERS HARDWARE SUPPLY DEPOT",
        "headers": ["Article Code", "Item Description", "Unit Price", "Quantity", "Total"],
        "cols": [50, 180, 420, 540, 640, 800],
        "rows": [
            ["ART-4011", "M10 Steel Hex Bolt", "4.50", "50", "225.00"],
            ["ART-4012", "M10 Nylon Lock Nut", "2.20", "50", "110.00"],
            ["ART-8890", "Heavy Duty Washer", "1.10", "100", "110.00"],
        ],
        "fields": [
            {"name": "bolt_total", "expected": "225.00", "row": 0, "col": 4, "type": "amount", "target_pattern": "ART-4011", "col_pattern": "Total"},
            {"name": "nut_total", "expected": "110.00", "row": 1, "col": 4, "type": "amount", "target_pattern": "ART-4012", "col_pattern": "Total"},
            {"name": "washer_qty", "expected": "100", "row": 2, "col": 3, "type": "count", "target_pattern": "ART-8890", "col_pattern": "Quantity"},
        ]
    },
    {
        "id": "COHORT_I_CAL_07_DISPATCH_MANIFEST",
        "cohort": "I_calibration",
        "family": "Delivery Challan",
        "condition": "scan",
        "title": "CONTAINER FLEET DISPATCH SCHEDULE",
        "headers": ["Truck Plate", "Driver Name", "Pallets Loaded", "Gross Weight (t)"],
        "cols": [50, 240, 450, 620, 800],
        "rows": [
            ["OD-02-AK-9921", "Rajesh Kumar", "18", "14.2"],
            ["OD-05-BL-4412", "Manoj Nayak", "22", "18.5"],
            ["OD-14-CM-8833", "Bikram Sahu", "15", "11.8"],
        ],
        "fields": [
            {"name": "truck_9921_pallets", "expected": "18", "row": 0, "col": 2, "type": "count", "target_pattern": "OD-02-AK-9921", "col_pattern": "Pallets Loaded"},
            {"name": "truck_9921_wt", "expected": "14.2", "row": 0, "col": 3, "type": "weight", "target_pattern": "OD-02-AK-9921", "col_pattern": "Gross Weight"},
            {"name": "truck_4412_wt", "expected": "18.5", "row": 1, "col": 3, "type": "weight", "target_pattern": "OD-05-BL-4412", "col_pattern": "Gross Weight"},
        ]
    },
    {
        "id": "COHORT_I_CAL_08_COMMODITY_STATEMENT",
        "cohort": "I_calibration",
        "family": "Commercial Invoice",
        "condition": "clean",
        "title": "AGRO COMMODITIES WHOLESALE REGISTER",
        "headers": ["Lot Code", "Grade", "Bags Procured", "Rate Per Bag", "Settlement Value"],
        "cols": [50, 180, 310, 470, 630, 800],
        "rows": [
            ["LOT-WHEAT-01", "Grade A", "200", "1850", "370000"],
            ["LOT-PADDY-02", "Grade B", "350", "1420", "497000"],
            ["LOT-MAIZE-03", "Standard", "150", "1600", "240000"],
        ],
        "fields": [
            {"name": "wheat_total", "expected": "370000", "row": 0, "col": 4, "type": "amount", "target_pattern": "LOT-WHEAT-01", "col_pattern": "Settlement Value"},
            {"name": "paddy_total", "expected": "497000", "row": 1, "col": 4, "type": "amount", "target_pattern": "LOT-PADDY-02", "col_pattern": "Settlement Value"},
            {"name": "maize_total", "expected": "240000", "row": 2, "col": 4, "type": "amount", "target_pattern": "LOT-MAIZE-03", "col_pattern": "Settlement Value"},
        ]
    },

    # --- COHORT C: LOCKED INDEPENDENT BLIND (10 docs) ---
    {
        "id": "COHORT_I_BLIND_01_SOLAR_TARIFF",
        "cohort": "I_blind_evaluation",
        "family": "Commercial Invoice",
        "condition": "clean",
        "title": "RENEWABLE ENERGY TARIFF INVOICE",
        "headers": ["Solar Plant ID", "Generation (MWh)", "Base Tariff", "Green Subsidy", "Net Due (INR)"],
        "cols": [50, 200, 360, 500, 650, 800],
        "rows": [
            ["SOL-ORISSA-01", "450", "3.15", "0.50", "1642500"],
            ["SOL-ORISSA-02", "620", "3.15", "0.50", "2263000"],
            ["SOL-ORISSA-03", "310", "3.15", "0.50", "1131500"],
        ],
        "fields": [
            {"name": "sol1_net", "expected": "1642500", "row": 0, "col": 4, "type": "amount", "target_pattern": "SOL-ORISSA-01", "col_pattern": "Net Due"},
            {"name": "sol1_tariff", "expected": "3.15", "row": 0, "col": 2, "type": "number", "target_pattern": "SOL-ORISSA-01", "col_pattern": "Base Tariff"},
            {"name": "sol2_net", "expected": "2263000", "row": 1, "col": 4, "type": "amount", "target_pattern": "SOL-ORISSA-02", "col_pattern": "Net Due"},
            {"name": "sol3_mwh", "expected": "310", "row": 2, "col": 1, "type": "count", "target_pattern": "SOL-ORISSA-03", "col_pattern": "Generation"},
        ]
    },
    {
        "id": "COHORT_I_BLIND_02_LOAN_AMORTIZATION",
        "cohort": "I_blind_evaluation",
        "family": "Bank Statement",
        "condition": "clean",
        "title": "HOUSING LOAN AMORTIZATION SCHEDULE",
        "headers": ["Installment", "Principal (INR)", "Interest (INR)", "EMI Amount", "Closing Principal"],
        "cols": [50, 180, 330, 480, 630, 800],
        "rows": [
            ["Month 01", "14500", "28500", "43000", "3485500"],
            ["Month 02", "14620", "28380", "43000", "3470880"],
            ["Month 03", "14740", "28260", "43000", "3456140"],
        ],
        "fields": [
            {"name": "m01_emi", "expected": "43000", "row": 0, "col": 3, "type": "amount", "target_pattern": "Month 01", "col_pattern": "EMI Amount"},
            {"name": "m01_closing", "expected": "3485500", "row": 0, "col": 4, "type": "amount", "target_pattern": "Month 01", "col_pattern": "Closing Principal"},
            {"name": "m02_emi", "expected": "43000", "row": 1, "col": 3, "type": "amount", "target_pattern": "Month 02", "col_pattern": "EMI Amount"},
            {"name": "m03_interest", "expected": "28260", "row": 2, "col": 2, "type": "amount", "target_pattern": "Month 03", "col_pattern": "Interest"},
        ]
    },
    {
        "id": "COHORT_I_BLIND_03_CUSTOMS_DUTY",
        "cohort": "I_blind_evaluation",
        "family": "Tax & Municipal Schedule",
        "condition": "scan",
        "title": "PORT CUSTOMS IMPORT DUTY BILL",
        "headers": ["HSN Code", "Assessable Value", "Basic Duty (7.5%)", "SWS Cess", "Total Duty"],
        "cols": [50, 180, 360, 520, 650, 800],
        "rows": [
            ["8471.30", "1200000", "90000", "9000", "99000"],
            ["8504.40", "650000", "48750", "4875", "53625"],
            ["9031.80", "420000", "31500", "3150", "34650"],
        ],
        "fields": [
            {"name": "hsn_8471_duty", "expected": "99000", "row": 0, "col": 4, "type": "amount", "target_pattern": "8471.30", "col_pattern": "Total Duty"},
            {"name": "hsn_8471_basic", "expected": "90000", "row": 0, "col": 2, "type": "amount", "target_pattern": "8471.30", "col_pattern": "Basic Duty"},
            {"name": "hsn_8504_duty", "expected": "53625", "row": 1, "col": 4, "type": "amount", "target_pattern": "8504.40", "col_pattern": "Total Duty"},
        ]
    },
    {
        "id": "COHORT_I_BLIND_04_THYROID_PROFILE",
        "cohort": "I_blind_evaluation",
        "family": "Medical & Diagnostic Panel",
        "condition": "clean",
        "title": "ENDOCRINOLOGY THYROID IMMUNOASSAY",
        "headers": ["Parameter", "Observed Concentration", "Units", "Biological Interval"],
        "cols": [50, 270, 480, 620, 800],
        "rows": [
            ["Free Triiodothyronine FT3", "3.2", "pg/mL", "2.0 - 4.4"],
            ["Free Thyroxine FT4", "1.35", "ng/dL", "0.82 - 1.77"],
            ["Thyroid Stimulating TSH", "2.45", "uIU/mL", "0.45 - 4.50"],
        ],
        "fields": [
            {"name": "ft3_val", "expected": "3.2", "row": 0, "col": 1, "type": "number", "target_pattern": "Free Triiodothyronine", "col_pattern": "Observed Concentration"},
            {"name": "ft4_val", "expected": "1.35", "row": 1, "col": 1, "type": "number", "target_pattern": "Free Thyroxine", "col_pattern": "Observed Concentration"},
            {"name": "tsh_val", "expected": "2.45", "row": 2, "col": 1, "type": "number", "target_pattern": "Thyroid Stimulating", "col_pattern": "Observed Concentration"},
        ]
    },
    {
        "id": "COHORT_I_BLIND_05_STERILITY_ASSAY",
        "cohort": "I_blind_evaluation",
        "family": "Pharmaceutical Quality Statement",
        "condition": "clean",
        "title": "PARENTERAL STERILE VIAL QUALITY SPECIFICATION",
        "headers": ["Vial Lot No", "Fill Volume (mL)", "Endotoxin (EU/mL)", "Particulate Count"],
        "cols": [50, 220, 410, 610, 800],
        "rows": [
            ["LOT-VIAL-091", "10.0", "0.05", "12"],
            ["LOT-VIAL-092", "10.1", "0.04", "8"],
            ["LOT-VIAL-093", "9.9", "0.06", "15"],
        ],
        "fields": [
            {"name": "v91_vol", "expected": "10.0", "row": 0, "col": 1, "type": "number", "target_pattern": "LOT-VIAL-091", "col_pattern": "Fill Volume"},
            {"name": "v91_endo", "expected": "0.05", "row": 0, "col": 2, "type": "number", "target_pattern": "LOT-VIAL-091", "col_pattern": "Endotoxin"},
            {"name": "v92_endo", "expected": "0.04", "row": 1, "col": 2, "type": "number", "target_pattern": "LOT-VIAL-092", "col_pattern": "Endotoxin"},
        ]
    },
    {
        "id": "COHORT_I_BLIND_06_PHARMACY_RECEIPT",
        "cohort": "I_blind_evaluation",
        "family": "Retail Receipt",
        "condition": "thermal",
        "title": "APOLLO PHARMACY DISPENSING COUNTER",
        "headers": ["Medicine Name", "Strip MRP", "Discount (INR)", "Net Payable (INR)"],
        "cols": [50, 320, 480, 640, 800],
        "rows": [
            ["Amoxicillin 500mg Strip", "145.00", "15.00", "130.00"],
            ["Cetirizine 10mg Strip", "35.00", "5.00", "30.00"],
            ["Pantoprazole 40mg Strip", "98.00", "10.00", "88.00"],
        ],
        "fields": [
            {"name": "amox_net", "expected": "130.00", "row": 0, "col": 3, "type": "amount", "target_pattern": "Amoxicillin 500mg", "col_pattern": "Net Payable"},
            {"name": "amox_mrp", "expected": "145.00", "row": 0, "col": 1, "type": "amount", "target_pattern": "Amoxicillin 500mg", "col_pattern": "Strip MRP"},
            {"name": "panto_net", "expected": "88.00", "row": 2, "col": 3, "type": "amount", "target_pattern": "Pantoprazole 40mg", "col_pattern": "Net Payable"},
        ]
    },
    {
        "id": "COHORT_I_BLIND_07_RAIL_FREIGHT",
        "cohort": "I_blind_evaluation",
        "family": "Delivery Challan",
        "condition": "scan",
        "title": "RAILWAY FREIGHT RECEIPT RAKE MANIFEST",
        "headers": ["Wagon ID", "Commodity", "Tare Weight", "Gross Weight", "Net Cargo (t)"],
        "cols": [50, 180, 340, 490, 640, 800],
        "rows": [
            ["WAG-7710-EC", "Thermal Coal", "22.5", "84.2", "61.7"],
            ["WAG-7711-EC", "Thermal Coal", "22.6", "85.1", "62.5"],
            ["WAG-7712-EC", "Thermal Coal", "22.4", "83.9", "61.5"],
        ],
        "fields": [
            {"name": "w10_cargo", "expected": "61.7", "row": 0, "col": 4, "type": "weight", "target_pattern": "WAG-7710-EC", "col_pattern": "Net Cargo"},
            {"name": "w10_gross", "expected": "84.2", "row": 0, "col": 3, "type": "weight", "target_pattern": "WAG-7710-EC", "col_pattern": "Gross Weight"},
            {"name": "w11_cargo", "expected": "62.5", "row": 1, "col": 4, "type": "weight", "target_pattern": "WAG-7711-EC", "col_pattern": "Net Cargo"},
        ]
    },
    {
        "id": "COHORT_I_BLIND_08_COMMERCIAL_LEASE",
        "cohort": "I_blind_evaluation",
        "family": "Commercial Invoice",
        "condition": "clean",
        "title": "COMMERCIAL REAL ESTATE LEASE RENT INVOICE",
        "headers": ["Unit Suite", "Area (sq ft)", "Base Rent", "Maintenance", "Total Due (INR)"],
        "cols": [50, 180, 330, 480, 640, 800],
        "rows": [
            ["SUITE-401", "2400", "120000", "18000", "138000"],
            ["SUITE-402", "1800", "90000", "13500", "103500"],
            ["SUITE-501", "3200", "160000", "24000", "184000"],
        ],
        "fields": [
            {"name": "s401_due", "expected": "138000", "row": 0, "col": 4, "type": "amount", "target_pattern": "SUITE-401", "col_pattern": "Total Due"},
            {"name": "s401_rent", "expected": "120000", "row": 0, "col": 2, "type": "amount", "target_pattern": "SUITE-401", "col_pattern": "Base Rent"},
            {"name": "s402_due", "expected": "103500", "row": 1, "col": 4, "type": "amount", "target_pattern": "SUITE-402", "col_pattern": "Total Due"},
            {"name": "s501_due", "expected": "184000", "row": 2, "col": 4, "type": "amount", "target_pattern": "SUITE-501", "col_pattern": "Total Due"},
        ]
    },
    {
        "id": "COHORT_I_BLIND_09_CREDIT_CARD",
        "cohort": "I_blind_evaluation",
        "family": "Bank Statement",
        "condition": "clean",
        "title": "PREMIER CARD MONTHLY BILLING STATEMENT",
        "headers": ["Statement Date", "Payment Due Date", "Minimum Due", "Total Outstanding"],
        "cols": [50, 240, 440, 620, 800],
        "rows": [
            ["05/04/2026", "25/04/2026", "2400", "48500"],
            ["05/05/2026", "25/05/2026", "3100", "62000"],
            ["05/06/2026", "25/06/2026", "1800", "36400"],
        ],
        "fields": [
            {"name": "apr_total", "expected": "48500", "row": 0, "col": 3, "type": "amount", "target_pattern": "05/04/2026", "col_pattern": "Total Outstanding"},
            {"name": "apr_min", "expected": "2400", "row": 0, "col": 2, "type": "amount", "target_pattern": "05/04/2026", "col_pattern": "Minimum Due"},
            {"name": "may_total", "expected": "62000", "row": 1, "col": 3, "type": "amount", "target_pattern": "05/05/2026", "col_pattern": "Total Outstanding"},
        ]
    },
    {
        "id": "COHORT_I_BLIND_10_WATER_MUNICIPAL",
        "cohort": "I_blind_evaluation",
        "family": "Tax & Municipal Schedule",
        "condition": "clean",
        "title": "MUNICIPAL WATER SUPPLY & SEWERAGE CHARGES",
        "headers": ["Connection ID", "Water Charges", "Sewerage Surcharge", "Arrears", "Net Payable"],
        "cols": [50, 210, 360, 520, 660, 800],
        "rows": [
            ["WAT-CONN-102", "450", "90", "0", "540"],
            ["WAT-CONN-103", "820", "164", "250", "1234"],
            ["WAT-CONN-104", "310", "62", "0", "372"],
        ],
        "fields": [
            {"name": "wat102_net", "expected": "540", "row": 0, "col": 4, "type": "amount", "target_pattern": "WAT-CONN-102", "col_pattern": "Net Payable"},
            {"name": "wat103_net", "expected": "1234", "row": 1, "col": 4, "type": "amount", "target_pattern": "WAT-CONN-103", "col_pattern": "Net Payable"},
            {"name": "wat103_arr", "expected": "250", "row": 1, "col": 3, "type": "amount", "target_pattern": "WAT-CONN-103", "col_pattern": "Arrears"},
            {"name": "wat104_net", "expected": "372", "row": 2, "col": 4, "type": "amount", "target_pattern": "WAT-CONN-104", "col_pattern": "Net Payable"},
        ]
    },

    # --- COHORT D: CHALLENGE / ADVERSARIAL (4 docs) ---
    {
        "id": "COHORT_I_ADV_01_EMPTY_TRAP",
        "cohort": "I_challenge_adversarial",
        "family": "Bank Statement",
        "condition": "clean",
        "title": "AUDIT REGISTER WITH INTERMITTENT EMPTY CELLS",
        "headers": ["Record No", "Debit Amount", "Credit Amount", "Remarks"],
        "cols": [50, 220, 420, 620, 800],
        "rows": [
            ["AUD-REC-01", "", "15000", "Verified"],
            ["AUD-REC-02", "8200", "", "Pending"],
            ["AUD-REC-03", "", "", "Reconciled"],
        ],
        "fields": [
            {"name": "rec01_debit", "expected": "", "row": 0, "col": 1, "type": "empty", "target_pattern": "AUD-REC-01", "col_pattern": "Debit Amount"},
            {"name": "rec01_credit", "expected": "15000", "row": 0, "col": 2, "type": "amount", "target_pattern": "AUD-REC-01", "col_pattern": "Credit Amount"},
            {"name": "rec02_credit", "expected": "", "row": 1, "col": 2, "type": "empty", "target_pattern": "AUD-REC-02", "col_pattern": "Credit Amount"},
        ]
    },
    {
        "id": "COHORT_I_ADV_02_COLLISION_IDENTIFIERS",
        "cohort": "I_challenge_adversarial",
        "family": "Commercial Invoice",
        "condition": "clean",
        "title": "BATCH AUDIT WITH REPEATED PREFIX COLLISION",
        "headers": ["Batch Code", "Quantity", "Unit Rate", "Total Value"],
        "cols": [50, 240, 420, 600, 800],
        "rows": [
            ["BATCH-AX-100", "50", "120", "6000"],
            ["BATCH-AX-100-A", "80", "120", "9600"],
            ["BATCH-AX-100-B", "20", "120", "2400"],
        ],
        "fields": [
            {"name": "batch_100_qty", "expected": "50", "row": 0, "col": 1, "type": "count", "target_pattern": "BATCH-AX-100", "col_pattern": "Quantity"},
            {"name": "batch_100_total", "expected": "6000", "row": 0, "col": 3, "type": "amount", "target_pattern": "BATCH-AX-100", "col_pattern": "Total Value"},
            {"name": "batch_100a_total", "expected": "9600", "row": 1, "col": 3, "type": "amount", "target_pattern": "BATCH-AX-100-A", "col_pattern": "Total Value"},
            {"name": "batch_100b_total", "expected": "2400", "row": 2, "col": 3, "type": "amount", "target_pattern": "BATCH-AX-100-B", "col_pattern": "Total Value"},
        ]
    },
    {
        "id": "COHORT_I_ADV_03_BORDERLESS_TIGHT_GUTTER",
        "cohort": "I_challenge_adversarial",
        "family": "Tax & Municipal Schedule",
        "condition": "clean",
        "title": "COMPACT MUNICIPAL PROPERTY LEDGER",
        "headers": ["Holding No", "Base Tax _ Surcharge", "Total Assessment"],
        "cols": [50, 240, 560, 800],
        "rows": [
            ["HOLD-4401", "12000 1200", "13200"],
            ["HOLD-4402", "18000 1800", "19800"],
            ["HOLD-4403", "25000 2500", "27500"],
        ],
        "fields": [
            {"name": "h4401_tax", "expected": "12000", "row": 0, "col": 1, "type": "amount", "target_pattern": "HOLD-4401", "col_pattern": "Base Tax"},
            {"name": "h4401_sur", "expected": "1200", "row": 0, "col": 1, "type": "amount", "target_pattern": "HOLD-4401", "col_pattern": "Surcharge"},
            {"name": "h4401_total", "expected": "13200", "row": 0, "col": 2, "type": "amount", "target_pattern": "HOLD-4401", "col_pattern": "Total Assessment"},
        ]
    },
    {
        "id": "COHORT_I_ADV_04_MICRO_DECIMAL_LOSS",
        "cohort": "I_challenge_adversarial",
        "family": "Pharmaceutical Quality Statement",
        "condition": "scan",
        "title": "MICRO-SCALE REAGENT CHEMICAL ASSAY",
        "headers": ["Sample Tube", "Density (g/mL)", "Viscosity (cP)", "pH Level"],
        "cols": [50, 240, 440, 620, 800],
        "rows": [
            ["TUBE-ALPHA-01", "1.08", "4.8", "6.8"],
            ["TUBE-ALPHA-02", "1.12", "5.2", "7.1"],
            ["TUBE-BETA-03", "0.98", "3.6", "6.4"],
        ],
        "fields": [
            {"name": "tube01_visc", "expected": "4.8", "row": 0, "col": 2, "type": "number", "target_pattern": "TUBE-ALPHA-01", "col_pattern": "Viscosity"},
            {"name": "tube01_ph", "expected": "6.8", "row": 0, "col": 3, "type": "number", "target_pattern": "TUBE-ALPHA-01", "col_pattern": "pH Level"},
            {"name": "tube02_visc", "expected": "5.2", "row": 1, "col": 2, "type": "number", "target_pattern": "TUBE-ALPHA-02", "col_pattern": "Viscosity"},
        ]
    },
]


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
            # Use micro font if condition is scan/tight
            f = font_micro if cond == "scan" else font_body
            d.text((c1 + 12, y_top + 14), str(val), fill=(0, 0, 0), font=f)

    # Apply degradation if specified
    final_img = apply_degradation(img, cond)
    img_path = TABLES_DIR / f"{doc_id}.png"
    final_img.save(img_path)

    # Manifest record
    manifest_docs[doc_id] = {
        "cohort": spec["cohort"],
        "category": spec["family"],
        "condition": cond,
        "image_path": str(img_path),
        "critical_fields": spec["fields"]
    }


def main():
    print(f"Generating {len(docs_spec)} documents for Loop 24 Cohort I...")
    for spec in docs_spec:
        render_document(spec)

    total_fields = sum(len(d["critical_fields"]) for d in manifest_docs.values())
    manifest_path = ROOT / "research" / "loop24" / "dataset_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_docs, f, indent=2)

    print(f"Generated {len(manifest_docs)} documents with {total_fields} critical fields.")
    print(f"Saved manifest to {manifest_path}")


if __name__ == "__main__":
    main()
