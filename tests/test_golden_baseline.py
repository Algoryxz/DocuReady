"""
DocuReady Golden Baseline Regression Test Suite
Verifies 100% bit-for-bit parity against committed legacy V0 golden snapshot.
"""

import json
from pathlib import Path
from typing import Any, List
import pytest

from docuready.pipeline import AuditPipeline

_REPO_ROOT = Path(__file__).resolve().parents[1]
_GOLDEN_DIR = _REPO_ROOT / "tests" / "golden" / "legacy_v0"
_GOLDEN_JSON = _GOLDEN_DIR / "GOLDEN_BASELINE.json"
_SYNTHETIC_DIR = _REPO_ROOT / "synthetic_data" if (_REPO_ROOT / "synthetic_data").is_dir() else Path.cwd() / "synthetic_data"


def normalize_path_fields(obj: Any) -> Any:
    """Recursively normalize path separators in file_path and file_name fields only."""
    if isinstance(obj, dict):
        return {
            k: (v.replace("\\", "/") if k in ("file_path", "file_name") and isinstance(v, str) else normalize_path_fields(v))
            for k, v in obj.items()
        }
    elif isinstance(obj, list):
        return [normalize_path_fields(item) for item in obj]
    return obj


def recursive_diff(expected: Any, actual: Any, path: str = "") -> List[str]:
    """Recursively identify all differences between expected and actual data structures."""
    diffs = []
    current_path = path or "<root>"

    if type(expected) != type(actual):
        diffs.append(
            f"{current_path}: Type mismatch - expected {type(expected).__name__} ({expected!r}), "
            f"got {type(actual).__name__} ({actual!r})"
        )
        return diffs

    if isinstance(expected, dict):
        exp_keys = set(expected.keys())
        act_keys = set(actual.keys())
        missing = exp_keys - act_keys
        extra = act_keys - exp_keys
        if missing:
            diffs.append(f"{current_path}: Missing keys in actual: {sorted(missing)}")
        if extra:
            diffs.append(f"{current_path}: Unexpected extra keys in actual: {sorted(extra)}")

        for k in sorted(exp_keys & act_keys):
            child_path = f"{path}.{k}" if path else k
            diffs.extend(recursive_diff(expected[k], actual[k], child_path))

    elif isinstance(expected, list):
        if len(expected) != len(actual):
            diffs.append(
                f"{current_path}: List length mismatch - expected {len(expected)} items, got {len(actual)} items"
            )
        min_len = min(len(expected), len(actual))
        for i in range(min_len):
            diffs.extend(recursive_diff(expected[i], actual[i], f"{current_path}[{i}]"))
        if len(actual) > len(expected):
            for i in range(min_len, len(actual)):
                diffs.append(f"{current_path}[{i}]: Unexpected extra list element: {actual[i]!r}")
        elif len(expected) > len(actual):
            for i in range(min_len, len(expected)):
                diffs.append(f"{current_path}[{i}]: Missing list element: {expected[i]!r}")

    else:
        if expected != actual:
            diffs.append(
                f"{current_path}: Value mismatch - expected {expected!r}, got {actual!r}"
            )

    return diffs


@pytest.fixture(scope="module")
def golden_data():
    assert _GOLDEN_JSON.is_file(), f"Golden baseline snapshot not found at {_GOLDEN_JSON}"
    with open(_GOLDEN_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def pipeline():
    return AuditPipeline()


VECTOR_PACKETS = [
    ("PKT_01_CLEAN", "pkt_01_clean"),
    ("PKT_02_NAME_CONFLICT", "pkt_02_name_conflict"),
    ("PKT_03_DOB_CONFLICT", "pkt_03_dob_conflict"),
    ("PKT_04_INCOME_CONFLICT", "pkt_04_income_conflict"),
    ("PKT_05_MISSING_CERTIFICATE", "pkt_05_missing_certificate"),
    ("PKT_06_MULTIPLE_DEFECTS", "pkt_06_multiple_defects"),
    ("PKT_08_AMBIGUOUS_EVIDENCE", "pkt_08_ambiguous_evidence"),
]
PACKETS = VECTOR_PACKETS


@pytest.mark.parametrize("packet_id,folder", VECTOR_PACKETS)
def test_golden_baseline_packet_parity(pipeline, golden_data, packet_id, folder, monkeypatch):
    """Assert 100% bit-for-bit parity against committed golden baseline for vector packets."""
    monkeypatch.chdir(_REPO_ROOT)
    packet_path = f"synthetic_data/{folder}"
    assert (_REPO_ROOT / packet_path).is_dir(), f"Packet fixture directory missing at {packet_path}"

    audit_res, docs = pipeline.load_and_audit_packet(packet_path, packet_id=packet_id)

    # Apply documented canonicalization
    audit_dict = audit_res.model_dump(mode="json")
    audit_dict["timestamp"] = "[NORMALIZED_AUDIT_TIMESTAMP]"
    audit_dict["execution_time_ms"] = 0.0

    docs_dict = {}
    for dt, ed in docs.items():
        key = dt.value if hasattr(dt, "value") else str(dt)
        docs_dict[key] = ed.model_dump(mode="json")

    actual_packet = {
        "audit_result": audit_dict,
        "extracted_documents": docs_dict,
    }

    expected_packet = golden_data["packets"][packet_id]

    # Normalize path separators in path-valued fields only across platforms
    actual_norm = normalize_path_fields(actual_packet)
    expected_norm = normalize_path_fields(expected_packet)

    diffs = recursive_diff(expected_norm, actual_norm)

    if diffs:
        formatted_diffs = "\n  - ".join(diffs)
        actual_json = json.dumps(actual_norm, indent=2, sort_keys=True)
        expected_json = json.dumps(expected_norm, indent=2, sort_keys=True)
        pytest.fail(
            f"Golden baseline parity mismatch for {packet_id} ({len(diffs)} differences found):\n"
            f"  - {formatted_diffs}\n\n"
            f"--- Expected (normalized) ---\n{expected_json}\n\n"
            f"--- Actual (normalized) ---\n{actual_json}"
        )

    # Bit-for-bit JSON parity assertion
    actual_json = json.dumps(actual_norm, indent=2, sort_keys=True)
    expected_json = json.dumps(expected_norm, indent=2, sort_keys=True)
    assert actual_json == expected_json


def test_golden_baseline_packet_07_semantic_ocr(pipeline, golden_data, monkeypatch):
    """
    Verify Packet 7 (PKT_07_UNREADABLE_DOC) adheres to semantic unreadable-document contracts
    without asserting exact string match on OCR text or confidence scores across differing
    Tesseract installations / host environments.
    """
    monkeypatch.chdir(_REPO_ROOT)
    packet_path = "synthetic_data/pkt_07_unreadable_doc"
    assert (_REPO_ROOT / packet_path).is_dir(), f"Packet fixture directory missing at {packet_path}"

    audit_res, docs = pipeline.load_and_audit_packet(packet_path, packet_id="PKT_07_UNREADABLE_DOC")

    audit_dict = audit_res.model_dump(mode="json")
    audit_dict["timestamp"] = "[NORMALIZED_AUDIT_TIMESTAMP]"
    audit_dict["execution_time_ms"] = 0.0

    docs_dict = {}
    for dt, ed in docs.items():
        key = dt.value if hasattr(dt, "value") else str(dt)
        docs_dict[key] = ed.model_dump(mode="json")

    expected_packet = golden_data["packets"]["PKT_07_UNREADABLE_DOC"]
    expected_audit = expected_packet["audit_result"]
    expected_docs = expected_packet["extracted_documents"]

    # 1. Verify exact audit_result parity (all rules, status, score, findings match bit-for-bit)
    actual_audit_norm = normalize_path_fields(audit_dict)
    expected_audit_norm = normalize_path_fields(expected_audit)
    audit_diffs = recursive_diff(expected_audit_norm, actual_audit_norm, path="audit_result")
    if audit_diffs:
        pytest.fail(
            f"PKT_07_UNREADABLE_DOC audit_result mismatch ({len(audit_diffs)} differences found):\n"
            + "\n  - ".join(audit_diffs)
        )

    # 2. Semantic assertions on unreadable document handling
    assert "INCOME_CERT" in docs_dict, "INCOME_CERT missing from extracted documents"
    income_doc = docs_dict["INCOME_CERT"]
    assert income_doc["status"] == "UNREADABLE", (
        f"Expected INCOME_CERT status 'UNREADABLE', got {income_doc['status']!r}"
    )
    assert income_doc["doc_type"] == "INCOME_CERT"
    assert income_doc["fields"] == {}, f"Expected empty extracted fields, got {income_doc['fields']!r}"
    assert income_doc["extraction_method"] == "LOCAL_OCR"
    assert income_doc["page_count"] == 1
    assert actual_audit_norm["overall_status"] == "UNREADABLE_PACKET"
    assert actual_audit_norm["readiness_score"] == 75

    # Verify RULE-DOC-02 presence in findings
    rule_doc_02 = [f for f in actual_audit_norm["findings"] if f.get("rule_id") == "RULE-DOC-02"]
    assert len(rule_doc_02) == 1, "Expected exactly one RULE-DOC-02 finding"
    assert rule_doc_02[0]["status"] == "UNKNOWN"
    assert rule_doc_02[0]["severity"] == "CRITICAL"
    assert rule_doc_02[0]["field"] == "SCAN_QUALITY"
    assert "INCOME_CERT" in rule_doc_02[0]["documents_involved"]

    # 3. Compare INCOME_CERT exactly apart from raw_text and mean_ocr_confidence
    assert "INCOME_CERT" in expected_docs, "INCOME_CERT missing from golden snapshot"
    exp_income_raw = expected_docs["INCOME_CERT"]
    act_income_raw = docs_dict["INCOME_CERT"]

    # Narrowly scoped copy excluding only approved OCR-dependent fields without mutating originals
    exp_income_filtered = {k: v for k, v in exp_income_raw.items() if k not in ("raw_text", "mean_ocr_confidence")}
    act_income_filtered = {k: v for k, v in act_income_raw.items() if k not in ("raw_text", "mean_ocr_confidence")}

    exp_income_norm = normalize_path_fields(exp_income_filtered)
    act_income_norm = normalize_path_fields(act_income_filtered)

    income_diffs = recursive_diff(exp_income_norm, act_income_norm, path="extracted_documents.INCOME_CERT")
    if income_diffs:
        pytest.fail(
            f"PKT_07_UNREADABLE_DOC INCOME_CERT deterministic field mismatch ({len(income_diffs)} differences found):\n"
            + "\n  - ".join(income_diffs)
        )

    # 4. Verify exact parity for all native vector documents in PKT_07
    for doc_name, exp_doc in expected_docs.items():
        if doc_name == "INCOME_CERT":
            continue
        assert doc_name in docs_dict, f"Expected vector document {doc_name} missing from actual docs"
        act_doc = docs_dict[doc_name]
        exp_doc_norm = normalize_path_fields(exp_doc)
        act_doc_norm = normalize_path_fields(act_doc)
        vec_diffs = recursive_diff(exp_doc_norm, act_doc_norm, path=f"extracted_documents.{doc_name}")
        if vec_diffs:
            pytest.fail(
                f"PKT_07_UNREADABLE_DOC vector document {doc_name} mismatch ({len(vec_diffs)} differences found):\n"
                + "\n  - ".join(vec_diffs)
            )


# ---------------------------------------------------------------------------
# Unit tests for comparison helpers (Contract Invariance Verification)
# ---------------------------------------------------------------------------

def test_path_normalization_designated_keys_only():
    """Verify that path normalization applies strictly to file_path and file_name keys."""
    sample = {
        "file_path": "dir\\subdir\\file.pdf",
        "file_name": "sub\\doc.pdf",
        "raw_snippet": "Name: JOHN \\ DOE",
        "message": "Error at path: C:\\Temp",
        "nested": {
            "file_path": "nested\\path\\doc.pdf",
            "other_field": "val\\with\\backslashes"
        },
        "list_items": [
            {"file_name": "item\\file.pdf", "text": "line\\break"}
        ]
    }
    normalized = normalize_path_fields(sample)

    # Designated keys are normalized to POSIX
    assert normalized["file_path"] == "dir/subdir/file.pdf"
    assert normalized["file_name"] == "sub/doc.pdf"
    assert normalized["nested"]["file_path"] == "nested/path/doc.pdf"
    assert normalized["list_items"][0]["file_name"] == "item/file.pdf"

    # Non-path fields are preserved exactly with backslashes intact
    assert normalized["raw_snippet"] == "Name: JOHN \\ DOE"
    assert normalized["message"] == "Error at path: C:\\Temp"
    assert normalized["nested"]["other_field"] == "val\\with\\backslashes"
    assert normalized["list_items"][0]["text"] == "line\\break"


def test_non_path_values_untouched():
    """Verify that numeric, boolean, list, and other non-path values are strictly preserved."""
    sample = {
        "score": 100,
        "ratio": 0.854,
        "is_valid": True,
        "none_val": None,
        "bounding_box": [100.5, 200.0, 300.5, 400.0],
        "tags": ["A", "B", "C"]
    }
    normalized = normalize_path_fields(sample)
    assert normalized == sample


def test_recursive_diff_diagnostics():
    """Verify recursive_diff detects missing keys, extra keys, types, lists, and values."""
    expected = {
        "score": 100,
        "status": "PASS",
        "items": [1, 2, 3],
        "nested": {"key_a": "val_a", "mismatch": "expected_val"}
    }
    actual = {
        "score": "100",  # Type mismatch (int vs str)
        "items": [1, 2],  # List length mismatch
        "nested": {"key_a": "val_a", "key_extra": "extra", "mismatch": "actual_val"}
        # "status" is missing
    }

    diffs = recursive_diff(expected, actual)
    diff_text = "\n".join(diffs)

    assert "<root>: Missing keys in actual: ['status']" in diff_text
    assert "nested: Unexpected extra keys in actual: ['key_extra']" in diff_text
    assert "score: Type mismatch" in diff_text
    assert "items: List length mismatch - expected 3 items, got 2 items" in diff_text
    assert "nested.mismatch: Value mismatch - expected 'expected_val', got 'actual_val'" in diff_text


def test_deliberate_non_path_mismatch_detected():
    """Verify that a deliberate change in score, status, or bounding box is caught by recursive_diff."""
    base = {
        "packet_id": "PKT_01",
        "audit_result": {
            "readiness_score": 100,
            "overall_status": "READY_TO_SUBMIT"
        },
        "extracted_documents": {
            "INCOME_CERT": {
                "bounding_box": [10.0, 20.0, 30.0, 40.0],
                "mean_ocr_confidence": 0.0
            }
        }
    }
    # Altered version with score and OCR confidence changed
    altered = {
        "packet_id": "PKT_01",
        "audit_result": {
            "readiness_score": 95,
            "overall_status": "READY_TO_SUBMIT"
        },
        "extracted_documents": {
            "INCOME_CERT": {
                "bounding_box": [10.0, 20.0, 30.0, 40.0],
                "mean_ocr_confidence": 0.25
            }
        }
    }

    diffs = recursive_diff(base, altered)
    assert len(diffs) == 2
    assert any("readiness_score: Value mismatch" in d for d in diffs)
    assert any("mean_ocr_confidence: Value mismatch" in d for d in diffs)


def test_packet_07_ocr_field_filtering_preserves_deterministic_keys():
    """Verify that excluding OCR fields retains all deterministic metadata and catches changes."""
    base_doc = {
        "doc_type": "INCOME_CERT",
        "file_path": "synthetic_data/pkt_07_unreadable_doc/income_cert.pdf",
        "status": "UNREADABLE",
        "fields": {},
        "raw_text": "",
        "page_count": 1,
        "extraction_method": "LOCAL_OCR",
        "mean_ocr_confidence": 0.0,
    }
    actual_doc = {
        "doc_type": "INCOME_CERT",
        "file_path": "synthetic_data/pkt_07_unreadable_doc/income_cert.pdf",
        "status": "UNREADABLE",
        "fields": {},
        "raw_text": "[DIFFERENT_OCR_TEXT]",
        "page_count": 1,
        "extraction_method": "LOCAL_OCR",
        "mean_ocr_confidence": 0.85,
    }

    # Filter only approved OCR fields
    base_filtered = {k: v for k, v in base_doc.items() if k not in ("raw_text", "mean_ocr_confidence")}
    actual_filtered = {k: v for k, v in actual_doc.items() if k not in ("raw_text", "mean_ocr_confidence")}

    # With only OCR fields differing, filtered comparison succeeds
    diffs = recursive_diff(base_filtered, actual_filtered)
    assert not diffs, "Expected no diff when only raw_text and mean_ocr_confidence differ"

    # If a deterministic field (e.g., status or page_count) differs, it is caught
    corrupted_doc = dict(actual_filtered)
    corrupted_doc["status"] = "PROCESSED"
    corrupted_diffs = recursive_diff(base_filtered, corrupted_doc)
    assert len(corrupted_diffs) == 1
    assert "status: Value mismatch" in corrupted_diffs[0]
