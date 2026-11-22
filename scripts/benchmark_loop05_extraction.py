"""
Loop 05 Benchmark: Field Extraction, Normalization & Cross-Document Intelligence.
Evaluates the 12 controlled extraction fixtures and cross-document comparison intelligence.
Outputs JSON and Markdown reports to docs/04-VALIDATION/
"""

import json
import time
from pathlib import Path
from datetime import date
from typing import Dict, Any, List

from docuready.ingest.extractor import DocumentExtractor
from docuready.domain.models import DocumentType, ExtractionMethod
from docuready.domain.enums import MatchGrade
from docuready.normalize.normalizer import (
    normalize_name, normalize_income, parse_and_normalize_date,
    normalize_cert_number, compare_names, compare_dates
)

CORPUS_DIR = Path("synthetic_data/loop05_extraction_corpus")
OUTPUT_JSON = Path("docs/04-VALIDATION/LOOP_05_EXTRACTION_BENCHMARK_RESULTS.json")
OUTPUT_MD = Path("docs/04-VALIDATION/LOOP_05_EXTRACTION_BENCHMARK_RESULTS.md")


def run_benchmark():
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    manifest_path = CORPUS_DIR / "LOOP05_CORPUS_MANIFEST.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    extractor = DocumentExtractor()
    fixture_results = []
    total_passed = 0

    print("Evaluating 12 Loop 05 Controlled Extraction Fixtures...")

    for pdf_name, fix in manifest.items():
        fid = fix.get("id", pdf_name)
        pdf_path = CORPUS_DIR / pdf_name
        doc_type = DocumentType(fix["doc_type"])
        expected_fields = fix["expected_fields"]

        t0 = time.perf_counter()
        doc = extractor.extract_document(str(pdf_path), expected_type=doc_type)
        elapsed_ms = round((time.perf_counter() - t0) * 1000.0, 2)

        failures = []
        extracted_summary = {}

        for fname, exp_val in expected_fields.items():
            if fname not in doc.fields:
                failures.append(f"Field '{fname}' not extracted")
                continue

            field_obj = doc.fields[fname]
            norm_val = field_obj.normalized_value
            extracted_summary[fname] = {
                "raw_value": field_obj.raw_value,
                "normalized_value": norm_val,
                "confidence": field_obj.confidence,
                "is_uncertain": field_obj.is_uncertain,
                "uncertainty_reason": field_obj.uncertainty_reason,
            }

            if fix.get("expect_uncertain") and fname == "annual_income":
                if not field_obj.is_uncertain:
                    failures.append(f"Field '{fname}' expected to be uncertain but is_uncertain=False")

            if exp_val is not None and not fix.get("expect_uncertain"):
                # Value verification
                if isinstance(exp_val, float):
                    if norm_val != exp_val:
                        failures.append(f"Field '{fname}': expected {exp_val}, got {norm_val}")
                elif isinstance(exp_val, str):
                    if str(norm_val) != exp_val:
                        failures.append(f"Field '{fname}': expected '{exp_val}', got '{norm_val}'")

        is_success = (len(failures) == 0)
        if is_success:
            total_passed += 1

        fixture_results.append({
            "id": fid,
            "pdf_name": pdf_name,
            "category": fix["category"],
            "doc_type": fix["doc_type"],
            "extraction_method": doc.extraction_method,
            "elapsed_ms": elapsed_ms,
            "success": is_success,
            "failures": failures,
            "extracted_fields": extracted_summary,
        })
        desc = fix.get("description", fix.get("category", pdf_name))
        status_str = "PASS" if is_success else f"FAIL ({', '.join(failures)})"
        print(f"  [{status_str}] {fid}: {desc}")

    # Cross-Document Name Matching Matrix
    print("\nEvaluating Cross-Document Name Intelligence Matrix...")
    name_pairs = [
        ("EXACT", "Smruti Ranjan Nayak", "Smruti Ranjan Nayak", MatchGrade.EXACT, "EXACT_MATCH"),
        ("SIBLING_RHYME_1", "Ramesh Nayak", "Suresh Nayak", MatchGrade.CONFLICT, "DISTINCT_GIVEN_NAMES"),
        ("SIBLING_RHYME_2", "Anita Das", "Sunita Das", MatchGrade.CONFLICT, "DISTINCT_GIVEN_NAMES"),
        ("MIDDLE_OMITTED", "Smruti Nayak", "Smruti Ranjan Nayak", MatchGrade.COMPATIBLE, "MIDDLE_NAME_VARIATION"),
        ("INITIALS_EXP", "S R Nayak", "Smruti Ranjan Nayak", MatchGrade.COMPATIBLE, "INITIALS_EXPANSION"),
        ("TOKEN_ORDER", "Nayak Smruti Ranjan", "Smruti Ranjan Nayak", MatchGrade.COMPATIBLE, "TOKEN_PERMUTATION"),
        ("TRANSLIT_MINOR", "Smruti Nayak", "Smruti Naik", MatchGrade.COMPATIBLE, "MINOR_TYPO_TRANSLITERATION"),
        ("SINGLE_TOKEN", "Smruti", "Smruti Ranjan Nayak", MatchGrade.AMBIGUOUS, "SINGLE_TOKEN_NAME"),
        ("DISTINCT_INDIVIDUAL", "Smruti Ranjan Nayak", "Rajesh Patel", MatchGrade.CONFLICT, "CONTRADICTORY_NAME"),
    ]

    name_matrix_results = []
    name_matrix_passed = 0

    for test_id, n1, n2, exp_grade, exp_type in name_pairs:
        res = compare_names(n1, n2)
        actual_grade = res["match_grade"]
        actual_type = res["type"]
        passed = (actual_grade == exp_grade and actual_type == exp_type)
        if passed:
            name_matrix_passed += 1
        name_matrix_results.append({
            "test_id": test_id,
            "name_1": n1,
            "name_2": n2,
            "expected_grade": exp_grade.value,
            "actual_grade": actual_grade.value,
            "expected_type": exp_type,
            "actual_type": actual_type,
            "similarity": res.get("similarity", 0.0),
            "passed": passed,
        })
        p_str = "PASS" if passed else f"FAIL (got {actual_grade.value}:{actual_type})"
        print(f"  [{p_str}] {test_id}: '{n1}' vs '{n2}' -> {actual_grade.value} ({actual_type})")

    # Date Normalization Matrix
    print("\nEvaluating Date Normalization Matrix...")
    date_cases = [
        ("Slash Unambiguous DD/MM/YYYY", "25/01/2025", "2025-01-25", False),
        ("Dot Unambiguous DD.MM.YYYY", "25.01.2025", "2025-01-25", False),
        ("Dash Unambiguous DD-MM-YYYY", "25-01-2025", "2025-01-25", False),
        ("Named Month DD Mon YYYY", "10 Jan 2025", "2025-01-10", False),
        ("Ambiguous Slash DD/MM vs MM/DD", "10/01/2025", "2025-01-10", True),
        ("Ambiguous Dot DD.MM vs MM.DD", "05.06.2025", "2025-06-05", True),
    ]

    date_results = []
    date_passed = 0
    for label, raw_dt, exp_iso, exp_amb in date_cases:
        d_obj, st, amb = parse_and_normalize_date(raw_dt)
        actual_iso = d_obj.isoformat() if d_obj else None
        p = (st == "VALID" and actual_iso == exp_iso and amb == exp_amb)
        if p:
            date_passed += 1
        date_results.append({
            "label": label,
            "raw_input": raw_dt,
            "expected_iso": exp_iso,
            "actual_iso": actual_iso,
            "expected_ambiguous": exp_amb,
            "actual_ambiguous": amb,
            "passed": p,
        })
        p_str = "PASS" if p else "FAIL"
        print(f"  [{p_str}] {label}: '{raw_dt}' -> {actual_iso} (ambiguous={amb})")

    summary = {
        "benchmark_timestamp": date.today().isoformat(),
        "total_fixtures": len(manifest),
        "fixtures_passed": total_passed,
        "fixture_pass_rate_pct": round(total_passed / len(manifest) * 100.0, 1),
        "name_matrix_cases": len(name_pairs),
        "name_matrix_passed": name_matrix_passed,
        "name_matrix_pass_rate_pct": round(name_matrix_passed / len(name_pairs) * 100.0, 1),
        "date_cases": len(date_cases),
        "date_passed": date_passed,
        "date_pass_rate_pct": round(date_passed / len(date_cases) * 100.0, 1),
        "fixture_details": fixture_results,
        "name_intelligence_matrix": name_matrix_results,
        "date_normalization_details": date_results,
    }

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    # Generate Markdown Report
    md_lines = [
        "# DocuReady Loop 05 Extraction, Normalization & Cross-Document Intelligence Benchmark",
        "",
        f"**Date:** {summary['benchmark_timestamp']}  ",
        f"**Corpus Fixtures:** {summary['fixtures_passed']} / {summary['total_fixtures']} ({summary['fixture_pass_rate_pct']}%)  ",
        f"**Name Matching Intelligence:** {summary['name_matrix_passed']} / {summary['name_matrix_cases']} ({summary['name_matrix_pass_rate_pct']}%)  ",
        f"**Date Normalization Accuracy:** {summary['date_passed']} / {summary['date_cases']} ({summary['date_pass_rate_pct']}%)  ",
        "",
        "---",
        "",
        "## 1. Controlled Extraction Corpus Results (12 Fixtures)",
        "",
        "| ID | Category | Doc Type | Status | Extracted Fields | Timing (ms) |",
        "|---|---|---|:---:|---|:---:|",
    ]

    for fr in fixture_results:
        st_icon = "PASS" if fr["success"] else "FAIL"
        f_list = ", ".join(f"`{k}`" for k in fr["extracted_fields"].keys())
        md_lines.append(f"| {fr['id']} | {fr['category']} | {fr['doc_type']} | {st_icon} | {f_list} | {fr['elapsed_ms']} |")

    md_lines.extend([
        "",
        "## 2. Cross-Document Name Intelligence Matrix",
        "",
        "| Test Case | Name 1 | Name 2 | Expected Grade | Actual Grade | Type | Status |",
        "|---|---|---|---|---|---|:---:|",
    ])

    for nm in name_matrix_results:
        st_icon = "PASS" if nm["passed"] else "FAIL"
        md_lines.append(f"| {nm['test_id']} | {nm['name_1']} | {nm['name_2']} | {nm['expected_grade']} | {nm['actual_grade']} | `{nm['actual_type']}` | {st_icon} |")

    md_lines.extend([
        "",
        "## 3. Date Normalization Matrix",
        "",
        "| Format | Raw String | Normalized ISO | Ambiguous Flag | Status |",
        "|---|---|---|:---:|:---:|",
    ])

    for dt in date_results:
        st_icon = "PASS" if dt["passed"] else "FAIL"
        md_lines.append(f"| {dt['label']} | `{dt['raw_input']}` | `{dt['actual_iso']}` | `{dt['actual_ambiguous']}` | {st_icon} |")

    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print(f"\nBenchmark completed successfully! Reports written to:")
    print(f"  - {OUTPUT_JSON}")
    print(f"  - {OUTPUT_MD}")


if __name__ == "__main__":
    run_benchmark()
