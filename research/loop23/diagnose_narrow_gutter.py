import json
import sys
from pathlib import Path
from PIL import Image
import pytesseract
import numpy as np

sys.path.insert(0, str(Path("src").resolve()))
sys.path.insert(0, str(Path(".").resolve()))
from docuready.ingest.tesseract_discovery import configure_pytesseract
from docuready.ingest.table_association import build_table_grid
from research.loop22.benchmark.run_loop22_benchmark import evaluate_field

configure_pytesseract()

img_path = Path("research/loop22/tables/ASSOC_03_GUTTER_BLEED_SPLIT_CELL.png")
img = Image.open(img_path)
w, h = img.size

ocr_data = pytesseract.image_to_data(img, lang="eng", output_type=pytesseract.Output.DICT)
grid = build_table_grid(ocr_data=ocr_data, page_width=w, page_height=h, image=img)

print(f"ASSOC_03 TableGrid: {len(grid.rows)} rows, {grid.num_cols} columns")
print(f"Col boundaries: {grid.col_boundaries}")
for r_idx, row in enumerate(grid.rows):
    row_str = " | ".join(f"col {c.col}: '{c.text}' (bbox={c.bbox})" for c in row)
    print(f"Row {r_idx}: {row_str}")

with open("research/loop22/dataset_manifest.json") as f:
    m22 = json.load(f)
doc_meta = m22["documents"]["ASSOC_03_GUTTER_BLEED_SPLIT_CELL"]

valid_words = [str(txt).strip() for txt in ocr_data.get("text", []) if str(txt).strip()]
page_text = " ".join(valid_words)

for cf in doc_meta["critical_fields"]:
    res = evaluate_field(grid, cf, "ASSOC_03_GUTTER_BLEED_SPLIT_CELL", page_text, img=img, conf_threshold=60.0)
    print(f"\nField '{cf['name']}':")
    print(f"  Expected:  '{cf['expected']}'")
    print(f"  Extracted: '{res.get('extracted_value')}'")
    print(f"  Status:    {res.get('status')}")
    print(f"  Conf:      {res.get('confidence')}")
    print(f"  Abstain:   {res.get('is_abstained')}")
    print(f"  Reason:    {res.get('abstention_reason')}")
