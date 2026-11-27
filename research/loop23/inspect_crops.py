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

def inspect_doc(doc_id):
    img_path = L21_DIR / "tables" / f"{doc_id}.png"
    img = Image.open(img_path)
    w, h = img.size
    ocr_data = pytesseract.image_to_data(img, lang="eng", output_type=pytesseract.Output.DICT)
    grid = build_table_grid(ocr_data=ocr_data, page_width=w, page_height=h, image=img)
    
    print(f"\n--- Cells in {doc_id} ---")
    for r_idx, row in enumerate(grid.rows):
        row_vals = []
        for c_idx, cell in enumerate(row):
            crop = img.crop(cell.bbox)
            arr = np.array(crop.convert("L"))
            row_vals.append(f"({r_idx},{c_idx}) '{cell.text}' bbox={cell.bbox} crop_shape={arr.shape}")
        print("\n".join(row_vals))

inspect_doc("DEC_01_BIOCHEMISTRY_REPORT")
inspect_doc("DEC_02_COMMODITY_RATES")
