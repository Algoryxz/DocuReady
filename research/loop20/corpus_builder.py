"""
Loop 20 - Blind Generalization & Verification Reliability Corpus Builder
DocuReady Engineering Research

Generates 34 controlled evaluation documents across four rigorously separated cohorts:
  - Cohort A: Development (8 documents - inspection, baseline profiling)
  - Cohort B: Validation (8 documents - parameter verification, layout stress)
  - Cohort C: Blind Evaluation (10 documents - held-out unseen table layouts across diverse domains)
  - Cohort D: Challenge & Adversarial (8 documents - false-verification traps, ambiguity, cross-doc conflicts)

Zero PII: All names, numbers, institutions, and identifiers are strictly synthetic.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
TABLES_DIR = ROOT / "research" / "loop20" / "tables"
MANIFEST_PATH = ROOT / "research" / "loop20" / "dataset_manifest.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def get_font(size: int = 20) -> ImageFont.FreeTypeFont:
    font_paths = [
        Path(r"C:\Windows\Fonts\arial.ttf"),
        Path(r"C:\Windows\Fonts\segoeui.ttf"),
        Path(r"C:\Windows\Fonts\Nirmala.ttc"),
    ]
    for p in font_paths:
        if p.exists():
            try:
                return ImageFont.truetype(str(p), size)
            except Exception:
                continue
    return ImageFont.load_default()


def render_table_doc(
    filename: str,
    title: str,
    subtitle: str,
    headers: List[str],
    rows_data: List[List[str]],
    col_x: List[int],
    row_y: List[int],
    draw_grid: bool = True,
    width: int = 1000,
    height: int = 900,
    font_scale: int = 16,
    sub_headers: List[Tuple[str, int, int]] = None, # (text, start_x, end_x)
    is_noise: bool = False,
) -> Path:
    img = Image.new("RGB", (width, height), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    f_title = get_font(font_scale + 8)
    f_sub = get_font(font_scale + 2)
    f_head = get_font(font_scale + 2)
    f_body = get_font(font_scale)

    # Title & Subtitle
    d.text((width // 2 - len(title) * 6, 40), title, font=f_title, fill=(0, 0, 0))
    if subtitle:
        d.text((width // 2 - len(subtitle) * 4, 75), subtitle, font=f_sub, fill=(60, 60, 60))

    # Gridlines if requested
    if draw_grid:
        for y in row_y:
            d.line([(col_x[0], y), (col_x[-1], y)], fill=(120, 120, 120), width=2)
        for x in col_x:
            d.line([(x, row_y[0]), (x, row_y[-1])], fill=(120, 120, 120), width=2)

    # Sub-headers (multi-tier merged)
    if sub_headers:
        for sh_txt, sx, ex in sub_headers:
            d.text((sx + 10, row_y[0] - 30), sh_txt, font=f_head, fill=(0, 0, 0))
            d.line([(sx, row_y[0] - 5), (ex, row_y[0] - 5)], fill=(100, 100, 100), width=1)

    # Headers
    for c_idx, h in enumerate(headers):
        if c_idx < len(col_x) - 1:
            d.text((col_x[c_idx] + 10, row_y[0] + 10), h, font=f_head, fill=(0, 0, 0))

    # Rows
    for r_idx, r in enumerate(rows_data):
        if r_idx + 1 < len(row_y):
            y = row_y[r_idx + 1] + 8
            for c_idx, val in enumerate(r):
                if c_idx < len(col_x) - 1 and val:
                    # Multi-line wrap handling
                    lines = str(val).split("\n")
                    curr_y = y
                    for line in lines:
                        d.text((col_x[c_idx] + 10, curr_y), line, font=f_body, fill=(10, 10, 10))
                        curr_y += font_scale + 4

    if is_noise:
        # Add slight gaussian blur and contrast degradation
        img = img.filter(ImageFilter.GaussianBlur(radius=0.7))

    out_path = TABLES_DIR / filename
    img.save(out_path, format="PNG")
    return out_path


def build_corpus():
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    manifest: Dict[str, Any] = {
        "benchmark_name": "Loop 20 Generalization and Verification Reliability Benchmark",
        "total_documents": 34,
        "cohorts": {
            "A_development": 8,
            "B_validation": 8,
            "C_blind_evaluation": 10,
            "D_challenge_adversarial": 8,
        },
        "documents": {},
    }

    print("Building Loop 20 Corpus across Cohorts A, B, C, D...")

    # =========================================================================
    # COHORT A: DEVELOPMENT (8 Documents)
    # =========================================================================
    dev_specs = [
        {
            "id": "DEV_01_ACCOUNTING_INVOICE",
            "title": "ODISHA STATE HANDICRAFTS SUPPLY INVOICE",
            "subtitle": "Tax Invoice Ref: INV-2026-7811 | Date: 14/03/2026",
            "headers": ["Item Code", "Description", "HSN", "Qty", "Rate (INR)", "Total (INR)"],
            "rows": [
                ["ITM-01", "Dhokra Brass Artwork", "8306", "10", "4500", "45000"],
                ["ITM-02", "Pattachitra Silk Scroll", "9701", "5", "8200", "41000"],
                ["ITM-03", "Terracotta Temple Bell", "6913", "20", "1200", "24000"],
                ["Total", "Grand Invoice Total", "", "35", "", "110000"],
            ],
            "col_x": [60, 180, 480, 580, 670, 800, 940],
            "row_y": [130, 180, 240, 300, 360, 420],
            "critical_fields": [
                {"name": "invoice_total", "expected": "110000", "row": 3, "col": 5, "type": "amount", "target_pattern": "Grand Invoice Total"},
                {"name": "pattachitra_subtotal", "expected": "41000", "row": 1, "col": 5, "type": "amount", "target_pattern": "Pattachitra Silk Scroll"},
            ],
        },
        {
            "id": "DEV_02_ACADEMIC_MARKSHEET",
            "title": "BOARD OF SECONDARY EDUCATION EXAMINATION",
            "subtitle": "Annual High School Certificate Examination - 2026",
            "headers": ["Sub Code", "Subject Name", "Max Marks", "Theory", "Practical", "Total"],
            "rows": [
                ["101", "First Language English", "100", "78", "-", "78"],
                ["102", "Second Language Hindi", "100", "84", "-", "84"],
                ["103", "Mathematics", "100", "68", "25", "93"],
                ["104", "General Science", "100", "64", "24", "88"],
                ["Total", "Aggregate Marks", "400", "294", "49", "343"],
            ],
            "col_x": [70, 180, 460, 580, 680, 800, 930],
            "row_y": [130, 180, 240, 300, 360, 420, 480],
            "critical_fields": [
                {"name": "maths_total", "expected": "93", "row": 2, "col": 5, "type": "marks", "target_pattern": "Mathematics"},
                {"name": "aggregate_total", "expected": "343", "row": 4, "col": 5, "type": "marks", "target_pattern": "Aggregate Marks"},
            ],
        },
        {
            "id": "DEV_03_GOVT_PENSION_ORDER",
            "title": "DISTRICT TREASURY PENSION DISBURSEMENT ORDER",
            "subtitle": "Treasury Code: TR-ORI-2026 | Financial Year: 2025-2026",
            "headers": ["PPO Number", "Beneficiary Name", "Basic Pay", "Dearness", "Medical", "Net Payable"],
            "rows": [
                ["PPO-90124", "Satyanarayan Mishra", "32500", "16250", "1000", "49750"],
                ["PPO-90125", "Brundaban Pradhan", "28400", "14200", "1000", "43600"],
                ["PPO-90126", "Subhadra Nayak", "35100", "17550", "1000", "53650"],
            ],
            "col_x": [60, 200, 460, 580, 700, 810, 940],
            "row_y": [130, 180, 240, 300, 360],
            "critical_fields": [
                {"name": "mishra_net", "expected": "49750", "row": 0, "col": 5, "type": "amount", "target_pattern": "Satyanarayan Mishra"},
                {"name": "nayak_basic", "expected": "35100", "row": 2, "col": 2, "type": "amount", "target_pattern": "Subhadra Nayak"},
            ],
        },
        {
            "id": "DEV_04_LAND_KHATAUNI_RECORD",
            "title": "REVENUE TEHSIL LAND RECORD - KHATAUNI",
            "subtitle": "Tehsil: Jatni | Mauza: Kantabada | Khata No: 418",
            "headers": ["Plot No", "Khasra Code", "Classification", "Area (Acres)", "Land Cess", "Total Tax"],
            "rows": [
                ["PLOT-101", "KH-4011", "Homestead Class I", "0.24", "120", "480"],
                ["PLOT-102", "KH-4012", "Irrigated Agriculture", "1.85", "450", "1800"],
                ["PLOT-103", "KH-4013", "Orchard Garden", "0.60", "200", "750"],
            ],
            "col_x": [60, 190, 350, 580, 710, 820, 940],
            "row_y": [130, 180, 240, 300, 360],
            "critical_fields": [
                {"name": "agri_tax", "expected": "1800", "row": 1, "col": 5, "type": "amount", "target_pattern": "Irrigated Agriculture"},
                {"name": "orchard_area", "expected": "0.60", "row": 2, "col": 3, "type": "area", "target_pattern": "Orchard Garden"},
            ],
        },
        {
            "id": "DEV_05_EMPLOYMENT_CERTIFICATE",
            "title": "MUNICIPAL CORPORATION SERVICE REGISTER",
            "subtitle": "Employee Service Record & Cadre Progression",
            "headers": ["Emp Code", "Cadre Post", "Appointment", "Confirmation", "Scale Band"],
            "rows": [
                ["EMP-771", "Junior Engineer (Civil)", "12/06/2018", "12/06/2020", "Level 10"],
                ["EMP-772", "Assistant Town Planner", "01/09/2019", "01/09/2021", "Level 12"],
                ["EMP-773", "Sanitary Inspector", "15/02/2021", "15/02/2023", "Level 08"],
            ],
            "col_x": [70, 200, 460, 620, 780, 930],
            "row_y": [130, 180, 240, 300, 360],
            "critical_fields": [
                {"name": "planner_confirm_date", "expected": "01/09/2021", "row": 1, "col": 3, "type": "date", "target_pattern": "Assistant Town Planner"},
                {"name": "inspector_scale", "expected": "Level 08", "row": 2, "col": 4, "type": "id", "target_pattern": "Sanitary Inspector"},
            ],
        },
        {
            "id": "DEV_06_RECEIPT_VOUCHER",
            "title": "URBAN LOCAL BODY RECEIPT VOUCHER",
            "subtitle": "Bhubaneswar Development Authority - Fee Schedule",
            "headers": ["Voucher ID", "Account Head", "Payment Mode", "Bank Ref", "Amount (INR)"],
            "rows": [
                ["VOU-101", "Plan Scrutiny Fee", "RTGS", "SBI-RTGS-8910", "15400"],
                ["VOU-102", "External Dev Charges", "NEFT", "HDFC-N-4412", "185000"],
                ["VOU-103", "Solid Waste Levy", "UPI", "UPI-881249", "2500"],
                ["Total", "Three Items Cleared", "", "BATCH-ALL", "202900"],
            ],
            "col_x": [70, 210, 450, 600, 780, 930],
            "row_y": [130, 180, 240, 300, 360, 420],
            "critical_fields": [
                {"name": "dev_charges_amount", "expected": "185000", "row": 1, "col": 4, "type": "amount", "target_pattern": "External Dev Charges"},
                {"name": "cleared_total", "expected": "202900", "row": 3, "col": 4, "type": "amount", "target_pattern": "Three Items Cleared"},
            ],
        },
        {
            "id": "DEV_07_ADMINISTRATIVE_CIRCULAR",
            "title": "GOVERNMENT RECRUITMENT NOTIFICATION ROSTER",
            "subtitle": "Post Quota Distribution - General Admin Department",
            "headers": ["Post Code", "Cadre Name", "Total Posts", "Unreserved", "SEBC", "SC/ST"],
            "rows": [
                ["POST-01", "Statistical Field Surveyor", "120", "60", "32", "28"],
                ["POST-02", "Sub-Inspector of Police", "85", "42", "23", "20"],
                ["POST-03", "Revenue Inspector", "64", "32", "18", "14"],
            ],
            "col_x": [70, 190, 460, 600, 720, 830, 930],
            "row_y": [130, 180, 240, 300, 360],
            "critical_fields": [
                {"name": "surveyor_total", "expected": "120", "row": 0, "col": 2, "type": "count", "target_pattern": "Statistical Field Surveyor"},
                {"name": "police_sebc", "expected": "23", "row": 1, "col": 4, "type": "count", "target_pattern": "Sub-Inspector of Police"},
            ],
        },
        {
            "id": "DEV_08_MEDICAL_BILL",
            "title": "CAPITAL HOSPITAL INPATIENT DISCHARGE BILL",
            "subtitle": "Billing Dept: Ward 4B | Patient ID: IPD-2026-992",
            "headers": ["Sl No", "Charge Description", "Days / Units", "Unit Price", "Net Amount"],
            "rows": [
                ["1", "ICU Monitoring Bed Charges", "4", "3500", "14000"],
                ["2", "Surgical Pathology Workup", "1", "4800", "4800"],
                ["3", "Essential Medicines Formulary", "1", "12450", "12450"],
                ["4", "Physiotherapy Rehabilitation", "3", "800", "2400"],
                ["Total", "Total Medical Bill Payable", "9", "", "33650"],
            ],
            "col_x": [70, 150, 480, 630, 770, 930],
            "row_y": [130, 180, 240, 300, 360, 420, 480],
            "critical_fields": [
                {"name": "medicines_amount", "expected": "12450", "row": 2, "col": 4, "type": "amount", "target_pattern": "Essential Medicines Formulary"},
                {"name": "bill_total", "expected": "33650", "row": 4, "col": 4, "type": "amount", "target_pattern": "Total Medical Bill Payable"},
            ],
        },
    ]

    for spec in dev_specs:
        p = render_table_doc(
            filename=f"{spec['id']}.png",
            title=spec["title"],
            subtitle=spec["subtitle"],
            headers=spec["headers"],
            rows_data=spec["rows"],
            col_x=spec["col_x"],
            row_y=spec["row_y"],
            draw_grid=True,
        )
        cf_path = TABLES_DIR / f"{spec['id']}_cf.json"
        with open(cf_path, "w", encoding="utf-8") as f:
            json.dump(spec["critical_fields"], f, indent=2)
        manifest["documents"][spec["id"]] = {
            "cohort": "A_development",
            "category": "Standard Tabular",
            "sha256": sha256_file(p),
            "critical_fields_count": len(spec["critical_fields"]),
            "critical_fields": spec["critical_fields"],
        }

    # =========================================================================
    # COHORT B: VALIDATION (8 Documents)
    # =========================================================================
    val_specs = [
        {
            "id": "VAL_01_WRAPPED_LINE_ITEMS",
            "title": "PANCHAYAT INFRASTRUCTURE PROCUREMENT",
            "subtitle": "Work Order Schedule - Gram Panchayat Development",
            "headers": ["Item", "Specification & Details", "Vendor Code", "Total Budget"],
            "rows": [
                ["01", "Submersible Water Pump\nThree Phase 5HP\nISI Standard Certified", "VND-401", "48500"],
                ["02", "Concrete Paving Tiles\nHeavy Duty M-40 Grade\nCoverage 500 Sq Meters", "VND-402", "125000"],
                ["03", "LED Flood Lights\n100W Solar Integrated\nMounting Brackets Included", "VND-403", "36000"],
            ],
            "col_x": [70, 160, 580, 750, 930],
            "row_y": [130, 180, 260, 340, 420],
            "critical_fields": [
                {"name": "tiles_budget", "expected": "125000", "row": 1, "col": 3, "type": "amount", "target_pattern": "Concrete Paving Tiles"},
                {"name": "pump_vendor", "expected": "VND-401", "row": 0, "col": 2, "type": "id", "target_pattern": "Submersible Water Pump"},
            ],
        },
        {
            "id": "VAL_02_DENSE_LEDGER",
            "title": "DISTRICT COOPERATIVE BANK FISCAL LEDGER",
            "subtitle": "Branch Code: DCB-041 | Date of Audit: 28/02/2026",
            "headers": ["Account No", "Customer Name", "Opening (INR)", "Debit (INR)", "Credit (INR)", "Closing (INR)"],
            "rows": [
                ["AC-400192", "Pabitra Mohan Das", "85000", "12000", "25000", "98000"],
                ["AC-400193", "Mamata Manjari Sahoo", "142000", "35000", "10000", "117000"],
                ["AC-400194", "Dhirendra Nath Ray", "64000", "8000", "14000", "70000"],
            ],
            "col_x": [50, 180, 400, 540, 680, 810, 950],
            "row_y": [130, 180, 240, 300, 360],
            "critical_fields": [
                {"name": "sahoo_closing", "expected": "117000", "row": 1, "col": 5, "type": "amount", "target_pattern": "Mamata Manjari Sahoo"},
                {"name": "das_credit", "expected": "25000", "row": 0, "col": 4, "type": "amount", "target_pattern": "Pabitra Mohan Das"},
            ],
        },
        {
            "id": "VAL_03_BORDERLESS_PAYSLIP",
            "title": "ODISHA POWER TRANSMISSION CORPORATION",
            "subtitle": "Monthly Salary Slip - February 2026",
            "headers": ["Pay Component", "Earnings (INR)", "Deductions", "Amount (INR)"],
            "rows": [
                ["Basic Salary", "54200", "Provident Fund", "6500"],
                ["Dearness Allowance", "27100", "Professional Tax", "250"],
                ["House Rent Allowance", "10840", "Income Tax (TDS)", "8400"],
                ["Gross Earnings", "92140", "Total Deductions", "15150"],
            ],
            "col_x": [80, 280, 520, 720, 920],
            "row_y": [130, 180, 240, 300, 360, 420],
            "draw_grid": False, # Borderless
            "critical_fields": [
                {"name": "gross_earnings", "expected": "92140", "row": 3, "col": 1, "type": "amount", "target_pattern": "Gross Earnings"},
                {"name": "total_deductions", "expected": "15150", "row": 3, "col": 3, "type": "amount", "target_pattern": "Total Deductions"},
            ],
        },
        {
            "id": "VAL_04_MIXED_SCRIPT_BILINGUAL",
            "title": "GRAM PANCHAYAT EXPENDITURE REGISTER",
            "subtitle": "Village Development - Odia / English Bilingual",
            "headers": ["Voucher", "Karya Bibarani / Work", "Manda Code", "Rashi / Amount (INR)"],
            "rows": [
                ["GP-01", "Pani Jala Jojana", "BLK-01", "54000"],
                ["GP-02", "Paka Rasta Nirmana", "BLK-02", "142000"],
                ["GP-03", "Bidyut Deepa Jojana", "BLK-03", "38000"],
            ],
            "col_x": [70, 200, 550, 720, 930],
            "row_y": [130, 180, 240, 300, 360],
            "critical_fields": [
                {"name": "rasta_amount", "expected": "142000", "row": 1, "col": 3, "type": "amount", "target_pattern": "Paka Rasta Nirmana"},
                {"name": "deepa_amount", "expected": "38000", "row": 2, "col": 3, "type": "amount", "target_pattern": "Bidyut Deepa Jojana"},
            ],
        },
        {
            "id": "VAL_05_MULTI_ROW_SUMMARY",
            "title": "QUARTERLY FISCAL BUDGET VARIANCE",
            "subtitle": "Department of Agriculture - Fiscal 2026",
            "headers": ["Scheme Head", "Q1 Budget", "Q1 Actual", "Q2 Budget", "Q2 Actual"],
            "sub_headers": [("Quarter 1 Status", 240, 560), ("Quarter 2 Status", 580, 920)],
            "rows": [
                ["Seed Subsidy", "40000", "38500", "45000", "42000"],
                ["Drip Irrigation", "80000", "76000", "85000", "84500"],
                ["Soil Health Card", "25000", "24000", "28000", "27500"],
            ],
            "col_x": [70, 240, 400, 560, 740, 920],
            "row_y": [150, 200, 260, 320, 380],
            "critical_fields": [
                {"name": "drip_q2_actual", "expected": "84500", "row": 1, "col": 4, "type": "amount", "target_pattern": "Drip Irrigation"},
                {"name": "seed_q1_budget", "expected": "40000", "row": 0, "col": 1, "type": "amount", "target_pattern": "Seed Subsidy"},
            ],
        },
        {
            "id": "VAL_06_PARTIALLY_FILLED_FORM",
            "title": "SOCIAL WELFARE BENEFIT VERIFICATION FORM",
            "subtitle": "Application ID: SW-2026-8819 | Status: Under Scrutiny",
            "headers": ["Field Label", "Primary Applicant", "Joint Applicant", "Remarks"],
            "rows": [
                ["Full Name", "Kishore Chandra Jena", "", "Verified"],
                ["Aadhaar Ref", "XXXX-XXXX-4019", "", "Masked UIDAI"],
                ["BPL Card No", "BPL-ORI-99120", "BPL-ORI-99121", "Family Linked"],
                ["Disability Cert", "", "", "Not Applicable"],
            ],
            "col_x": [70, 260, 520, 750, 930],
            "row_y": [130, 180, 240, 300, 360, 420],
            "critical_fields": [
                {"name": "primary_bpl", "expected": "BPL-ORI-99120", "row": 2, "col": 1, "type": "id", "target_pattern": "BPL Card No"},
                {"name": "joint_name_empty", "expected": "", "row": 0, "col": 2, "type": "empty", "target_pattern": "Full Name"},
            ],
        },
        {
            "id": "VAL_07_TAX_ASSESSMENT_SCHEDULE",
            "title": "MUNICIPAL CORPORATION PROPERTY TAX ASSESSMENT",
            "subtitle": "Holding Tax Demand Schedule - Financial Year 2026",
            "headers": ["Holding No", "Ward", "Property Type", "Annual Value", "Rebate", "Net Due (INR)"],
            "rows": [
                ["HLD-201", "Ward 12", "Residential RCC", "60000", "6000", "5400"],
                ["HLD-202", "Ward 12", "Commercial Complex", "240000", "0", "28800"],
                ["HLD-203", "Ward 14", "Mixed Occupancy", "110000", "11000", "11000"],
            ],
            "col_x": [60, 190, 310, 520, 680, 800, 940],
            "row_y": [130, 180, 240, 300, 360],
            "critical_fields": [
                {"name": "commercial_net_tax", "expected": "28800", "row": 1, "col": 5, "type": "amount", "target_pattern": "Commercial Complex"},
                {"name": "residence_rebate", "expected": "6000", "row": 0, "col": 4, "type": "amount", "target_pattern": "Residential RCC"},
            ],
        },
        {
            "id": "VAL_08_SHADOW_NOISE_SCAN",
            "title": "SECONDARY EDUCATION SCHOLARSHIP AWARDS",
            "subtitle": "Merit List - District Collectorate Verified",
            "headers": ["Roll No", "Scholar Name", "School Affiliation", "Scholarship (INR)"],
            "rows": [
                ["SCH-101", "Alok Kumar Srichandan", "Buxi Jagabandhu Bidyapitha", "15000"],
                ["SCH-102", "Priyanka Priyadarshini", "Government Girls High School", "15000"],
                ["SCH-103", "Soumyaranjan Mohanty", "Capital High School Unit 3", "12000"],
            ],
            "col_x": [70, 210, 460, 750, 930],
            "row_y": [130, 180, 240, 300, 360],
            "is_noise": True, # Simulated degraded photocopy
            "critical_fields": [
                {"name": "alok_amount", "expected": "15000", "row": 0, "col": 3, "type": "amount", "target_pattern": "Alok Kumar Srichandan"},
                {"name": "soumya_amount", "expected": "12000", "row": 2, "col": 3, "type": "amount", "target_pattern": "Soumyaranjan Mohanty"},
            ],
        },
    ]

    for spec in val_specs:
        p = render_table_doc(
            filename=f"{spec['id']}.png",
            title=spec["title"],
            subtitle=spec["subtitle"],
            headers=spec["headers"],
            rows_data=spec["rows"],
            col_x=spec["col_x"],
            row_y=spec["row_y"],
            draw_grid=spec.get("draw_grid", True),
            sub_headers=spec.get("sub_headers"),
            is_noise=spec.get("is_noise", False),
        )
        cf_path = TABLES_DIR / f"{spec['id']}_cf.json"
        with open(cf_path, "w", encoding="utf-8") as f:
            json.dump(spec["critical_fields"], f, indent=2)
        manifest["documents"][spec["id"]] = {
            "cohort": "B_validation",
            "category": "Validation Stress",
            "sha256": sha256_file(p),
            "critical_fields_count": len(spec["critical_fields"]),
            "critical_fields": spec["critical_fields"],
        }

    # =========================================================================
    # COHORT C: BLIND EVALUATION (10 Documents - Strictly Held Out)
    # =========================================================================
    blind_specs = [
        {
            "id": "BLIND_01_SALARY_SLIP",
            "title": "NATIONAL INFRASTRUCTURE VENTURES LTD",
            "subtitle": "Confidential Employee Earnings Record - March 2026",
            "headers": ["Description", "Earnings (INR)", "Deductions", "Amount (INR)"],
            "rows": [
                ["Basic Pay", "68000", "PF Contribution", "8160"],
                ["Special Allowance", "24000", "Gratuity Deduction", "3264"],
                ["Performance Bonus", "15000", "Voluntary PF", "5000"],
                ["Net Pay Disbursed", "107000", "Total Deductions", "16424"],
            ],
            "col_x": [80, 320, 540, 740, 920],
            "row_y": [130, 180, 240, 300, 360, 420],
            "critical_fields": [
                {"name": "net_pay", "expected": "107000", "row": 3, "col": 1, "type": "amount", "target_pattern": "Net Pay Disbursed"},
                {"name": "pf_contrib", "expected": "8160", "row": 0, "col": 3, "type": "amount", "target_pattern": "PF Contribution"},
            ],
        },
        {
            "id": "BLIND_02_CUSTOMS_DECLARATION",
            "title": "PARADIP PORT CUSTOMS CARGO DECLARATION",
            "subtitle": "Bill of Entry: BOE-2026-90412 | Port Code: INPRT1",
            "headers": ["Item", "HS Code", "Declared Goods", "Declared CIF", "Assessable Value", "Duty Payable"],
            "rows": [
                ["01", "847130", "Industrial Controllers", "450000", "454500", "49995"],
                ["02", "850440", "Static Converters 50KW", "820000", "828200", "91102"],
                ["03", "903180", "Optical Inspection Sensors", "280000", "282800", "31108"],
            ],
            "col_x": [50, 140, 260, 520, 670, 810, 950],
            "row_y": [130, 180, 240, 300, 360],
            "critical_fields": [
                {"name": "sensors_duty", "expected": "31108", "row": 2, "col": 5, "type": "amount", "target_pattern": "Optical Inspection Sensors"},
                {"name": "converters_cif", "expected": "820000", "row": 1, "col": 3, "type": "amount", "target_pattern": "Static Converters 50KW"},
            ],
        },
        {
            "id": "BLIND_03_UTILITY_ELECTRICITY_BILL",
            "title": "TP CENTRAL ODISHA DISTRIBUTION LIMITED",
            "subtitle": "Electricity Tariff Bill | Consumer No: 04189021",
            "headers": ["Meter No", "Prev Reading", "Curr Reading", "Units Billed", "Tariff Slab", "Payable (INR)"],
            "rows": [
                ["MTR-88120", "14820", "15460", "640", "Commercial 2", "4280"],
                ["Fixed Demand", "10 KW", "Sanctioned", "", "Levy 5%", "550"],
                ["Total Payable", "Due: 25/03/2026", "Net Amount", "", "Discount Eligible", "4830"],
            ],
            "col_x": [60, 190, 340, 480, 620, 790, 940],
            "row_y": [130, 180, 240, 300, 360],
            "critical_fields": [
                {"name": "units_billed", "expected": "640", "row": 0, "col": 3, "type": "count", "target_pattern": "MTR-88120"},
                {"name": "total_bill_due", "expected": "4830", "row": 2, "col": 5, "type": "amount", "target_pattern": "Total Payable"},
            ],
        },
        {
            "id": "BLIND_04_MUNICIPAL_HOLDING_TAX",
            "title": "CUTTACK MUNICIPAL CORPORATION NOTICE",
            "subtitle": "Annual Holding Tax Notice | Holding No: CMC-2026-118",
            "headers": ["Demand Head", "Arrears", "Current Year", "Total Due", "Rebate 10%", "Net Payable"],
            "rows": [
                ["Holding Tax", "1200", "3600", "4800", "360", "4440"],
                ["Lighting Tax", "0", "900", "900", "90", "810"],
                ["Drainage Cess", "400", "1200", "1600", "120", "1480"],
                ["Grand Total", "1600", "5700", "7300", "570", "6730"],
            ],
            "col_x": [60, 220, 360, 500, 640, 780, 940],
            "row_y": [130, 180, 240, 300, 360, 420],
            "critical_fields": [
                {"name": "drainage_net", "expected": "1480", "row": 2, "col": 5, "type": "amount", "target_pattern": "Drainage Cess"},
                {"name": "grand_net_tax", "expected": "6730", "row": 3, "col": 5, "type": "amount", "target_pattern": "Grand Total"},
            ],
        },
        {
            "id": "BLIND_05_BANK_ACCOUNT_STATEMENT",
            "title": "STATE BANK OF INDIA SAVINGS ACCOUNT",
            "subtitle": "Statement of Account: 2011004819 | Period: Feb 2026",
            "headers": ["Txn Date", "Details", "Ref Number", "Debit (INR)", "Credit (INR)", "Balance (INR)"],
            "rows": [
                ["02/02/2026", "Salary Disbursed", "SAL-OPTCL-99", "-", "64200", "128400"],
                ["08/02/2026", "House Loan EMI", "HL-SBI-4410", "28400", "-", "100000"],
                ["15/02/2026", "Dividend Mutual Fund", "DIV-UTI-12", "-", "8500", "108500"],
            ],
            "col_x": [50, 180, 380, 540, 670, 800, 950],
            "row_y": [130, 180, 240, 300, 360],
            "critical_fields": [
                {"name": "emi_debit", "expected": "28400", "row": 1, "col": 3, "type": "amount", "target_pattern": "House Loan EMI"},
                {"name": "dividend_credit", "expected": "8500", "row": 2, "col": 4, "type": "amount", "target_pattern": "Dividend Mutual Fund"},
            ],
        },
        {
            "id": "BLIND_06_CLINICAL_LAB_REPORT",
            "title": "AIIMS BHUBANESWAR CLINICAL BIOCHEMISTRY",
            "subtitle": "Comprehensive Metabolic Profile | Patient: IPD-8812",
            "headers": ["Investigation", "Result Value", "Unit", "Biological Reference", "Status Flag"],
            "rows": [
                ["Fasting Blood Glucose", "98", "mg/dL", "70 - 100", "NORMAL"],
                ["Serum Creatinine", "1.1", "mg/dL", "0.7 - 1.2", "NORMAL"],
                ["Serum Bilirubin Total", "0.9", "mg/dL", "0.2 - 1.0", "NORMAL"],
                ["Glycated Hemoglobin", "5.6", "%", "4.0 - 5.6", "OPTIMAL"],
            ],
            "col_x": [60, 320, 480, 600, 800, 940],
            "row_y": [130, 180, 240, 300, 360, 420],
            "critical_fields": [
                {"name": "glucose_result", "expected": "98", "row": 0, "col": 1, "type": "count", "target_pattern": "Fasting Blood Glucose"},
                {"name": "hba1c_result", "expected": "5.6", "row": 3, "col": 1, "type": "count", "target_pattern": "Glycated Hemoglobin"},
            ],
        },
        {
            "id": "BLIND_07_PUBLIC_DISTRIBUTION_RATION",
            "title": "ODISHA STATE FOOD SUPPLIES & CONSUMER WELFARE",
            "subtitle": "Fair Price Shop Allocation | Ration Card: AAY-ORI-441",
            "headers": ["Commodity", "Monthly Entitlement", "Rate per Kg", "Issued Qty", "Balance Due"],
            "rows": [
                ["Fortified Rice", "35 Kg", "Free of Cost", "35 Kg", "0 Kg"],
                ["Whole Wheat", "10 Kg", "Rs. 2.00", "10 Kg", "0 Kg"],
                ["Refined Sugar", "2 Kg", "Rs. 13.50", "2 Kg", "0 Kg"],
            ],
            "col_x": [60, 240, 480, 660, 800, 940],
            "row_y": [130, 180, 240, 300, 360],
            "critical_fields": [
                {"name": "sugar_rate", "expected": "13.50", "row": 2, "col": 2, "type": "amount", "target_pattern": "Refined Sugar"},
                {"name": "rice_quota", "expected": "35 Kg", "row": 0, "col": 1, "type": "weight", "target_pattern": "Fortified Rice"},
            ],
        },
        {
            "id": "BLIND_08_UNIVERSITY_SEMESTER_TRANSCRIPT",
            "title": "BIJU PATNAIK UNIVERSITY OF TECHNOLOGY",
            "subtitle": "B.Tech Computer Science Semester VI Grade Card",
            "headers": ["Course Code", "Course Title", "Credits", "Letter Grade", "Grade Point"],
            "rows": [
                ["CS-601", "Compiler Design", "4", "A", "9"],
                ["CS-602", "Computer Networks", "4", "O", "10"],
                ["CS-603", "Software Engineering", "3", "A", "9"],
                ["CS-604", "Machine Learning Lab", "2", "O", "10"],
            ],
            "col_x": [70, 200, 540, 670, 810, 930],
            "row_y": [130, 180, 240, 300, 360, 420],
            "critical_fields": [
                {"name": "networks_grade", "expected": "O", "row": 1, "col": 3, "type": "grade", "target_pattern": "Computer Networks"},
                {"name": "compiler_credits", "expected": "4", "row": 0, "col": 2, "type": "count", "target_pattern": "Compiler Design"},
            ],
        },
        {
            "id": "BLIND_09_TRANSPORT_FREIGHT_MANIFEST",
            "title": "EAST COAST LOGISTICS & FREIGHT CARRIERS",
            "subtitle": "Lorry Receipt Manifest: LR-2026-88019 | Fleet: OD-02-X-9941",
            "headers": ["Consignment No", "Consignee", "Packages", "Weight (MT)", "Freight (INR)", "Status"],
            "rows": [
                ["CN-9011", "Jindal Steel Works", "48", "18.5", "54000", "Delivered"],
                ["CN-9012", "Vedanta Aluminium", "32", "12.0", "38000", "In Transit"],
                ["CN-9013", "Tata Sponge Iron", "60", "22.0", "66000", "Delivered"],
            ],
            "col_x": [60, 210, 440, 560, 700, 830, 940],
            "row_y": [130, 180, 240, 300, 360],
            "critical_fields": [
                {"name": "vedanta_freight", "expected": "38000", "row": 1, "col": 4, "type": "amount", "target_pattern": "Vedanta Aluminium"},
                {"name": "jindal_weight", "expected": "18.5", "row": 0, "col": 3, "type": "weight", "target_pattern": "Jindal Steel Works"},
            ],
        },
        {
            "id": "BLIND_10_COURT_FEE_REGISTRY",
            "title": "ORISSA HIGH COURT REGISTER OF PETITIONS",
            "subtitle": "Writ Petition Civil Register | Bench Registry Record",
            "headers": ["Case Number", "Petitioner Name", "Respondent", "Stamp Fee", "Hearing Date"],
            "rows": [
                ["WPC-4180/2026", "Subrat Kumar Panda", "State of Odisha", "500", "18/04/2026"],
                ["WPC-4181/2026", "Minati Sahoo", "Bhubaneswar Municipal", "500", "21/04/2026"],
                ["WPC-4182/2026", "Kalinga Transporters", "Transport Commissioner", "1000", "24/04/2026"],
            ],
            "col_x": [60, 220, 440, 670, 790, 940],
            "row_y": [130, 180, 240, 300, 360],
            "critical_fields": [
                {"name": "panda_hearing", "expected": "18/04/2026", "row": 0, "col": 4, "type": "date", "target_pattern": "Subrat Kumar Panda"},
                {"name": "kalinga_fee", "expected": "1000", "row": 2, "col": 3, "type": "amount", "target_pattern": "Kalinga Transporters"},
            ],
        },
    ]

    for spec in blind_specs:
        p = render_table_doc(
            filename=f"{spec['id']}.png",
            title=spec["title"],
            subtitle=spec["subtitle"],
            headers=spec["headers"],
            rows_data=spec["rows"],
            col_x=spec["col_x"],
            row_y=spec["row_y"],
            draw_grid=True,
        )
        cf_path = TABLES_DIR / f"{spec['id']}_cf.json"
        with open(cf_path, "w", encoding="utf-8") as f:
            json.dump(spec["critical_fields"], f, indent=2)
        manifest["documents"][spec["id"]] = {
            "cohort": "C_blind_evaluation",
            "category": "Blind Unseen Layout",
            "sha256": sha256_file(p),
            "critical_fields_count": len(spec["critical_fields"]),
            "critical_fields": spec["critical_fields"],
        }

    # =========================================================================
    # COHORT D: CHALLENGE & ADVERSARIAL (8 Documents)
    # =========================================================================
    chall_specs = [
        {
            "id": "CHALL_01_IDENTICAL_AMOUNT_DIFF_COLUMNS",
            "title": "ADVERSARIAL CONTRADICTION AUDIT SCHEDULE",
            "subtitle": "Voucher Settlement: ₹25000 in Advance and Penalty",
            "headers": ["Vendor Ref", "Advance Paid (INR)", "Work Cleared (INR)", "Penalty Levy (INR)", "Net Release (INR)"],
            "rows": [
                ["VND-881", "25000", "120000", "25000", "70000"],
                ["VND-882", "15000", "80000", "5000", "60000"],
            ],
            "col_x": [60, 220, 420, 600, 780, 940],
            "row_y": [130, 180, 240, 300],
            "critical_fields": [
                {"name": "penalty_levy_881", "expected": "25000", "row": 0, "col": 3, "type": "amount", "target_pattern": "VND-881", "is_trap": True, "trap_note": "Advance Paid is also 25000"},
                {"name": "advance_paid_881", "expected": "25000", "row": 0, "col": 1, "type": "amount", "target_pattern": "VND-881", "is_trap": True, "trap_note": "Penalty Levy is also 25000"},
            ],
        },
        {
            "id": "CHALL_02_WRONG_PERSON_ADJACENT_ROWS",
            "title": "DISTRICT ROSTER CANDIDATE MERIT SCHEDULE",
            "subtitle": "Similar Names in Consecutive Rows Trap",
            "headers": ["Candidate Name", "Roll Code", "Written Score", "Interview Score", "Rank Status"],
            "rows": [
                ["Ramesh Kumar Sahoo", "ROL-101", "92", "24", "QUALIFIED"],
                ["Ramesh Chand Sahoo", "ROL-102", "45", "12", "REJECTED"],
            ],
            "col_x": [60, 300, 460, 620, 780, 940],
            "row_y": [130, 180, 240, 300],
            "critical_fields": [
                {"name": "ramesh_kumar_score", "expected": "92", "row": 0, "col": 2, "type": "marks", "target_pattern": "Ramesh Kumar Sahoo"},
                {"name": "ramesh_chand_score", "expected": "45", "row": 1, "col": 2, "type": "marks", "target_pattern": "Ramesh Chand Sahoo"},
            ],
        },
        {
            "id": "CHALL_03_FAINT_COLUMN_BLEED",
            "title": "TIGHT COLUMN PACKING LEDGER",
            "subtitle": "Narrow Gutter (12px) - Bounding Box Bleed Stress",
            "headers": ["Ref", "Qty", "Rate", "Gross", "Tax", "Net"],
            "rows": [
                ["R1", "10", "400", "4000", "720", "4720"],
                ["R2", "20", "800", "16000", "2880", "18880"],
            ],
            "col_x": [70, 160, 260, 400, 560, 720, 880],
            "row_y": [130, 180, 240, 300],
            "critical_fields": [
                {"name": "r1_gross", "expected": "4000", "row": 0, "col": 3, "type": "amount", "target_pattern": "R1"},
                {"name": "r1_tax", "expected": "720", "row": 0, "col": 4, "type": "amount", "target_pattern": "R1"},
            ],
        },
        {
            "id": "CHALL_04_REPEATED_ACCOUNT_NUMBERS",
            "title": "REPEATED IDENTIFIER TRANSACTION LOG",
            "subtitle": "Identical Account AC-99881 in Multiple Rows",
            "headers": ["Account No", "Transaction ID", "Txn Type", "Amount (INR)", "Date Stamp"],
            "rows": [
                ["AC-99881", "TXN-001", "DEPOSIT", "10000", "01/03/2026"],
                ["AC-99881", "TXN-002", "WITHDRAWAL", "4000", "05/03/2026"],
                ["AC-99881", "TXN-003", "TRANSFER", "8500", "10/03/2026"],
            ],
            "col_x": [60, 220, 400, 560, 740, 940],
            "row_y": [130, 180, 240, 300, 360],
            "critical_fields": [
                {"name": "txn_002_amount", "expected": "4000", "row": 1, "col": 3, "type": "amount", "target_pattern": "TXN-002"},
                {"name": "txn_003_date", "expected": "10/03/2026", "row": 2, "col": 4, "type": "date", "target_pattern": "TXN-003"},
            ],
        },
        {
            "id": "CHALL_05_EMPTY_AMOUNT_CELL",
            "title": "SPARSE DEMAND SCHEDULE WITH BLANK ARREARS",
            "subtitle": "Testing Value Inheritance Trap on Empty Cells",
            "headers": ["Holding Ref", "Arrears (INR)", "Current Demand (INR)", "Cess (INR)", "Net Payable (INR)"],
            "rows": [
                ["HOLD-401", "", "15000", "1500", "16500"],
                ["HOLD-402", "4500", "12000", "1200", "17700"],
            ],
            "col_x": [60, 220, 400, 600, 760, 940],
            "row_y": [130, 180, 240, 300],
            "critical_fields": [
                {"name": "hold_401_arrears", "expected": "", "row": 0, "col": 1, "type": "empty", "target_pattern": "HOLD-401", "is_trap": True, "trap_note": "Empty cell must not inherit 15000"},
                {"name": "hold_401_current", "expected": "15000", "row": 0, "col": 2, "type": "amount", "target_pattern": "HOLD-401"},
            ],
        },
        {
            "id": "CHALL_06_LABEL_AS_VALUE_TRAP",
            "title": "APPLICATION FORM WITH MISSING DATES",
            "subtitle": "Column Header Directly Above Blank Cell Trap",
            "headers": ["Applicant ID", "Form Date", "Verification Date", "Approval Stamp"],
            "rows": [
                ["APP-901", "12/01/2026", "", "PENDING"],
            ],
            "col_x": [70, 240, 460, 680, 930],
            "row_y": [130, 180, 250],
            "critical_fields": [
                {"name": "app_901_verification_date", "expected": "", "row": 0, "col": 2, "type": "empty", "target_pattern": "APP-901", "is_trap": True, "trap_note": "Blank cell under Verification Date must not return 'Verification Date'"},
            ],
        },
        {
            "id": "CHALL_07_CROSS_DOC_PAIR_A",
            "title": "CENTRAL WAREHOUSING INVOICE (ORIGINAL)",
            "subtitle": "Invoice Ref: INV-2026-904 | Dispatched: 12/04/2026",
            "headers": ["Item Ref", "Material", "Batch Code", "Sanction Amount (INR)"],
            "rows": [
                ["MAT-01", "Portland Slag Cement", "BAT-881", "75400"],
                ["MAT-02", "Structural Steel TMT", "BAT-882", "124000"],
            ],
            "col_x": [70, 220, 520, 720, 930],
            "row_y": [130, 180, 240, 300],
            "critical_fields": [
                {"name": "cement_sanction_a", "expected": "75400", "row": 0, "col": 3, "type": "amount", "target_pattern": "Portland Slag Cement"},
            ],
        },
        {
            "id": "CHALL_08_CROSS_DOC_PAIR_B",
            "title": "DISTRICT SITE RECEIPT VOUCHER (MISMATCH)",
            "subtitle": "Verification against Invoice Ref: INV-2026-904",
            "headers": ["Item Ref", "Material", "Batch Code", "Site Claim Amount (INR)"],
            "rows": [
                ["MAT-01", "Portland Slag Cement", "BAT-881", "78400"], # DELIBERATE CONFLICT: 78400 vs 75400
                ["MAT-02", "Structural Steel TMT", "BAT-882", "124000"],
            ],
            "col_x": [70, 220, 520, 720, 930],
            "row_y": [130, 180, 240, 300],
            "critical_fields": [
                {"name": "cement_claim_b", "expected": "78400", "row": 0, "col": 3, "type": "amount", "target_pattern": "Portland Slag Cement", "is_cross_conflict": True, "pair_doc": "CHALL_07_CROSS_DOC_PAIR_A", "pair_expected": "75400"},
            ],
        },
    ]

    for spec in chall_specs:
        p = render_table_doc(
            filename=f"{spec['id']}.png",
            title=spec["title"],
            subtitle=spec["subtitle"],
            headers=spec["headers"],
            rows_data=spec["rows"],
            col_x=spec["col_x"],
            row_y=spec["row_y"],
            draw_grid=True,
        )
        cf_path = TABLES_DIR / f"{spec['id']}_cf.json"
        with open(cf_path, "w", encoding="utf-8") as f:
            json.dump(spec["critical_fields"], f, indent=2)
        manifest["documents"][spec["id"]] = {
            "cohort": "D_challenge_adversarial",
            "category": "Adversarial Trap",
            "sha256": sha256_file(p),
            "critical_fields_count": len(spec["critical_fields"]),
            "critical_fields": spec["critical_fields"],
        }

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"Loop 20 Corpus generated: 34 documents saved to {TABLES_DIR}")
    print(f"Manifest written to {MANIFEST_PATH}")


if __name__ == "__main__":
    build_corpus()
