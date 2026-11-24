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
    verification_decision: str = "VERIFY"
    abstention_reason: Optional[str] = None


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

    # Detect if row 0 is a spanning multi-tier super-header bridging gutters of child columns
    exclude_first_row = False
    if len(multi_col_rows) >= 3:
        r0_words = multi_col_rows[0][2]
        r1_words = multi_col_rows[1][2]

        def _has_digit(w_list: List[Dict[str, Any]]) -> bool:
            return any(any(c.isdigit() for c in w["text"]) for w in w_list)

        if not _has_digit(r0_words) and not _has_digit(r1_words) and any(_has_digit(r[2]) for r in multi_col_rows[2:]):
            if len(r0_words) < len(r1_words):
                exclude_first_row = True

    projection_rows = multi_col_rows[1:] if exclude_first_row else multi_col_rows

    # 1D projection over words in multi-column rows
    occupancy = np.zeros(page_width, dtype=np.int32)
    for _, _, r_words in projection_rows:
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


def refine_cell_decimal_point(cell_text: str, cell_crop: Any) -> str:
    """
    Detects dropped baseline decimal points in low-resolution OCR crops using
    fast pixel morphology (NumPy). When a 1-3px strictly isolated dot is detected in the
    baseline zone between digits, re-inserts the decimal point into cell_text.
    Strictly isolated: requires pure whitespace left, right, and above the dot to prevent
    character strokes (e.g. crossbar of '4') from triggering false decimals.
    Execution time: ~0.05ms per check (pure NumPy, zero subprocess overhead).
    """
    if not cell_text or "." in cell_text or cell_crop is None:
        return cell_text

    clean_digits = re.sub(r"^(Rs\.?|INR|₹)\s*", "", cell_text, flags=re.IGNORECASE).replace(",", "").strip()
    if not clean_digits.isdigit() or not (2 <= len(clean_digits) <= 4):
        return cell_text

    # Numbers with trailing zero >= 100 like 640, 4000, 3100, 4830 are standard integers
    if len(clean_digits) >= 3 and clean_digits.endswith("0"):
        return cell_text

    try:
        if hasattr(cell_crop, "convert"):
            arr = np.array(cell_crop.convert("L"))
        elif isinstance(cell_crop, np.ndarray):
            arr = cell_crop
        else:
            return cell_text

        h, w = arr.shape[:2]
        if h < 8 or w < 10:
            return cell_text

        thresh = (int(arr.min()) + int(arr.max())) // 2
        binary = arr < thresh  # True for ink (dark)

        # A genuine decimal dot is strictly at the baseline (bottom 30% of character height)
        baseline_zone_start = int(h * 0.70)
        upper_ink = binary[:baseline_zone_start, :].sum(axis=0)
        gap_cols = np.where(upper_ink == 0)[0]
        if len(gap_cols) == 0:
            return cell_text

        gaps = []
        curr = [gap_cols[0]]
        for c in gap_cols[1:]:
            if c == curr[-1] + 1:
                curr.append(c)
            else:
                gaps.append(curr)
                curr = [c]
        gaps.append(curr)

        dot_x = None
        for g in gaps:
            # Must be an interior gap with blank columns on both sides (not edge of crop)
            if g[0] >= 2 and g[-1] <= w - 3 and len(g) >= 2:
                gap_sub = binary[baseline_zone_start:h, g]
                dot_ink = gap_sub.sum()
                if 1 <= dot_ink <= 6:
                    dot_rows, dot_cols = np.where(gap_sub)
                    dot_abs_rows = baseline_zone_start + dot_rows
                    dot_abs_cols = g[0] + dot_cols

                    min_c = dot_abs_cols.min()
                    max_c = dot_abs_cols.max()

                    # Dot must be strictly isolated: zero ink in adjacent columns across the dot rows
                    left_ink = binary[dot_abs_rows, min_c - 1].sum() if min_c > 0 else 1
                    right_ink = binary[dot_abs_rows, max_c + 1].sum() if max_c < w - 1 else 1

                    # Zero ink above the dot for at least 2 rows
                    min_r = dot_abs_rows.min()
                    above_ink = binary[max(0, min_r - 2):min_r, min_c:max_c + 1].sum()

                    if left_ink == 0 and right_ink == 0 and above_ink == 0:
                        dot_h = dot_rows.max() - dot_rows.min() + 1
                        dot_w = dot_cols.max() - dot_cols.min() + 1
                        if dot_h <= 3 and dot_w <= 3:
                            dot_x = int(dot_abs_cols.mean())
                            break

        if dot_x is not None:
            num_chars = len(clean_digits)
            char_w = w / num_chars
            insert_idx = int(dot_x / char_w) + 1
            insert_idx = max(1, min(insert_idx, num_chars - 1))
            refined = clean_digits[:insert_idx] + "." + clean_digits[insert_idx:]
            return cell_text.replace(clean_digits, refined)
    except Exception:
        pass

    return cell_text


def build_table_grid(
    ocr_data: Dict[str, Any],
    page_width: int,
    page_height: int,
    region_bbox: Optional[Tuple[int, int, int, int]] = None,
    min_internal_gap: int = 35,
    min_gutter_width: int = 25,
    image: Optional[Any] = None,
) -> TableGrid:
    """
    Constructs a complete 2D TableGrid by mapping OCR words to row and column intervals.
    Automatically detects and fuses multi-tier hierarchical column headers, and
    refines dropped decimal points when image is supplied.
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

            # Refine dropped decimal point if image is provided
            if image is not None and cell_text and ("." not in cell_text):
                bx1, by1, bx2, by2 = c_bbox
                if bx2 > bx1 and by2 > by1:
                    pad = 5
                    pw = image.width if hasattr(image, "width") else bx2 + pad
                    ph = image.height if hasattr(image, "height") else by2 + pad
                    crop = image.crop((max(0, bx1 - pad), max(0, by1 - pad), min(pw, bx2 + pad), min(ph, by2 + pad)))
                    cell_text = refine_cell_decimal_point(cell_text, crop)

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

    # Hierarchical multi-tier header detection and fusion
    if len(grid_rows) >= 3:
        r0 = [c.text.strip() for c in grid_rows[0]]
        r1 = [c.text.strip() for c in grid_rows[1]]

        def _is_numeric_val(t: str) -> bool:
            clean = re.sub(r"^(Rs\.?|INR|₹|[%$€£])\s*", "", t, flags=re.IGNORECASE).replace(",", "").strip()
            if not clean:
                return False
            try:
                float(clean)
                return True
            except ValueError:
                return False

        r0_nums = sum(1 for t in r0 if _is_numeric_val(t))
        r1_nums = sum(1 for t in r1 if _is_numeric_val(t))
        r0_empty = sum(1 for t in r0 if not t)
        r1_empty = sum(1 for t in r1 if not t)

        # Multi-tier signature: both header candidate rows have zero numeric values,
        # and row 0 has empty cells (spanning super-headers) while row 1 has more filled column labels.
        if r0_nums == 0 and r1_nums == 0 and r0_empty > 0 and r1_empty < r0_empty:
            parent_labels: List[str] = []
            curr_parent = ""
            for c in grid_rows[0]:
                txt = c.text.strip()
                if txt:
                    curr_parent = txt
                parent_labels.append(curr_parent)

            fused_col_headers: List[str] = []
            fused_r0: List[TableCell] = []
            for col_i, (p_label, c0, c1) in enumerate(zip(parent_labels, grid_rows[0], grid_rows[1])):
                c1_txt = c1.text.strip()
                if p_label and c1_txt:
                    fused_name = f"{p_label} / {c1_txt}"
                elif c1_txt:
                    fused_name = c1_txt
                else:
                    fused_name = p_label
                fused_col_headers.append(fused_name)

                union_bbox = (
                    min(c0.bbox[0], c1.bbox[0]),
                    min(c0.bbox[1], c1.bbox[1]),
                    max(c0.bbox[2], c1.bbox[2]),
                    max(c0.bbox[3], c1.bbox[3]),
                )
                fused_cell = TableCell(
                    row=0,
                    col=col_i,
                    bbox=union_bbox,
                    text=fused_name,
                    words=c0.words + c1.words,
                    conf=round((c0.conf + c1.conf) / 2.0, 2),
                    is_header=True,
                    is_ambiguous=False,
                )
                fused_r0.append(fused_cell)

            # Replace row 0 with fused row, drop row 1 from data rows, and re-index remaining rows
            new_grid_rows = [fused_r0]
            new_grid_cells = list(fused_r0)
            for new_r_idx, r in enumerate(grid_rows[2:], start=1):
                row_cells = []
                for c in r:
                    c.row = new_r_idx
                    row_cells.append(c)
                    new_grid_cells.append(c)
                new_grid_rows.append(row_cells)

            grid_rows = new_grid_rows
            grid_cells = new_grid_cells
            headers = fused_col_headers
            num_rows = len(grid_rows)
            row_bounds = [(r[0].bbox[1], r[0].bbox[3]) for r in grid_rows]
        else:
            headers = [cell.text for cell in grid_rows[0]] if grid_rows else []
    else:
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
    expected_type: Optional[str] = None,
    doc_id: str = "doc",
    page_idx: int = 0,
    image: Optional[Any] = None,
) -> Optional[FieldEvidence]:
    """
    Extracts the cell value at the intersection of a matched row and column header.
    Validates column header compatibility and guards against multi-row collision.
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

    header_text = grid.col_headers[target_col] if target_col < len(grid.col_headers) else ""
    header_lower = header_text.lower()
    fn_lower = field_name.lower().replace("_", " ")

    # Header-pattern validation if col_pattern provided
    header_mismatch = False
    if col_pattern and col_pattern.strip():
        if not re.search(re.escape(col_pattern.strip()), header_text, re.IGNORECASE):
            if not any(t.lower() in header_lower for t in col_pattern.split() if len(t) >= 3):
                header_mismatch = True

    # Semantic type/category contradiction checks
    type_contradiction = False
    if expected_type == "weight" and any(k in header_lower for k in ["freight", "amount", "rs", "inr"]) and not any(k in header_lower for k in ["weight", "kg", "mt", "wt"]):
        type_contradiction = True
    elif "penalty" in fn_lower and "penalty" not in header_lower and any(k in header_lower for k in ["release", "cleared", "advance", "base"]):
        type_contradiction = True

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

    if image is not None and clean_val and ("." not in clean_val):
        bx1, by1, bx2, by2 = cell.bbox
        if bx2 > bx1 and by2 > by1:
            pad = 5
            pw = image.width if hasattr(image, "width") else bx2 + pad
            ph = image.height if hasattr(image, "height") else by2 + pad
            crop = image.crop((max(0, bx1 - pad), max(0, by1 - pad), min(pw, bx2 + pad), min(ph, by2 + pad)))
            clean_val = refine_cell_decimal_point(clean_val, crop)

    # Integrity and risk-calibrated verification decisions
    is_low_conf = (cell.conf < 60.0)
    is_multi_token = (len(clean_val.split()) > 1 and expected_type in ["amount", "code", "id", "weight", "percentage", "unit"])
    has_syntax_garble = bool(re.search(r"[{}\[\]~|`^§]", clean_val))

    ambiguous = cell.is_ambiguous or is_multi_row or header_mismatch or type_contradiction or is_low_conf or is_multi_token or has_syntax_garble

    verification_decision = "VERIFY"
    abstention_reason = None
    if is_low_conf:
        verification_decision = "ABSTAIN"
        abstention_reason = f"Low OCR confidence ({cell.conf:.1f} < 60.0)"
    elif is_multi_token:
        verification_decision = "ABSTAIN"
        abstention_reason = "Multiple whitespace-separated tokens detected in numeric cell (gutter bleed)"
    elif has_syntax_garble:
        verification_decision = "ABSTAIN"
        abstention_reason = "Stray punctuation or non-alphanumeric syntax garble in extracted text"
    elif type_contradiction:
        verification_decision = "ABSTAIN"
        abstention_reason = f"Column header '{header_text}' contradicts expected field semantic '{field_name}' ({expected_type})"
    elif header_mismatch:
        verification_decision = "ABSTAIN"
        abstention_reason = f"Column header '{header_text}' does not match required pattern '{col_pattern}'"
    elif ambiguous:
        verification_decision = "ABSTAIN"
        abstention_reason = "Ambiguous cell boundaries, label-echo, or multi-row candidate collision"

    return FieldEvidence(
        field_name=field_name,
        value=clean_val,
        raw_text=cell.text,
        bbox=cell.bbox,
        row_idx=cell.row,
        col_idx=cell.col,
        col_header=header_text,
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
            "header_mismatch": header_mismatch,
            "type_contradiction": type_contradiction,
        },
        verification_decision=verification_decision,
        abstention_reason=abstention_reason,
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
    image: Optional[Any] = None,
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
            expected_type=expected_type,
            doc_id=doc_id,
            page_idx=page_idx,
            image=image,
        )
        if ev:
            # Validate syntax / label echo
            if expected_type == "empty" and ev.value != "":
                ev.is_ambiguous = True
                ev.verification_decision = "ABSTAIN"
                ev.abstention_reason = "Spurious value in expected empty cell"
            elif expected_type == "amount" and ev.value and not re.search(r"\d", ev.value):
                ev.is_ambiguous = True
                ev.verification_decision = "ABSTAIN"
                ev.abstention_reason = "Non-numeric value in expected amount field"
            elif expected_type == "date" and ev.value and not re.search(r"\d{1,2}[/-]\d{1,2}", ev.value):
                ev.is_ambiguous = True
                ev.verification_decision = "ABSTAIN"
                ev.abstention_reason = "Invalid date format"
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

                if image is not None and clean_val and ("." not in clean_val):
                    bx1, by1, bx2, by2 = target_cell.bbox
                    if bx2 > bx1 and by2 > by1:
                        pad = 5
                        pw = image.width if hasattr(image, "width") else bx2 + pad
                        ph = image.height if hasattr(image, "height") else by2 + pad
                        crop = image.crop((max(0, bx1 - pad), max(0, by1 - pad), min(pw, bx2 + pad), min(ph, by2 + pad)))
                        clean_val = refine_cell_decimal_point(clean_val, crop)

                # Label echo check: only flag if field was expected to be an amount, date, or empty
                is_label_echo = False
                if expected_type in ["amount", "date", "empty"] and clean_val.upper() == norm_target:
                    is_label_echo = True
                    clean_val = ""

                is_low_conf = (target_cell.conf < 60.0)
                is_multi_token = (len(clean_val.split()) > 1 and expected_type in ["amount", "code", "id", "weight", "percentage", "unit"])
                has_syntax_garble = bool(re.search(r"[{}\[\]~|`^§]", clean_val))

                ambiguous = target_cell.is_ambiguous or is_label_echo or is_low_conf or is_multi_token or has_syntax_garble

                # Type-specific validation
                if expected_type == "empty" and clean_val != "":
                    ambiguous = True
                elif expected_type == "amount" and clean_val and not re.search(r"\d", clean_val):
                    ambiguous = True
                elif expected_type == "date" and clean_val and not re.search(r"\d{1,2}[/-]\d{1,2}", clean_val):
                    ambiguous = True

                verification_decision = "VERIFY"
                abstention_reason = None
                if is_low_conf:
                    verification_decision = "ABSTAIN"
                    abstention_reason = f"Low OCR confidence ({target_cell.conf:.1f} < 60.0)"
                elif is_multi_token:
                    verification_decision = "ABSTAIN"
                    abstention_reason = "Multiple whitespace-separated tokens detected in numeric cell (gutter bleed)"
                elif has_syntax_garble:
                    verification_decision = "ABSTAIN"
                    abstention_reason = "Stray punctuation or non-alphanumeric syntax garble in extracted text"
                elif is_label_echo:
                    verification_decision = "ABSTAIN"
                    abstention_reason = "Label-echo rejected"
                elif ambiguous:
                    verification_decision = "ABSTAIN"
                    abstention_reason = "Ambiguous cell boundaries or candidate collision"

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
                    verification_decision=verification_decision,
                    abstention_reason=abstention_reason,
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
