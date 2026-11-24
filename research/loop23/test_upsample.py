import sys
from pathlib import Path
from PIL import Image
import pytesseract

sys.path.insert(0, str(Path("src").resolve()))
from docuready.ingest.tesseract_discovery import configure_pytesseract

configure_pytesseract()
L21_DIR = Path("research/loop21")

img1 = Image.open(L21_DIR / "tables" / "DEC_01_BIOCHEMISTRY_REPORT.png")
# Cell (4,1) '24': bbox=(292, 236, 304, 244)
crop1_24 = img1.crop((292, 236, 304, 244))

print("Raw crop size:", crop1_24.size)
for psm in [7, 8, 10, 6]:
    txt_raw = pytesseract.image_to_string(crop1_24, config=f"--psm {psm} -c tessedit_char_whitelist=0123456789.").strip()
    print(f"Raw PSM {psm}: '{txt_raw}'")

for scale in [2, 3, 4]:
    scaled = crop1_24.resize((crop1_24.width * scale, crop1_24.height * scale), Image.Resampling.BICUBIC)
    for psm in [7, 8, 10, 6]:
        txt_scaled = pytesseract.image_to_string(scaled, config=f"--psm {psm} -c tessedit_char_whitelist=0123456789.").strip()
        print(f"Scaled {scale}x PSM {psm}: '{txt_scaled}'")

# Also test cell (1,1) '4.2'
crop1_42 = img1.crop((292, 122, 307, 130))
print("\nRaw crop1_42 size:", crop1_42.size)
for scale in [1, 2, 3]:
    target = crop1_42 if scale == 1 else crop1_42.resize((crop1_42.width * scale, crop1_42.height * scale), Image.Resampling.BICUBIC)
    for psm in [7, 8, 6]:
        txt = pytesseract.image_to_string(target, config=f"--psm {psm} -c tessedit_char_whitelist=0123456789.").strip()
        print(f"4.2 Scaled {scale}x PSM {psm}: '{txt}'")
