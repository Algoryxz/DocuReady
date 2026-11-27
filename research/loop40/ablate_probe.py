import os
import sys
import time
import ctypes
from pathlib import Path
from PIL import Image
import numpy as np
import fitz

REPO = Path(r"C:\Users\smara\Desktop\New folder")
sys.path.insert(0, str(REPO / "src"))

from docuready.ingest.script_router import detect_unicode_script
from docuready.ingest.tesseract_discovery import find_tesseract_binary_with_source, get_unified_tessdata_dir

os.environ.setdefault("OMP_THREAD_LIMIT", "1")

tess_bin, _ = find_tesseract_binary_with_source()
tess_dir = Path(tess_bin).parent
dll_path = tess_dir / "libtesseract-5.dll"
tessdata_dir = get_unified_tessdata_dir(tess_bin)

lib = ctypes.CDLL(str(dll_path))
lib.TessBaseAPICreate.restype = ctypes.c_void_p
lib.TessBaseAPIDelete.argtypes = [ctypes.c_void_p]
lib.TessBaseAPIInit3.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p]
lib.TessBaseAPIInit3.restype = ctypes.c_int
lib.TessBaseAPISetPageSegMode.argtypes = [ctypes.c_void_p, ctypes.c_int]
lib.TessBaseAPISetImage.argtypes = [
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
]
lib.TessBaseAPIGetUTF8Text.argtypes = [ctypes.c_void_p]
lib.TessBaseAPIGetUTF8Text.restype = ctypes.c_void_p
lib.TessDeleteText.argtypes = [ctypes.c_void_p]

t_init0 = time.perf_counter()
api = lib.TessBaseAPICreate()
rc = lib.TessBaseAPIInit3(api, str(tessdata_dir).encode("utf-8"), b"eng+hin+ori")
lib.TessBaseAPISetPageSegMode(api, 6)
t_init_ms = (time.perf_counter() - t_init0) * 1000.0
print(f"TessBaseAPIInit3 rc={rc}, init_ms={t_init_ms:.2f}")

CORPUS_DIRS = [
    REPO / "research/loop18/corpus",
    REPO / "research/loop17/corpus",
    REPO / "research/loop14/corpus",
]

def load_doc(doc_id: str) -> Image.Image:
    for d in CORPUS_DIRS:
        pdf_p = d / f"{doc_id}.pdf"
        png_p = d / f"{doc_id}.png"
        if pdf_p.exists():
            doc = fitz.open(str(pdf_p))
            pix = doc[0].get_pixmap(dpi=200)
            return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        if png_p.exists():
            return Image.open(png_p).convert("RGB")
    raise FileNotFoundError(doc_id)

DOC_IDS = [
    "DOC_CTRL_01_ENGLISH_CERTIFICATE",
    "DOC_EXT_06_ODIA_REVENUE_NOTICE",
    "DOC_HIN_01_ADMIN_CIRCULAR",
    "DOC_ORI_01_ADMIN_CIRCULAR",
    "DOC_MIX_01_HIN_ENG_SCHOLARSHIP",
    "DOC_MIX_02_ORI_ENG_SCHOLARSHIP",
]

def run_probe(img: Image.Image, y0_frac: float, y1_frac: float, max_dim: float):
    t0 = time.perf_counter()
    gray = img.convert("L") if img.mode != "L" else img
    w, h = gray.size
    strip = gray.crop((int(w * 0.15), int(h * y0_frac), int(w * 0.85), int(h * y1_frac)))
    scale = min(1.0, max_dim / max(strip.size))
    tw, th = max(10, int(strip.width * scale)), max(10, int(strip.height * scale))
    thumb = strip.resize((tw, th), Image.Resampling.BILINEAR)
    arr = np.ascontiguousarray(np.asarray(thumb, dtype=np.uint8))
    lib.TessBaseAPISetImage(api, arr.ctypes.data, tw, th, 1, tw)
    ptr = lib.TessBaseAPIGetUTF8Text(api)
    txt = ctypes.string_at(ptr).decode("utf-8", errors="replace") if ptr else ""
    if ptr:
        lib.TessDeleteText(ptr)
    dt = (time.perf_counter() - t0) * 1000.0
    res = detect_unicode_script(txt) if len(txt.strip()) >= 5 else {"primary_script": "UNKNOWN", "is_mixed": False, "counts": {}}
    return dt, res["primary_script"], res["is_mixed"], res["counts"], len(txt.strip())

loaded = {}
for did in DOC_IDS:
    try:
        loaded[did] = load_doc(did)
    except FileNotFoundError:
        print(f"MISSING: {did}")

for cfg in [
    ("450px_0.25_0.55", 0.25, 0.55, 450.0),
    ("350px_0.25_0.45", 0.25, 0.45, 350.0),
]:
    label, y0, y1, md = cfg
    print(f"\n=== {label} ===")
    for did, img in loaded.items():
        run_probe(img, y0, y1, md)
        times = []
        last = None
        for _ in range(5):
            dt, ps, mx, cnt, nch = run_probe(img, y0, y1, md)
            times.append(dt)
            last = (ps, mx, cnt, nch)
        mean_ms = sum(times) / len(times)
        print(f"  {did:34s} mean={mean_ms:6.1f}ms script={last[0]:10s} mixed={str(last[1]):5s} chars={last[3]:3d} counts={last[2]}")

lib.TessBaseAPIDelete(api)
