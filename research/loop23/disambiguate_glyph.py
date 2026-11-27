import numpy as np

def disambiguate_4_vs_8(digit_crop_arr: np.ndarray) -> str:
    """
    Distinguishes digit '4' vs '8' in low-resolution (sub-12px) crops using pure NumPy.
    A digit '8' has ink on both left and right sides of its bottom loop.
    A digit '4' has a vertical stem on the right and completely blank space on the left in the bottom third.
    """
    thresh = (int(digit_crop_arr.min()) + int(digit_crop_arr.max())) // 2
    binary = digit_crop_arr < thresh
    
    # Active ink box
    row_ink = binary.sum(axis=1)
    col_ink = binary.sum(axis=0)
    active_rows = np.where(row_ink > 0)[0]
    active_cols = np.where(col_ink > 0)[0]
    if len(active_rows) < 6 or len(active_cols) < 3:
        return "unknown"
        
    top, bot = active_rows.min(), active_rows.max()
    left, right = active_cols.min(), active_cols.max()
    h = bot - top + 1
    w = right - left + 1
    
    # Bottom 30% of glyph
    bot_zone = binary[bot - int(h * 0.3):bot + 1, left:right + 1]
    # Check left half vs right half in bottom zone
    mid_col = w // 2
    left_bot_ink = bot_zone[:, :mid_col].sum()
    right_bot_ink = bot_zone[:, mid_col:].sum()
    
    if left_bot_ink == 0 and right_bot_ink > 0:
        return "4"
    elif left_bot_ink > 0 and right_bot_ink > 0:
        return "8"
    return "unknown"
