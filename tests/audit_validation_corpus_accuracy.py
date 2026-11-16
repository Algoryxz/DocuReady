"""
Synthetic Validation Corpus Accuracy & Evidence Integrity Audit
Loop 4 Validation Task - DocuReady Desktop Application
"""

import json
import os
import shutil
import tempfile
from datetime import date
from pathlib import Path
from typing import Any, Dict, List

from docuready.domain.models import DocumentType
from docuready.ingest.extractor import DocumentExtractor
from docuready.pipeline import AuditPipeline


def run_accuracy_audit() -> Dict[str, Any]:
    corpus_dir = Path(__file__).resolve().parent / "validation_corpus"
    manifest_path = Path(__file__).resolve().parents[1] / "docs" / "validation_corpus_manifest.json"

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    extractor = DocumentExtractor()
    as_of = date(2026, 4, 15)

    results: Dict[str, Any] = {
        "summary": {},
        "documents": {},
        "workflows": {},
        "evidence_integrity": {
            "total_evidence_fields": 0,
            "valid_bounding_boxes": 0,
            "invalid_bounding_boxes": 0,
            "valid_page_indices": 0,
            "invalid_page_indices": 0,
            "unextracted_or_null_provenance": 0,
        },
        "confusion_matrix": {
            "true_positives": 0,    # Defect correctly detected
            "false_positives": 0,   # Non-defect incorrectly flagged
            "true_negatives": 0,    # Clean rule correctly passed
            "false_negatives": 0,   # Defect missed
        }
    }

    print("=== Step 1: Individual Document Extraction & Integrity Audit ===")
    for entry in manifest["documents"]:
        doc_id = entry["document_id"]
        file_name = entry["file_name"]
        file_path = corpus_dir / file_name

        print(f"Testing {doc_id} ({file_name})...")
        extracted = extractor.extract_document(str(file_path))

        doc_res: Dict[str, Any] = {
            "status": extracted.status,
            "expected_category": entry["category"],
            "expected_extraction": entry["expected_extraction"],
            "extraction_method": extracted.extraction_method,
            "doc_type": extracted.doc_type.value if extracted.doc_type else None,
            "field_count": len(extracted.fields),
            "mean_ocr_confidence": extracted.mean_ocr_confidence,
        }

        # Check evidence bounding boxes and provenance
        for fld_name, fld_val in extracted.fields.items():
            results["evidence_integrity"]["total_evidence_fields"] += 1
            prov = getattr(fld_val, "provenance", None)

            if prov is not None:
                page_no = getattr(prov, "page_number", None)
                bbox = getattr(prov, "bounding_box", None)

                if page_no is not None and page_no >= 1:
                    results["evidence_integrity"]["valid_page_indices"] += 1
                else:
                    results["evidence_integrity"]["invalid_page_indices"] += 1

                if bbox is not None and len(bbox) == 4:
                    x0, y0, x1, y1 = bbox
                    if x0 <= x1 and y0 <= y1 and not any(v is None for v in bbox):
                        results["evidence_integrity"]["valid_bounding_boxes"] += 1
                    else:
                        results["evidence_integrity"]["invalid_bounding_boxes"] += 1
                else:
                    results["evidence_integrity"]["unextracted_or_null_provenance"] += 1
            else:
                results["evidence_integrity"]["unextracted_or_null_provenance"] += 1

        results["documents"][doc_id] = doc_res

    print("\n=== Step 2: Workflow Validation Testing ===")
    
    # Workflow A: Clean Full Packet (All 6 Statutory Documents)
    with tempfile.TemporaryDirectory() as td:
        temp_p = Path(td)
        shutil.copy2(corpus_dir / "VAL_01_application_form.pdf", temp_p / "application_form.pdf")
        shutil.copy2(corpus_dir / "VAL_02_income_cert_clean.pdf", temp_p / "income_cert.pdf")
        shutil.copy2(corpus_dir / "VAL_03_caste_cert_clean.pdf", temp_p / "caste_cert.pdf")
        shutil.copy2(corpus_dir / "VAL_04_residence_cert_clean.pdf", temp_p / "residence_cert.pdf")
        shutil.copy2(corpus_dir / "VAL_05_bank_passbook_clean.pdf", temp_p / "bank_passbook.pdf")
        shutil.copy2(corpus_dir / "VAL_06_marksheet_clean.pdf", temp_p / "marksheet.pdf")

        pipeline = AuditPipeline(as_of=as_of)
        audit_res, extracted_docs = pipeline.load_and_audit_packet(str(temp_p), as_of=as_of)

        passed_rules = [f.rule_id for f in audit_res.findings if f.status.value == "PASS"]
        failed_rules = [f.rule_id for f in audit_res.findings if f.status.value == "FAIL"]

        wf_a_clean = (
            audit_res.overall_status.value in ("READY", "NO_ISSUES_FOUND")
            and audit_res.readiness_score == 100
            and len(failed_rules) == 0
        )

        results["workflows"]["WORKFLOW_A_CLEAN_PACKET"] = {
            "overall_status": audit_res.overall_status.value,
            "readiness_score": audit_res.readiness_score,
            "passed_rules_count": len(passed_rules),
            "failed_rules_count": len(failed_rules),
            "success": wf_a_clean,
        }

        # Confusion matrix tally:
        results["confusion_matrix"]["true_negatives"] += len(passed_rules)
        results["confusion_matrix"]["false_positives"] += len(failed_rules)

    # Workflow B: Contradictory Name Conflict (VAL_07 + VAL_01, 03, 04, 05, 06)
    with tempfile.TemporaryDirectory() as td:
        temp_p = Path(td)
        shutil.copy2(corpus_dir / "VAL_01_application_form.pdf", temp_p / "application_form.pdf")
        shutil.copy2(corpus_dir / "VAL_07_income_cert_name_conflict.pdf", temp_p / "income_cert.pdf")
        shutil.copy2(corpus_dir / "VAL_03_caste_cert_clean.pdf", temp_p / "caste_cert.pdf")
        shutil.copy2(corpus_dir / "VAL_04_residence_cert_clean.pdf", temp_p / "residence_cert.pdf")
        shutil.copy2(corpus_dir / "VAL_05_bank_passbook_clean.pdf", temp_p / "bank_passbook.pdf")
        shutil.copy2(corpus_dir / "VAL_06_marksheet_clean.pdf", temp_p / "marksheet.pdf")

        pipeline = AuditPipeline(as_of=as_of)
        audit_res, _ = pipeline.load_and_audit_packet(str(temp_p), as_of=as_of)

        name_fail = any(
            f.rule_id == "RULE-NAME-01" and f.status.value == "FAIL"
            for f in audit_res.findings
        )
        passed_rules = [f.rule_id for f in audit_res.findings if f.status.value == "PASS"]

        results["workflows"]["WORKFLOW_B_NAME_CONFLICT"] = {
            "overall_status": audit_res.overall_status.value,
            "readiness_score": audit_res.readiness_score,
            "name_rule_failed": name_fail,
            "success": name_fail,
        }

        if name_fail:
            results["confusion_matrix"]["true_positives"] += 1
        else:
            results["confusion_matrix"]["false_negatives"] += 1
        results["confusion_matrix"]["true_negatives"] += len(passed_rules)

    # Workflow C: Income Ceiling Exceeded (VAL_08 + VAL_01, 03, 04, 05, 06)
    with tempfile.TemporaryDirectory() as td:
        temp_p = Path(td)
        shutil.copy2(corpus_dir / "VAL_01_application_form.pdf", temp_p / "application_form.pdf")
        shutil.copy2(corpus_dir / "VAL_08_income_cert_ceiling_exceeded.pdf", temp_p / "income_cert.pdf")
        shutil.copy2(corpus_dir / "VAL_03_caste_cert_clean.pdf", temp_p / "caste_cert.pdf")
        shutil.copy2(corpus_dir / "VAL_04_residence_cert_clean.pdf", temp_p / "residence_cert.pdf")
        shutil.copy2(corpus_dir / "VAL_05_bank_passbook_clean.pdf", temp_p / "bank_passbook.pdf")
        shutil.copy2(corpus_dir / "VAL_06_marksheet_clean.pdf", temp_p / "marksheet.pdf")

        pipeline = AuditPipeline(as_of=as_of)
        audit_res, _ = pipeline.load_and_audit_packet(str(temp_p), as_of=as_of)

        inc_fail = any(
            f.rule_id == "RULE-INC-01" and f.status.value == "FAIL"
            for f in audit_res.findings
        )
        passed_rules = [f.rule_id for f in audit_res.findings if f.status.value == "PASS"]

        results["workflows"]["WORKFLOW_C_INCOME_CEILING"] = {
            "overall_status": audit_res.overall_status.value,
            "readiness_score": audit_res.readiness_score,
            "income_rule_failed": inc_fail,
            "success": inc_fail,
        }

        if inc_fail:
            results["confusion_matrix"]["true_positives"] += 1
        else:
            results["confusion_matrix"]["false_negatives"] += 1
        results["confusion_matrix"]["true_negatives"] += len(passed_rules)

    # Workflow D: Negative Document Non-interference (VAL_13)
    with tempfile.TemporaryDirectory() as td:
        temp_p = Path(td)
        shutil.copy2(corpus_dir / "VAL_13_irrelevant_resume.pdf", temp_p / "irrelevant_resume.pdf")

        pipeline = AuditPipeline(as_of=as_of)
        audit_res, extracted_docs = pipeline.load_and_audit_packet(str(temp_p), as_of=as_of)

        # Unmapped document should not create false rule failures
        unexpected_fails = [f.rule_id for f in audit_res.findings if f.status.value == "FAIL" and f.rule_id != "RULE-DOC-01"]
        
        results["workflows"]["WORKFLOW_D_NEGATIVE_DOCUMENT"] = {
            "extracted_count": len(extracted_docs),
            "unexpected_fails": unexpected_fails,
            "success": len(unexpected_fails) == 0,
        }

    # Workflow E: Scanned OCR Packet (VAL_14, VAL_15)
    with tempfile.TemporaryDirectory() as td:
        temp_p = Path(td)
        shutil.copy2(corpus_dir / "VAL_14_residence_cert_scanned.pdf", temp_p / "residence_cert.pdf")
        shutil.copy2(corpus_dir / "VAL_15_bank_passbook_scanned.pdf", temp_p / "bank_passbook.pdf")

        pipeline = AuditPipeline(as_of=as_of)
        audit_res, extracted_docs = pipeline.load_and_audit_packet(str(temp_p), as_of=as_of)

        ocr_methods = [d.extraction_method for d in extracted_docs.values()]
        all_ocr = all(m == "LOCAL_OCR" for m in ocr_methods)

        results["workflows"]["WORKFLOW_E_SCANNED_OCR"] = {
            "overall_status": audit_res.overall_status.value,
            "readiness_score": audit_res.readiness_score,
            "extraction_methods": ocr_methods,
            "all_local_ocr": all_ocr,
            "success": len(extracted_docs) == 2 and all_ocr,
        }

    # Calculate Sensitivity, Specificity, Accuracy
    tp = results["confusion_matrix"]["true_positives"]
    tn = results["confusion_matrix"]["true_negatives"]
    fp = results["confusion_matrix"]["false_positives"]
    fn = results["confusion_matrix"]["false_negatives"]

    precision = tp / (tp + fp) if (tp + fp) > 0 else 1.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 1.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 1.0
    accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 1.0

    results["summary"] = {
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "specificity": round(specificity, 4),
        "accuracy": round(accuracy, 4),
        "all_workflows_passed": all(w["success"] for w in results["workflows"].values()),
    }

    out_file = Path(__file__).resolve().parents[1] / "docs" / "accuracy_audit_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\nAccuracy audit completed. Output saved to {out_file}")
    print(f"Summary: {json.dumps(results['summary'], indent=2)}")
    print(f"Confusion Matrix: {json.dumps(results['confusion_matrix'], indent=2)}")
    print(f"Evidence Integrity: {json.dumps(results['evidence_integrity'], indent=2)}")
    return results


if __name__ == "__main__":
    run_accuracy_audit()
