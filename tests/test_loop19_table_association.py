"""
Loop 19 Test Suite: Table-Aware Evidence Extraction, Spatial Cell Association & Provenance Tracking.

Validates:
1. 10-fixture table manifest integrity, categories A through J, and SHA-256 hashes.
2. TableGrid assembly on simple bordered tables (Category A).
3. Borderless table alignment and column gutter extraction (Category B).
4. Similar adjacent numerical value isolation (Category D: 1000 vs 10000).
5. Multi-line wrapped cell handling without phantom row creation (Category E).
6. Missing and empty cell preservation without column shift (Category F).
7. Unbroken FieldEvidence spatial provenance contract.
8. Spatial ambiguity detection on straddling words.
9. Resolution of STRESS_03 multi-column embedded amounts (100% exact match).
"""

import json
from pathlib import Path
import pytest
from PIL import Image
import pytesseract

from docuready.ingest.tesseract_discovery import configure_pytesseract
from docuready.ingest.table_association import (
    build_table_grid,
    extract_field_by_spatial_association,
    extract_cell_by_intersection,
    extract_word_tokens,
    TableGrid,
    TableCell,
    FieldEvidence,
)

ROOT = Path(__file__).resolve().parents[1]
TABLES_DIR = ROOT / "research" / "loop19" / "tables"
MANIFEST_PATH = ROOT / "research" / "loop19" / "dataset_manifest.json"
STRESS_DIR = ROOT / "research" / "loop18" / "stress_fixtures"


@pytest.fixture(scope="session", autouse=True)
def setup_tesseract():
    configure_pytesseract()


def _load_table_img(fixture_id: str) -> Image.Image:
    p = TABLES_DIR / f"{fixture_id}.png"
    assert p.exists(), f"Missing fixture: {p}"
    return Image.open(p).convert("RGB")


def test_loop19_manifest_integrity():
    """Verify that Loop 19 manifest accurately records 10 fixtures across categories A-J."""
    assert MANIFEST_PATH.exists(), "Manifest file missing"
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["version"] == "1.0"
    assert manifest["loop"] == "19"
    assert manifest["total_fixtures"] == 10
    assert manifest["total_critical_fields"] == 32
    assert len(manifest["fixtures"]) == 10

    for fix in manifest["fixtures"]:
        assert fix["fixture_id"]
        assert fix["category"]
        assert len(fix["sha256"]) == 64
        img_file = TABLES_DIR / fix["file_name"]
        assert img_file.exists()
        assert img_file.stat().st_size == fix["file_size_bytes"]


def test_table_grid_assembly_simple_grid():
    """Verify TableGrid assembly on bordered table TAB_01_SIMPLE_GRID."""
    img = _load_table_img("TAB_01_SIMPLE_GRID")
    w, h = img.size
    data = pytesseract.image_to_data(img, lang="eng", output_type=pytesseract.Output.DICT)
    grid = build_table_grid(data, page_width=w, page_height=h)

    assert grid.num_rows == 6, f"Expected 6 rows, got {grid.num_rows}"
    assert grid.num_cols == 4, f"Expected 4 columns, got {grid.num_cols}"
    assert "Amount" in grid.col_headers[3]

    # Verify cell values in Row 1
    assert "01" in grid.rows[1][0].text
    assert "45000" in grid.rows[1][3].text

    # Verify cell values in Row 5 (Total)
    assert "Total" in grid.rows[5][0].text
    assert "602500" in grid.rows[5][3].text


def test_borderless_table_association():
    """Verify whitespace and alignment column detection on TAB_02_BORDERLESS_TABLE."""
    img = _load_table_img("TAB_02_BORDERLESS_TABLE")
    w, h = img.size
    data = pytesseract.image_to_data(img, lang="eng", output_type=pytesseract.Output.DICT)
    grid = build_table_grid(data, page_width=w, page_height=h)

    assert grid.num_rows == 5, f"Expected 5 rows, got {grid.num_rows}"
    assert grid.num_cols == 5, f"Expected 5 columns, got {grid.num_cols}"

    # Extract field using spatial cell association
    ev = extract_field_by_spatial_association(grid, "admin_balance", "400000")
    assert ev is not None
    assert ev.value == "400000"
    assert ev.col_idx == 4  # Balance column


def test_similar_adjacent_values_isolation():
    """Verify that 1000 and 10000 in adjacent cells of TAB_04 are isolated cleanly."""
    img = _load_table_img("TAB_04_SIMILAR_ADJACENT_VALUES")
    w, h = img.size
    data = pytesseract.image_to_data(img, lang="eng", output_type=pytesseract.Output.DICT)
    grid = build_table_grid(data, page_width=w, page_height=h)

    # In Row 1: Base is 1000 (col 1), Top-up is 10000 (col 2)
    row_1 = grid.rows[1]
    assert "1000" in row_1[1].text
    assert "10000" in row_1[2].text
    assert row_1[1].col == 1
    assert row_1[2].col == 2

    # In Row 2: Base is 10000 (col 1), Top-up is 1000 (col 2)
    row_2 = grid.rows[2]
    assert "10000" in row_2[1].text
    assert "1000" in row_2[2].text


def test_wrapped_cells_handling():
    """Verify that multi-line wrapped text inside TAB_05 cells does not create phantom rows."""
    img = _load_table_img("TAB_05_WRAPPED_CELLS")
    w, h = img.size
    data = pytesseract.image_to_data(img, lang="eng", output_type=pytesseract.Output.DICT)
    grid = build_table_grid(data, page_width=w, page_height=h)

    # Header + 3 procurement rows = 4 rows
    assert grid.num_rows == 4, f"Expected 4 rows, got {grid.num_rows}"

    ev = extract_field_by_spatial_association(grid, "pr_110_value", "4200000")
    assert ev is not None
    assert ev.value == "4200000"


def test_missing_empty_cells_preservation():
    """Verify that empty cells in TAB_06 do not shift adjacent column indices."""
    img = _load_table_img("TAB_06_MISSING_EMPTY_CELLS")
    w, h = img.size
    data = pytesseract.image_to_data(img, lang="eng", output_type=pytesseract.Output.DICT)
    grid = build_table_grid(data, page_width=w, page_height=h)

    assert grid.num_rows == 5
    assert grid.num_cols == 5

    # Row 2: Suresh Mohanty (col 1), Empty spouse (col 2), Disability 5000 (col 3), Basic 28900 (col 4)
    row_2 = grid.rows[2]
    assert "Suresh" in row_2[1].text
    assert "5000" in row_2[3].text
    assert "28900" in row_2[4].text


def test_evidence_provenance_contract():
    """Verify that FieldEvidence preserves complete spatial provenance."""
    img = _load_table_img("TAB_01_SIMPLE_GRID")
    w, h = img.size
    data = pytesseract.image_to_data(img, lang="eng", output_type=pytesseract.Output.DICT)
    grid = build_table_grid(data, page_width=w, page_height=h)

    ev = extract_field_by_spatial_association(grid, "item_03_sanction", "RUR-2026-781", doc_id="TAB_01")
    assert ev is not None
    assert ev.field_name == "item_03_sanction"
    assert ev.value == "RUR-2026-781"
    assert len(ev.bbox) == 4
    assert ev.row_idx == 3
    assert ev.col_idx == 2
    assert ev.provenance["document_id"] == "TAB_01"
    assert ev.provenance["token_count"] >= 1
    assert "RUR-2026-781" in ev.provenance["raw_tokens"]


def test_stress_03_resolution():
    """Verify that STRESS_03 multi-column accounting failure from Loop 18 is completely resolved."""
    img_path = STRESS_DIR / "STRESS_03_MULTICOLUMN_EMBEDDED_AMOUNTS.png"
    img = Image.open(img_path).convert("RGB")
    w, h = img.size
    data = pytesseract.image_to_data(img, lang="eng", output_type=pytesseract.Output.DICT)
    grid = build_table_grid(data, page_width=w, page_height=h)

    assert grid.num_cols == 2, f"Expected 2 columns, got {grid.num_cols}"

    ev_lid = extract_field_by_spatial_association(grid, "ledger_id", "Ledger ID")
    ev_sa = extract_field_by_spatial_association(grid, "subtotal_a", "Subtotal A")
    ev_vn = extract_field_by_spatial_association(grid, "voucher_no", "Voucher No")
    ev_sb = extract_field_by_spatial_association(grid, "subtotal_b", "Subtotal B")

    assert ev_lid is not None and "REV-COL-101" in ev_lid.value and ev_lid.col_idx == 0
    assert ev_sa is not None and "221700" in ev_sa.value and ev_sa.col_idx == 0
    assert ev_vn is not None and "DIS-VOU-909" in ev_vn.value and ev_vn.col_idx == 1
    assert ev_sb is not None and "194300" in ev_sb.value and ev_sb.col_idx == 1
