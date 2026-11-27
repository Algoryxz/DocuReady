"""
Column-Aware Spatial Reading Order Reconstruction
DocuReady - Ingestion Subsystem

Provides robust geometric de-interleaving for multi-column documents while
guaranteeing preservation of single-column certificates, tabular key-value forms,
and coordinate bounds.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Set, Tuple


def is_label_value_or_table_row(left_words: List[Dict[str, Any]], right_words: List[Dict[str, Any]]) -> bool:
    """
    Checks whether a horizontal line split resembles a key-value form row or a table row.
    Examples:
      - 'Applicant Name:' / 'ROHIT VERMA'
      - 'Date of Birth:' / '05/09/2004'
      - 'Annual Household Income:' / 'INR 180000'
      - 'Mathematics' / '100' or '92'
      - 'Subject' / 'Marks'
    """
    if not left_words or not right_words:
        return False

    left_text = " ".join(w["word"] for w in left_words).strip()
    right_text = " ".join(w["word"] for w in right_words).strip()

    # Both sides ending in colons indicates parallel column headings, not a label-value pair
    if right_text.endswith(":") or right_text.endswith(":-"):
        return False

    # Punctuation indicators on the left
    if left_text.endswith(":") or left_text.endswith(":-") or left_text.endswith("="):
        return True

    # Numeric or tabular value patterns on the right (marks, amount, percentage, year)
    right_words_text = [w["word"].strip() for w in right_words]
    is_right_numeric = all(
        w.replace(".", "").replace(",", "").replace("%", "").replace("-", "").isdigit()
        or w.lower() in ("pass", "fail", "na", "n/a", "nil")
        for w in right_words_text
    )
    if is_right_numeric and len(right_words) <= 4:
        return True

    # Common form metadata & table column keywords
    tabular_cues = (
        "name", "date", "birth", "income", "roll", "registration", "district",
        "category", "quota", "ifsc", "branch", "code", "total", "amount",
        "address", "authority", "gender", "status", "percentage", "score",
        "caste", "domicile", "parent", "father", "guardian", "religion",
        "subject", "marks", "grade", "credits", "max", "obtained", "sr",
        "serial", "sl", "particulars", "fee", "tuition", "hostel", "year"
    )
    left_lower = left_text.lower()
    if any(cue in left_lower for cue in tabular_cues) and len(left_words) <= 6:
        if len(right_words) <= 8:
            return True

    return False


is_label_value_row = is_label_value_or_table_row


def detect_page_layout_structure(
    raw_lines: List[List[Dict[str, Any]]],
    min_gutter_width: float = 20.0,
    min_split_lines: int = 2
) -> Dict[str, Any]:
    """
    Analyzes raw scanlines to detect layout structure:
    Returns layout type ('SINGLE_COLUMN', 'KEY_VALUE_TABLE', or 'MULTI_COLUMN_FLOW')
    and geometry parameters.
    """
    if len(raw_lines) < 2:
        return {"layout_type": "SINGLE_COLUMN"}

    # Check for multi-column Table Grids (e.g., 3+ columns where lines have >= 2 gaps)
    multi_gap_lines = 0
    candidate_lines = 0

    for line in raw_lines:
        if len(line) >= 3:
            candidate_lines += 1
            gaps_in_line = 0
            for i in range(len(line) - 1):
                gap = line[i + 1]["box"][0] - line[i]["box"][2]
                if gap >= min_gutter_width:
                    gaps_in_line += 1
            if gaps_in_line >= 2:
                multi_gap_lines += 1

    # If multiple lines have 2 or more wide gaps, it is a 3+ column table grid!
    # Table grids must preserve row-by-row reading order.
    if multi_gap_lines >= 2 or (candidate_lines >= 2 and multi_gap_lines == candidate_lines):
        return {
            "layout_type": "KEY_VALUE_TABLE",
            "reason": "table_grid_multiple_gaps"
        }

    split_lines = []

    for l_idx, line in enumerate(raw_lines):
        if len(line) < 2:
            continue

        # Find significant internal horizontal gaps in this line
        line_gaps = []
        for i in range(len(line) - 1):
            w_left = line[i]
            w_right = line[i + 1]
            gap = w_right["box"][0] - w_left["box"][2]
            if gap >= min_gutter_width:
                line_gaps.append((w_left["box"][2], w_right["box"][0], gap, i))

        if line_gaps:
            # Sort gaps descending by width
            line_gaps.sort(key=lambda g: g[2], reverse=True)
            best_gap = line_gaps[0]
            left_part = line[:best_gap[3] + 1]
            right_part = line[best_gap[3] + 1:]

            split_lines.append({
                "line_idx": l_idx,
                "gap_x0": best_gap[0],
                "gap_x1": best_gap[1],
                "gap_width": best_gap[2],
                "left_words": left_part,
                "right_words": right_part,
                "is_kv": is_label_value_or_table_row(left_part, right_part)
            })

    if not split_lines:
        return {"layout_type": "SINGLE_COLUMN"}

    # Find common overlapping gap across split lines or prominent single split gap
    best_split_x = None
    best_matching_indices = set()

    for info in split_lines:
        cand_x = (info["gap_x0"] + info["gap_x1"]) / 2.0
        # Check how many lines have a gap containing cand_x
        matching = {
            other["line_idx"]
            for other in split_lines
            if other["gap_x0"] <= cand_x <= other["gap_x1"]
        }
        if len(matching) > len(best_matching_indices):
            best_matching_indices = matching
            best_split_x = cand_x

    # If only 1 line had words on both sides, but it has a very prominent gap (>= 50 pt)
    # and other lines lie completely on one side of cand_x without crossing it:
    if len(best_matching_indices) < min_split_lines:
        for info in split_lines:
            if info["gap_width"] >= 50.0:
                cand_x = (info["gap_x0"] + info["gap_x1"]) / 2.0
                # Check if other lines lie cleanly on left or right without cutting across cand_x
                cuts_across = False
                left_count = 0
                right_count = 0
                for l_other_idx, l in enumerate(raw_lines):
                    if l_other_idx == info["line_idx"]:
                        continue
                    lx0 = min(w["box"][0] for w in l)
                    lx1 = max(w["box"][2] for w in l)
                    if lx0 < cand_x and lx1 > cand_x:
                        # Line cuts across cand_x without a gap
                        cuts_across = True
                        break
                    if lx1 <= cand_x:
                        left_count += 1
                    elif lx0 >= cand_x:
                        right_count += 1
                has_left_continuation = (left_count >= 1 and len(info["right_words"]) >= 1)
                has_right_continuation = (right_count >= 1 and len(info["left_words"]) >= 1)
                if not cuts_across and (has_left_continuation or has_right_continuation):
                    best_split_x = cand_x
                    best_matching_indices = {info["line_idx"]}
                    break

    if not best_split_x or (len(best_matching_indices) < min_split_lines and not (best_split_x and len(raw_lines) >= 3)):
        return {"layout_type": "SINGLE_COLUMN"}

    # Check Key-Value ratio among the matching split lines
    matching_info = [info for info in split_lines if info["line_idx"] in best_matching_indices]
    kv_count = sum(1 for info in matching_info if info["is_kv"])
    kv_ratio = kv_count / len(matching_info)

    # If the majority of split lines are Key-Value label-value pairs or tabular rows,
    # preserve row-wise reading order so that field extraction and rules work seamlessly
    if kv_ratio >= 0.50:
        return {
            "layout_type": "KEY_VALUE_TABLE",
            "split_x": best_split_x,
            "matching_lines": best_matching_indices,
            "kv_ratio": kv_ratio
        }

    # Otherwise, it is an independent multi-column text narrative
    min_split_idx = min(best_matching_indices)
    max_split_idx = max(best_matching_indices)

    gutter_x0 = max(info["gap_x0"] for info in matching_info)
    gutter_x1 = min(info["gap_x1"] for info in matching_info)

    return {
        "layout_type": "MULTI_COLUMN_FLOW",
        "split_x": best_split_x,
        "gutter_x0": gutter_x0,
        "gutter_x1": gutter_x1,
        "matching_lines": best_matching_indices,
        "header_end_idx": min_split_idx,
        "footer_start_idx": max_split_idx
    }


def cluster_and_order_words(
    words_meta: List[Dict[str, Any]],
    y_tol: float = 8.0,
    min_gutter_width: float = 20.0
) -> Optional[List[List[Dict[str, Any]]]]:
    """
    Main spatial layout reconstruction entrypoint.
    Returns:
      - None if layout is SINGLE_COLUMN or KEY_VALUE_TABLE (allowing caller to use default grouping).
      - List of word groups in de-interleaved reading order if MULTI_COLUMN_FLOW is detected.
    """
    if not words_meta:
        return None

    # 1. Initial scanline clustering
    raw_lines = _cluster_words_raw(words_meta, y_tol)
    if len(raw_lines) < 2:
        return None

    # 2. Detect layout structure
    struct = detect_page_layout_structure(raw_lines, min_gutter_width)
    layout_type = struct["layout_type"]

    # If Single-Column or Key-Value Table, signal to use default grouping
    if layout_type != "MULTI_COLUMN_FLOW":
        return None

    # 3. For MULTI_COLUMN_FLOW, de-interleave into Header -> Left Col -> Right Col -> Footer
    split_x = struct["split_x"]
    first_split_idx = min(struct["matching_lines"])
    last_split_idx = max(struct["matching_lines"])

    # Determine vertical boundary for header (top of column region)
    first_split_line = raw_lines[first_split_idx]
    col_top_y = min(w["box"][1] for w in first_split_line)

    # Determine vertical boundary for column continuation vs footer
    # Find last line that is part of column flow
    col_bottom_y = max(w["box"][3] for w in raw_lines[last_split_idx])
    last_col_line_idx = last_split_idx

    for idx in range(last_split_idx + 1, len(raw_lines)):
        line = raw_lines[idx]
        line_y0 = min(w["box"][1] for w in line)
        line_x0 = min(w["box"][0] for w in line)
        line_x1 = max(w["box"][2] for w in line)

        # If there is a large vertical jump (>= 35 pt), or line spans across split_x, it is a footer
        y_gap = line_y0 - col_bottom_y
        is_spanning = (line_x0 < split_x - 20.0 and line_x1 > split_x + 20.0)

        if y_gap >= 35.0 or is_spanning:
            break
        else:
            # Continuous column flow (one column has more lines than the other)
            last_col_line_idx = idx
            col_bottom_y = max(w["box"][3] for w in line)

    header_lines = []
    left_words = []
    right_words = []
    footer_lines = []

    matching_set = struct["matching_lines"]

    for idx, line in enumerate(raw_lines):
        line_x0 = min(w["box"][0] for w in line)
        line_x1 = max(w["box"][2] for w in line)

        if idx < first_split_idx:
            # Strictly above the column split region
            header_lines.append(line)
        elif idx > last_col_line_idx:
            # Strictly below the column split region
            footer_lines.append(line)
        else:
            # Within the column region
            if idx in matching_set:
                # Line has an internal gutter: split into left and right words
                for w in line:
                    w_center = (w["box"][0] + w["box"][2]) / 2.0
                    if w["box"][2] <= split_x or w_center < split_x:
                        left_words.append(w)
                    else:
                        right_words.append(w)
            else:
                # Line does not have a gutter
                if line_x1 <= split_x:
                    left_words.extend(line)
                elif line_x0 >= split_x:
                    right_words.extend(line)
                else:
                    # Spans across split_x without a gutter (mid-column banner)
                    if left_words:
                        header_lines.extend(_cluster_words_raw(left_words, y_tol))
                        left_words = []
                    if right_words:
                        header_lines.extend(_cluster_words_raw(right_words, y_tol))
                        right_words = []
                    header_lines.append(line)

    ordered_lines = []
    ordered_lines.extend(header_lines)
    if left_words:
        ordered_lines.extend(_cluster_words_raw(left_words, y_tol))
    if right_words:
        ordered_lines.extend(_cluster_words_raw(right_words, y_tol))
    ordered_lines.extend(footer_lines)

    return ordered_lines


def _cluster_words_raw(
    words: List[Dict[str, Any]],
    y_tol: float = 8.0
) -> List[List[Dict[str, Any]]]:
    """Clusters words into horizontal scanlines by sorting by y0 and x0."""
    if not words:
        return []

    sorted_words = sorted(words, key=lambda w: (w["y0"], w["x0"]))
    lines: List[List[Dict[str, Any]]] = []

    for w in sorted_words:
        if not lines:
            lines.append([w])
            continue

        last_line = lines[-1]
        line_y_avg = sum(item["y0"] for item in last_line) / len(last_line)
        line_h_avg = sum(item["box"][3] - item["box"][1] for item in last_line) / len(last_line)
        tol = max(y_tol, line_h_avg * 0.6)

        if abs(w["y0"] - line_y_avg) <= tol:
            last_line.append(w)
        else:
            lines.append([w])

    for l in lines:
        l.sort(key=lambda w: w["x0"])

    return lines
