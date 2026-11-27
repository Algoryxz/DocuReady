import sys
from pathlib import Path
from PIL import Image
import pytesseract

sys.path.insert(0, str(Path("src").resolve()))
from docuready.ingest.tesseract_discovery import configure_pytesseract

configure_pytesseract()
L21_DIR = Path("research/loop21")

def refine_micro_numeric(cell_text: str, crop: Image.Image) -> str:
    """
    If cell_text is numeric (digits/decimals) and crop is very small (height <= 12),
    upsample 2x bicubic and re-read with whitelist to eliminate low-res LSTM confusion.
    """
    clean = cell_text.replace(" ", "").replace(",", "")
    # Check if purely numeric
    if not clean.replace(".", "").isdigit():
        return cell_text
    
    # If crop is small:
    if crop.height <= 14:
        # Add a small white border and upsample 2x
        scaled = crop.resize((crop.width * 2, crop.height * 2), Image.Resampling.BICUBIC)
        # Pad with 10px white border for Tesseract LSTM safety
        padded = Image.new("RGB", (scaled.width + 20, scaled.height + 20), (255, 255, 255))
        padded.paste(scaled, (10, 10))
        
        re_txt = pytesseract.image_to_string(
            padded,
            config="--psm 7 -c tessedit_char_whitelist=0123456789."
        ).strip()
        if re_txt and re_txt.replace(".", "").isdigit():
            # If the re_txt has the same length or is a valid numeric replacement
            return re_txt
            
    return cell_text

img1 = Image.open(L21_DIR / "tables" / "DEC_01_BIOCHEMISTRY_REPORT.png")
# Cell (4,1) '24' was read as '28' on full page.
crop1_24 = img1.crop((292, 236, 304, 244))
print("cell (4,1) '28' refined ->", refine_micro_numeric("28", crop1_24))

# Also test on other cells
crop1_42 = img1.crop((292, 122, 307, 130))
print("cell (1,1) '42' refined ->", refine_micro_numeric("42", crop1_42))
