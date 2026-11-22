"""
Table-Aware Evidence Extraction, Spatial Cell Association & Provenance Tracking
DocuReady - Structured Ingestion Subsystem

Provides robust, offline, geometry-driven table detection and field-to-cell association:
  - Detects column gutters and horizontal row boundaries using 1D projection profiling
  - Reconstructs 2D cell grids without destructive whole-image cropping
  - Separates full-width title banners from multi-column tabular bodies
  - Binds OCR word tokens to (row, column) coordinates with center-point membership
  - Distinguishes header rows, label cells, and value cells
  - Detects spatial ambiguity (e.g. cross-column bridging words) for safe abstention
  - Preserves complete spatial provenance for downstream evidence verification
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


@dataclass
class TableCell:
    """Represents a discrete structural cell within a table grid."""
    row: int
    col: int
    bbox: Tuple[int, int, int, int]  # (left, top, right, bottom) in pixels
    text: str = ""
    words: List[Dict[str, Any]] = field(default_factory=list)
    conf: float = 0.0
    is_header: bool = False
    is_ambiguous: bool = False


@dataclass
class TableGrid:
    """Represents an assembled 2D table grid with row and column semantics."""
    bbox: Tuple[int, int, int, int]
    num_rows: int
    num_cols: int
    col_boundaries: List[Tuple[int, int]]  # [(left, right), ...]
    row_boundaries: List[Tuple[int, int]]  # [(top, bottom), ...]
    col_headers: List[str]
    cells: List[TableCell]
    rows: List[List[TableCell]] = field(default_factory=list)
    banner_text: str = ""


@dataclass
class FieldEvidence:
    """Traceable evidence binding an extracted field to its spatial cell origin."""
    field_name: str
    value: str
    raw_text: str
    bbox: Tuple[int, int, int, int]
    row_idx: int
    col_idx: int
    col_header: str
    confidence: float
    is_ambiguous: bool
    provenance: Dict[str, Any]


def normalize_token_text(text: str) -> str:
    if not text:
        return ""
    norm = unicodedata.normalize("NFC", text)
    norm = re.sub(r"[ \t]+", " ", norm)
    return norm.strip()


def extract_word_tokens(ocr_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extracts valid word bounding boxes from Tesseract image_to_data dictionary."""
    words = []
    texts = ocr_data.get("text", [])
    confs = ocr_data.get("conf", [])
    lefts = ocr_data.get("left", [])
    tops = ocr_data.get("top", [])
    widths = ocr_data.get("width", [])
    heights = ocr_data.get("height", [])

    for i in range(len(texts)):
        txt = str(texts[i]).strip()
        c = float(confs[i]) if i < len(confs) and confs[i] != "" else -1.0
        # Filter empty tokens and vertical grid line stroke artifacts (| or ¦)
        if txt and c >= 0 and txt not in ["|", "¦"]:
            l = int(lefts[i])
            t = int(tops[i])
            w = int(widths[i])
            h = int(heights[i])
            words.append({
                "text": txt,
                "conf": c,
                "left": l,
                "top": t,
                "width": w,
                "height": h,
                "right": l + w,
                "bottom": t + h,
                "center_x": l + w / 2.0,
                "center_y": t + h / 2.0,
            })
    return words


def cluster_rows(words: List[Dict[str, Any]], vertical_tolerance: int = 8) -> List[Tuple[int, int, List[Dict[str, Any]]]]:
    """
    Clusters words into horizontal rows based on vertical overlap.
    Returns sorted rows: [(row_top, row_bottom, [words_in_row]), ...]
    """
    if not words:
        return []

    sorted_words = sorted(words, key=lambda w: (w["top"], w["left"]))
    rows: List[List[Dict[str, Any]]] = []

    for w in sorted_words:
        placed = False
        for r in rows:
            r_top = min(item["top"] for item in r)
            r_bot = max(item["bottom"] for item in r)
            r_h = r_bot - r_top
            overlap = min(w["bottom"], r_bot) - max(w["top"], r_top)
            if overlap > 0.45 * min(w["height"], r_h) or abs(w["center_y"] - (r_top + r_bot) / 2.0) <= vertical_tolerance:
                r.append(w)
                placed = True
                break
        if not placed:
            rows.append([w])

    row_clusters = []
    for r in rows:
        r_top = min(item["top"] for item in r)
        r_bot = max(item["bottom"] for item in r)
        r_sorted = sorted(r, key=lambda item: item["left"])
        row_clusters.append((r_top, r_bot, r_sorted))

    row_clusters.sort(key=lambda item: item[0])
    return row_clusters


def detect_column_gutters_from_multi_rows(
    rows: List[Tuple[int, int, List[Dict[str, Any]]]],
    page_width: int,
    min_internal_gap: int = 35,
    min_gutter_width: int = 25,
) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int, List[Dict[str, Any]]]], str]:
    """
    Separates full-width banners from multi-column rows and identifies true column intervals.
    """
    banner_texts = []
    multi_col_rows = []

    for r_top, r_bot, r_words in rows:
        has_internal_gap = False
        for i in range(len(r_words) - 1):
            gap = r_words[i + 1]["left"] - r_words[i]["right"]
            if gap >= min_internal_gap:
                has_internal_gap = True
                break
        if has_internal_gap:
            multi_col_rows.append((r_top, r_bot, r_words))
        else:
            line_txt = " ".join(w["text"] for w in r_words)
            banner_texts.append(line_txt)

    if not multi_col_rows:
        return [(0, page_width)], rows, "\n".join(banner_texts)

    # 1D projection over words in multi-column rows only
    occupancy = np.zeros(page_width, dtype=np.int32)
    for _, _, r_words in multi_col_rows:
        for w in r_words:
            l = max(0, min(page_width - 1, w["left"]))
            r = max(0, min(page_width, w["right"]))
            if r > l:
                occupancy[l:r] += 1

    # Find column boundaries separated by zero-occupancy valleys
    columns = []
    in_col = False
    col_start = 0

    for x in range(page_width):
        if occupancy[x] > 0 and not in_col:
            in_col = True
            col_start = x
        elif occupancy[x] == 0 and in_col:
            gap_len = 0
            while (x + gap_len < page_width) and (occupancy[x + gap_len] == 0):
                gap_len += 1
            if gap_len >= min_gutter_width:
                in_col = False
                col_end = x
                if col_end - col_start > 20:
                    columns.append((col_start, col_end))

    if in_col:
        columns.append((col_start, page_width))

    if not columns:
        columns = [(0, page_width)]

    return columns, multi_col_rows, "\n".join(banner_texts)


def build_table_grid(
    ocr_data: Dict[str, Any],
    page_width: int,
    page_height: int,
    region_bbox: Optional[Tuple[int, int, int, int]] = None,
    min_internal_gap: int = 35,
    min_gutter_width: int = 25,
) -> TableGrid:
    """
    Constructs a complete 2D TableGrid by mapping OCR words to row and column intervals.
    """
    all_words = extract_word_tokens(ocr_data)

    if region_bbox:
        rx1, ry1, rx2, ry2 = region_bbox
        words = [w for w in all_words if (rx1 <= w["center_x"] <= rx2 and ry1 <= w["center_y"] <= ry2)]
    else:
        words = all_words
        rx1, ry1, rx2, ry2 = 0, 0, page_width, page_height

    if not words:
        return TableGrid(
            bbox=(rx1, ry1, rx2, ry2),
            num_rows=0,
            num_cols=0,
            col_boundaries=[],
            row_boundaries=[],
            col_headers=[],
            cells=[],
            rows=[],
            banner_text="",
        )

    all_rows = cluster_rows(words, vertical_tolerance=8)
    cols, table_rows, banner_txt = detect_column_gutters_from_multi_rows(
        all_rows,
        page_width=page_width,
        min_internal_gap=min_internal_gap,
        min_gutter_width=min_gutter_width,
    )

    num_rows = len(table_rows)
    num_cols = len(cols)
    row_bounds = [(r[0], r[1]) for r in table_rows]

    grid_cells: List[TableCell] = []
    grid_rows: List[List[TableCell]] = []

    for r_idx, (r_top, r_bot, r_words) in enumerate(table_rows):
        row_cell_list = []
        for c_idx, (c_left, c_right) in enumerate(cols):
            cell_words = [
                w for w in r_words
                if (c_left - 10 <= w["center_x"] <= c_right + 10)
            ]
            cell_text = " ".join([w["text"] for w in cell_words]).strip()
            cell_conf = sum(w["conf"] for w in cell_words) / len(cell_words) if cell_words else 0.0

            if cell_words:
                c_bbox = (
                    min(w["left"] for w in cell_words),
                    min(w["top"] for w in cell_words),
                    max(w["right"] for w in cell_words),
                    max(w["bottom"] for w in cell_words),
                )
            else:
                c_bbox = (c_left, r_top, c_right, r_bot)

            ambiguous = False
            for w in cell_words:
                if w["left"] < c_left - 20 or w["right"] > c_right + 20:
                    ambiguous = True
                    break

            cell = TableCell(
                row=r_idx,
                col=c_idx,
                bbox=c_bbox,
                text=cell_text,
                words=cell_words,
                conf=round(cell_conf, 2),
                is_header=(r_idx == 0),
                is_ambiguous=ambiguous,
            )
            grid_cells.append(cell)
            row_cell_list.append(cell)
        grid_rows.append(row_cell_list)

    headers = [cell.text for cell in grid_rows[0]] if grid_rows else []

    return TableGrid(
        bbox=(rx1, ry1, rx2, ry2),
        num_rows=num_rows,
        num_cols=num_cols,
        col_boundaries=cols,
        row_boundaries=row_bounds,
        col_headers=headers,
        cells=grid_cells,
        rows=grid_rows,
        banner_text=banner_txt,
    )


def extract_cell_by_intersection(
    grid: TableGrid,
    field_name: str,
    row_pattern: str,
    col_pattern: Optional[str] = None,
    col_idx: Optional[int] = None,
    doc_id: str = "doc",
    page_idx: int = 0,
) -> Optional[FieldEvidence]:
    """
    Extracts the cell value at the intersection of a matched row and column header.
    """
    target_col = -1
    if col_idx is not None and 0 <= col_idx < grid.num_cols:
        target_col = col_idx
    elif col_pattern:
        for c_idx, h in enumerate(grid.col_headers):
            if col_pattern.upper() in h.upper():
                target_col = c_idx
                break
    if target_col == -1:
        return None

    norm_row_pattern = normalize_token_text(row_pattern).upper()
    matching_rows = []
    for r_idx, row in enumerate(grid.rows):
        row_text = " ".join(c.text for c in row).upper()
        if norm_row_pattern in row_text:
            matching_rows.append((r_idx, row))

    if not matching_rows:
        return None

    # Ambiguity check: multiple rows match the same row_pattern (e.g. repeated account number)
    is_multi_row = (len(matching_rows) > 1)
    r_idx, row = matching_rows[0]
    cell = row[target_col]
    clean_val = cell.text.strip()
    clean_val = re.sub(r"^(Rs\.?|INR|₹)\s*", "", clean_val, flags=re.IGNORECASE).strip()

    ambiguous = cell.is_ambiguous or is_multi_row

    return FieldEvidence(
        field_name=field_name,
        value=clean_val,
        raw_text=cell.text,
        bbox=cell.bbox,
        row_idx=cell.row,
        col_idx=cell.col,
        col_header=grid.col_headers[target_col] if target_col < len(grid.col_headers) else "",
        confidence=cell.conf,
        is_ambiguous=ambiguous,
        provenance={
            "document_id": doc_id,
            "page_index": page_idx,
            "cell_bbox": cell.bbox,
            "token_count": len(cell.words),
            "raw_tokens": [w["text"] for w in cell.words],
            "query_mode": "row_col_intersection",
            "multiple_row_matches": is_multi_row,
        },
    )


def extract_field_by_spatial_association(
    grid: TableGrid,
    field_name: str,
    target_pattern: str,
    col_pattern: Optional[str] = None,
    col_idx: Optional[int] = None,
    expected_type: Optional[str] = None,
    doc_id: str = "doc",
    page_idx: int = 0,
) -> Optional[FieldEvidence]:
    """
    Extracts a critical field value using spatial association:
      - If col_pattern or col_idx is provided: performs strict row-and-column intersection
      - If col_pattern is omitted: searches for label in cell and binds to adjacent or inline value
      - Rejects label-echoes (where label is falsely returned as value)
      - Detects and preserves empty cells without spurious adjacent value inheritance
      - Gated by syntactic type checks for reliable evidence-based abstention
    """
    # 1. If column context is provided, delegate to cell intersection
    if col_pattern is not None or col_idx is not None:
        ev = extract_cell_by_intersection(
            grid=grid,
            field_name=field_name,
            row_pattern=target_pattern,
            col_pattern=col_pattern or "",
            col_idx=col_idx,
            doc_id=doc_id,
            page_idx=page_idx,
        )
        if ev:
            # Validate syntax / label echo
            if expected_type == "empty" and ev.value != "":
                ev.is_ambiguous = True
            elif expected_type == "amount" and ev.value and not re.search(r"\d", ev.value):
                ev.is_ambiguous = True
            elif expected_type == "date" and ev.value and not re.search(r"\d{1,2}[/-]\d{1,2}", ev.value):
                ev.is_ambiguous = True
            return ev

    norm_target = normalize_token_text(target_pattern).upper()

    for r_idx, row in enumerate(grid.rows):
        for c_idx, cell in enumerate(row):
            norm_cell = normalize_token_text(cell.text).upper()
            if norm_target in norm_cell:
                raw_text = cell.text
                target_cell = cell

                # Case A: Direct exact match of token/value within cell
                if norm_target == norm_cell:
                    clean_val = raw_text.strip()
                    target_cell = cell
                # Case B: Value is inline after colon
                elif ":" in raw_text:
                    parts = raw_text.split(":", 1)
                    clean_val = parts[1].strip()
                    clean_val = re.sub(r"^(Rs\.?|INR|₹)\s*", "", clean_val, flags=re.IGNORECASE).strip()
                # Case C: Value is in adjacent column to the right
                elif c_idx + 1 < len(row):
                    val_cell = row[c_idx + 1]
                    clean_val = val_cell.text.strip()
                    clean_val = re.sub(r"^(Rs\.?|INR|₹)\s*", "", clean_val, flags=re.IGNORECASE).strip()
                    target_cell = val_cell
                else:
                    clean_val = raw_text.strip()

                # Label echo check: only flag if field was expected to be an amount, date, or empty
                is_label_echo = False
                if expected_type in ["amount", "date", "empty"] and clean_val.upper() == norm_target:
                    is_label_echo = True
                    clean_val = ""

                ambiguous = target_cell.is_ambiguous or is_label_echo

                # Type-specific validation
                if expected_type == "empty" and clean_val != "":
                    ambiguous = True
                elif expected_type == "amount" and clean_val and not re.search(r"\d", clean_val):
                    ambiguous = True
                elif expected_type == "date" and clean_val and not re.search(r"\d{1,2}[/-]\d{1,2}", clean_val):
                    ambiguous = True

                return FieldEvidence(
                    field_name=field_name,
                    value=clean_val,
                    raw_text=raw_text,
                    bbox=target_cell.bbox,
                    row_idx=target_cell.row,
                    col_idx=target_cell.col,
                    col_header=grid.col_headers[target_cell.col] if target_cell.col < len(grid.col_headers) else "",
                    confidence=target_cell.conf,
                    is_ambiguous=ambiguous,
                    provenance={
                        "document_id": doc_id,
                        "page_index": page_idx,
                        "cell_bbox": target_cell.bbox,
                        "token_count": len(target_cell.words),
                        "raw_tokens": [w["text"] for w in target_cell.words],
                        "query_mode": "spatial_cell_binding",
                        "label_echo_rejected": is_label_echo,
                    },
                )

    return None


def verify_cross_document_evidence(
    ev1: Optional[FieldEvidence],
    ev2: Optional[FieldEvidence],
    field_type: str = "text",
) -> Dict[str, Any]:
    """
    Verifies cross-document agreement between two pieces of spatial field evidence.
    Returns discrete classification:
      - AGREEMENT
      - MISMATCH
      - MISSING
      - UNREADABLE
      - AMBIGUOUS_ASSOCIATION
      - INSUFFICIENT_EVIDENCE
    """
    if ev1 is None and ev2 is None:
        return {
            "status": "MISSING",
            "is_verified": False,
            "reason": "Field absent in both documents",
            "ev1_value": None,
            "ev2_value": None,
        }

    if ev1 is None or ev2 is None:
        return {
            "status": "MISSING",
            "is_verified": False,
            "reason": "Field present in one document but missing in the second document",
            "ev1_value": ev1.value if ev1 else None,
            "ev2_value": ev2.value if ev2 else None,
        }

    if ev1.value == "" or ev2.value == "":
        return {
            "status": "MISSING",
            "is_verified": False,
            "reason": "Field cell is empty in one or both documents",
            "ev1_value": ev1.value,
            "ev2_value": ev2.value,
        }

    if ev1.is_ambiguous or ev2.is_ambiguous:
        return {
            "status": "AMBIGUOUS_ASSOCIATION",
            "is_verified": False,
            "reason": "Cell evidence has ambiguous spatial boundaries or multiple candidate rows",
            "ev1_value": ev1.value,
            "ev2_value": ev2.value,
        }

    if ev1.confidence < 30.0 or ev2.confidence < 30.0:
        return {
            "status": "UNREADABLE",
            "is_verified": False,
            "reason": f"OCR confidence is below legible threshold (ev1: {ev1.confidence}%, ev2: {ev2.confidence}%)",
            "ev1_value": ev1.value,
            "ev2_value": ev2.value,
        }

    # Normalize values for fair semantic comparison
    v1 = ev1.value.strip().replace("₹", "").replace("Rs.", "").replace("INR", "").replace(",", "").replace(" ", "").upper()
    v2 = ev2.value.strip().replace("₹", "").replace("Rs.", "").replace("INR", "").replace(",", "").replace(" ", "").upper()

    if v1 == v2:
        return {
            "status": "AGREEMENT",
            "is_verified": True,
            "reason": "Values match exactly with verifiable cell provenance in both documents",
            "ev1_value": ev1.value,
            "ev2_value": ev2.value,
            "ev1_bbox": ev1.bbox,
            "ev2_bbox": ev2.bbox,
        }
    else:
        return {
            "status": "MISMATCH",
            "is_verified": False,
            "reason": f"Evidence discrepancy: Document 1 has '{ev1.value}' while Document 2 has '{ev2.value}'",
            "ev1_value": ev1.value,
            "ev2_value": ev2.value,
            "ev1_bbox": ev1.bbox,
            "ev2_bbox": ev2.bbox,
        }
