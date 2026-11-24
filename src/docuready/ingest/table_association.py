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

import difflib
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
    Detects dropped baseline decimal points and micro-font digit confusions in
    low-resolution OCR crops using fast pixel morphology (NumPy).
    1. Isolated baseline decimal dot:
       Requires active ink bounding box, zero upper ink, zero ink above the dot,
       and strict whitespace flanking to avoid character strokes.
       Enforces baseline contact (touching bottom or bottom - 1) to protect integers (e.g. 88, 48).
    2. Micro-glyph 4 vs 8 disambiguation:
       For sub-12px glyph heights where Tesseract LSTM confounds the triangular opening of 4 as 8,
       verifies whether beneath the horizontal crossbar the lower-left quadrant is empty.
    Execution time: ~0.05ms per check (pure NumPy, zero subprocess overhead).
    """
    if not cell_text or cell_crop is None:
        return cell_text

    text = cell_text

    # --- Part 1: Dropped Decimal Point Recovery ---
    if "." not in text:
        clean_digits = re.sub(r"^(Rs\.?|INR|₹)\s*", "", text, flags=re.IGNORECASE).replace(",", "").strip()
        # Only evaluate numeric tokens of length 2 to 5 that don't end in two zeros (if >= 1000)
        if clean_digits.isdigit() and (2 <= len(clean_digits) <= 5):
            if not (len(clean_digits) >= 4 and clean_digits.endswith("00")):
                try:
                    if hasattr(cell_crop, "convert"):
                        arr = np.array(cell_crop.convert("L"))
                    elif isinstance(cell_crop, np.ndarray):
                        arr = cell_crop
                    else:
                        arr = None

                    if arr is not None:
                        h, w = arr.shape[:2]
                        if h >= 6 and w >= 8:
                            thresh = (int(arr.min()) + int(arr.max())) // 2
                            binary = arr < thresh  # True for ink (dark)

                            # Strip boundary grid line strokes touching edges separated by blank rows/cols
                            for _ in range(2):
                                r_ink = binary.sum(axis=1)
                                if len(r_ink) > 2 and r_ink[0] >= w * 0.7 and r_ink[1] == 0:
                                    binary[0, :] = False
                                if len(r_ink) > 2 and r_ink[-1] >= w * 0.7 and r_ink[-2] == 0:
                                    binary[-1, :] = False
                                c_ink = binary.sum(axis=0)
                                if len(c_ink) > 2 and c_ink[0] >= h * 0.7 and c_ink[1] == 0:
                                    binary[:, 0] = False
                                if len(c_ink) > 2 and c_ink[-1] >= h * 0.7 and c_ink[-2] == 0:
                                    binary[:, -1] = False

                            row_ink = binary.sum(axis=1)
                            col_ink = binary.sum(axis=0)
                            active_rows = np.where(row_ink > 0)[0]
                            active_cols = np.where(col_ink > 0)[0]

                            if len(active_rows) > 0 and len(active_cols) > 0:
                                top, bottom = active_rows.min(), active_rows.max()
                                left, right = active_cols.min(), active_cols.max()
                                char_h = bottom - top + 1
                                char_w_span = right - left + 1

                                if char_h >= 6 and char_w_span >= 8:
                                    baseline_start = top + int(char_h * 0.65)
                                    upper_end = baseline_start
                                    found_dot_x = None

                                    for dw in [1, 2, 3]:
                                        if found_dot_x is not None:
                                            break
                                        for c in range(left + 2, right - dw - 1):
                                            cols = list(range(c, c + dw))
                                            # Zero ink in upper zone
                                            if binary[top:upper_end, cols].sum() > 0:
                                                continue

                                            base_sub = binary[baseline_start:bottom + 1, cols]
                                            dot_ink_count = base_sub.sum()
                                            if not (1 <= dot_ink_count <= 6):
                                                continue

                                            dot_r, dot_c = np.where(base_sub)
                                            dot_h = dot_r.max() - dot_r.min() + 1
                                            if dot_h > 3:
                                                continue

                                            abs_dot_rows = baseline_start + dot_r
                                            min_r, max_r = abs_dot_rows.min(), abs_dot_rows.max()

                                            # Baseline contact: must touch bottom or bottom - 1
                                            if max_r < bottom - 1:
                                                continue

                                            # Left and right isolation
                                            if binary[min_r:max_r + 1, c - 1].sum() > 0:
                                                continue
                                            if binary[min_r:max_r + 1, c + dw].sum() > 0:
                                                continue

                                            # Above isolation
                                            above_check_top = max(top, min_r - 2)
                                            if min_r > above_check_top and binary[above_check_top:min_r, cols].sum() > 0:
                                                continue

                                            found_dot_x = c + (dw - 1) / 2.0
                                            break

                                    if found_dot_x is not None:
                                        num_chars = len(clean_digits)
                                        rel_x = (found_dot_x - left) / float(char_w_span)
                                        insert_idx = int(round(rel_x * num_chars))
                                        insert_idx = max(1, min(insert_idx, num_chars - 1))
                                        refined = clean_digits[:insert_idx] + "." + clean_digits[insert_idx:]
                                        text = text.replace(clean_digits, refined)
                except Exception:
                    pass

    # --- Part 2: Micro-Glyph 4 vs 8 Disambiguation ---
    clean_num = re.sub(r"^(Rs\.?|INR|₹)\s*", "", text, flags=re.IGNORECASE).replace(",", "").strip()
    if clean_num.isdigit() and "8" in clean_num:
        try:
            if hasattr(cell_crop, "convert"):
                arr = np.array(cell_crop.convert("L"))
            elif isinstance(cell_crop, np.ndarray):
                arr = cell_crop
            else:
                arr = None

            if arr is not None:
                thresh = (int(arr.min()) + int(arr.max())) // 2
                binary = arr < thresh
                row_ink = binary.sum(axis=1)
                active_r = np.where(row_ink > 0)[0]
                if len(active_r) >= 6 and (active_r.max() - active_r.min() + 1) <= 12:
                    col_ink = binary[active_r.min():active_r.max() + 1, :].sum(axis=0)
                    active_c = np.where(col_ink > 0)[0]
                    if len(active_c) > 0:
                        c_left, c_right = active_c.min(), active_c.max()
                        num_chars = len(clean_num)
                        char_w = (c_right - c_left + 1) / float(num_chars)

                        chars = list(clean_num)
                        changed = False
                        for idx, ch in enumerate(chars):
                            if ch == "8":
                                ch_c1 = int(c_left + idx * char_w)
                                ch_c2 = int(c_left + (idx + 1) * char_w)
                                ch_bin = binary[active_r.min():active_r.max() + 1, ch_c1:ch_c2]
                                row_sums = ch_bin.sum(axis=1)
                                if len(row_sums) >= 6:
                                    bar_row = int(np.argmax(row_sums))
                                    if 2 <= bar_row < len(ch_bin) - 1:
                                        below_bar = ch_bin[bar_row + 1:, :]
                                        mid_w = ch_bin.shape[1] // 2
                                        left_below = below_bar[:, :mid_w].sum()
                                        right_below = below_bar[:, mid_w:].sum()
                                        if left_below == 0 and right_below > 0:
                                            chars[idx] = "4"
                                            changed = True
                        if changed:
                            new_num = "".join(chars)
                            text = text.replace(clean_num, new_num)
        except Exception:
            pass

    return text


def resolve_narrow_gutter_cell_token(
    cell_words: List[Dict[str, Any]],
    header_text: str,
    col_pattern: Optional[str],
    field_name: str,
    clean_val: str,
    image: Optional[Any] = None,
) -> Tuple[str, bool, float, Optional[str]]:
    """
    Resolves multi-token narrow-gutter cell bleed via localized spatial association.
    If a cell contains multiple tokens (e.g. '85000 8500') due to narrow gutter fusion,
    checks if col_pattern or field_name matches a specific sub-column header.
    Refines decimal points on the resolved sub-token crop when image is provided.
    Returns: (resolved_value, is_resolved, sub_conf, reason)
    """
    tokens = clean_val.split()
    if len(tokens) <= 1 or not cell_words or len(cell_words) < len(tokens):
        return clean_val, False, 0.0, None

    sub_headers = [h.strip() for h in re.split(r"[_|/]|(?<=[)])\s+(?=[A-Z])", header_text) if h.strip()]

    if len(sub_headers) >= 2 and len(tokens) == 2:
        target = col_pattern or field_name
        target_norm = target.lower().replace("_", " ")

        match_idx = -1
        for idx, sh in enumerate(sub_headers[:2]):
            sh_norm = sh.lower()
            if any(term in sh_norm for term in target_norm.split()):
                match_idx = idx
                break

        if match_idx != -1 and match_idx < len(cell_words):
            w1 = cell_words[0]
            w2 = cell_words[1]
            gap = w2["left"] - w1["right"]
            if gap >= 8:
                resolved_token = tokens[match_idx]
                token_conf = cell_words[match_idx].get("conf", 75.0)

                # Refine decimal points on the isolated sub-token crop if image is provided
                if image is not None and ("." not in resolved_token):
                    tw = cell_words[match_idx]
                    tx1, ty1, tx2, ty2 = tw["left"], tw["top"], tw["right"], tw["bottom"]
                    pad = 5
                    pw = image.width if hasattr(image, "width") else tx2 + pad
                    ph = image.height if hasattr(image, "height") else ty2 + pad
                    crop = image.crop((max(0, tx1 - pad), max(0, ty1 - pad), min(pw, tx2 + pad), min(ph, ty2 + pad)))
                    resolved_token = refine_cell_decimal_point(resolved_token, crop)

                return resolved_token, True, max(token_conf, 70.0), None

    return clean_val, False, 0.0, "Multiple whitespace-separated tokens detected in numeric cell (gutter bleed)"


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

            # Targeted decimal/glyph refinement is deferred to extraction time
            # for the specific requested cells, avoiding eager O(R*C) PIL image crops.

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


def canonical_ocr_key(s: str) -> str:
    """Normalizes common OCR character confusions (O/0, I/1, S/5, B/8, Z/2) and strips punctuation."""
    s = s.upper()
    s = re.sub(r"[^A-Z0-9]", "", s)
    trans = str.maketrans({
        "O": "0",
        "I": "1",
        "L": "1",
        "S": "5",
        "B": "8",
        "Z": "2",
    })
    return s.translate(trans)


def find_matching_row_evidence_guided(
    grid: TableGrid,
    target_pattern: str,
    expected_type: Optional[str],
    target_col: int,
) -> Tuple[Optional[int], Optional[List[TableCell]], float, Optional[str]]:
    """
    Recovers degraded row labels using multi-evidence agreement:
    1. Canonical OCR equivalence mapping (substitutions of 0/O, 5/S, 8/B, 1/I/l, 2/Z).
    2. High-confidence Levenshtein string similarity with strict margin guard (Delta >= 0.15).
    3. Structural validation in the target column (target cell must satisfy expected syntactic type).
    Returns: (row_idx, row_cells, recovery_score, recovery_method)
    """
    norm_pattern = normalize_token_text(target_pattern).upper()
    canon_pattern = canonical_ocr_key(target_pattern)

    # 1. Canonical OCR Equivalence match
    candidates_canon: List[Tuple[int, List[TableCell]]] = []
    for r_idx, row in enumerate(grid.rows):
        if r_idx == 0 and len(grid.rows) > 1:
            continue
        row_canon = canonical_ocr_key(" ".join(c.text for c in row))
        if canon_pattern and (canon_pattern in row_canon or (len(canon_pattern) >= 4 and row_canon in canon_pattern)):
            if target_col < len(row):
                cell_val = row[target_col].text.strip()
                if expected_type in ["amount", "count", "weight", "number", "percentage"]:
                    if any(c.isdigit() for c in cell_val):
                        candidates_canon.append((r_idx, row))
                else:
                    candidates_canon.append((r_idx, row))

    if len(candidates_canon) == 1:
        return candidates_canon[0][0], candidates_canon[0][1], 0.95, "canonical_equivalence"
    elif len(candidates_canon) > 1:
        return None, None, 0.0, "canon_collision"

    # 2. High-Confidence Levenshtein Similarity with Strict Margin Guard
    best_ratio = 0.0
    second_best = 0.0
    best_row_info: Optional[Tuple[int, List[TableCell]]] = None

    for r_idx, row in enumerate(grid.rows):
        if r_idx == 0 and len(grid.rows) > 1:
            continue
        label_text = normalize_token_text(row[0].text if row else "").upper()
        full_row_text = normalize_token_text(" ".join(c.text for c in row)).upper()

        r1 = difflib.SequenceMatcher(None, norm_pattern, label_text).ratio()
        r2 = difflib.SequenceMatcher(None, norm_pattern, full_row_text[: len(norm_pattern) + 5]).ratio()
        r = max(r1, r2)

        if r > best_ratio:
            second_best = best_ratio
            best_ratio = r
            best_row_info = (r_idx, row)
        elif r > second_best:
            second_best = r

    # Strict Safety Margin: ratio >= 0.85 and margin >= 0.15 to prevent prefix collisions
    if best_ratio >= 0.85 and (best_ratio - second_best) >= 0.15 and best_row_info is not None:
        r_idx, row = best_row_info
        if target_col < len(row):
            cell_val = row[target_col].text.strip()
            if expected_type in ["amount", "count", "weight", "number", "percentage"]:
                if any(c.isdigit() for c in cell_val):
                    return r_idx, row, best_ratio, "levenshtein_similarity"
            else:
                return r_idx, row, best_ratio, "levenshtein_similarity"

    return None, None, 0.0, None


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

    row_recovery_method = "exact_match"
    row_recovery_score = 1.0

    if not matching_rows:
        r_rec, row_rec, s_rec, m_rec = find_matching_row_evidence_guided(
            grid=grid,
            target_pattern=row_pattern,
            expected_type=expected_type,
            target_col=target_col,
        )
        if r_rec is not None and row_rec is not None:
            matching_rows.append((r_rec, row_rec))
            row_recovery_method = m_rec or "evidence_guided"
            row_recovery_score = s_rec

    if not matching_rows:
        return None

    # Ambiguity check: multiple rows match the same row_pattern (e.g. repeated account number)
    is_multi_row = (len(matching_rows) > 1)
    r_idx, row = matching_rows[0]
    cell = row[target_col]
    clean_val = cell.text.strip()
    clean_val = re.sub(r"^[‘'\"Rs\.INR₹\s]+", "", clean_val, flags=re.IGNORECASE).strip()
    clean_val = re.sub(r"^(Rs\.?|INR|₹)\s*", "", clean_val, flags=re.IGNORECASE).strip()
    clean_val = re.sub(r"[,;:\s]+$", "", clean_val).strip()

    if expected_type in ["amount", "percentage", "number", "weight"]:
        clean_val = re.sub(r",(\d{1,2})$", r".\1", clean_val)

    is_pure_count = (expected_type in ["count", "id", "code", "integer"] and not any(k in field_name.lower() for k in ["hba1c", "a1c", "potency", "rate", "percent", "pct", "ratio", "vol", "weight"]))
    if (
        image is not None
        and clean_val
        and not is_pure_count
        and any(c.isdigit() for c in clean_val)
        and (("." not in clean_val and len(re.sub(r"[^\d]", "", clean_val)) >= 2) or ("8" in clean_val))
    ):
        bx1, by1, bx2, by2 = cell.bbox
        if bx2 > bx1 and by2 > by1:
            pad = 5
            pw = image.width if hasattr(image, "width") else bx2 + pad
            ph = image.height if hasattr(image, "height") else by2 + pad
            crop = image.crop((max(0, bx1 - pad), max(0, by1 - pad), min(pw, bx2 + pad), min(ph, by2 + pad)))
            refined_val = refine_cell_decimal_point(clean_val, crop)
            if expected_type == "amount" and "." in refined_val:
                parts = refined_val.split(".")
                if len(parts) == 2 and len(parts[1]) > 2:
                    refined_val = clean_val
            clean_val = refined_val

    # Check for multi-token narrow-gutter resolution
    cell_conf = cell.conf * row_recovery_score
    sub_headers = [h.strip() for h in re.split(r"[_|/]|(?<=[)])\s+(?=[A-Z])", header_text) if h.strip()]
    was_resolved = False
    if len(clean_val.split()) > 1 and expected_type in ["amount", "code", "id", "weight", "percentage", "unit", "number", "count"]:
        resolved_tok, is_res, sub_conf, _ = resolve_narrow_gutter_cell_token(
            cell_words=cell.words,
            header_text=header_text,
            col_pattern=col_pattern,
            field_name=field_name,
            clean_val=clean_val,
            image=image,
        )
        if is_res:
            clean_val = resolved_tok
            cell_conf = max(cell_conf, sub_conf * row_recovery_score)
            was_resolved = True

    compound_unresolved = False
    if len(sub_headers) >= 2 and col_pattern and not was_resolved:
        if len(clean_val) >= 7 and clean_val.replace(".", "").isdigit():
            compound_unresolved = True

    if expected_type in ["amount", "number", "count", "percentage", "weight", "unit"]:
        if re.search(r"[a-zA-Z]", clean_val):
            type_contradiction = True

    # Integrity and risk-calibrated verification decisions
    effective_floor = 75.0 if row_recovery_method == "levenshtein_similarity" else 60.0
    is_low_conf = (cell_conf < effective_floor)
    is_multi_token = (len(clean_val.split()) > 1 and expected_type in ["amount", "code", "id", "weight", "percentage", "unit", "number", "count"])
    has_syntax_garble = bool(re.search(r"[{}\[\]~|`^§]", clean_val))

    ambiguous = cell.is_ambiguous or is_multi_row or header_mismatch or type_contradiction or is_low_conf or is_multi_token or has_syntax_garble or compound_unresolved

    verification_decision = "VERIFY"
    abstention_reason = None
    if not clean_val and expected_type != "empty":
        verification_decision = "ABSTAIN"
        abstention_reason = "Empty cell text / no value extracted"
    elif is_low_conf:
        verification_decision = "ABSTAIN"
        abstention_reason = f"Low OCR confidence ({cell_conf:.1f} < {effective_floor:.1f})"
    elif is_multi_token:
        verification_decision = "ABSTAIN"
        abstention_reason = "Multiple whitespace-separated tokens detected in numeric cell (gutter bleed)"
    elif compound_unresolved:
        verification_decision = "ABSTAIN"
        abstention_reason = "Compound column header contains merged/unseparated tokens across sub-columns"
    elif has_syntax_garble:
        verification_decision = "ABSTAIN"
        abstention_reason = "Stray punctuation or non-alphanumeric syntax garble in extracted text"
    elif type_contradiction:
        verification_decision = "ABSTAIN"
        abstention_reason = f"Column header '{header_text}' or token text contradicts expected field semantic '{field_name}' ({expected_type})"
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
        confidence=cell_conf,
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
            "row_recovery_method": row_recovery_method,
            "row_recovery_score": round(row_recovery_score, 3),
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

                # Case A: Value is inline after colon
                if ":" in raw_text and raw_text.split(":", 1)[1].strip():
                    parts = raw_text.split(":", 1)
                    clean_val = parts[1].strip()
                    clean_val = re.sub(r"^(Rs\.?|INR|₹)\s*", "", clean_val, flags=re.IGNORECASE).strip()
                # Case B: Value is in adjacent column to the right
                elif c_idx + 1 < len(row):
                    val_cell = row[c_idx + 1]
                    clean_val = val_cell.text.strip()
                    clean_val = re.sub(r"^(Rs\.?|INR|₹)\s*", "", clean_val, flags=re.IGNORECASE).strip()
                    target_cell = val_cell
                # Case C: Direct exact match of token/value within cell
                elif norm_target == norm_cell:
                    clean_val = raw_text.strip()
                    target_cell = cell
                else:
                    clean_val = raw_text.strip()

                is_pure_count = (expected_type in ["count", "id", "code", "integer"] and not any(k in field_name.lower() for k in ["hba1c", "a1c", "potency", "rate", "percent", "pct", "ratio", "vol", "weight"]))
                if (
                    image is not None
                    and clean_val
                    and not is_pure_count
                    and any(c.isdigit() for c in clean_val)
                    and (("." not in clean_val and len(re.sub(r"[^\d]", "", clean_val)) >= 2) or ("8" in clean_val))
                ):
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

                # Check for multi-token narrow-gutter resolution
                target_conf = target_cell.conf
                h_text = grid.col_headers[target_cell.col] if target_cell.col < len(grid.col_headers) else ""
                sub_headers = [h.strip() for h in re.split(r"[_|/]|(?<=[)])\s+(?=[A-Z])", h_text) if h.strip()]
                was_resolved = False
                if len(clean_val.split()) > 1 and expected_type in ["amount", "code", "id", "weight", "percentage", "unit", "number", "count"]:
                    resolved_tok, is_res, sub_conf, _ = resolve_narrow_gutter_cell_token(
                        cell_words=target_cell.words,
                        header_text=h_text,
                        col_pattern=col_pattern,
                        field_name=field_name,
                        clean_val=clean_val,
                        image=image,
                    )
                    if is_res:
                        clean_val = resolved_tok
                        target_conf = max(target_conf, sub_conf)
                        was_resolved = True

                compound_unresolved = False
                if len(sub_headers) >= 2 and col_pattern and not was_resolved:
                    if len(clean_val) >= 7 and clean_val.replace(".", "").isdigit():
                        compound_unresolved = True

                type_contradiction = False
                if expected_type in ["amount", "number", "count", "percentage", "weight", "unit"]:
                    if re.search(r"[a-zA-Z]", clean_val):
                        type_contradiction = True

                is_low_conf = (target_conf < 60.0)
                is_multi_token = (len(clean_val.split()) > 1 and expected_type in ["amount", "code", "id", "weight", "percentage", "unit", "number", "count"])
                has_syntax_garble = bool(re.search(r"[{}\[\]~|`^§]", clean_val))

                ambiguous = target_cell.is_ambiguous or is_label_echo or is_low_conf or is_multi_token or has_syntax_garble or compound_unresolved or type_contradiction

                # Type-specific validation
                if expected_type == "empty" and clean_val != "":
                    ambiguous = True
                elif expected_type == "amount" and clean_val and not re.search(r"\d", clean_val):
                    ambiguous = True
                elif expected_type == "date" and clean_val and not re.search(r"\d{1,2}[/-]\d{1,2}", clean_val):
                    ambiguous = True

                verification_decision = "VERIFY"
                abstention_reason = None
                if not clean_val and expected_type != "empty":
                    verification_decision = "ABSTAIN"
                    abstention_reason = "Empty cell text / no value extracted"
                elif is_low_conf:
                    verification_decision = "ABSTAIN"
                    abstention_reason = f"Low OCR confidence ({target_conf:.1f} < 60.0)"
                elif is_multi_token:
                    verification_decision = "ABSTAIN"
                    abstention_reason = "Multiple whitespace-separated tokens detected in numeric cell (gutter bleed)"
                elif compound_unresolved:
                    verification_decision = "ABSTAIN"
                    abstention_reason = "Compound column header contains merged/unseparated tokens across sub-columns"
                elif has_syntax_garble:
                    verification_decision = "ABSTAIN"
                    abstention_reason = "Stray punctuation or non-alphanumeric syntax garble in extracted text"
                elif is_label_echo:
                    verification_decision = "ABSTAIN"
                    abstention_reason = "Label-echo rejected"
                elif type_contradiction:
                    verification_decision = "ABSTAIN"
                    abstention_reason = f"Token text contradicts expected numeric field semantic '{field_name}' ({clean_val})"
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
                    confidence=target_conf,
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
