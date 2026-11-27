import json
import sys
from pathlib import Path
from PIL import Image
import pytesseract

sys.path.insert(0, str(Path("src").resolve()))
sys.path.insert(0, str(Path(".").resolve()))
from docuready.ingest.tesseract_discovery import configure_pytesseract
from docuready.ingest.table_association import build_table_grid
from research.loop23.narrow_gutter import resolve_narrow_gutter_cell_token

configure_pytesseract()

img_path = Path("research/loop22/tables/ASSOC_03_GUTTER_BLEED_SPLIT_CELL.png")
img = Image.open(img_path)
w, h = img.size

ocr_data = pytesseract.image_to_data(img, lang="eng", output_type=pytesseract.Output.DICT)
grid = build_table_grid(ocr_data=ocr_data, page_width=w, page_height=h, image=img)

cell = grid.rows[1][1]
header = grid.rows[0][1].text
print("Header text:", header)
print("Cell text:  ", cell.text)
print("Cell words: ", cell.words)

resolved, is_res, conf, reason = resolve_narrow_gutter_cell_token(
    cell_words=cell.words,
    header_text=header,
    col_pattern="Base Tax",
    field_name="binodini_base_tax",
    clean_val=cell.text,
)
print("\nResolution for 'Base Tax':")
print(f"  Resolved value: '{resolved}'")
print(f"  Is resolved:     {is_res}")
print(f"  Conf:            {conf}")
print(f"  Reason:          {reason}")

resolved2, is_res2, conf2, reason2 = resolve_narrow_gutter_cell_token(
    cell_words=cell.words,
    header_text=header,
    col_pattern="Penalty",
    field_name="binodini_penalty",
    clean_val=cell.text,
)
print("\nResolution for 'Penalty':")
print(f"  Resolved value: '{resolved2}'")
print(f"  Is resolved:     {is_res2}")
print(f"  Conf:            {conf2}")
print(f"  Reason:          {reason2}")
