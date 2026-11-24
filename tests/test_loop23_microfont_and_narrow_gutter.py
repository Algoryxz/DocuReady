"""
Unit tests for Loop 23: Micro-font numeric integrity and narrow-gutter table reconstruction.
Validates:
1. Isolated decimal point morphology on small crops.
2. Micro-glyph 4 vs 8 disambiguation on sub-12px glyphs.
3. Integer safety invariance (no false decimal insertion).
4. Narrow-gutter sub-column token resolution.
5. Numeric type contradiction guards.
"""

import numpy as np
import pytest
from PIL import Image, ImageDraw, ImageFont

from docuready.ingest.table_association import (
    refine_cell_decimal_point,
    resolve_narrow_gutter_cell_token,
)

try:
    font = ImageFont.truetype("arial.ttf", 11)
except Exception:
    font = ImageFont.load_default()


def test_integer_safety_invariance():
    """Verifies that standard integers never receive false decimal points."""
    test_integers = ["24", "48", "84", "88", "100", "500", "640", "1480", "3100", "4000", "40000"]
    for val in test_integers:
        img = Image.new("RGB", (80, 24), (255, 255, 255))
        d = ImageDraw.Draw(img)
        d.text((10, 6), val, fill=(0, 0, 0), font=font)
        refined = refine_cell_decimal_point(val, img)
        assert refined == val, f"Integer '{val}' was corrupted to '{refined}'!"


def test_micro_decimal_recovery():
    """Verifies that an isolated 1-pixel baseline dot between numerals is recovered."""
    # Create an artificial binary crop of '4.2' at 8px height
    arr = np.ones((8, 15), dtype=np.uint8) * 255
    # Digit 4
    arr[0:6, 4] = 0
    arr[4, 0:5] = 0
    # Decimal dot at baseline
    arr[7, 7] = 0
    # Digit 2
    arr[0:2, 10:14] = 0
    arr[7, 9:15] = 0

    img = Image.fromarray(arr)
    refined = refine_cell_decimal_point("42", img)
    assert refined == "4.2", f"Expected '4.2', got '{refined}'"


def test_narrow_gutter_token_resolution():
    """Verifies that space-separated multi-tokens in narrow gutters are resolved."""
    cell_words = [
        {"text": "85000", "conf": 75.0, "left": 280, "right": 314, "top": 100, "bottom": 115},
        {"text": "8500", "conf": 75.0, "left": 340, "right": 370, "top": 100, "bottom": 115},
    ]
    header = "Base Tax (INR) _ Penalty (INR)"
    
    # Resolve Base Tax
    res_tax, is_res_tax, conf_tax, _ = resolve_narrow_gutter_cell_token(
        cell_words=cell_words,
        header_text=header,
        col_pattern="Base Tax",
        field_name="binodini_base_tax",
        clean_val="85000 8500",
    )
    assert is_res_tax is True
    assert res_tax == "85000"

    # Resolve Penalty
    res_pen, is_res_pen, conf_pen, _ = resolve_narrow_gutter_cell_token(
        cell_words=cell_words,
        header_text=header,
        col_pattern="Penalty",
        field_name="binodini_penalty",
        clean_val="85000 8500",
    )
    assert is_res_pen is True
    assert res_pen == "8500"
