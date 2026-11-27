"""
Unit and Regression Tests for Loop 22:
- Isolated baseline decimal dot refinement (prevents '640' -> '64.0', '4000' -> '40.00', restores '5.6')
- Header-path and column consistency validation (prevents wrong-column capture)
- Multi-token cell gutter bleed detection (triggers ABSTAIN)
- Low confidence OCR filtering (< 60.0 triggers ABSTAIN)
- Syntax garble filtering (triggers ABSTAIN)
- Discrete FieldEvidence verification decisions and abstention provenance
"""

import numpy as np
import pytest
from PIL import Image, ImageDraw, ImageFont
from docuready.ingest.table_association import (
    TableCell,
    TableGrid,
    FieldEvidence,
    refine_cell_decimal_point,
    extract_cell_by_intersection,
    extract_field_by_spatial_association,
    build_table_grid,
)


def test_decimal_refinement_integer_safety():
    """Verify that integer values like 640, 4000, 3100, 343 are never corrupted into decimals."""
    # Create synthetic crop of '640' with character crossbars
    img = Image.new("L", (30, 14), color=255)
    d = ImageDraw.Draw(img)
    d.text((2, 1), "640", fill=0)

    # Calling refine_cell_decimal_point on '640' must remain '640'
    res = refine_cell_decimal_point("640", img)
    assert res == "640", f"Expected '640', got '{res}'"

    # '4000' must remain '4000'
    img4 = Image.new("L", (40, 14), color=255)
    d4 = ImageDraw.Draw(img4)
    d4.text((2, 1), "4000", fill=0)
    res4 = refine_cell_decimal_point("4000", img4)
    assert res4 == "4000", f"Expected '4000', got '{res4}'"

    # '343' must remain '343'
    img3 = Image.new("L", (30, 14), color=255)
    d3 = ImageDraw.Draw(img3)
    d3.text((2, 1), "343", fill=0)
    res3 = refine_cell_decimal_point("343", img3)
    assert res3 == "343", f"Expected '343', got '{res3}'"


def test_decimal_refinement_true_dot_recovery():
    """Verify that a genuine isolated baseline decimal dot is recovered (e.g. '56' -> '5.6')."""
    # Create image with '5' and '6' and a small 2x2 dot at the baseline between them
    img = Image.new("L", (32, 16), color=255)
    d = ImageDraw.Draw(img)
    # Draw '5' on left
    d.text((2, 1), "5", fill=0)
    # Draw isolated 2x2 dot at row 12-13, col 15-16
    d.rectangle([15, 12, 16, 13], fill=0)
    # Draw '6' on right
    d.text((20, 1), "6", fill=0)

    # When OCR read '56', the morphology scan should insert '.'
    res = refine_cell_decimal_point("56", img)
    assert res == "5.6", f"Expected '5.6', got '{res}'"


def test_header_semantic_contradiction_abstention():
    """Verify that when a column header explicitly contradicts the field type (e.g. Weight vs Freight), the system abstains."""
    cell_words = [{"text": "54000", "center_x": 100, "center_y": 50, "bbox": (80, 40, 120, 60)}]
    cells = [
        TableCell(row=0, col=0, bbox=(0, 0, 150, 30), text="Consignee", conf=95.0, is_header=True),
        TableCell(row=0, col=1, bbox=(150, 0, 300, 30), text="Freight (INR)", conf=95.0, is_header=True),
        TableCell(row=1, col=0, bbox=(0, 30, 150, 70), text="Jindal Steel", conf=95.0),
        TableCell(row=1, col=1, bbox=(150, 30, 300, 70), text="54000", conf=95.0, words=cell_words),
    ]
    grid = TableGrid(
        bbox=(0, 0, 300, 70),
        num_rows=2,
        num_cols=2,
        col_boundaries=[(0, 150), (150, 300)],
        row_boundaries=[(0, 30), (30, 70)],
        col_headers=["Consignee", "Freight (INR)"],
        cells=cells,
        rows=[[cells[0], cells[1]], [cells[2], cells[3]]]
    )

    ev = extract_field_by_spatial_association(
        grid=grid,
        field_name="jindal_weight",
        target_pattern="Jindal Steel",
        col_idx=1,
        expected_type="weight"
    )
    assert ev is not None
    assert ev.is_ambiguous is True
    assert ev.verification_decision == "ABSTAIN"
    assert "contradicts expected field semantic" in (ev.abstention_reason or "")


def test_multi_token_gutter_bleed_abstention():
    """Verify that numeric fields containing multiple space-separated tokens trigger gutter bleed abstention."""
    cell_words = [
        {"text": "15000", "center_x": 50, "center_y": 50, "bbox": (30, 40, 70, 60)},
        {"text": "1500", "center_x": 100, "center_y": 50, "bbox": (80, 40, 120, 60)}
    ]
    cells = [
        TableCell(row=0, col=0, bbox=(0, 0, 150, 30), text="Holder", conf=95.0, is_header=True),
        TableCell(row=0, col=1, bbox=(150, 0, 300, 30), text="Current Amount", conf=95.0, is_header=True),
        TableCell(row=1, col=0, bbox=(0, 30, 150, 70), text="HOLD-401", conf=95.0),
        TableCell(row=1, col=1, bbox=(150, 30, 300, 70), text="15000 1500", conf=95.0, words=cell_words),
    ]
    grid = TableGrid(
        bbox=(0, 0, 300, 70),
        num_rows=2,
        num_cols=2,
        col_boundaries=[(0, 150), (150, 300)],
        row_boundaries=[(0, 30), (30, 70)],
        col_headers=["Holder", "Current Amount"],
        cells=cells,
        rows=[[cells[0], cells[1]], [cells[2], cells[3]]]
    )

    ev = extract_field_by_spatial_association(
        grid=grid,
        field_name="hold_401_amount",
        target_pattern="HOLD-401",
        col_idx=1,
        expected_type="amount"
    )
    assert ev is not None
    assert ev.is_ambiguous is True
    assert ev.verification_decision == "ABSTAIN"
    assert "Multiple whitespace-separated tokens" in (ev.abstention_reason or "")


def test_low_ocr_confidence_abstention():
    """Verify that cells with OCR confidence below 60.0 are marked for abstention."""
    cells = [
        TableCell(row=0, col=0, bbox=(0, 0, 150, 30), text="Subject", conf=90.0, is_header=True),
        TableCell(row=0, col=1, bbox=(150, 0, 300, 30), text="Grade", conf=90.0, is_header=True),
        TableCell(row=1, col=0, bbox=(0, 30, 150, 70), text="Computer Networks", conf=90.0),
        TableCell(row=1, col=1, bbox=(150, 30, 300, 70), text="fe}", conf=35.0),
    ]
    grid = TableGrid(
        bbox=(0, 0, 300, 70),
        num_rows=2,
        num_cols=2,
        col_boundaries=[(0, 150), (150, 300)],
        row_boundaries=[(0, 30), (30, 70)],
        col_headers=["Subject", "Grade"],
        cells=cells,
        rows=[[cells[0], cells[1]], [cells[2], cells[3]]]
    )

    ev = extract_field_by_spatial_association(
        grid=grid,
        field_name="networks_grade",
        target_pattern="Computer Networks",
        col_idx=1,
        expected_type="code"
    )
    assert ev is not None
    assert ev.is_ambiguous is True
    assert ev.verification_decision == "ABSTAIN"
    assert "Low OCR confidence" in (ev.abstention_reason or "") or "Stray punctuation" in (ev.abstention_reason or "")
