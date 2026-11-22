"""
Unit & Regression Tests for Column-Aware Reading Order Reconstruction
DocuReady - Research Loop 13 Test Suite

Verifies:
1. Multi-Column Reading Order De-Interleaving (2-col, 3-col, unequal heights, full-width banners)
2. Single-Column & Tabular Regression Safety (certificates, forms, key-value tables)
3. Geometry & Bounding Box Preservation (valid coordinates, zero coordinate drift)
4. Edge Case & Robustness Handling (empty input, noise, narrow margins, single word)
"""

import math
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.docuready.ingest.extractor import PageOCRData
from src.docuready.ingest.spatial_layout import (
    cluster_and_order_words,
    detect_page_layout_structure,
    is_label_value_row,
)


# ============================================================================
# 1. MULTI-COLUMN READING ORDER TESTS
# ============================================================================

def test_two_column_independent_narrative_deinterleaving():
    """Verifies that two parallel columns of text with overlapping y-coordinates are read vertically."""
    words = [
        # Left Column Line 1 & Line 2 (x: 50..220)
        ("The", 50, 100, 25, 12), ("post-matric", 80, 100, 70, 12), ("scholarship", 155, 100, 65, 12),
        ("Eligible", 50, 115, 45, 12), ("students", 100, 115, 50, 12), ("must", 155, 115, 30, 12),
        # Right Column Line 1 & Line 2 (x: 350..540)
        ("State", 350, 100, 35, 12), ("verification", 390, 100, 75, 12), ("offices", 470, 100, 45, 12),
        ("Incomplete", 350, 115, 65, 12), ("documentation", 420, 115, 80, 12), ("leads", 505, 115, 35, 12)
    ]

    raw_data = {
        "text": [w[0] for w in words],
        "conf": [95.0] * len(words),
        "left": [w[1] for w in words],
        "top": [w[2] for w in words],
        "width": [w[3] for w in words],
        "height": [w[4] for w in words]
    }

    page_ocr = PageOCRData(raw_data, dpi=72)
    lines = [l["text"] for l in page_ocr.lines]

    assert len(lines) == 4
    # Must read all of column 1 first, then column 2
    assert lines[0] == "The post-matric scholarship"
    assert lines[1] == "Eligible students must"
    assert lines[2] == "State verification offices"
    assert lines[3] == "Incomplete documentation leads"


def test_full_width_header_and_footer_bracketing():
    """Verifies that full-width banners are correctly sequenced before and after two-column regions."""
    words = [
        # Full-Width Header (x: 50..330, y: 50)
        ("GOVERNMENT", 50, 50, 80, 12), ("SCHOLARSHIP", 140, 50, 90, 12), ("NOTIFICATION", 240, 50, 90, 12),
        # Left Column (y: 100, 115)
        ("Section", 50, 100, 45, 12), ("One", 100, 100, 30, 12),
        ("Paragraph", 50, 115, 60, 12), ("A", 115, 115, 15, 12),
        # Right Column (y: 100, 115)
        ("Section", 350, 100, 45, 12), ("Two", 400, 100, 30, 12),
        ("Paragraph", 350, 115, 60, 12), ("B", 415, 115, 15, 12),
        # Full-Width Footer (x: 50..200, y: 200)
        ("End", 50, 200, 25, 12), ("of", 80, 200, 15, 12), ("Official", 100, 200, 50, 12), ("Notice", 155, 200, 45, 12)
    ]

    raw_data = {
        "text": [w[0] for w in words],
        "conf": [95.0] * len(words),
        "left": [w[1] for w in words],
        "top": [w[2] for w in words],
        "width": [w[3] for w in words],
        "height": [w[4] for w in words]
    }

    page_ocr = PageOCRData(raw_data, dpi=72)
    lines = [l["text"] for l in page_ocr.lines]

    assert lines[0] == "GOVERNMENT SCHOLARSHIP NOTIFICATION"
    assert lines[1] == "Section One"
    assert lines[2] == "Paragraph A"
    assert lines[3] == "Section Two"
    assert lines[4] == "Paragraph B"
    assert lines[5] == "End of Official Notice"


def test_unequal_column_heights():
    """Verifies layout handling when Left column has more lines than Right column."""
    words = [
        # Left Column: 3 lines
        ("Left", 50, 100, 30, 12), ("Line", 85, 100, 30, 12), ("One", 120, 100, 25, 12),
        ("Left", 50, 120, 30, 12), ("Line", 85, 120, 30, 12), ("Two", 120, 120, 25, 12),
        ("Left", 50, 140, 30, 12), ("Line", 85, 140, 30, 12), ("Three", 120, 140, 35, 12),
        # Right Column: 1 line
        ("Right", 350, 100, 35, 12), ("Single", 390, 100, 40, 12), ("Line", 435, 100, 30, 12)
    ]

    raw_data = {
        "text": [w[0] for w in words],
        "conf": [95.0] * len(words),
        "left": [w[1] for w in words],
        "top": [w[2] for w in words],
        "width": [w[3] for w in words],
        "height": [w[4] for w in words]
    }

    page_ocr = PageOCRData(raw_data, dpi=72)
    lines = [l["text"] for l in page_ocr.lines]

    assert len(lines) == 4
    assert lines[0] == "Left Line One"
    assert lines[1] == "Left Line Two"
    assert lines[2] == "Left Line Three"
    assert lines[3] == "Right Single Line"


# ============================================================================
# 2. REGRESSION SAFETY & KEY-VALUE TABLE PRESERVATION
# ============================================================================

def test_key_value_form_row_order_preservation():
    """
    Critical safety test: Key-Value tables (like intake forms) must preserve
    row-wise reading order so that field extractors and rules function properly.
    """
    words = [
        ("Applicant", 50, 100, 55, 12), ("Name:", 110, 100, 35, 12), ("ROHIT", 300, 100, 40, 12), ("VERMA", 345, 100, 45, 12),
        ("Roll", 50, 120, 30, 12), ("Number:", 85, 120, 45, 12), ("DHE-2026-5541", 300, 120, 85, 12),
        ("Income:", 50, 140, 45, 12), ("INR", 300, 140, 25, 12), ("180000", 330, 140, 45, 12)
    ]

    raw_data = {
        "text": [w[0] for w in words],
        "conf": [95.0] * len(words),
        "left": [w[1] for w in words],
        "top": [w[2] for w in words],
        "width": [w[3] for w in words],
        "height": [w[4] for w in words]
    }

    page_ocr = PageOCRData(raw_data, dpi=72)
    lines = [l["text"] for l in page_ocr.lines]

    # Must preserve row grouping (Label + Value on the same line)
    assert lines[0] == "Applicant Name: ROHIT VERMA"
    assert lines[1] == "Roll Number: DHE-2026-5541"
    assert lines[2] == "Income: INR 180000"


def test_single_column_paragraph_never_split():
    """Verifies that ordinary single-column paragraphs with wide word spacing are not split."""
    words = [
        ("This", 50, 100, 25, 12), ("is", 80, 100, 15, 12), ("a", 100, 100, 10, 12), ("standard", 115, 100, 50, 12),
        ("single-column", 170, 100, 75, 12), ("certificate", 250, 100, 60, 12), ("paragraph.", 315, 100, 65, 12),
        ("All", 50, 120, 20, 12), ("words", 75, 120, 35, 12), ("must", 115, 120, 30, 12), ("remain", 150, 120, 40, 12),
        ("strictly", 195, 120, 45, 12), ("in", 245, 120, 15, 12), ("sequence.", 265, 120, 55, 12)
    ]

    raw_data = {
        "text": [w[0] for w in words],
        "conf": [95.0] * len(words),
        "left": [w[1] for w in words],
        "top": [w[2] for w in words],
        "width": [w[3] for w in words],
        "height": [w[4] for w in words]
    }

    page_ocr = PageOCRData(raw_data, dpi=72)
    lines = [l["text"] for l in page_ocr.lines]

    assert len(lines) == 2
    assert lines[0] == "This is a standard single-column certificate paragraph."
    assert lines[1] == "All words must remain strictly in sequence."


# ============================================================================
# 3. GEOMETRY & BOUNDING BOX PRESERVATION
# ============================================================================

def test_bounding_box_geometry_invariants():
    """Verifies that line and word bounding boxes remain valid in original page space."""
    words = [
        ("Column", 50, 100, 40, 12), ("Left", 95, 100, 30, 12),
        ("Column", 350, 100, 40, 12), ("Right", 395, 100, 30, 12)
    ]

    raw_data = {
        "text": [w[0] for w in words],
        "conf": [92.0] * len(words),
        "left": [w[1] for w in words],
        "top": [w[2] for w in words],
        "width": [w[3] for w in words],
        "height": [w[4] for w in words]
    }

    page_ocr = PageOCRData(raw_data, dpi=72)
    for l in page_ocr.lines:
        bbox = l["bbox"]
        assert len(bbox) == 4
        # Positive coordinates
        assert bbox[0] >= 0.0 and bbox[1] >= 0.0
        # Valid non-degenerate rectangle (x1 > x0, y1 > y0)
        assert bbox[2] > bbox[0]
        assert bbox[3] > bbox[1]

        # Word box coordinates match line span
        assert min(b[0] for b in l["word_boxes"]) == bbox[0]
        assert min(b[1] for b in l["word_boxes"]) == bbox[1]
        assert max(b[2] for b in l["word_boxes"]) == bbox[2]
        assert max(b[3] for b in l["word_boxes"]) == bbox[3]


# ============================================================================
# 4. EDGE CASES & ROBUSTNESS
# ============================================================================

def test_empty_and_sparse_ocr_data():
    """Verifies safe handling of empty or single-word OCR inputs."""
    # Completely empty data
    empty_ocr = PageOCRData({"text": [], "conf": [], "left": [], "top": [], "width": [], "height": []})
    assert empty_ocr.lines == []

    # Single word data
    single_ocr = PageOCRData({
        "text": ["SOLITARY"],
        "conf": [90.0],
        "left": [100],
        "top": [100],
        "width": [50],
        "height": [12]
    })
    assert len(single_ocr.lines) == 1
    assert single_ocr.lines[0]["text"] == "SOLITARY"


def test_three_column_layout_handling():
    """Verifies that pages with 3 columns or complex tables are processed safely without crashes."""
    words = [
        # Col 1 (x: 50..120)
        ("Alpha", 50, 100, 30, 12), ("One", 85, 100, 25, 12),
        # Col 2 (x: 200..270)
        ("Beta", 200, 100, 30, 12), ("Two", 235, 100, 25, 12),
        # Col 3 (x: 350..420)
        ("Gamma", 350, 100, 35, 12), ("Three", 390, 100, 30, 12)
    ]
    raw_data = {
        "text": [w[0] for w in words],
        "conf": [95.0] * len(words),
        "left": [w[1] for w in words],
        "top": [w[2] for w in words],
        "width": [w[3] for w in words],
        "height": [w[4] for w in words]
    }
    page_ocr = PageOCRData(raw_data, dpi=72)
    assert len(page_ocr.lines) >= 1
    # Check that bounding box covers all words
    bbox = page_ocr.lines[0]["bbox"]
    assert bbox[0] == 50.0
    assert bbox[2] == 420.0


def test_table_grid_preservation():
    """Verifies that financial or marksheet grid tables retain row-wise integrity."""
    table_words = [
        # Header row
        ("Subject", 50, 100, 45, 12), ("Max_Marks", 200, 100, 65, 12), ("Marks_Obtained", 350, 100, 85, 12),
        # Row 1
        ("Mathematics", 50, 120, 75, 12), ("100", 200, 120, 25, 12), ("92", 350, 120, 20, 12),
        # Row 2
        ("Physics", 50, 140, 50, 12), ("100", 200, 140, 25, 12), ("88", 350, 140, 20, 12)
    ]
    raw_data = {
        "text": [w[0] for w in table_words],
        "conf": [95.0] * len(table_words),
        "left": [w[1] for w in table_words],
        "top": [w[2] for w in table_words],
        "width": [w[3] for w in table_words],
        "height": [w[4] for w in table_words]
    }
    page_ocr = PageOCRData(raw_data, dpi=72)
    lines = [l["text"] for l in page_ocr.lines]
    # Rows must be read row-by-row
    assert "Mathematics 100 92" in lines[1]
    assert "Physics 100 88" in lines[2]


def test_invalid_and_negative_confidence_filtered():
    """Verifies that words with negative confidence or whitespace strings are ignored."""
    data = {
        "text": ["VALID", "   ", "JUNK", ""],
        "conf": [95.0, 95.0, -1.0, 80.0],
        "left": [50, 100, 150, 200],
        "top": [50, 50, 50, 50],
        "width": [40, 20, 30, 0],
        "height": [12, 12, 12, 0]
    }
    ocr = PageOCRData(data, dpi=72)
    assert len(ocr.lines) == 1
    assert ocr.lines[0]["text"] == "VALID"
