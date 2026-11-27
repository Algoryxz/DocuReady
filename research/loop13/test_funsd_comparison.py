"""
Compare Baseline vs Column-Aware on FUNSD Documents
"""
import sys
import pymupdf
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.docuready.ingest.extractor import PageOCRData, _ocr_page
from research.loop13.spatial_layout_experiment import cluster_words_column_aware

doc = pymupdf.open("research/loop11_benchmark/data/funsd/funsd_001.pdf")
page = doc[0]
pix = page.get_pixmap(dpi=150)
import PIL.Image, pytesseract
img = PIL.Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
doc.close()

# 1. Baseline PageOCRData
base_ocr = PageOCRData(data, dpi=150)
print("=== BASELINE PageOCRData (First 8 lines) ===")
for i, l in enumerate(base_ocr.lines[:8]):
    print(f"Line {i+1}: {l['text']}")

# 2. Extract words_meta
scale = 72.0 / 150.0
words_meta = []
for i in range(len(data["text"])):
    w = str(data["text"][i]).strip()
    conf = float(data["conf"][i])
    if not w or conf < 0:
        continue
    lx = float(data["left"][i])
    ty = float(data["top"][i])
    rx = lx + float(data["width"][i])
    by = ty + float(data["height"][i])
    words_meta.append({
        "word": w,
        "box": [round(lx * scale, 1), round(ty * scale, 1), round(rx * scale, 1), round(by * scale, 1)],
        "conf": conf,
        "x0": lx * scale,
        "y0": ty * scale
    })

# 3. Column-aware grouping
new_lines = cluster_words_column_aware(words_meta, y_tol=6.0, min_gutter_width=20.0)
print("\n=== COLUMN-AWARE PageOCRData (First 8 lines) ===")
for i, l in enumerate(new_lines[:8]):
    line_text = " ".join(item["word"] for item in l)
    print(f"Line {i+1}: {line_text}")
