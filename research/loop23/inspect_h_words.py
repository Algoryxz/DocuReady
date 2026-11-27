from PIL import Image
import pytesseract
from pathlib import Path
import sys
sys.path.insert(0, str(Path("src").resolve()))
from docuready.ingest.tesseract_discovery import configure_pytesseract
configure_pytesseract()

def inspect_doc(p):
    img = Image.open(p)
    d = pytesseract.image_to_data(img, lang="eng", output_type=pytesseract.Output.DICT)
    print(f"\n--- Words in {p.name} ---")
    for i in range(len(d["text"])):
        t = d["text"][i].strip()
        if t:
            l = d["left"][i]
            r = l + d["width"][i]
            print(f"  '{t}' left={l} right={r} top={d['top'][i]} conf={d['conf'][i]}")

inspect_doc(Path("research/loop23/tables/COHORT_H_03_NARROW_GUTTER_LEDGER.png"))
inspect_doc(Path("research/loop23/tables/COHORT_H_04_NARROW_GUTTER_INVOICE.png"))
inspect_doc(Path("research/loop23/tables/COHORT_H_01_MICRO_CLINICAL_PANEL.png"))
