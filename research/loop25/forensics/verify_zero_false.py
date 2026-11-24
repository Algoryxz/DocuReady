import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import json
from PIL import Image
import pytesseract
from docuready.ingest.table_association import build_table_grid
from research.loop25.benchmark.run_loop25_benchmark import evaluate_field_record, configure_pytesseract

configure_pytesseract()
ROOT = Path(".")
manifests = [
    (ROOT / "research/loop20/dataset_manifest.json", ROOT / "research/loop20/tables", True),
    (ROOT / "research/loop21/dataset_manifest.json", ROOT / "research/loop21/tables", True),
    (ROOT / "research/loop22/dataset_manifest.json", ROOT / "research/loop22/tables", True),
    (ROOT / "research/loop23/dataset_manifest.json", ROOT / "research/loop23/tables", True),
    (ROOT / "research/loop24/dataset_manifest.json", None, False),
    (ROOT / "research/loop25/dataset_manifest.json", None, False),
]

all_docs = {}
for m_path, t_dir, has_docs_key in manifests:
    m = json.load(open(m_path))
    docs = m["documents"] if has_docs_key else m
    for doc_id, meta in docs.items():
        img_p = (t_dir / f"{doc_id}.png") if t_dir else Path(meta["image_path"])
        all_docs[doc_id] = (meta, img_p)

print(f"Checking all {len(all_docs)} documents across Loops 20-25 for false verifications...")
false_count = 0
for doc_id, (meta, img_p) in all_docs.items():
    img = Image.open(img_p)
    ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    grid = build_table_grid(ocr_data, page_width=img.width, page_height=img.height, image=img)
    for f in meta["critical_fields"]:
        res = evaluate_field_record(grid, f, doc_id, img, 70.0)
        if res["is_false_verification"]:
            false_count += 1
            print(f"FAIL [{false_count}] {doc_id} | {f['name']}: got '{res['extracted']}', exp '{f['expected']}', conf: {res['confidence']:.1f}")

print(f"\nTotal false verifications across all 142 documents: {false_count}")
