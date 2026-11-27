"""
Unit and Integration Tests for Loop 21:
- Multi-tier hierarchical header reconstruction and span fusion
- Low-resolution baseline decimal point retention and integer safety
- Cross-column and cross-row spatial integrity
"""

import numpy as np
import pytest
from PIL import Image, ImageDraw, ImageFont

from docuready.ingest.table_association import (
    TableGrid,
    TableCell,
    FieldEvidence,
    build_table_grid,
    extract_field_by_spatial_association,
    extract_cell_by_intersection,
    refine_cell_decimal_point,
)


def test_refine_cell_decimal_point_reconstruction():
    """
    Verifies that a 12px high numeric crop with a dropped 2x2 baseline dot
    is accurately recovered as a decimal number.
    """
    # Create synthetic 20x12 bitmap mimicking '5.6'
    # Digit '5' on left, digit '6' on right, 2x2 dot at bottom between them
    img = Image.new("L", (20, 12), color=255)
    d = ImageDraw.Draw(img)
    # Left digit '5'
    d.rectangle([2, 1, 6, 10], fill=0)
    # Right digit '6'
    d.rectangle([13, 1, 17, 10], fill=0)
    # Isolated baseline dot at x=9, y=10..11
    d.rectangle([9, 10, 10, 11], fill=0)

    # Raw text was '56'
    refined = refine_cell_decimal_point("56", img)
    assert refined == "5.6", f"Expected '5.6', got '{refined}'"


def test_refine_cell_decimal_point_preserves_integers():
    """
    Verifies that genuine integers without a baseline dot are NEVER
    falsely modified into decimals.
    """
    # Create clean integer '98' with clean blank inter-character gap
    img = Image.new("L", (20, 12), color=255)
    d = ImageDraw.Draw(img)
    d.rectangle([2, 1, 6, 10], fill=0)
    d.rectangle([13, 1, 17, 10], fill=0)
    # No dot!

    refined = refine_cell_decimal_point("98", img)
    assert refined == "98", f"Expected integer '98' to remain unchanged, got '{refined}'"

    # Multi-digit integers
    assert refine_cell_decimal_point("40000", img) == "40000"
    assert refine_cell_decimal_point("84500", img) == "84500"


def test_refine_cell_decimal_point_preserves_existing_decimals():
    """
    Verifies that strings already containing a decimal point are untouched.
    """
    img = Image.new("L", (20, 12), color=255)
    assert refine_cell_decimal_point("12.50", img) == "12.50"
    assert refine_cell_decimal_point("0.85", img) == "0.85"


def test_refine_cell_decimal_point_non_numeric_safety():
    """
    Verifies that non-numeric strings, currency labels, and empty inputs
    are returned safely without errors.
    """
    img = Image.new("L", (20, 12), color=255)
    assert refine_cell_decimal_point("", img) == ""
    assert refine_cell_decimal_point("TOTAL", img) == "TOTAL"
    assert refine_cell_decimal_point("N/A", img) == "N/A"
    assert refine_cell_decimal_point("56", None) == "56"


def test_hierarchical_header_fusion_detection():
    """
    Verifies that a 2-tier header structure with spanning parent super-headers
    and leaf child headers is detected, propagated, and fused into a single
    composite header row, with data rows correctly indexed starting from 1.
    """
    # Construct mock OCR data for a 2-tier table
    # Row 0: ['', 'Quarter 1 Status', '', 'Quarter 2 Status', '']
    # Row 1: ['Scheme Head', 'Q1 Budget', 'Q1 Actual', 'Q2 Budget', 'Q2 Actual']
    # Row 2: ['Seed Subsidy', '40000', '38500', '45000', '42000']
    # Row 3: ['Drip Irrigation', '80000', '76000', '85000', '84500']
    ocr_words = [
        # Row 0 (y: 120..140)
        {"text": "Quarter", "left": 250, "top": 124, "width": 35, "height": 18, "conf": 95},
        {"text": "1", "left": 290, "top": 124, "width": 10, "height": 18, "conf": 95},
        {"text": "Status", "left": 305, "top": 124, "width": 30, "height": 18, "conf": 95},
        {"text": "Quarter", "left": 570, "top": 124, "width": 35, "height": 18, "conf": 95},
        {"text": "2", "left": 610, "top": 124, "width": 10, "height": 18, "conf": 95},
        {"text": "Status", "left": 625, "top": 124, "width": 30, "height": 18, "conf": 95},

        # Row 1 (y: 160..180)
        {"text": "Scheme", "left": 80, "top": 164, "width": 60, "height": 18, "conf": 95},
        {"text": "Head", "left": 145, "top": 164, "width": 40, "height": 18, "conf": 95},
        {"text": "Q1", "left": 250, "top": 164, "width": 20, "height": 18, "conf": 95},
        {"text": "Budget", "left": 275, "top": 164, "width": 50, "height": 18, "conf": 95},
        {"text": "Q1", "left": 410, "top": 164, "width": 20, "height": 18, "conf": 95},
        {"text": "Actual", "left": 435, "top": 164, "width": 45, "height": 18, "conf": 95},
        {"text": "Q2", "left": 570, "top": 164, "width": 20, "height": 18, "conf": 95},
        {"text": "Budget", "left": 595, "top": 164, "width": 50, "height": 18, "conf": 95},
        {"text": "Q2", "left": 750, "top": 164, "width": 20, "height": 18, "conf": 95},
        {"text": "Actual", "left": 775, "top": 164, "width": 45, "height": 18, "conf": 95},

        # Row 2 (y: 210..230)
        {"text": "Seed", "left": 80, "top": 211, "width": 35, "height": 18, "conf": 95},
        {"text": "Subsidy", "left": 120, "top": 211, "width": 50, "height": 18, "conf": 95},
        {"text": "40000", "left": 250, "top": 211, "width": 45, "height": 18, "conf": 95},
        {"text": "38500", "left": 410, "top": 211, "width": 45, "height": 18, "conf": 95},
        {"text": "45000", "left": 570, "top": 211, "width": 45, "height": 18, "conf": 95},
        {"text": "42000", "left": 750, "top": 211, "width": 45, "height": 18, "conf": 95},

        # Row 3 (y: 270..290)
        {"text": "Drip", "left": 80, "top": 271, "width": 30, "height": 18, "conf": 95},
        {"text": "Irrigation", "left": 115, "top": 271, "width": 60, "height": 18, "conf": 95},
        {"text": "80000", "left": 250, "top": 271, "width": 45, "height": 18, "conf": 95},
        {"text": "76000", "left": 410, "top": 271, "width": 45, "height": 18, "conf": 95},
        {"text": "85000", "left": 570, "top": 271, "width": 45, "height": 18, "conf": 95},
        {"text": "84500", "left": 750, "top": 271, "width": 45, "height": 18, "conf": 95},
    ]

    mock_ocr = {
        "text": [w["text"] for w in ocr_words],
        "left": [w["left"] for w in ocr_words],
        "top": [w["top"] for w in ocr_words],
        "width": [w["width"] for w in ocr_words],
        "height": [w["height"] for w in ocr_words],
        "conf": [w["conf"] for w in ocr_words],
    }

    grid = build_table_grid(mock_ocr, page_width=1000, page_height=500)

    # Grid must have 3 rows: 1 header row + 2 data rows
    assert grid.num_rows == 3, f"Expected 3 rows after fusion, got {grid.num_rows}"
    assert grid.num_cols == 5, f"Expected 5 columns, got {grid.num_cols}"

    # Verify column headers contain both parent and child info
    assert "Quarter 1 Status / Q1 Budget" in grid.col_headers[1]
    assert "Quarter 1 Status / Q1 Actual" in grid.col_headers[2]
    assert "Quarter 2 Status / Q2 Budget" in grid.col_headers[3]
    assert "Quarter 2 Status / Q2 Actual" in grid.col_headers[4]

    # Verify data rows are properly indexed starting from 1
    assert grid.rows[1][0].text == "Seed Subsidy"
    assert grid.rows[1][0].row == 1
    assert grid.rows[2][0].text == "Drip Irrigation"
    assert grid.rows[2][0].row == 2

    # Verify spatial field extraction works with both column pattern and column index
    ev_seed = extract_field_by_spatial_association(
        grid=grid,
        field_name="seed_budget",
        target_pattern="Seed Subsidy",
        col_pattern="Q1 Budget",
        expected_type="amount",
    )
    assert ev_seed is not None
    assert ev_seed.value == "40000"
    assert ev_seed.row_idx == 1
    assert ev_seed.col_idx == 1

    ev_drip = extract_field_by_spatial_association(
        grid=grid,
        field_name="drip_actual",
        target_pattern="Drip Irrigation",
        col_pattern="Q2 Actual",
        expected_type="amount",
    )
    assert ev_drip is not None
    assert ev_drip.value == "84500"
    assert ev_drip.row_idx == 2
    assert ev_drip.col_idx == 4


def test_standard_single_header_table_not_fused():
    """
    Verifies that a standard single-header table where Row 1 is already data
    is NOT incorrectly detected or mutated as multi-tier.
    """
    ocr_words = [
        # Row 0 (Headers)
        {"text": "Item", "left": 50, "top": 100, "width": 40, "height": 18, "conf": 95},
        {"text": "Rate", "left": 250, "top": 100, "width": 40, "height": 18, "conf": 95},
        {"text": "Amount", "left": 450, "top": 100, "width": 50, "height": 18, "conf": 95},

        # Row 1 (Data with numbers)
        {"text": "Pattachitra", "left": 50, "top": 140, "width": 70, "height": 18, "conf": 95},
        {"text": "20500", "left": 250, "top": 140, "width": 45, "height": 18, "conf": 95},
        {"text": "41000", "left": 450, "top": 140, "width": 45, "height": 18, "conf": 95},
    ]

    mock_ocr = {
        "text": [w["text"] for w in ocr_words],
        "left": [w["left"] for w in ocr_words],
        "top": [w["top"] for w in ocr_words],
        "width": [w["width"] for w in ocr_words],
        "height": [w["height"] for w in ocr_words],
        "conf": [w["conf"] for w in ocr_words],
    }

    grid = build_table_grid(mock_ocr, page_width=1000, page_height=500)
    assert grid.num_rows == 2, f"Expected 2 rows, got {grid.num_rows}"
    assert grid.col_headers == ["Item", "Rate", "Amount"]
    assert grid.rows[1][0].text == "Pattachitra"
    assert grid.rows[1][1].text == "20500"
