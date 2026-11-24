import json
import sys
from pathlib import Path
from PIL import Image
import numpy as np
import pytesseract

sys.path.insert(0, str(Path("src").resolve()))
sys.path.insert(0, str(Path(".").resolve()))
from docuready.ingest.tesseract_discovery import configure_pytesseract
from docuready.ingest.table_association import build_table_grid, refine_cell_decimal_point

configure_pytesseract()
L21_DIR = Path("research/loop21")

img1 = Image.open(L21_DIR / "tables" / "DEC_01_BIOCHEMISTRY_REPORT.png")
# Let's inspect cell (1,1): expected '4.2', got '42', bbox=(292, 122, 307, 130)
crop1 = img1.crop((292, 122, 307, 130))
arr1 = np.array(crop1.convert("L"))
print("=== DEC_01 cell (1,1) ===")
print("arr1 shape:", arr1.shape)
print("Binary (min, max):", arr1.min(), arr1.max())
thresh1 = (int(arr1.min()) + int(arr1.max())) // 2
bin1 = arr1 < thresh1
print("Ink map (1=ink, 0=white):")
for r in bin1:
    print("".join("#" if x else "." for x in r))

print("\nRunning refine_cell_decimal_point('42', crop1):")
print("Result:", refine_cell_decimal_point("42", crop1))

# Let's inspect cell (4,1) in DEC_01: expected '24', got '28', bbox=(292, 236, 304, 244)
crop1_24 = img1.crop((292, 236, 304, 244))
arr1_24 = np.array(crop1_24.convert("L"))
print("\n=== DEC_01 cell (4,1) '24' ===")
print("arr1_24 shape:", arr1_24.shape)
thresh1_24 = (int(arr1_24.min()) + int(arr1_24.max())) // 2
bin1_24 = arr1_24 < thresh1_24
for r in bin1_24:
    print("".join("#" if x else "." for x in r))

# Let's inspect DEC_02 cell (3,1): expected '68.5', got '685', bbox=(288, 187, 313, 216)
img2 = Image.open(L21_DIR / "tables" / "DEC_02_COMMODITY_RATES.png")
crop2 = img2.crop((288, 187, 313, 216))
arr2 = np.array(crop2.convert("L"))
print("\n=== DEC_02 cell (3,1) '685' ===")
print("arr2 shape:", arr2.shape)
thresh2 = (int(arr2.min()) + int(arr2.max())) // 2
bin2 = arr2 < thresh2
# Trim empty rows
row_ink = bin2.sum(axis=1)
col_ink = bin2.sum(axis=0)
active_rows = np.where(row_ink > 0)[0]
active_cols = np.where(col_ink > 0)[0]
print(f"Active rows: {active_rows.min()}..{active_rows.max()}, Active cols: {active_cols.min()}..{active_cols.max()}")
for r in bin2[active_rows.min():active_rows.max()+1, active_cols.min():active_cols.max()+1]:
    print("".join("#" if x else "." for x in r))

print("\nRunning refine_cell_decimal_point('685', crop2):")
print("Result:", refine_cell_decimal_point("685", crop2))
