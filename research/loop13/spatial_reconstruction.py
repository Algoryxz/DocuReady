"""
Column-Aware Spatial Reading Order Reconstruction Engine
DocuReady - Research Loop 13

Architecture:
1. Token Validation & Coordinate Scaling
2. Candidate Gutter Detection across horizontal word positions
3. Layout Classification:
   - SINGLE_COLUMN: Standard top-to-bottom layout
   - KEY_VALUE_TABLE: Preserves row-wise label-value reading order
   - MULTI_COLUMN_FLOW: De-interleaves columns into natural sequential reading order
4. Full-Width Header & Footer Detection
5. Spatial Line Grouping & Bounding Box Preservation
"""

from __future__ import annotations

import math
import re
from typing import Any, Dict, List, Optional, Set, Tuple


def is_label_value_row(left_words: List[Dict[str, Any]], right_words: List[Dict[str, Any]]) -> bool:
    """
    Checks whether a split line resembles a key-value form row (Label on left, Value on right).
    Examples:
      - 'Applicant Name:' / 'ROHIT VERMA'
      - 'Date of Birth (DD/MM/YYYY):' / '05/09/2004'
      - 'Annual Income:' / 'INR 180000'
    """
    if not left_words or not right_words:
        return False

    left_text = " ".join(w["word"] for w in left_words).strip()
    right_text = " ".join(w["word"] for w in right_words).strip()

    # Left ends in colon or common label prompts
    if left_text.endswith(":") or left_text.endswith(":-") or left_text.endswith("="):
        return True

    # Common label keywords on left
    label_cues = (
        "name", "date", "birth", "income", "roll", "registration", "district",
        "category", "quota", "ifsc", "branch", "code", "total", "amount",
        "address", "authority", "gender", "status", "percentage", "score"
    )
    if any(cue in left_text.lower() for cue in label_cues) and len(left_words) <= 5:
        # And right is relatively short (value-like) or matches date/amount/ID
        if len(right_words) <= 6:
            return True

    return False


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
                "is_kv": is_label_value_row(left_part, right_part)
            })

    if len(split_lines) < min_split_lines:
        return {"layout_type": "SINGLE_COLUMN"}

    # Find common overlapping gap across split lines
    # Candidate split x-coordinates
    candidate_splits = [(info["gap_x0"] + info["gap_x1"]) / 2.0 for info in split_lines]
    
    best_split_x = None
    best_matching_indices = set()

    for cand_x in candidate_splits:
        matching = {
            info["line_idx"]
            for info in split_lines
            if info["gap_x0"] <= cand_x <= info["gap_x1"]
        }
        if len(matching) > len(best_matching_indices):
            best_matching_indices = matching
            best_split_x = cand_x

    if not best_split_x or len(best_matching_indices) < min_split_lines:
        return {"layout_type": "SINGLE_COLUMN"}

    # Check Key-Value ratio among the matching split lines
    matching_info = [info for info in split_lines if info["line_idx"] in best_matching_indices]
    kv_count = sum(1 for info in matching_info if info["is_kv"])
    kv_ratio = kv_count / len(matching_info)

    # If the majority of split lines are Key-Value label-value pairs,
    # preserve row-wise reading order so that field extraction and rules work seamlessly!
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

    # Compute gutter bounds from matching lines
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
) -> List[List[Dict[str, Any]]]:
    """
    Main entrypoint for spatial reading order reconstruction.
    Clusters word tokens into lines, detects layout structure, and orders lines
    naturally based on document geometry while preserving single-column and table integrity.
    """
    if not words_meta:
        return []

    # 1. Initial scanline clustering
    raw_lines = _cluster_words_raw(words_meta, y_tol)
    if len(raw_lines) < 2:
        return raw_lines

    # 2. Detect layout structure
    struct = detect_page_layout_structure(raw_lines, min_gutter_width)
    layout_type = struct["layout_type"]

    # If Single-Column or Key-Value Table, raw row-wise scanlines are correct
    if layout_type in ("SINGLE_COLUMN", "KEY_VALUE_TABLE"):
        return raw_lines

    # 3. For MULTI_COLUMN_FLOW, de-interleave the two columns
    split_x = struct["split_x"]
    header_end = struct["header_end_idx"]
    footer_start = struct["footer_start_idx"]

    header_lines = []
    left_words = []
    right_words = []
    footer_lines = []

    for idx, line in enumerate(raw_lines):
        if idx < header_end:
            header_lines.append(line)
        elif idx > footer_start:
            footer_lines.append(line)
        else:
            # Check if this line within the column zone is a full-width header/banner
            lx0 = min(w["box"][0] for w in line)
            lx1 = max(w["box"][2] for w in line)
            is_full_width_banner = (lx0 < split_x - 30.0 and lx1 > split_x + 30.0 and idx not in struct["matching_lines"])

            if is_full_width_banner:
                # Banner line within columns: if left words accumulated, flush them
                if left_words:
                    header_lines.extend(_cluster_words_raw(left_words, y_tol))
                    left_words = []
                if right_words:
                    header_lines.extend(_cluster_words_raw(right_words, y_tol))
                    right_words = []
                header_lines.append(line)
            else:
                for w in line:
                    w_center = (w["box"][0] + w["box"][2]) / 2.0
                    if w["box"][2] <= split_x or w_center < split_x:
                        left_words.append(w)
                    else:
                        right_words.append(w)

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
