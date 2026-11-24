import numpy as np
import re
from typing import Any
from PIL import Image

def test_dot_morphology(cell_text: str, cell_crop: Any) -> str:
    if not cell_text or "." in cell_text or cell_crop is None:
        return cell_text

    clean_digits = re.sub(r"^(Rs\.?|INR|₹)\s*", "", cell_text, flags=re.IGNORECASE).replace(",", "").strip()
    if not clean_digits.isdigit() or not (2 <= len(clean_digits) <= 5):
        return cell_text

    # Standard integers with two trailing zeros (e.g. 100, 500, 3100, 4000) are always integers
    if len(clean_digits) >= 3 and clean_digits.endswith("00"):
        return cell_text

    try:
        arr = np.array(cell_crop.convert("L")) if hasattr(cell_crop, "convert") else np.array(cell_crop)
        h, w = arr.shape[:2]
        if h < 6 or w < 8:
            return cell_text

        thresh = (int(arr.min()) + int(arr.max())) // 2
        binary = arr < thresh

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

        baseline_start = top + int(char_h * 0.65)
        upper_end = baseline_start
        found_dot_x = None

        for dw in [1, 2, 3]:
            if found_dot_x is not None:
                break
            for c in range(left + 2, right - dw - 1):
                cols = list(range(c, c + dw))
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

                # Must sit on baseline
                if max_r < bottom - 1:
                    continue

                if binary[min_r:max_r + 1, c - 1].sum() > 0:
                    continue
                if binary[min_r:max_r + 1, c + dw].sum() > 0:
                    continue

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
            return cell_text.replace(clean_digits, refined)

    except Exception:
        pass

    return cell_text

img_inv = Image.open("research/loop23/tables/COHORT_H_04_NARROW_GUTTER_INVOICE.png")
crop_4550 = img_inv.crop((280 - 5, 132 - 5, 307 + 5, 141 + 5))
crop_3820 = img_inv.crop((281 - 5, 222 - 5, 307 + 5, 231 + 5))

img_dec = Image.open("research/loop21/tables/DEC_02_COMMODITY_RATES.png")
crop_3100 = img_dec.crop((572 - 5, 274 - 5, 596 + 5, 282 + 5))
crop_640 = img_dec.crop((432 - 5, 160 - 5, 459 + 5, 168 + 5))

print("4550 ->", test_dot_morphology("4550", crop_4550))
print("3820 ->", test_dot_morphology("3820", crop_3820))
print("3100 ->", test_dot_morphology("3100", crop_3100))
