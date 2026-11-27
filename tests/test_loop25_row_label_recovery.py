"""
Unit and regression tests for Loop 25 Evidence-Guided Row-Label Recovery.
Verifies canonical OCR equivalence, Levenshtein similarity with safety margin guard,
target column structural validation, and confidence-calibrated abstention.
"""

import pytest
from docuready.ingest.table_association import (
    TableCell,
    TableGrid,
    canonical_ocr_key,
    find_matching_row_evidence_guided,
    extract_cell_by_intersection,
)


def _make_grid(num_rows, num_cols, headers, rows):
    cells = [c for r in rows for c in r]
    return TableGrid(
        bbox=(0, 0, 500, 300),
        num_rows=num_rows,
        num_cols=num_cols,
        col_boundaries=[(0, 250), (250, 500)],
        row_boundaries=[(i * 30, (i + 1) * 30) for i in range(num_rows)],
        col_headers=headers,
        cells=cells,
        rows=rows,
    )


def test_canonical_ocr_key():
    """Verify canonical equivalence mappings (O/0, I/1, L/1, S/5, B/8, Z/2)."""
    assert canonical_ocr_key("SOL-ORISSA.O1") == "5010R155A01"
    assert canonical_ocr_key("SOL-ORISSA-01") == "5010R155A01"
    assert canonical_ocr_key("SUITE-S01") == "5U1TE501"
    assert canonical_ocr_key("SUITE-501") == "5U1TE501"
    assert canonical_ocr_key("BATCH-B82") == "8ATCH882"
    assert canonical_ocr_key("ZONE-Z2") == "20NE22"


def test_find_matching_row_canonical_equivalence():
    """Verify recovery of degraded row labels via canonical OCR equivalence."""
    row0 = [
        TableCell(text="Item Code", bbox=(10, 10, 50, 20), row=0, col=0, conf=95.0),
        TableCell(text="Qty", bbox=(60, 10, 90, 20), row=0, col=1, conf=95.0),
    ]
    # Row with degraded label 'SOL-ORISSA.O1' instead of 'SOL-ORISSA-01'
    row1 = [
        TableCell(text="SOL-ORISSA.O1", bbox=(10, 25, 50, 35), row=1, col=0, conf=88.0),
        TableCell(text="450", bbox=(60, 25, 90, 35), row=1, col=1, conf=92.0),
    ]
    grid = _make_grid(2, 2, ["Item Code", "Qty"], [row0, row1])

    r_idx, matched_row, score, method = find_matching_row_evidence_guided(
        grid=grid,
        target_pattern="SOL-ORISSA-01",
        expected_type="count",
        target_col=1,
    )

    assert r_idx == 1
    assert matched_row is not None
    assert method == "canonical_equivalence"
    assert score == 0.95


def test_find_matching_row_levenshtein_margin_guard():
    """Verify Levenshtein matching succeeds only when margin >= 0.15."""
    row0 = [
        TableCell(text="Product", bbox=(10, 10, 50, 20), row=0, col=0, conf=95.0),
        TableCell(text="Price", bbox=(60, 10, 90, 20), row=0, col=1, conf=95.0),
    ]
    # Single near match: 'AMOXICILIN' vs 'AMOXICILLIN'
    row1 = [
        TableCell(text="AMOXICILIN 500MG", bbox=(10, 25, 50, 35), row=1, col=0, conf=85.0),
        TableCell(text="125.50", bbox=(60, 25, 90, 35), row=1, col=1, conf=90.0),
    ]
    grid = _make_grid(2, 2, ["Product", "Price"], [row0, row1])

    r_idx, matched_row, score, method = find_matching_row_evidence_guided(
        grid=grid,
        target_pattern="AMOXICILLIN 500MG",
        expected_type="amount",
        target_col=1,
    )

    assert r_idx == 1
    assert method == "levenshtein_similarity"
    assert score >= 0.85


def test_levenshtein_rejects_ambiguous_candidates():
    """Verify Levenshtein matching rejects collision when two rows have near-identical similarity."""
    row0 = [
        TableCell(text="Product", bbox=(10, 10, 50, 20), row=0, col=0, conf=95.0),
        TableCell(text="Price", bbox=(60, 10, 90, 20), row=0, col=1, conf=95.0),
    ]
    row1 = [
        TableCell(text="BATCH-ORD-500-A", bbox=(10, 25, 50, 35), row=1, col=0, conf=85.0),
        TableCell(text="100.00", bbox=(60, 25, 90, 35), row=1, col=1, conf=90.0),
    ]
    row2 = [
        TableCell(text="BATCH-ORD-500-B", bbox=(10, 40, 50, 50), row=2, col=0, conf=85.0),
        TableCell(text="200.00", bbox=(60, 40, 90, 50), row=2, col=1, conf=90.0),
    ]
    grid = _make_grid(3, 2, ["Product", "Price"], [row0, row1, row2])

    # Target 'BATCH-ORD-500' is equally close to both rows, margin guard must reject it
    r_idx, matched_row, score, method = find_matching_row_evidence_guided(
        grid=grid,
        target_pattern="BATCH-ORD-500",
        expected_type="amount",
        target_col=1,
    )

    assert r_idx is None
    assert matched_row is None


def test_extract_cell_by_intersection_recovery_and_confidence():
    """Verify end-to-end recovery through extract_cell_by_intersection with provenance and confidence adjustment."""
    row0 = [
        TableCell(text="Description", bbox=(10, 10, 50, 20), row=0, col=0, conf=98.0),
        TableCell(text="Balance", bbox=(60, 10, 90, 20), row=0, col=1, conf=98.0),
    ]
    # Label degraded with 'O' instead of '0'
    row1 = [
        TableCell(text="SUITE-S01", bbox=(10, 25, 50, 35), row=1, col=0, conf=80.0),
        TableCell(text="1450.00", bbox=(60, 25, 90, 35), row=1, col=1, conf=80.0),
    ]
    grid = _make_grid(2, 2, ["Description", "Balance"], [row0, row1])

    ev = extract_cell_by_intersection(
        grid=grid,
        field_name="suite_balance",
        row_pattern="SUITE-501",
        col_pattern="Balance",
        expected_type="amount",
    )

    assert ev is not None
    assert ev.value == "1450.00"
    assert ev.verification_decision == "VERIFY"
    assert ev.provenance["row_recovery_method"] == "canonical_equivalence"
    assert ev.provenance["row_recovery_score"] == 0.95
    # Cell conf penalized: 80.0 * 0.95 = 76.0
    assert pytest.approx(ev.confidence, 0.1) == 76.0


def test_fuzzy_recovery_low_conf_abstention():
    """Verify that a fuzzy Levenshtein match with cell conf < 75.0 abstains for safety."""
    row0 = [
        TableCell(text="Description", bbox=(10, 10, 50, 20), row=0, col=0, conf=98.0),
        TableCell(text="Balance", bbox=(60, 10, 90, 20), row=0, col=1, conf=98.0),
    ]
    # Minor fuzzy match but low cell confidence (70.0 * 0.9 = 63.0 < 75.0)
    row1 = [
        TableCell(text="AMOXICILIN", bbox=(10, 25, 50, 35), row=1, col=0, conf=80.0),
        TableCell(text="1450.00", bbox=(60, 25, 90, 35), row=1, col=1, conf=72.0),
    ]
    grid = _make_grid(2, 2, ["Description", "Balance"], [row0, row1])

    ev = extract_cell_by_intersection(
        grid=grid,
        field_name="amox_balance",
        row_pattern="AMOXICILLIN",
        col_pattern="Balance",
        expected_type="amount",
    )

    assert ev is not None
    # Confidence is 72.0 * ~0.9 = ~64.8 < 75.0 -> ABSTAIN
    assert ev.verification_decision == "ABSTAIN"
    assert "Low OCR confidence" in ev.abstention_reason
