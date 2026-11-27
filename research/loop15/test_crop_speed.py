import time
import pytesseract
from PIL import Image
from docuready.ingest.tesseract_discovery import configure_pytesseract

configure_pytesseract()

img = Image.open('research/loop14/corpus/DOC_MIX_01_HIN_ENG_SCHOLARSHIP.png')
c1 = img.crop((0, 0, 1000, 150))
c2 = img.crop((0, 150, 1000, 750))

t0 = time.perf_counter()
d1 = pytesseract.image_to_data(c1, lang='eng', output_type=pytesseract.Output.DICT)
t1 = time.perf_counter()
d2 = pytesseract.image_to_data(c2, lang='eng+hin', output_type=pytesseract.Output.DICT)
t2 = time.perf_counter()

w1 = [w for w in d1["text"] if w.strip()]
w2 = [w for w in d2["text"] if w.strip()]

print(f"Crop 1 (eng): {(t1-t0)*1000:.1f} ms, tokens: {len(w1)}")
print(f"Crop 2 (eng+hin): {(t2-t1)*1000:.1f} ms, tokens: {len(w2)}")
print(f"Total: {(t2-t0)*1000:.1f} ms")
