import numpy as np
import re
from typing import Any, Optional

def refine_decimal_v2(cell_text: str, cell_crop: Any) -> str:
    """
    Refined decimal point recovery using morphology on active character ink.
    Handles sub-10px character heights and padded bounding boxes.
    """
    if not cell_text or "." in cell_text or cell_crop is None:
        return cell_text

    clean_digits = re.sub(r"^(Rs\.?|INR|₹)\s*", "", cell_text, flags=re.IGNORECASE).replace(",", "").strip()
    if not clean_digits.isdigit() or not (2 <= len(clean_digits) <= 5):
        return cell_text

    # Standard integer filters: numbers >= 100 ending in 0 (e.g. 640, 4000, 3100) are standard integers
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
        if h < 6 or w < 8:
            return cell_text

        thresh = (int(arr.min()) + int(arr.max())) // 2
        binary = arr < thresh  # True for ink (dark)

        # 1. Active ink bounding box to handle padded crops
        row_ink = binary.sum(axis=1)
        col_ink = binary.sum(axis=0)
        active_rows = np.where(row_ink > 0)[0]
        active_cols = np.where(col_ink > 0)[0]
        if len(active_rows) == 0 or len(active_cols) == 0:
            return cell_text

        top, bottom = active_rows.min(), active_rows.max()
        left, right = active_cols.min(), active_cols.max()
        char_h = bottom - top + 1
        char_w_span = right - left + 1

        if char_h < 6 or char_w_span < 8:
            return cell_text

        # 2. Baseline zone is bottom 35% of active character height
        baseline_start = top + int(char_h * 0.65)
        upper_end = baseline_start

        # Check for isolated dot in baseline zone
        # A decimal dot has:
        # - width 1 to 3 pixels
        # - height 1 to 3 pixels
        # - zero ink in upper zone (from top to upper_end) in its columns
        # - zero ink directly above it for at least 2 pixels (or to top)
        # - at least 1 pixel of blank space to the left and right in the baseline rows
        # - positioned strictly between the left and right edges of active ink
        
        found_dot_x = None

        # Scan candidate dot column intervals [c, c + dw - 1]
        for dw in [1, 2, 3]:
            if found_dot_x is not None:
                break
            for c in range(left + 2, right - dw - 1):
                cols = list(range(c, c + dw))
                
                # Must have zero ink in the upper zone for all these columns
                if binary[top:upper_end, cols].sum() > 0:
                    continue

                # Check ink in the baseline zone for these columns
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

                # A genuine decimal dot must sit on the baseline (touching bottom or bottom - 1)
                if max_r < bottom - 1:
                    continue

                # Left isolation: column c - 1 must have zero ink across [min_r .. max_r]
                if binary[min_r:max_r + 1, c - 1].sum() > 0:
                    continue

                # Right isolation: column c + dw must have zero ink across [min_r .. max_r]
                if binary[min_r:max_r + 1, c + dw].sum() > 0:
                    continue

                # Above isolation: at least 2 pixels of whitespace directly above dot
                above_check_top = max(top, min_r - 2)
                if min_r > above_check_top and binary[above_check_top:min_r, cols].sum() > 0:
                    continue

                # Found genuine isolated baseline dot!
                found_dot_x = c + (dw - 1) / 2.0
                break

        if found_dot_x is not None:
            # Determine character insertion position based on relative x coordinate
            num_chars = len(clean_digits)
            # Relative position in active character span
            rel_x = (found_dot_x - left) / float(char_w_span)
            insert_idx = int(round(rel_x * num_chars))
            insert_idx = max(1, min(insert_idx, num_chars - 1))
            refined = clean_digits[:insert_idx] + "." + clean_digits[insert_idx:]
            return cell_text.replace(clean_digits, refined)

    except Exception as e:
        pass

    return cell_text
