import json
import sys
from pathlib import Path
from PIL import Image
import pytesseract
import numpy as np
import re
from typing import Any

sys.path.insert(0, str(Path("src").resolve()))
sys.path.insert(0, str(Path(".").resolve()))
from docuready.ingest.tesseract_discovery import configure_pytesseract
from docuready.ingest.table_association import build_table_grid, TableGrid, TableCell
from research.loop22.benchmark.run_loop22_benchmark import evaluate_field
from research.loop23.refine_v2 import refine_decimal_v2

configure_pytesseract()

def refine_micro_cell(cell_text: str, crop: Any) -> str:
    """
    Unified micro-font numeric and decimal integrity refinement.
    """
    if not cell_text or crop is None:
        return cell_text

    # 1. Decimal point recovery
    text = refine_decimal_v2(cell_text, crop)

    # 2. Check for '8' vs '4' confusion in sub-12px numeric text
    clean_digits = re.sub(r"^(Rs\.?|INR|₹)\s*", "", text, flags=re.IGNORECASE).replace(",", "").strip()
    if clean_digits.isdigit() and "8" in clean_digits:
        try:
            arr = np.array(crop.convert("L")) if hasattr(crop, "convert") else np.array(crop)
            thresh = (int(arr.min()) + int(arr.max())) // 2
            binary = arr < thresh
            row_ink = binary.sum(axis=1)
            active_r = np.where(row_ink > 0)[0]
            if len(active_r) >= 6 and (active_r.max() - active_r.min() + 1) <= 12:
                # Sub-12px character height!
                # Split characters horizontally
                col_ink = binary[active_r.min():active_r.max()+1, :].sum(axis=0)
                active_c = np.where(col_ink > 0)[0]
                if len(active_c) > 0:
                    c_left, c_right = active_c.min(), active_c.max()
                    num_chars = len(clean_digits)
                    char_w = (c_right - c_left + 1) / float(num_chars)
                    
                    chars = list(clean_digits)
                    changed = False
                    for idx, ch in enumerate(chars):
                        if ch == "8":
                            ch_c1 = int(c_left + idx * char_w)
                            ch_c2 = int(c_left + (idx + 1) * char_w)
                            ch_bin = binary[active_r.min():active_r.max()+1, ch_c1:ch_c2]
                            # Check if glyph is actually '4'
                            row_sums = ch_bin.sum(axis=1)
                            if len(row_sums) >= 6:
                                bar_row = int(np.argmax(row_sums))
                                if 2 <= bar_row < len(ch_bin) - 1:
                                    below_bar = ch_bin[bar_row + 1:, :]
                                    mid_w = ch_bin.shape[1] // 2
                                    left_below = below_bar[:, :mid_w].sum()
                                    right_below = below_bar[:, mid_w:].sum()
                                    if left_below == 0 and right_below > 0:
                                        chars[idx] = "4"
                                        changed = True
                    if changed:
                        new_digits = "".join(chars)
                        text = text.replace(clean_digits, new_digits)
        except Exception:
            pass

    return text

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
    
    # Apply our unified micro refinement to all grid cells
    for r in grid.rows:
        for c in r:
            crop = img.crop(c.bbox)
            c.text = refine_micro_cell(c.text, crop)
            
    for fld in doc_meta["critical_fields"]:
        res = evaluate_field(grid, fld, doc_id, page_text, img=img, conf_threshold=60.0)
        print(f"  Field '{fld['name']}':")
        print(f"    Expected:  '{fld['expected']}'")
        print(f"    Extracted: '{res.get('extracted_value')}'")
        print(f"    Status:    {res.get('status')}")
        print(f"    Conf:      {res.get('confidence')}")
        print(f"    Is FV:     {res.get('is_false_verification')}")
