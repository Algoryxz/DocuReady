"""
Column-Aware Spatial Reading Order Reconstruction Experiment
DocuReady - Research Loop 13

Implements:
1. Gutter and Column Detection using aligned horizontal gaps and Y-band analysis
2. Region Partitioning: Full-width Headers, Left Column, Right Column, Full-width Footers
3. Column-isolated Line Grouping
4. Sequential Reading-Order Assembly
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple


def _cluster_words_into_raw_horizontal_lines(
    words_meta: List[Dict[str, Any]],
    y_tol: float = 8.0
) -> List[List[Dict[str, Any]]]:
    """Clusters words into raw horizontal scanlines based on vertical overlap."""
    if not words_meta:
        return []

    # Sort primarily by y0, secondarily by x0
    sorted_words = sorted(words_meta, key=lambda w: (w["y0"], w["x0"]))
    raw_lines: List[List[Dict[str, Any]]] = []

    for w in sorted_words:
        if not raw_lines:
            raw_lines.append([w])
            continue

        last_line = raw_lines[-1]
        line_y_avg = sum(item["y0"] for item in last_line) / len(last_line)
        line_h_avg = sum(item["box"][3] - item["box"][1] for item in last_line) / len(last_line)
        tol = max(y_tol, line_h_avg * 0.6)

        if abs(w["y0"] - line_y_avg) <= tol:
            last_line.append(w)
        else:
            raw_lines.append([w])

    for l in raw_lines:
        l.sort(key=lambda w: w["x0"])

    return raw_lines


def detect_column_gutter(
    raw_lines: List[List[Dict[str, Any]]],
    min_gutter_width: float = 25.0,
    min_split_lines: int = 2
) -> Optional[Dict[str, Any]]:
    """
    Detects whether a multi-line section contains an aligned vertical gutter.
    A line is 'split' if it contains an internal horizontal gap >= min_gutter_width.
    If multiple lines share an overlapping gap interval, a gutter is detected.
    """
    split_lines_info = []

    for l_idx, line in enumerate(raw_lines):
        if len(line) < 2:
            continue

        # Find maximum internal gap in this line
        max_gap = 0.0
        gap_interval = None
        for i in range(len(line) - 1):
            w_left = line[i]
            w_right = line[i + 1]
            gap = w_right["box"][0] - w_left["box"][2]
            if gap > max_gap:
                max_gap = gap
                gap_interval = (w_left["box"][2], w_right["box"][0], gap)

        if gap_interval and max_gap >= min_gutter_width:
            split_lines_info.append({
                "line_idx": l_idx,
                "gap_x0": gap_interval[0],
                "gap_x1": gap_interval[1],
                "gap_width": gap_interval[2]
            })

    if len(split_lines_info) < min_split_lines:
        return None

    # Check for overlapping gap intervals across split lines
    # Intersection of gap intervals:
    common_x0 = max(info["gap_x0"] for info in split_lines_info)
    common_x1 = min(info["gap_x1"] for info in split_lines_info)

    if common_x1 - common_x0 >= min_gutter_width:
        split_x = (common_x0 + common_x1) / 2.0
        return {
            "gutter_x0": common_x0,
            "gutter_x1": common_x1,
            "split_x": split_x,
            "split_line_indices": set(info["line_idx"] for info in split_lines_info),
            "num_split_lines": len(split_lines_info)
        }

    # If common intersection is too tight due to slight alignment variance,
    # find the most consistent pairwise overlap
    best_interval = None
    best_count = 0
    for info in split_lines_info:
        cand_x = (info["gap_x0"] + info["gap_x1"]) / 2.0
        # Count how many lines have a gap containing cand_x
        count = sum(1 for other in split_lines_info if other["gap_x0"] <= cand_x <= other["gap_x1"])
        if count > best_count:
            best_count = count
            best_interval = (info["gap_x0"], info["gap_x1"], cand_x)

    if best_interval and best_count >= min_split_lines:
        return {
            "gutter_x0": best_interval[0],
            "gutter_x1": best_interval[1],
            "split_x": best_interval[2],
            "split_line_indices": set(info["line_idx"] for info in split_lines_info if info["gap_x0"] <= best_interval[2] <= info["gap_x1"]),
            "num_split_lines": best_count
        }

    return None


def cluster_words_column_aware(
    words_meta: List[Dict[str, Any]],
    y_tol: float = 8.0,
    min_gutter_width: float = 25.0
) -> List[List[Dict[str, Any]]]:
    """
    Reconstructs document lines in column-aware spatial reading order.
    1. Clusters words into initial horizontal lines.
    2. Detects candidate vertical gutter across lines.
    3. If gutter exists, separates into:
       - Header lines (above split lines or spanning full width)
       - Left Column lines
       - Right Column lines
       - Footer lines (below split lines or spanning full width)
    4. Sequences: Headers -> Left Column -> Right Column -> Footers.
    """
    if not words_meta:
        return []

    raw_lines = _cluster_words_into_raw_horizontal_lines(words_meta, y_tol)
    if len(raw_lines) < 2:
        return raw_lines

    gutter = detect_column_gutter(raw_lines, min_gutter_width)
    if not gutter:
        # Standard single-column document
        return raw_lines

    split_x = gutter["split_x"]
    split_indices = gutter["split_line_indices"]

    min_split_idx = min(split_indices)
    max_split_idx = max(split_indices)

    header_lines = []
    left_words = []
    right_words = []
    footer_lines = []

    for idx, line in enumerate(raw_lines):
        if idx < min_split_idx:
            # Entire line is above the first split line
            header_lines.append(line)
        elif idx > max_split_idx:
            # Entire line is below the last split line
            footer_lines.append(line)
        else:
            # Line is in the column zone
            # Check if this line is a full-width banner within the column zone
            line_x0 = min(w["box"][0] for w in line)
            line_x1 = max(w["box"][2] for w in line)
            is_full_width_banner = (line_x0 < split_x - 30.0 and line_x1 > split_x + 30.0 and idx not in split_indices)

            if is_full_width_banner:
                # Treat as mid-section banner, append to headers or sequence
                # If we already have left words, sequence them before banner
                header_lines.append(line)
            else:
                for w in line:
                    if w["box"][2] <= split_x:
                        left_words.append(w)
                    elif w["box"][0] >= split_x:
                        right_words.append(w)
                    else:
                        # Crosses split_x: assign based on center
                        w_center = (w["box"][0] + w["box"][2]) / 2.0
                        if w_center < split_x:
                            left_words.append(w)
                        else:
                            right_words.append(w)

    # Cluster left column words into lines
    left_lines = _cluster_words_into_raw_horizontal_lines(left_words, y_tol)
    # Cluster right column words into lines
    right_lines = _cluster_words_into_raw_horizontal_lines(right_words, y_tol)

    # Reconstruct global reading order
    ordered_lines = []
    ordered_lines.extend(header_lines)
    ordered_lines.extend(left_lines)
    ordered_lines.extend(right_lines)
    ordered_lines.extend(footer_lines)

    return ordered_lines
