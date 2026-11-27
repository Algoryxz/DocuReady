"""
Loop 19 - Table Association Benchmark Fixture Builder
DocuReady Engineering Research

Generates 10 controlled benchmark fixtures across categories A through J:
  - TAB_01_SIMPLE_GRID (Category A: Clean bordered table with numeric amounts)
  - TAB_02_BORDERLESS_TABLE (Category B: Alignment and whitespace only)
  - TAB_03_DENSE_NUMERIC_COLUMNS (Category C: Multi-column ledger with fiscal totals)
  - TAB_04_SIMILAR_ADJACENT_VALUES (Category D: 1000 vs 10000, 0 vs 8, 1 vs 7)
  - TAB_05_WRAPPED_CELLS (Category E: Multi-line wrapped text adjacent to short codes)
  - TAB_06_MISSING_EMPTY_CELLS (Category F: Explicitly empty and missing cells)
  - TAB_07_MERGED_HEADERS (Category G: Hierarchical 2-tier merged column headers)
  - TAB_08_IRREGULAR_LAYOUTS (Category H: Nonuniform row heights and variable widths)
  - TAB_09_MULTICOLUMN_DOCUMENT (Category I: Two-column page layout with embedded tables)
  - TAB_10_ADVERSARIAL_GEOMETRY (Category J: Skewed, noisy scan with faint borders)

Outputs to:
  - research/loop19/tables/ (Images, Ground Truth, Cell Contracts, Critical Fields)
  - research/loop19/dataset_manifest.json
"""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

ROOT = Path(__file__).resolve().parents[2]
TABLES_DIR = ROOT / "research" / "loop19" / "tables"
MANIFEST_PATH = ROOT / "research" / "loop19" / "dataset_manifest.json"


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


def build_table_fixtures():
    TABLES_DIR.mkdir(parents=True, exist_ok=True)
    font_title = get_font(24)
    font_head = get_font(18)
    font_body = get_font(16)
    font_sm = get_font(14)

    samples = []

    # -------------------------------------------------------------
    # 1. TAB_01: SIMPLE GRID (Category A: Clean bordered table)
    # -------------------------------------------------------------
    img = Image.new("RGB", (1000, 1000), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((250, 50), "DISTRICT TREASURY VOUCHER SCHEDULE", font=font_title, fill=(0, 0, 0))

    headers = ["Item No", "Description", "Sanction ID", "Amount (INR)"]
    rows_data = [
        ["01", "Primary Health Supplies", "MED-2026-901", "45000"],
        ["02", "School Uniform Grant", "EDU-2026-442", "128000"],
        ["03", "Rural Road Maintenance", "RUR-2026-781", "340000"],
        ["04", "Solar Street Lighting", "ENG-2026-119", "89500"],
        ["Total", "Four Projects Approved", "SCH-ALL-2026", "602500"],
    ]
    col_x = [80, 200, 520, 750, 920]
    row_y = [120, 170, 230, 290, 350, 410, 470]

    # Draw grid lines
    for y in row_y:
        d.line([(80, y), (920, y)], fill=(80, 80, 80), width=2)
    for x in col_x:
        d.line([(x, 120), (x, 470)], fill=(80, 80, 80), width=2)

    # Draw headers
    for c_idx, h in enumerate(headers):
        d.text((col_x[c_idx] + 15, 135), h, font=font_head, fill=(0, 0, 0))
    # Draw body
    for r_idx, r in enumerate(rows_data):
        y = row_y[r_idx + 1] + 15
        for c_idx, val in enumerate(r):
            d.text((col_x[c_idx] + 15, y), val, font=font_body, fill=(20, 20, 20))

    p = TABLES_DIR / "TAB_01_SIMPLE_GRID.png"
    img.save(p)

    cf_01 = {
        "item_01_amount": "45000",
        "item_03_sanction": "RUR-2026-781",
        "total_amount": "602500"
    }
    with open(TABLES_DIR / "TAB_01_SIMPLE_GRID_cf.json", "w", encoding="utf-8") as f:
        json.dump({"fixture_id": "TAB_01_SIMPLE_GRID", "category": "Category A: Simple Grid", "critical_fields": cf_01}, f, indent=2)

    # -------------------------------------------------------------
    # 2. TAB_02: BORDERLESS TABLE (Category B: Alignment & Whitespace only)
    # -------------------------------------------------------------
    img = Image.new("RGB", (1000, 1000), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((220, 60), "DEPARTMENTAL EXPENDITURE STATEMENT", font=font_title, fill=(0, 0, 0))
    d.text((220, 95), "(BORDERLESS TABULAR ALIGNMENT)", font=font_sm, fill=(80, 80, 80))

    b_headers = ["Code", "Account Head", "Budget Allocation", "Utilized", "Balance"]
    b_rows = [
        ["101", "Administrative Salaries", "5200000", "4800000", "400000"],
        ["102", "Office Infrastructure", "1800000", "1650000", "150000"],
        ["103", "Field Survey Operations", "950000", "890000", "60000"],
        ["104", "Public Information Wing", "420000", "400000", "20000"],
    ]
    b_cols = [80, 180, 480, 680, 840]
    y = 160
    for c_idx, h in enumerate(b_headers):
        d.text((b_cols[c_idx], y), h, font=font_head, fill=(0, 0, 0))
    d.line([(80, y + 35), (940, y + 35)], fill=(150, 150, 150), width=1)

    y = 220
    for r in b_rows:
        for c_idx, val in enumerate(r):
            d.text((b_cols[c_idx], y), val, font=font_body, fill=(30, 30, 30))
        y += 60

    p = TABLES_DIR / "TAB_02_BORDERLESS_TABLE.png"
    img.save(p)

    cf_02 = {
        "admin_balance": "400000",
        "survey_utilized": "890000",
        "info_budget": "420000"
    }
    with open(TABLES_DIR / "TAB_02_BORDERLESS_TABLE_cf.json", "w", encoding="utf-8") as f:
        json.dump({"fixture_id": "TAB_02_BORDERLESS_TABLE", "category": "Category B: Borderless Table", "critical_fields": cf_02}, f, indent=2)

    # -------------------------------------------------------------
    # 3. TAB_03: DENSE NUMERIC COLUMNS (Category C: Multi-column ledger)
    # -------------------------------------------------------------
    img = Image.new("RGB", (1000, 1000), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((200, 50), "FISCAL RECONCILIATION SUMMARY 2026", font=font_title, fill=(0, 0, 0))

    d_headers = ["Month", "Tax Inflow", "Grant Inflow", "Capital Out", "Revenue Out", "Net Surplus"]
    d_rows = [
        ["APR", "845100", "120000", "450000", "310000", "205100"],
        ["MAY", "912400", "150000", "520000", "340000", "202400"],
        ["JUN", "789300", "100000", "410000", "290000", "189300"],
        ["JUL", "865900", "130000", "480000", "325000", "190900"],
    ]
    d_cols = [70, 190, 350, 520, 680, 840]
    y = 130
    for c_idx, h in enumerate(d_headers):
        d.text((d_cols[c_idx], y), h, font=font_head, fill=(0, 0, 0))
    d.line([(70, y + 30), (950, y + 30)], fill=(0, 0, 0), width=2)

    y = 180
    for r in d_rows:
        for c_idx, val in enumerate(r):
            d.text((d_cols[c_idx], y), val, font=font_body, fill=(0, 0, 0))
        y += 50
    d.line([(70, y + 10), (950, y + 10)], fill=(0, 0, 0), width=2)

    p = TABLES_DIR / "TAB_03_DENSE_NUMERIC_COLUMNS.png"
    img.save(p)

    cf_03 = {
        "may_tax_inflow": "912400",
        "jun_revenue_out": "290000",
        "jul_net_surplus": "190900"
    }
    with open(TABLES_DIR / "TAB_03_DENSE_NUMERIC_COLUMNS_cf.json", "w", encoding="utf-8") as f:
        json.dump({"fixture_id": "TAB_03_DENSE_NUMERIC_COLUMNS", "category": "Category C: Dense Numeric", "critical_fields": cf_03}, f, indent=2)

    # -------------------------------------------------------------
    # 4. TAB_04: SIMILAR ADJACENT VALUES (Category D: 1000 vs 10000, 0 vs 8)
    # -------------------------------------------------------------
    img = Image.new("RGB", (1000, 1000), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((220, 50), "SUBSIDY TIER DISBURSEMENT SCHEDULE", font=font_title, fill=(0, 0, 0))

    s_headers = ["Tier Code", "Base Subsidy", "Top-Up Grant", "Final Total", "Beneficiaries"]
    s_rows = [
        ["T-01", "1000", "10000", "11000", "8080"],
        ["T-02", "10000", "1000", "11000", "8880"],
        ["T-03", "1700", "7100", "8800", "1080"],
        ["T-04", "7100", "1700", "8800", "1800"],
    ]
    s_cols = [80, 230, 420, 610, 800]
    y = 140
    for c_idx, h in enumerate(s_headers):
        d.text((s_cols[c_idx], y), h, font=font_head, fill=(0, 0, 0))
    d.line([(80, y + 30), (940, y + 30)], fill=(0, 0, 0), width=1)

    y = 190
    for r in s_rows:
        for c_idx, val in enumerate(r):
            d.text((s_cols[c_idx], y), val, font=font_body, fill=(0, 0, 0))
        y += 55

    p = TABLES_DIR / "TAB_04_SIMILAR_ADJACENT_VALUES.png"
    img.save(p)

    cf_04 = {
        "tier_01_topup": "10000",
        "tier_02_base": "10000",
        "tier_03_beneficiaries": "1080",
        "tier_04_beneficiaries": "1800"
    }
    with open(TABLES_DIR / "TAB_04_SIMILAR_ADJACENT_VALUES_cf.json", "w", encoding="utf-8") as f:
        json.dump({"fixture_id": "TAB_04_SIMILAR_ADJACENT_VALUES", "category": "Category D: Similar Adjacent", "critical_fields": cf_04}, f, indent=2)

    # -------------------------------------------------------------
    # 5. TAB_05: WRAPPED CELLS (Category E: Multi-line text inside cell)
    # -------------------------------------------------------------
    img = Image.new("RGB", (1000, 1000), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((240, 50), "PUBLIC PROCUREMENT AUDIT REGISTER", font=font_title, fill=(0, 0, 0))

    w_headers = ["Procurement ID", "Specification Scope", "Vendor", "Total Value"]
    w_rows = [
        ["PR-2026-110", "Supply of automated digital medical monitors\nand emergency mobile power backups", "Apex Lifecare", "4200000"],
        ["PR-2026-114", "Installation of fiber optic network cables\nconnecting district administrative hubs", "Netcom Infra", "8900000"],
        ["PR-2026-118", "Annual maintenance and calibration contract\nfor laboratory equipment units", "Precision Lab", "1450000"],
    ]
    w_cols = [70, 240, 680, 840]
    y = 130
    for c_idx, h in enumerate(w_headers):
        d.text((w_cols[c_idx], y), h, font=font_head, fill=(0, 0, 0))
    d.line([(70, y + 30), (940, y + 30)], fill=(0, 0, 0), width=2)

    y = 180
    for r in w_rows:
        d.text((w_cols[0], y), r[0], font=font_body, fill=(0, 0, 0))
        d.text((w_cols[1], y), r[1], font=font_body, fill=(0, 0, 0))
        d.text((w_cols[2], y), r[2], font=font_body, fill=(0, 0, 0))
        d.text((w_cols[3], y), r[3], font=font_body, fill=(0, 0, 0))
        y += 80
        d.line([(70, y - 10), (940, y - 10)], fill=(200, 200, 200), width=1)

    p = TABLES_DIR / "TAB_05_WRAPPED_CELLS.png"
    img.save(p)

    cf_05 = {
        "pr_110_value": "4200000",
        "pr_114_vendor": "Netcom Infra",
        "pr_118_value": "1450000"
    }
    with open(TABLES_DIR / "TAB_05_WRAPPED_CELLS_cf.json", "w", encoding="utf-8") as f:
        json.dump({"fixture_id": "TAB_05_WRAPPED_CELLS", "category": "Category E: Wrapped Cells", "critical_fields": cf_05}, f, indent=2)

    # -------------------------------------------------------------
    # 6. TAB_06: MISSING & EMPTY CELLS (Category F: Explicitly empty cells)
    # -------------------------------------------------------------
    img = Image.new("RGB", (1000, 1000), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((220, 50), "PENSIONER IDENTITY & ADMISSIBILITY MATRIX", font=font_title, fill=(0, 0, 0))

    m_headers = ["PPO No", "Pensioner Name", "Spouse Name", "Disability Grant", "Basic Pension"]
    m_rows = [
        ["PPO-9011", "Harish Chandra", "Kamla Devi", "-", "32400"],
        ["PPO-9012", "Suresh Mohanty", "", "5000", "28900"],
        ["PPO-9013", "Debendra Das", "Geeta Das", "-", "35000"],
        ["PPO-9014", "Prakash Rao", "", "", "41000"],
    ]
    m_cols = [70, 210, 420, 610, 800]
    y = 130
    for c_idx, h in enumerate(m_headers):
        d.text((m_cols[c_idx], y), h, font=font_head, fill=(0, 0, 0))
    d.line([(70, y + 30), (940, y + 30)], fill=(0, 0, 0), width=2)

    y = 180
    for r in m_rows:
        for c_idx, val in enumerate(r):
            d.text((m_cols[c_idx], y), val, font=font_body, fill=(0, 0, 0))
        y += 55
        d.line([(70, y - 10), (940, y - 10)], fill=(220, 220, 220), width=1)

    p = TABLES_DIR / "TAB_06_MISSING_EMPTY_CELLS.png"
    img.save(p)

    cf_06 = {
        "ppo_9011_pension": "32400",
        "ppo_9012_disability": "5000",
        "ppo_9014_pension": "41000"
    }
    with open(TABLES_DIR / "TAB_06_MISSING_EMPTY_CELLS_cf.json", "w", encoding="utf-8") as f:
        json.dump({"fixture_id": "TAB_06_MISSING_EMPTY_CELLS", "category": "Category F: Empty Cells", "critical_fields": cf_06}, f, indent=2)

    # -------------------------------------------------------------
    # 7. TAB_07: MERGED HEADERS (Category G: 2-tier hierarchical header)
    # -------------------------------------------------------------
    img = Image.new("RGB", (1000, 1000), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((220, 40), "DISTRICT REVENUE COLLECTION SCHEDULE", font=font_title, fill=(0, 0, 0))

    # Tier 1 headers
    d.rectangle([80, 100, 280, 150], outline=(0, 0, 0), width=2)
    d.text((120, 115), "LOCATION", font=font_head, fill=(0, 0, 0))

    d.rectangle([280, 100, 600, 150], outline=(0, 0, 0), width=2)
    d.text((370, 115), "ASSESSED TAX", font=font_head, fill=(0, 0, 0))

    d.rectangle([600, 100, 920, 150], outline=(0, 0, 0), width=2)
    d.text((690, 115), "REALIZED TAX", font=font_head, fill=(0, 0, 0))

    # Tier 2 headers
    sub_headers = ["Tehsil Code", "Tehsil Name", "Property Cess", "Water Cess", "Property Coll", "Water Coll"]
    sub_cols = [80, 180, 280, 440, 600, 760, 920]
    for c_idx in range(len(sub_headers)):
        d.rectangle([sub_cols[c_idx], 150, sub_cols[c_idx + 1], 195], outline=(0, 0, 0), width=1)
        d.text((sub_cols[c_idx] + 10, 162), sub_headers[c_idx], font=font_sm, fill=(0, 0, 0))

    rows_7 = [
        ["TH-01", "Jatni", "120000", "45000", "115000", "42000"],
        ["TH-02", "Bhubaneswar", "340000", "89000", "325000", "85000"],
        ["TH-03", "Balianta", "95000", "28000", "90000", "26000"],
    ]
    y = 195
    for r in rows_7:
        for c_idx, val in enumerate(r):
            d.rectangle([sub_cols[c_idx], y, sub_cols[c_idx + 1], y + 45], outline=(0, 0, 0), width=1)
            d.text((sub_cols[c_idx] + 10, y + 12), val, font=font_body, fill=(0, 0, 0))
        y += 45

    p = TABLES_DIR / "TAB_07_MERGED_HEADERS.png"
    img.save(p)

    cf_07 = {
        "jatni_property_cess": "120000",
        "bbsr_property_coll": "325000",
        "balianta_water_coll": "26000"
    }
    with open(TABLES_DIR / "TAB_07_MERGED_HEADERS_cf.json", "w", encoding="utf-8") as f:
        json.dump({"fixture_id": "TAB_07_MERGED_HEADERS", "category": "Category G: Merged Headers", "critical_fields": cf_07}, f, indent=2)

    # -------------------------------------------------------------
    # 8. TAB_08: IRREGULAR LAYOUTS (Category H: Nonuniform row heights & variable widths)
    # -------------------------------------------------------------
    img = Image.new("RGB", (1000, 1000), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((220, 50), "LAND REVENUE SETTLEMENT CASE REGISTER", font=font_title, fill=(0, 0, 0))

    irr_headers = ["Case ID", "Khatian & Plot Record", "Legal Status", "Assessed Duty"]
    irr_cols = [70, 210, 560, 750, 930]
    y = 130
    for c_idx in range(len(irr_headers)):
        d.rectangle([irr_cols[c_idx], y, irr_cols[c_idx + 1], y + 40], outline=(50, 50, 50), width=2)
        d.text((irr_cols[c_idx] + 15, y + 10), irr_headers[c_idx], font=font_head, fill=(0, 0, 0))

    irr_rows = [
        ("REV-801", "Khata 110/2, Plot 405 (0.45 Hectare)\nMouza: Sundarpur", "Mutation Sanctioned", "4850", 70),
        ("REV-804", "Khata 89, Plot 112 (1.20 Hectare)", "Hearing Scheduled", "12500", 50),
        ("REV-809", "Khata 44/1, Plot 908, 909, 910\nTotal Area: 3.10 Hectare\nMouza: Tamando, Tahsil: Jatni", "Disposed under Section 8", "31200", 90),
    ]
    y = 170
    for r in irr_rows:
        cid, kp, stat, duty, row_h = r
        d.rectangle([irr_cols[0], y, irr_cols[1], y + row_h], outline=(100, 100, 100), width=1)
        d.text((irr_cols[0] + 10, y + 10), cid, font=font_body, fill=(0, 0, 0))

        d.rectangle([irr_cols[1], y, irr_cols[2], y + row_h], outline=(100, 100, 100), width=1)
        d.text((irr_cols[1] + 10, y + 10), kp, font=font_body, fill=(0, 0, 0))

        d.rectangle([irr_cols[2], y, irr_cols[3], y + row_h], outline=(100, 100, 100), width=1)
        d.text((irr_cols[2] + 10, y + 10), stat, font=font_body, fill=(0, 0, 0))

        d.rectangle([irr_cols[3], y, irr_cols[4], y + row_h], outline=(100, 100, 100), width=1)
        d.text((irr_cols[3] + 10, y + 10), duty, font=font_body, fill=(0, 0, 0))
        y += row_h

    p = TABLES_DIR / "TAB_08_IRREGULAR_LAYOUTS.png"
    img.save(p)

    cf_08 = {
        "rev_801_duty": "4850",
        "rev_804_duty": "12500",
        "rev_809_duty": "31200"
    }
    with open(TABLES_DIR / "TAB_08_IRREGULAR_LAYOUTS_cf.json", "w", encoding="utf-8") as f:
        json.dump({"fixture_id": "TAB_08_IRREGULAR_LAYOUTS", "category": "Category H: Irregular Layouts", "critical_fields": cf_08}, f, indent=2)

    # -------------------------------------------------------------
    # 9. TAB_09: MULTICOLUMN DOCUMENT (Category I: Page columns with tables)
    # -------------------------------------------------------------
    img = Image.new("RGB", (1000, 1000), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((200, 40), "OFFICIAL GAZETTE: DISBURSEMENT DISPATCH", font=font_title, fill=(0, 0, 0))
    d.line([(50, 85), (950, 85)], fill=(0, 0, 0), width=2)
    d.line([(500, 95), (500, 950)], fill=(120, 120, 120), width=1)

    # Column A text & mini-table
    d.text((60, 110), "SECTION I: WESTERN ZONE", font=font_head, fill=(0, 0, 0))
    d.text((60, 140), "The following orders are sanctioned:", font=font_sm, fill=(50, 50, 50))
    a_rows = [
        ("Batch A-1", "VOU-901", "185000"),
        ("Batch A-2", "VOU-902", "240000"),
        ("Batch A-3", "VOU-903", "310000"),
    ]
    ay = 180
    d.text((60, ay), "Batch ID        Voucher      Amount", font=font_head, fill=(0, 0, 0))
    ay += 35
    for b, v, a in a_rows:
        d.text((60, ay), f"{b:<15} {v:<12} {a}", font=font_body, fill=(0, 0, 0))
        ay += 45

    # Column B text & mini-table
    d.text((530, 110), "SECTION II: EASTERN ZONE", font=font_head, fill=(0, 0, 0))
    d.text((530, 140), "The following orders are sanctioned:", font=font_sm, fill=(50, 50, 50))
    b_rows = [
        ("Batch B-1", "VOU-981", "142000"),
        ("Batch B-2", "VOU-982", "195000"),
        ("Batch B-3", "VOU-983", "275000"),
    ]
    by = 180
    d.text((530, by), "Batch ID        Voucher      Amount", font=font_head, fill=(0, 0, 0))
    by += 35
    for b, v, a in b_rows:
        d.text((530, by), f"{b:<15} {v:<12} {a}", font=font_body, fill=(0, 0, 0))
        by += 45

    p = TABLES_DIR / "TAB_09_MULTICOLUMN_DOCUMENT.png"
    img.save(p)

    cf_09 = {
        "batch_a2_amount": "240000",
        "batch_a3_voucher": "VOU-903",
        "batch_b2_amount": "195000",
        "batch_b3_voucher": "VOU-983"
    }
    with open(TABLES_DIR / "TAB_09_MULTICOLUMN_DOCUMENT_cf.json", "w", encoding="utf-8") as f:
        json.dump({"fixture_id": "TAB_09_MULTICOLUMN_DOCUMENT", "category": "Category I: Multi-column", "critical_fields": cf_09}, f, indent=2)

    # -------------------------------------------------------------
    # 10. TAB_10: ADVERSARIAL GEOMETRY (Category J: Skewed, noisy scan)
    # -------------------------------------------------------------
    img = Image.new("RGB", (1000, 1000), color=(245, 245, 245))
    d = ImageDraw.Draw(img)
    d.text((220, 50), "DISTRICT AUDIT VOUCHER REGISTER", font=font_title, fill=(70, 70, 70))

    adv_headers = ["Token No", "Payee Name", "Order Date", "Amount (INR)"]
    adv_rows = [
        ["TK-801", "Deepak Sharma", "14/04/2026", "85000"],
        ["TK-802", "Pooja Mishra", "19/04/2026", "142000"],
        ["TK-803", "Rohan Das", "25/04/2026", "67000"],
    ]
    adv_cols = [80, 220, 520, 740, 920]
    y = 130
    for c_idx in range(len(adv_headers)):
        d.rectangle([adv_cols[c_idx], y, adv_cols[c_idx + 1], y + 40], outline=(120, 120, 120), width=1)
        d.text((adv_cols[c_idx] + 15, y + 10), adv_headers[c_idx], font=font_head, fill=(60, 60, 60))

    y = 170
    for r in adv_rows:
        for c_idx, val in enumerate(r):
            d.rectangle([adv_cols[c_idx], y, adv_cols[c_idx + 1], y + 45], outline=(150, 150, 150), width=1)
            d.text((adv_cols[c_idx] + 15, y + 12), val, font=font_body, fill=(50, 50, 50))
        y += 45

    # Apply 2.2 degree skew and contrast reduction
    img = img.rotate(2.2, resample=Image.Resampling.BICUBIC, expand=False, fillcolor=(245, 245, 245))
    enh = ImageEnhance.Contrast(img)
    img = enh.enhance(0.75)

    p = TABLES_DIR / "TAB_10_ADVERSARIAL_GEOMETRY.png"
    img.save(p)

    cf_10 = {
        "tk_801_amount": "85000",
        "tk_802_date": "19/04/2026",
        "tk_803_amount": "67000"
    }
    with open(TABLES_DIR / "TAB_10_ADVERSARIAL_GEOMETRY_cf.json", "w", encoding="utf-8") as f:
        json.dump({"fixture_id": "TAB_10_ADVERSARIAL_GEOMETRY", "category": "Category J: Adversarial Geometry", "critical_fields": cf_10}, f, indent=2)

    # -------------------------------------------------------------
    # Build Dataset Manifest
    # -------------------------------------------------------------
    fixtures = [
        "TAB_01_SIMPLE_GRID",
        "TAB_02_BORDERLESS_TABLE",
        "TAB_03_DENSE_NUMERIC_COLUMNS",
        "TAB_04_SIMILAR_ADJACENT_VALUES",
        "TAB_05_WRAPPED_CELLS",
        "TAB_06_MISSING_EMPTY_CELLS",
        "TAB_07_MERGED_HEADERS",
        "TAB_08_IRREGULAR_LAYOUTS",
        "TAB_09_MULTICOLUMN_DOCUMENT",
        "TAB_10_ADVERSARIAL_GEOMETRY",
    ]

    manifest_entries = []
    for fix in fixtures:
        img_p = TABLES_DIR / f"{fix}.png"
        cf_p = TABLES_DIR / f"{fix}_cf.json"
        with open(cf_p, "r", encoding="utf-8") as fp:
            cf_info = json.load(fp)

        manifest_entries.append({
            "fixture_id": fix,
            "category": cf_info["category"],
            "file_name": f"{fix}.png",
            "sha256": sha256_file(img_p),
            "file_size_bytes": img_p.stat().st_size,
            "critical_field_count": len(cf_info["critical_fields"]),
            "critical_fields": cf_info["critical_fields"]
        })

    manifest = {
        "version": "1.0",
        "loop": "19",
        "benchmark": "Table-Aware Spatial Evidence Association",
        "total_fixtures": len(manifest_entries),
        "total_critical_fields": sum(m["critical_field_count"] for m in manifest_entries),
        "fixtures": manifest_entries
    }

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"Generated {len(manifest_entries)} table fixtures in {TABLES_DIR}")
    print(f"Total critical fields: {manifest['total_critical_fields']}")
    print(f"Manifest written to {MANIFEST_PATH}")


if __name__ == "__main__":
    build_table_fixtures()
