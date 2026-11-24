import numpy as np

def verify_digit_4_vs_8(char_binary: np.ndarray) -> str:
    """
    Checks if a character glyph (height <= 12) read as '8' is actually '4'.
    In '4', the lower-left quadrant (below 60% height, left 60% width) is strictly empty,
    while the right side has the descending stem.
    In '8', the lower loop contains ink in both the left and right halves.
    """
    row_ink = char_binary.sum(axis=1)
    col_ink = char_binary.sum(axis=0)
    active_r = np.where(row_ink > 0)[0]
    active_c = np.where(col_ink > 0)[0]
    if len(active_r) < 6 or len(active_c) < 3:
        return "unknown"

    sub = char_binary[active_r.min():active_r.max()+1, active_c.min():active_c.max()+1]
    h, w = sub.shape

    # Lower 35% of the glyph
    low_start = int(h * 0.65)
    lower_zone = sub[low_start:, :]
    
    # Left 50% vs Right 50%
    mid_w = w // 2
    left_ink = lower_zone[:, :mid_w].sum()
    right_ink = lower_zone[:, mid_w:].sum()

    # Upper 50% must have ink
    upper_ink = sub[:low_start, :].sum()

    if left_ink == 0 and right_ink >= 1 and upper_ink >= 4:
        return "4"
    elif left_ink >= 1 and right_ink >= 1:
        return "8"
    return "unknown"

# Test on DEC_01 '24' second digit (columns 6..12)
from PIL import Image
img1 = Image.open('research/loop21/tables/DEC_01_BIOCHEMISTRY_REPORT.png')
crop_24 = img1.crop((292, 236, 304, 244))
bin_24 = np.array(crop_24.convert('L')) < 128
char_24_second = bin_24[:, 6:]
print("DEC_01 second digit in '28':", verify_digit_4_vs_8(char_24_second))

# Test on DEC_01 '0.8' digit 8 (columns 9..15)
crop_08 = img1.crop((292, 160, 307, 168))
bin_08 = np.array(crop_08.convert('L')) < 128
char_08_digit = bin_08[:, 9:]
print("DEC_01 digit '8' in '0.8':", verify_digit_4_vs_8(char_08_digit))
