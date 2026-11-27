import sys
from pathlib import Path
from PIL import Image
import numpy as np

sys.path.insert(0, str(Path("src").resolve()))
from docuready.ingest.table_association import refine_cell_decimal_point

L21_DIR = Path("research/loop21")
img2 = Image.open(L21_DIR / "tables" / "DEC_02_COMMODITY_RATES.png")
crop2 = img2.crop((288, 187, 313, 216))

arr = np.array(crop2.convert("L"))
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
