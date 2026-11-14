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


PACKETS = [
    ("PKT_01_CLEAN", "pkt_01_clean"),
    ("PKT_02_NAME_CONFLICT", "pkt_02_name_conflict"),
    ("PKT_03_DOB_CONFLICT", "pkt_03_dob_conflict"),
    ("PKT_04_INCOME_CONFLICT", "pkt_04_income_conflict"),
    ("PKT_05_MISSING_CERTIFICATE", "pkt_05_missing_certificate"),
    ("PKT_06_MULTIPLE_DEFECTS", "pkt_06_multiple_defects"),
    ("PKT_07_UNREADABLE_DOC", "pkt_07_unreadable_doc"),
    ("PKT_08_AMBIGUOUS_EVIDENCE", "pkt_08_ambiguous_evidence"),
]


@pytest.mark.parametrize("packet_id,folder", PACKETS)
def test_golden_baseline_packet_parity(pipeline, golden_data, packet_id, folder, monkeypatch):
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
