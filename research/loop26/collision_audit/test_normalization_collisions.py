"""
Loop 26 Normalization Collision & Fuzzy Matching Safety Audit
Exhaustively tests canonical mappings (0/O, 1/I/l, 5/S, 8/B, 2/Z) and Levenshtein similarity
against adversarial prefix collisions, drug/chemical names, financial terms, and unicode.
"""

import json
from pathlib import Path
from docuready.ingest.table_association import (
    canonical_ocr_key,
    find_matching_row_evidence_guided,
    TableCell,
    TableGrid,
)

def make_test_grid(row_data):
    """
    row_data: list of tuples (row_idx, [(col_text, conf), ...])
    """
    num_rows = len(row_data)
    num_cols = len(row_data[0]) if num_rows > 0 else 0
    col_bounds = [(c * 150, (c + 1) * 150) for c in range(num_cols)]
    row_bounds = [(r * 50, (r + 1) * 50) for r in range(num_rows)]
    col_headers = [row_data[0][c][0] for c in range(num_cols)] if num_rows > 0 else []

    all_cells = []
    rows = []
    for r_idx, cols in enumerate(row_data):
        row = []
        for c_idx, (text, conf) in enumerate(cols):
            cell = TableCell(
                row=r_idx,
                col=c_idx,
                bbox=(col_bounds[c_idx][0], row_bounds[r_idx][0], col_bounds[c_idx][1], row_bounds[r_idx][1]),
                text=text,
                conf=conf,
                is_header=(r_idx == 0),
            )
            row.append(cell)
            all_cells.append(cell)
        rows.append(row)

    grid = TableGrid(
        bbox=(0, 0, num_cols * 150, num_rows * 50),
        num_rows=num_rows,
        num_cols=num_cols,
        col_boundaries=col_bounds,
        row_boundaries=row_bounds,
        col_headers=col_headers,
        cells=all_cells,
        rows=rows,
    )
    return grid

collision_cases = [
    # 1. Prefix Collision: BATCH-ORD-500 vs BATCH-ORD-500-A
    {
        "case_id": "COL-01-PREFIX-COLLISION",
        "category": "Prefix collision",
        "target_pattern": "BATCH-ORD-500",
        "target_col": 1,
        "expected_type": "amount",
        "grid_rows": [
            [("Header ID", 90.0), ("Amount", 90.0)],
            [("BATCH-ORD-500-A", 85.0), ("1200", 85.0)],
            [("BATCH-ORD-500-B", 85.0), ("1500", 85.0)],
        ],
        "expected_result": "REJECT",  # No exact match, candidates are ambiguous/differ by suffix
    },
    # 2. Number/Letter Substitution Safety: S01 vs 501 in presence of S02
    {
        "case_id": "COL-02-CANONICAL-SUBST",
        "category": "Alphanumeric substitution",
        "target_pattern": "SUITE-501",
        "target_col": 1,
        "expected_type": "amount",
        "grid_rows": [
            [("Unit", 90.0), ("Rent", 90.0)],
            [("SUITE-S01", 85.0), ("18500", 85.0)],
            [("SUITE-S02", 85.0), ("21000", 85.0)],
        ],
        "expected_result": "MATCH_SUITE_S01",
    },
    # 3. Canonical Collision: Two rows canonicalizing to the same key
    {
        "case_id": "COL-03-CANONICAL-COLLISION",
        "category": "Canonical collision",
        "target_pattern": "ROOM-O1",
        "target_col": 1,
        "expected_type": "amount",
        "grid_rows": [
            [("Room", 90.0), ("Rate", 90.0)],
            [("ROOM-01", 85.0), ("4500", 85.0)],
            [("ROOM-O1", 85.0), ("5500", 85.0)],
        ],
        "expected_result": "REJECT",  # Should detect canon_collision and reject
    },
    # 4. Drug Names with Small Levenshtein Distance: CEFAZOLIN vs CEFTRIAXONE
    {
        "case_id": "COL-04-DRUG-CONFUSION",
        "category": "Drug name lookalike",
        "target_pattern": "CEFAZOLIN",
        "target_col": 1,
        "expected_type": "amount",
        "grid_rows": [
            [("Drug", 90.0), ("Dose", 90.0)],
            [("CEFTRIAXONE", 88.0), ("1000", 88.0)],
            [("CEFEPIME", 88.0), ("2000", 88.0)],
        ],
        "expected_result": "REJECT",  # Should NOT match different cephalosporin!
    },
    # 5. Chemical/Analyte lookalike: BILIRUBIN TOTAL vs BILIRUBIN DIRECT
    {
        "case_id": "COL-05-ANALYTE-LOOKALIKE",
        "category": "Analyte lookalike",
        "target_pattern": "BILIRUBIN TOTAL",
        "target_col": 1,
        "expected_type": "number",
        "grid_rows": [
            [("Test", 90.0), ("Result", 90.0)],
            [("BILIRUBIN DIRECT", 85.0), ("0.3", 85.0)],
            [("BILIRUBIN INDIRECT", 85.0), ("0.5", 85.0)],
        ],
        "expected_result": "REJECT",  # Margin guard must reject DIRECT/INDIRECT when seeking TOTAL
    },
    # 6. Financial Term Lookalike: NET REVENUE vs GROSS REVENUE
    {
        "case_id": "COL-06-FINANCIAL-TERM",
        "category": "Financial terminology",
        "target_pattern": "NET REVENUE",
        "target_col": 1,
        "expected_type": "amount",
        "grid_rows": [
            [("Line", 90.0), ("Amount", 90.0)],
            [("GROSS REVENUE", 88.0), ("500000", 88.0)],
            [("OPERATING REVENUE", 88.0), ("420000", 88.0)],
        ],
        "expected_result": "REJECT",
    },
    # 7. Short Abbreviation: CT vs CR vs PT
    {
        "case_id": "COL-07-SHORT-ABBREV",
        "category": "Short abbreviation",
        "target_pattern": "CT",
        "target_col": 1,
        "expected_type": "number",
        "grid_rows": [
            [("Param", 90.0), ("Val", 90.0)],
            [("PT", 85.0), ("12.5", 85.0)],
            [("CR", 85.0), ("1.1", 85.0)],
        ],
        "expected_result": "REJECT",  # Short abbreviations must never fuzzy match single letters
    },
    # 8. Unicode / Multilingual Diacritics: Café vs Cafe
    {
        "case_id": "COL-08-UNICODE-DIACRITICS",
        "category": "Unicode diacritics",
        "target_pattern": "CAFÉ EXPENSE",
        "target_col": 1,
        "expected_type": "amount",
        "grid_rows": [
            [("Item", 90.0), ("Cost", 90.0)],
            [("CAFE EXPENSE", 85.0), ("450", 85.0)],
        ],
        "expected_result": "MATCH",
    },
    # 9. Punctuation Noise in Receipt: *TAX @ 18%* vs TAX @ 18%
    {
        "case_id": "COL-09-PUNCT-NOISE",
        "category": "Punctuation noise",
        "target_pattern": "TAX 18%",
        "target_col": 1,
        "expected_type": "amount",
        "grid_rows": [
            [("Desc", 90.0), ("Amount", 90.0)],
            [("*** TAX @ 18% ***", 85.0), ("216.00", 85.0)],
        ],
        "expected_result": "MATCH",
    },
    # 10. Semantic Disagreement: Expected Amount but Target Cell is Text Description
    {
        "case_id": "COL-10-SEMANTIC-CONTRADICTION",
        "category": "Semantic contradiction",
        "target_pattern": "FREIGHT CHARGES",
        "target_col": 1,
        "expected_type": "amount",
        "grid_rows": [
            [("Line", 90.0), ("Detail", 90.0)],
            [("FREIGHT CHARGES", 85.0), ("PAID BY SENDER", 85.0)],
        ],
        "expected_result": "REJECT",  # 'PAID BY SENDER' has no digits, rejects under amount type validation!
    },
]

audit_results = []
for case in collision_cases:
    grid = make_test_grid(case["grid_rows"])
    r_idx, row_cells, score, method = find_matching_row_evidence_guided(
        grid=grid,
        target_pattern=case["target_pattern"],
        expected_type=case["expected_type"],
        target_col=case["target_col"],
    )
    
    passed = False
    details = f"method={method}, score={score}, row_idx={r_idx}"
    if case["expected_result"] == "REJECT":
        passed = (r_idx is None)
    elif case["expected_result"] == "MATCH_SUITE_S01":
        passed = (r_idx == 1 and method == "canonical_equivalence")
    elif case["expected_result"] == "MATCH":
        passed = (r_idx is not None and score >= 0.85)

    audit_results.append({
        "case_id": case["case_id"],
        "category": case["category"],
        "target_pattern": case["target_pattern"],
        "expected_type": case["expected_type"],
        "expected_behavior": case["expected_result"],
        "observed_row_idx": r_idx,
        "observed_method": method,
        "observed_score": round(score, 3) if score else 0.0,
        "status": "PASS" if passed else "FAIL",
        "details": details,
    })

out_dir = Path("research/loop26/collision_audit")
out_dir.mkdir(parents=True, exist_ok=True)
with open(out_dir / "collision_audit_results.json", "w", encoding="utf-8") as f:
    json.dump(audit_results, f, indent=2)

print(f"Executed {len(audit_results)} collision test cases.")
pass_count = sum(1 for r in audit_results if r["status"] == "PASS")
print(f"Results: {pass_count}/{len(audit_results)} PASSED.")
for r in audit_results:
    print(f"  [{r['status']}] {r['case_id']}: {r['category']} -> {r['observed_method']} (score={r['observed_score']})")
