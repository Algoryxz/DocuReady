from PIL import Image
import pytesseract
from pathlib import Path
import sys
sys.path.insert(0, str(Path("src").resolve()))
from docuready.ingest.tesseract_discovery import configure_pytesseract
configure_pytesseract()

img = Image.open('research/loop22/tables/ASSOC_03_GUTTER_BLEED_SPLIT_CELL.png')
d = pytesseract.image_to_data(img, lang='eng', output_type=pytesseract.Output.DICT)
for i in range(len(d['text'])):
    t = d['text'][i].strip()
    if t:
        l = d['left'][i]
        top = d['top'][i]
        r = l + d['width'][i]
        b = top + d['height'][i]
        print(f"word: {t:<28} left={l:<4} top={top:<4} right={r:<4} bot={b:<4}")
