import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import json
from PIL import Image
import pytesseract
from docuready.ingest.table_association import build_table_grid
from research.loop25.benchmark.calibrate_thresholds import evaluate_field, configure_pytesseract

configure_pytesseract()
manifest = json.load(open('research/loop25/dataset_manifest.json'))
eval_docs = [dict(v, id=k, fields=v['critical_fields']) for k, v in manifest.items() if v['cohort'] in ['J_development', 'J_calibration']]

print("Inspecting Dev and Cal false verifications at T=70.0:")
for doc in eval_docs:
    img = Image.open(doc['image_path'])
    ocr_data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    grid = build_table_grid(ocr_data, page_width=img.width, page_height=img.height, image=img)
    for field in doc['fields']:
        res = evaluate_field(grid, field, doc['id'], img, conf_threshold=70.0)
        if res['is_verified'] and not res['is_exact']:
            print(f"{doc['id']} | {field['name']}: got '{res['extracted']}', expected '{res['expected']}', conf: {res['confidence']:.1f}")
