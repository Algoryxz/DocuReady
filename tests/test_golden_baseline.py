"""
DocuReady Golden Baseline Regression Test Suite
Verifies 100% bit-for-bit parity against committed legacy V0 golden snapshot.
"""

import json
from pathlib import Path
import pytest

from docuready.pipeline import AuditPipeline

_REPO_ROOT = Path(__file__).resolve().parents[1]
_GOLDEN_DIR = _REPO_ROOT / "tests" / "golden" / "legacy_v0"
_GOLDEN_JSON = _GOLDEN_DIR / "GOLDEN_BASELINE.json"
_SYNTHETIC_DIR = _REPO_ROOT / "synthetic_data" if (_REPO_ROOT / "synthetic_data").is_dir() else Path.cwd() / "synthetic_data"


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
    audit_dict = audit_res.model_dump()
    audit_dict["timestamp"] = "[NORMALIZED_AUDIT_TIMESTAMP]"
    audit_dict["execution_time_ms"] = 0.0

    docs_dict = {}
    for dt, ed in docs.items():
        key = dt.value if hasattr(dt, "value") else str(dt)
        docs_dict[key] = ed.model_dump()

    actual_packet = {
        "audit_result": audit_dict,
        "extracted_documents": docs_dict,
    }

    expected_packet = golden_data["packets"][packet_id]

    actual_json = json.dumps(actual_packet, indent=2, sort_keys=True)
    expected_json = json.dumps(expected_packet, indent=2, sort_keys=True)

    if actual_json != expected_json:
        # Compare high-level fields first for clear diagnostic reporting
        exp_ar = expected_packet["audit_result"]
        act_ar = actual_packet["audit_result"]

        diffs = []
        if exp_ar["overall_status"] != act_ar["overall_status"]:
            diffs.append(f"Status mismatch: expected {exp_ar['overall_status']}, got {act_ar['overall_status']}")
        if exp_ar["readiness_score"] != act_ar["readiness_score"]:
            diffs.append(f"Score mismatch: expected {exp_ar['readiness_score']}, got {act_ar['readiness_score']}")
        if len(exp_ar["findings"]) != len(act_ar["findings"]):
            diffs.append(f"Finding count mismatch: expected {len(exp_ar['findings'])}, got {len(act_ar['findings'])}")

        diagnostic = "\n".join(diffs) if diffs else "Nested document or evidence difference"
        pytest.fail(f"Golden baseline mismatch for {packet_id}:\n{diagnostic}\n\nDiff details:\nExpected:\n{expected_json[:500]}\nActual:\n{actual_json[:500]}")

    assert actual_json == expected_json
