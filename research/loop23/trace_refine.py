import sys
from pathlib import Path
from PIL import Image
import numpy as np

sys.path.insert(0, str(Path("src").resolve()))
from docuready.ingest.table_association import refine_cell_decimal_point

L21_DIR = Path("research/loop21")
img1 = Image.open(L21_DIR / "tables" / "DEC_01_BIOCHEMISTRY_REPORT.png")
crop1 = img1.crop((292, 122, 307, 130))

arr = np.array(crop1.convert("L"))
h, w = arr.shape[:2]
thresh = (int(arr.min()) + int(arr.max())) // 2
binary = arr < thresh
baseline_zone_start = int(h * 0.70)
upper_ink = binary[:baseline_zone_start, :].sum(axis=0)
gap_cols = np.where(upper_ink == 0)[0]
print("h, w:", h, w)
print("baseline_zone_start:", baseline_zone_start)
print("upper_ink:", upper_ink)
print("gap_cols:", gap_cols)

gaps = []
curr = [gap_cols[0]]
for c in gap_cols[1:]:
    if c == curr[-1] + 1:
        curr.append(c)
    else:
        gaps.append(curr)
        curr = [c]
gaps.append(curr)
print("gaps:", gaps)

for g in gaps:
    print(f"Checking gap {g}: g[0]={g[0]}, g[-1]={g[-1]}, w={w}, len(g)={len(g)}")
    if g[0] >= 2 and g[-1] <= w - 3 and len(g) >= 2:
        gap_sub = binary[baseline_zone_start:h, g]
        dot_ink = gap_sub.sum()
        print(f"  Passed initial check! dot_ink = {dot_ink}")
        if 1 <= dot_ink <= 6:
            dot_rows, dot_cols = np.where(gap_sub)
            dot_abs_rows = baseline_zone_start + dot_rows
            dot_abs_cols = g[0] + dot_cols
            min_c = dot_abs_cols.min()
            max_c = dot_abs_cols.max()
            left_ink = binary[dot_abs_rows, min_c - 1].sum() if min_c > 0 else 1
            right_ink = binary[dot_abs_rows, max_c + 1].sum() if max_c < w - 1 else 1
            min_r = dot_abs_rows.min()
            above_ink = binary[max(0, min_r - 2):min_r, min_c:max_c + 1].sum()
            print(f"  left_ink={left_ink}, right_ink={right_ink}, above_ink={above_ink}")
    else:
        print("  Failed initial condition:", g[0] >= 2, g[-1] <= w - 3, len(g) >= 2)
