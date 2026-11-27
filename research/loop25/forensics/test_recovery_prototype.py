"""
Test Prototype of Evidence-Guided Row-Label Recovery
Evaluates recovery on the 83 Cohort I abstentions to test safety and yield.
"""

import json
import re
import difflib
from pathlib import Path
from PIL import Image
import pytesseract

from docuready.ingest.table_association import (
    build_table_grid,
    normalize_token_text,
    extract_cell_by_intersection,
)

ROOT = Path(__file__).resolve().parents[3]
L24_MANIFEST = ROOT / "research" / "loop24" / "dataset_manifest.json"


def canonical_ocr_key(s: str) -> str:
    """Normalizes common OCR character confusions."""
    s = s.upper()
    s = re.sub(r"[^A-Z0-9]", "", s)
    trans = str.maketrans({
        "O": "0",
        "I": "1",
        "L": "1",
        "S": "5",
        "B": "8",
        "Z": "2",
    })
    return s.translate(trans)


def find_matching_row_evidence_guided(grid, target_pattern, expected_type, target_col):
    norm_pattern = normalize_token_text(target_pattern).upper()
    canon_pattern = canonical_ocr_key(target_pattern)

    # 1. Exact match
    for r_idx, row in enumerate(grid.rows):
        row_text = " ".join(c.text for c in row).upper()
        if norm_pattern in row_text:
            return r_idx, row, 1.0, "exact_match"

    # 2. Canonical OCR Equivalence match
    candidates_canon = []
    for r_idx, row in enumerate(grid.rows):
        row_canon = canonical_ocr_key(" ".join(c.text for c in row))
        if canon_pattern and (canon_pattern in row_canon or (len(canon_pattern) >= 4 and row_canon in canon_pattern)):
            # Check target cell validity
            if target_col < len(row):
                cell_val = row[target_col].text.strip()
                if expected_type in ["amount", "count", "weight", "number", "percentage"]:
                    if any(c.isdigit() for c in cell_val):
                        candidates_canon.append((r_idx, row))
                else:
                    candidates_canon.append((r_idx, row))

    if len(candidates_canon) == 1:
        return candidates_canon[0][0], candidates_canon[0][1], 0.95, "canonical_equivalence"

    # 3. High-Confidence Levenshtein Similarity with Margin Guard
    best_ratio = 0.0
    second_best = 0.0
    best_row_info = None

    for r_idx, row in enumerate(grid.rows):
        if r_idx == 0 and len(grid.rows) > 1:
            # Skip header row
            continue
        # Compare against first cell or row label
        label_text = normalize_token_text(row[0].text if row else "").upper()
        full_row_text = normalize_token_text(" ".join(c.text for c in row)).upper()

        r1 = difflib.SequenceMatcher(None, norm_pattern, label_text).ratio()
        r2 = difflib.SequenceMatcher(None, norm_pattern, full_row_text[:len(norm_pattern)+5]).ratio()
        r = max(r1, r2)

        if r > best_ratio:
            second_best = best_ratio
            best_ratio = r
            best_row_info = (r_idx, row)
        elif r > second_best:
            second_best = r

    # Safety margin: best_ratio >= 0.85 and margin >= 0.12 to prevent prefix collisions
    if best_ratio >= 0.85 and (best_ratio - second_best) >= 0.12 and best_row_info is not None:
        r_idx, row = best_row_info
        if target_col < len(row):
            cell_val = row[target_col].text.strip()
            if expected_type in ["amount", "count", "weight", "number", "percentage"]:
                if any(c.isdigit() for c in cell_val):
                    return r_idx, row, best_ratio, "levenshtein_similarity"
            else:
                return r_idx, row, best_ratio, "levenshtein_similarity"

    return None, None, 0.0, None


def test_prototype():
    tess_path = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
    if tess_path.exists():
        pytesseract.pytesseract.tesseract_cmd = str(tess_path)

    with open(L24_MANIFEST, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    recovered_count = 0
    correct_count = 0
    false_count = 0

    for doc_id, meta in manifest.items():
        img = Image.open(meta["image_path"])
        ocr_data = pytesseract.image_to_data(img, lang="eng", output_type=pytesseract.Output.DICT)
        grid = build_table_grid(ocr_data, img.width, img.height, image=img)

        for f in meta["critical_fields"]:
            fname = f["name"]
            expected = str(f["expected"]).strip()
            exp_row = f.get("row")
            exp_col = f.get("col")
            t_col = exp_col if exp_col is not None else 1
            exp_type = f.get("type", "text")

            r_idx, row, score, method = find_matching_row_evidence_guided(grid, f["target_pattern"], exp_type, t_col)
            if method in ["canonical_equivalence", "levenshtein_similarity"]:
                recovered_count += 1
                val = row[t_col].text.strip() if t_col < len(row) else ""
                val_norm = val.replace("₹", "").replace("Rs.", "").replace(",", "").replace("$", "").strip()
                exp_norm = expected.replace("₹", "").replace("Rs.", "").replace(",", "").replace("$", "").strip()
                is_exact = (val_norm == exp_norm and (exp_row is None or r_idx == exp_row or r_idx == exp_row + 1))
                if is_exact:
                    correct_count += 1
                    print(f"[RECOVERED EXACT] {doc_id} | {fname}: '{val}' == '{expected}' via {method} (score={score:.2f})")
                else:
                    false_count += 1
                    print(f"[RECOVERED MISMATCH] {doc_id} | {fname}: got '{val}', exp '{expected}' via {method}")

    print(f"\n--- Prototype Summary ---")
    print(f"Total Recovered: {recovered_count}")
    print(f"Exact Matches:   {correct_count}")
    print(f"False Matches:   {false_count}")


if __name__ == "__main__":
    test_prototype()
