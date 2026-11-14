"""
Field-Level Extraction Evaluation Script for Realistic Document Corpus (60 Samples)
Measures exact-match, normalized-match, precision, recall, and abstention across degradation categories.
"""

import os
import json
import time
from collections import defaultdict
from typing import Dict, Any

from docuready.domain.models import DocumentType, ExtractionMethod
from docuready.ingest.extractor import DocumentExtractor
from docuready.normalize.normalizer import normalize_name, normalize_income, normalize_cert_number


def run_evaluation(manifest_path: str = "synthetic_data/REALISTIC_CORPUS_MANIFEST.json"):
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    samples = manifest_data.get("samples", {})
    if isinstance(samples, list):
        samples_dict = {s["sample_id"]: s for s in samples}
    else:
        samples_dict = samples

    extractor = DocumentExtractor(dpi=200, low_conf_threshold=0.60)
    corpus_dir = "synthetic_data/realistic_corpus_60"

    # Metrics storage
    category_metrics = defaultdict(lambda: {
        "total_samples": 0,
        "total_expected_fields": 0,
        "extracted_fields": 0,
        "correct_exact": 0,
        "correct_normalized": 0,
        "incorrect": 0,
        "missing": 0,
        "abstained": 0,
        "native_vector_count": 0,
        "local_ocr_count": 0,
        "latencies_ms": []
    })

    field_type_metrics = defaultdict(lambda: {
        "expected": 0,
        "extracted": 0,
        "correct_exact": 0,
        "correct_normalized": 0,
        "incorrect": 0,
        "missing": 0,
        "abstained": 0
    })

    total_eval_samples = len(samples_dict)
    detailed_results = []

    for sample_id, meta in sorted(samples_dict.items()):
        file_name = meta["file_name"]
        file_path = os.path.join(corpus_dir, file_name)
        doc_type_str = meta["document_type"]
        doc_type = DocumentType[doc_type_str] if doc_type_str in DocumentType.__members__ else DocumentType.APPLICATION_FORM
        degradation = meta.get("degradation_applied", "Clean")
        expected_fields = meta.get("expected_fields", {})
        expected_audit_status = meta.get("expected_audit_status", "PASS")

        # Map degradation to category
        if "Clean" in degradation:
            category = "Native PDF Vector"
        elif "Raster" in degradation or "Clean 200 DPI" in degradation:
            category = "Clean Scanned PDF (Raster)"
        elif "Rotated" in degradation:
            category = "Rotated Scan"
        elif "Low Resolution" in degradation or "70 DPI" in degradation:
            category = "Low-DPI Scan (70 DPI)"
        elif "Perspective" in degradation or "Keystone" in degradation:
            category = "Mobile Perspective Distortion"
        elif "Shadow" in degradation:
            category = "Uneven Lighting & Shadows"
        elif "JPEG" in degradation:
            category = "Compression Artifacts"
        elif "Seal" in degradation or "Stamp" in degradation:
            category = "Overlapping Seals & Stamps"
        elif "Handwritten" in degradation:
            category = "Handwritten Annotations"
        elif "Multi-page" in degradation:
            category = "Multi-Page Layout"
        elif "Blank" in degradation:
            category = "Blank Document"
        elif "Corrupted" in degradation:
            category = "Corrupted Document"
        else:
            category = "Other"

        cat = category_metrics[category]
        cat["total_samples"] += 1

        t0 = time.perf_counter()
        # In real-world processing, extractor auto-detects the document type from content
        extracted_doc = extractor.extract_document(file_path, expected_type=None)
        t_elap_ms = (time.perf_counter() - t0) * 1000.0
        cat["latencies_ms"].append(t_elap_ms)

        if extracted_doc.extraction_method == ExtractionMethod.NATIVE_VECTOR.value:
            cat["native_vector_count"] += 1
        elif extracted_doc.extraction_method == ExtractionMethod.LOCAL_OCR.value:
            cat["local_ocr_count"] += 1

        # Check document level status
        sample_res = {
            "sample_id": sample_id,
            "category": category,
            "file_name": file_name,
            "extraction_method": extracted_doc.extraction_method,
            "status": extracted_doc.status,
            "mean_ocr_confidence": extracted_doc.mean_ocr_confidence,
            "latency_ms": round(t_elap_ms, 2),
            "fields": {}
        }

        if extracted_doc.status in ["UNREADABLE", "CORRUPTED"]:
            # Document abstained / unreadable
            for f_name, exp_val in expected_fields.items():
                cat["total_expected_fields"] += 1
                cat["abstained"] += 1
                field_type_metrics[f_name]["expected"] += 1
                field_type_metrics[f_name]["abstained"] += 1
            detailed_results.append(sample_res)
            continue

        for f_name, exp_val in expected_fields.items():
            cat["total_expected_fields"] += 1
            field_type_metrics[f_name]["expected"] += 1

            act_f = extracted_doc.fields.get(f_name)
            if not act_f or not act_f.raw_value:
                cat["missing"] += 1
                field_type_metrics[f_name]["missing"] += 1
                sample_res["fields"][f_name] = {"status": "MISSING", "expected": str(exp_val), "actual": None}
                continue

            cat["extracted_fields"] += 1
            field_type_metrics[f_name]["extracted"] += 1

            raw_str = str(act_f.raw_value).strip()
            exp_str = str(exp_val).strip()

            # Exact match check
            exact_match = (raw_str.upper() == exp_str.upper())

            # Normalized match check
            norm_match = False
            if exact_match:
                norm_match = True
            elif f_name == "applicant_name":
                norm_match = (normalize_name(raw_str) == normalize_name(exp_str))
            elif f_name == "annual_income":
                norm_match = (normalize_income(raw_str) == normalize_income(exp_str))
            elif "cert_no" in f_name or "certificate_no" in f_name:
                norm_match = (normalize_cert_number(raw_str) == normalize_cert_number(exp_str))
            elif act_f.normalized_value is not None:
                norm_match = (str(act_f.normalized_value).upper() == exp_str.upper())

            if exact_match:
                cat["correct_exact"] += 1
                field_type_metrics[f_name]["correct_exact"] += 1
            if norm_match:
                cat["correct_normalized"] += 1
                field_type_metrics[f_name]["correct_normalized"] += 1
            else:
                cat["incorrect"] += 1
                field_type_metrics[f_name]["incorrect"] += 1

            sample_res["fields"][f_name] = {
                "status": "EXACT" if exact_match else ("NORMALIZED" if norm_match else "INCORRECT"),
                "expected": exp_str,
                "actual": raw_str,
                "normalized": str(act_f.normalized_value),
                "is_uncertain": act_f.is_uncertain,
                "ocr_conf": act_f.provenance.ocr_confidence if act_f.provenance else None
            }

        detailed_results.append(sample_res)

    # Print Summary Tables
    print("=" * 95)
    print("DOCUREADY - REALISTIC CORPUS EXTRACTION BENCHMARK (60 SAMPLES)")
    print("=" * 95)
    print(f"{'Degradation Category':32s} | {'Samples':7s} | {'Method':12s} | {'Fields':6s} | {'Exact%':6s} | {'Norm%':6s} | {'Abst%':6s} | {'Lat(ms)':7s}")
    print("-" * 95)

    tot_samples = 0
    tot_fields = 0
    tot_exact = 0
    tot_norm = 0
    tot_abstained = 0
    all_latencies = []

    for cat_name, m in sorted(category_metrics.items()):
        samples_n = m["total_samples"]
        fields_n = m["total_expected_fields"]
        exact_pct = (m["correct_exact"] / fields_n * 100.0) if fields_n else 0.0
        norm_pct = (m["correct_normalized"] / fields_n * 100.0) if fields_n else 0.0
        abst_pct = (m["abstained"] / fields_n * 100.0) if fields_n else 0.0
        mean_lat = sum(m["latencies_ms"]) / len(m["latencies_ms"]) if m["latencies_ms"] else 0.0

        method_str = f"Vec:{m['native_vector_count']} OCR:{m['local_ocr_count']}"

        tot_samples += samples_n
        tot_fields += fields_n
        tot_exact += m["correct_exact"]
        tot_norm += m["correct_normalized"]
        tot_abstained += m["abstained"]
        all_latencies.extend(m["latencies_ms"])

        print(f"{cat_name:32s} | {samples_n:7d} | {method_str:12s} | {fields_n:6d} | {exact_pct:5.1f}% | {norm_pct:5.1f}% | {abst_pct:5.1f}% | {mean_lat:7.1f}")

    overall_exact = (tot_exact / tot_fields * 100.0) if tot_fields else 0.0
    overall_norm = (tot_norm / tot_fields * 100.0) if tot_fields else 0.0
    overall_abst = (tot_abstained / tot_fields * 100.0) if tot_fields else 0.0
    overall_lat = sum(all_latencies) / len(all_latencies) if all_latencies else 0.0

    print("-" * 95)
    print(f"{'OVERALL TOTALS':32s} | {tot_samples:7d} | {'ALL':12s} | {tot_fields:6d} | {overall_exact:5.1f}% | {overall_norm:5.1f}% | {overall_abst:5.1f}% | {overall_lat:7.1f}")
    print("=" * 95)

    print("\nFIELD TYPE BREAKDOWN:")
    print(f"{'Field Name':25s} | {'Expected':8s} | {'Extracted':9s} | {'Exact Match%':12s} | {'Norm Match%':11s} | {'Precision':9s} | {'Recall':8s}")
    print("-" * 95)
    for f_name, fm in sorted(field_type_metrics.items()):
        exp = fm["expected"]
        ext = fm["extracted"]
        exact_pct = (fm["correct_exact"] / exp * 100.0) if exp else 0.0
        norm_pct = (fm["correct_normalized"] / exp * 100.0) if exp else 0.0
        precision = (fm["correct_normalized"] / ext * 100.0) if ext else 0.0
        recall = (fm["correct_normalized"] / exp * 100.0) if exp else 0.0
        print(f"{f_name:25s} | {exp:8d} | {ext:9d} | {exact_pct:11.1f}% | {norm_pct:10.1f}% | {precision:8.1f}% | {recall:7.1f}%")
    print("=" * 95)

    # Save evaluation report JSON
    eval_summary = {
        "overall": {
            "total_samples": tot_samples,
            "total_expected_fields": tot_fields,
            "exact_match_pct": round(overall_exact, 2),
            "normalized_match_pct": round(overall_norm, 2),
            "abstention_rate_pct": round(overall_abst, 2),
            "mean_latency_ms": round(overall_lat, 2)
        },
        "by_category": {cat: {k: v for k, v in m.items() if k != "latencies_ms"} for cat, m in category_metrics.items()},
        "by_field_type": dict(field_type_metrics),
        "detailed_results": detailed_results
    }
    with open("EXTRACTION_EVALUATION_DATA.json", "w", encoding="utf-8") as f_out:
        json.dump(eval_summary, f_out, indent=2)
    print("\nWrote evaluation summary to EXTRACTION_EVALUATION_DATA.json")


if __name__ == "__main__":
    run_evaluation()
