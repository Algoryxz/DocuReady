import sys
from pathlib import Path
from PIL import Image
import numpy as np

sys.path.insert(0, str(Path(".").resolve()))
from research.loop23.refine_v2 import refine_decimal_v2

img_inv = Image.open("research/loop23/tables/COHORT_H_04_NARROW_GUTTER_INVOICE.png")
crop_4550 = img_inv.crop((280 - 5, 132 - 5, 307 + 5, 141 + 5))

img_dec = Image.open("research/loop21/tables/DEC_02_COMMODITY_RATES.png")
crop_3100 = img_dec.crop((572 - 5, 274 - 5, 596 + 5, 282 + 5))

# Let's inspect ink map of crop_4550
arr = np.array(crop_4550.convert("L")) < 128
r = np.where(arr.sum(axis=1) > 0)[0]
c = np.where(arr.sum(axis=0) > 0)[0]
active = arr[r.min():r.max()+1, c.min():c.max()+1]
print("Shape of 45.50 active:", active.shape)
for row in active:
    print("".join("#" if x else "." for x in row))

# Test refine_decimal_v2 on 4550 and 3100
print("refine_decimal_v2('4550'):", refine_decimal_v2("4550", crop_4550))
print("refine_decimal_v2('3100'):", refine_decimal_v2("3100", crop_3100))
