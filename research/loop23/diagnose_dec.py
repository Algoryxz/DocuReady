import json
import sys
from pathlib import Path
from PIL import Image
import pytesseract

sys.path.insert(0, str(Path("src").resolve()))
sys.path.insert(0, str(Path(".").resolve()))
from docuready.ingest.tesseract_discovery import configure_pytesseract
from docuready.ingest.table_association import build_table_grid
from research.loop22.benchmark.run_loop22_benchmark import evaluate_field

configure_pytesseract()

L21_DIR = Path("research/loop21")
with open(L21_DIR / "dataset_manifest.json", "r", encoding="utf-8") as f:
    manifest = json.load(f)

for doc_id in ["DEC_01_BIOCHEMISTRY_REPORT", "DEC_02_COMMODITY_RATES", "DEC_03_PHARMA_DOSAGE"]:
    doc_meta = manifest["documents"][doc_id]
    img_path = L21_DIR / "tables" / f"{doc_id}.png"
    print(f"\n=================== Testing {doc_id} ===================")
    img = Image.open(img_path)
    w, h = img.size
    ocr_data = pytesseract.image_to_data(img, lang="eng", output_type=pytesseract.Output.DICT)
    valid_words = [str(txt).strip() for txt in ocr_data.get("text", []) if str(txt).strip()]
    page_text = " ".join(valid_words)

    grid = build_table_grid(ocr_data=ocr_data, page_width=w, page_height=h, image=img)
    print(f"TableGrid: {len(grid.rows)} rows, {grid.num_cols} columns")
    for fld in doc_meta["critical_fields"]:
        res = evaluate_field(grid, fld, doc_id, page_text, img=img, conf_threshold=60.0)
        print(f"  Field '{fld['name']}':")
        print(f"    Expected:  '{fld['expected']}'")
        print(f"    Extracted: '{res.get('extracted_value')}'")
        print(f"    Status:    {res.get('status')}")
        print(f"    Conf:      {res.get('confidence')}")
        print(f"    Is FV:     {res.get('is_false_verification')}")
