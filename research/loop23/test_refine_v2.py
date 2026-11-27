import sys
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(".").resolve()))
from research.loop23.refine_v2 import refine_decimal_v2

L21_DIR = Path("research/loop21")
img1 = Image.open(L21_DIR / "tables" / "DEC_01_BIOCHEMISTRY_REPORT.png")
crop1_42 = img1.crop((292, 122, 307, 130))
crop1_24 = img1.crop((292, 236, 304, 244))

img2 = Image.open(L21_DIR / "tables" / "DEC_02_COMMODITY_RATES.png")
crop2_685 = img2.crop((288, 187, 313, 216))
crop2_3100 = img2.crop((572, 274, 596, 282))

print("DEC_01 '42' ->", refine_decimal_v2("42", crop1_42))
print("DEC_01 '24' ->", refine_decimal_v2("24", crop1_24))
print("DEC_02 '685' ->", refine_decimal_v2("685", crop2_685))
print("DEC_02 '3100' ->", refine_decimal_v2("3100", crop2_3100))
