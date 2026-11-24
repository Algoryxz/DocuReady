from pathlib import Path
from PIL import Image
import pytesseract
from docuready.ingest.table_association import (
    build_table_grid,
    extract_field_by_spatial_association,
)

img_path = Path("research/loop11_benchmark/data/funsd/funsd_001.png")
img = Image.open(img_path).convert("RGB")
tess_path = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
if tess_path.exists():
    pytesseract.pytesseract.tesseract_cmd = str(tess_path)

ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
grid = build_table_grid(ocr_data, page_width=img.width, page_height=img.height, image=img)

print(f"Grid num_rows: {grid.num_rows}, num_cols: {grid.num_cols}")
print("Col boundaries:", grid.col_boundaries)
print("Col headers:", grid.col_headers)
for r_idx, row in enumerate(grid.rows[:8]):
    row_texts = [f"col{c_idx}: '{c.text}'" for c_idx, c in enumerate(row)]
    print(f"Row {r_idx}:", " | ".join(row_texts))

ev = extract_field_by_spatial_association(
    grid=grid,
    field_name="Enrollment Roll Number",
    target_pattern="Enrollment Roll Number",
    expected_type="id",
    image=img,
)
print("\nExtraction result for 'Enrollment Roll Number':")
if ev:
    print(f"  value: '{ev.value}', conf: {ev.confidence}, decision: {ev.verification_decision}, reason: {ev.abstention_reason}, row: {ev.row_idx}, col: {ev.col_idx}")
else:
    print("  None returned")
