import sys
from pathlib import Path
from PIL import Image
import numpy as np

sys.path.insert(0, str(Path(".").resolve()))
from research.loop23.disambiguate_glyph import disambiguate_4_vs_8

L21_DIR = Path("research/loop21")
img1 = Image.open(L21_DIR / "tables" / "DEC_01_BIOCHEMISTRY_REPORT.png")

# Digit 4 in '24': bbox=(292, 236, 304, 244)
crop_24 = img1.crop((292, 236, 304, 244))
arr_24 = np.array(crop_24.convert("L"))
# Second digit is columns 6..12
digit_4 = arr_24[:, 6:]
print("Digit '4' in '24' detected as:", disambiguate_4_vs_8(digit_4))

# Digit 8 in '0.8': bbox=(292, 160, 307, 168)
crop_08 = img1.crop((292, 160, 307, 168))
arr_08 = np.array(crop_08.convert("L"))
# '0.8' has '8' in the rightmost columns
digit_8 = arr_08[:, 9:]
print("Digit '8' in '0.8' detected as:", disambiguate_4_vs_8(digit_8))
