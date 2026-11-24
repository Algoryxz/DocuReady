import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np

sys.path.insert(0, str(Path(".").resolve()))
from research.loop23.test_full_dec_fix import refine_micro_cell

try:
    font = ImageFont.truetype("arial.ttf", 11)
except Exception:
    font = ImageFont.load_default()

test_integers = [
    "24", "48", "84", "44", "88", "1480", "640", "3100", "4000",
    "40000", "84500", "100000", "50000", "75000", "120000", "80000", "500"
]

all_passed = True
for val in test_integers:
    img = Image.new("RGB", (100, 30), (255, 255, 255))
    d = ImageDraw.Draw(img)
    d.text((10, 8), val, fill=(0, 0, 0), font=font)
    
    # Bounding box of text
    arr = np.array(img.convert("L")) < 128
    r = np.where(arr.sum(axis=1) > 0)[0]
    c = np.where(arr.sum(axis=0) > 0)[0]
    crop = img.crop((c.min(), r.min(), c.max() + 1, r.max() + 1))
    
    refined = refine_micro_cell(val, crop)
    status = "PASS" if refined == val else f"FAIL (became '{refined}')"
    if refined != val:
        all_passed = False
    print(f"Integer '{val}': {status}")

print("\nInteger Safety Suite Result:", "ALL PASSED (100% Invariant)" if all_passed else "FAILURES DETECTED")
