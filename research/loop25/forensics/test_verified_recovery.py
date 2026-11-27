"""
Rigorous Evaluation of Evidence-Guided Row-Label Recovery with Full Verification Pipeline
Applies:
  - Canonical OCR equivalence + Levenshtein margin guard
  - Decimal point morphology on candidate crops
  - Syntax noise & stray punctuation stripping
  - Calibrated confidence threshold T=70.0
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
    refine_cell_decimal_point,
    resolve_narrow_gutter_cell_token,
)

ROOT = Path(__file__).resolve().parents[3]
L24_MANIFEST = ROOT / "research" / "loop24" / "dataset_manifest.json"


def canonical_ocr_key(s: str) -> str:
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
    matching_rows = []
    for r_idx, row in enumerate(grid.rows):
        row_text = " ".join(c.text for c in row).upper()
        if norm_pattern in row_text:
            matching_rows.append((r_idx, row))

    if len(matching_rows) == 1:
        return matching_rows[0][0], matching_rows[0][1], 1.0, "exact_match"
    elif len(matching_rows) > 1:
        # Candidate ambiguity
        return None, None, 0.0, "collision_ambiguity"

    # 2. Canonical OCR Equivalence match
    candidates_canon = []
    for r_idx, row in enumerate(grid.rows):
        if r_idx == 0 and len(grid.rows) > 1:
            continue
        row_canon = canonical_ocr_key(" ".join(c.text for c in row))
        if canon_pattern and (canon_pattern in row_canon or (len(canon_pattern) >= 4 and row_canon in canon_pattern)):
            if target_col < len(row):
                cell_val = row[target_col].text.strip()
                if expected_type in ["amount", "count", "weight", "number", "percentage"]:
                    if any(c.isdigit() for c in cell_val):
                        candidates_canon.append((r_idx, row))
                else:
                    candidates_canon.append((r_idx, row))

    if len(candidates_canon) == 1:
        return candidates_canon[0][0], candidates_canon[0][1], 0.95, "canonical_equivalence"
    elif len(candidates_canon) > 1:
        return None, None, 0.0, "canon_collision"

    # 3. High-Confidence Levenshtein Similarity with Strict Margin Guard
    best_ratio = 0.0
    second_best = 0.0
    best_row_info = None

    for r_idx, row in enumerate(grid.rows):
        if r_idx == 0 and len(grid.rows) > 1:
            continue
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

    # Strict Safety margin: best_ratio >= 0.85 and (best_ratio - second_best) >= 0.15
    if best_ratio >= 0.85 and (best_ratio - second_best) >= 0.15 and best_row_info is not None:
        r_idx, row = best_row_info
        if target_col < len(row):
            cell_val = row[target_col].text.strip()
            if expected_type in ["amount", "count", "weight", "number", "percentage"]:
                if any(c.isdigit() for c in cell_val):
                    return r_idx, row, best_ratio, "levenshtein_similarity"
            else:
                return r_idx, row, best_ratio, "levenshtein_similarity"

    return None, None, 0.0, None


def test_verified_recovery():
    tess_path = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")
    if tess_path.exists():
        pytesseract.pytesseract.tesseract_cmd = str(tess_path)

    with open(L24_MANIFEST, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Filter to Cohort I documents
    cohort_i = {k: v for k, v in manifest.items() if v["cohort"].startswith("I_")}

    baseline_verified = 19
    baseline_exact = 19
    baseline_fv = 0

    new_verified = 0
    new_exact = 0
    new_fv = 0
    new_abstentions = 0

    conf_threshold = 70.0

    for doc_id, meta in cohort_i.items():
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
            col_pat = f.get("col_pattern")

            # Resolve target column
            target_col = -1
            if exp_col is not None and 0 <= exp_col < grid.num_cols:
                target_col = exp_col
            elif col_pat:
                for c_i, h in enumerate(grid.col_headers):
                    if col_pat.upper() in h.upper():
                        target_col = c_i
                        break
            if target_col == -1:
                new_abstentions += 1
                continue

            r_idx, row, score, method = find_matching_row_evidence_guided(grid, f["target_pattern"], exp_type, target_col)
            if r_idx is None or row is None:
                new_abstentions += 1
                continue

            cell = row[target_col]
            clean_val = cell.text.strip()
            # Clean stray quote/currency
            clean_val = re.sub(r"^[‘'\"Rs\.INR₹\s]+", "", clean_val).strip()

            # Refine decimal point on crop
            if (
                clean_val
                and any(c.isdigit() for c in clean_val)
                and (("." not in clean_val and len(re.sub(r"[^\d]", "", clean_val)) >= 2) or ("8" in clean_val))
            ):
                bx1, by1, bx2, by2 = cell.bbox
                if bx2 > bx1 and by2 > by1:
                    pad = 5
                    crop = img.crop((max(0, bx1 - pad), max(0, by1 - pad), min(img.width, bx2 + pad), min(img.height, by2 + pad)))
                    clean_val = refine_cell_decimal_point(clean_val, crop)

            # Cell confidence penalized by label similarity
            cell_conf = cell.conf * score

            # Threshold & ambiguity gating:
            # Exact and canonical equivalence use calibrated T=70.0;
            # Fuzzy Levenshtein matches enforce safety floor T=75.0 to suppress corrupted cells
            effective_floor = 75.0 if method == "levenshtein_similarity" else conf_threshold
            if cell_conf < effective_floor or cell.is_ambiguous:
                new_abstentions += 1
                continue

            # Verified claim
            new_verified += 1
            norm_val = clean_val.replace("₹", "").replace("Rs.", "").replace(",", "").replace("$", "").strip()
            norm_exp = expected.replace("₹", "").replace("Rs.", "").replace(",", "").replace("$", "").strip()
            is_exact = (norm_val == norm_exp and (exp_row is None or r_idx == exp_row or r_idx == exp_row + 1))

            if is_exact:
                new_exact += 1
                if method != "exact_match":
                    print(f"[RECOVERED VERIFIED EXACT] {doc_id} | {fname}: '{clean_val}' == '{expected}' via {method} (conf={cell_conf:.1f})")
            else:
                new_fv += 1
                print(f"[FALSE VERIFICATION ALERT] {doc_id} | {fname}: got '{clean_val}', exp '{expected}' via {method} (conf={cell_conf:.1f})")

    print("\n" + "=" * 60)
    print(f"BASELINE COHORT I: Verified={baseline_verified}, Exact={baseline_exact}, FV={baseline_fv}")
    print(f"RECOVERED COHORT I: Verified={new_verified}, Exact={new_exact}, FV={new_fv}, Abstentions={new_abstentions}")
    prec = (new_exact / new_verified * 100.0) if new_verified > 0 else 100.0
    cov = (new_verified / (new_verified + new_abstentions) * 100.0)
    print(f"PRECISION: {prec:.2f}% | COVERAGE: {cov:.2f}%")
    print("=" * 60)


if __name__ == "__main__":
    test_verified_recovery()
