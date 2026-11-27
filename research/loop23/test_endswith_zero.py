import sys
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(".").resolve()))
from docuready.ingest.table_association import refine_cell_decimal_point

img_inv = Image.open("research/loop23/tables/COHORT_H_04_NARROW_GUTTER_INVOICE.png")
# '45.50' is at left=280, top=132, right=307, bot=141
crop_4550 = img_inv.crop((280 - 5, 132 - 5, 307 + 5, 141 + 5))

# Also check integers: 3100 and 640
img_dec = Image.open("research/loop21/tables/DEC_02_COMMODITY_RATES.png")
crop_3100 = img_dec.crop((572 - 5, 274 - 5, 596 + 5, 282 + 5))

print("Current refine_cell_decimal_point('4550'):", refine_cell_decimal_point("4550", crop_4550))
print("Current refine_cell_decimal_point('3100'):", refine_cell_decimal_point("3100", crop_3100))
