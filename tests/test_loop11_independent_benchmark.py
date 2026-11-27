"""
Permanent Independent Benchmark Test Suite for Loop 11
DocuReady - Research Loop 11
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
BENCHMARK_DIR = REPO_ROOT / "research" / "loop11_benchmark"
RESULTS_DIR = BENCHMARK_DIR / "results"
GROUND_TRUTH_DIR = BENCHMARK_DIR / "ground_truth"


def test_loop11_manifest_and_ground_truth_integrity() -> None:
    """Verifies that all 5 benchmark dataset ground-truth manifests exist and are valid JSON."""
    gt_files = [
        "funsd_ground_truth.json",
        "sroie_ground_truth.json",
        "indic_ground_truth.json",
        "doclaynet_ground_truth.json",
        "degradation_ground_truth.json",
    ]
    for gtf in gt_files:
        p = GROUND_TRUTH_DIR / gtf
        assert p.is_file(), f"Missing ground truth file: {p}"
        data = json.loads(p.read_text(encoding="utf-8"))
        assert len(data) > 0, f"Empty ground truth dataset: {gtf}"


def test_loop11_benchmark_results_artifacts_exist() -> None:
    """Verifies that benchmark output JSON files exist and have recorded metrics."""
    res_file = RESULTS_DIR / "loop11_benchmark_results.json"
    assert res_file.is_file(), f"Benchmark results missing: {res_file}"
    results = json.loads(res_file.read_text(encoding="utf-8"))

    for expected_suite in ["funsd", "sroie", "indic_ocr", "doclaynet", "degradation"]:
        assert expected_suite in results, f"Missing suite in results: {expected_suite}"

    # Verify FUNSD recorded metrics
    assert "mean_cer" in results["funsd"]
    assert results["funsd"]["sample_count"] == 50

    # Verify SROIE recorded metrics
    assert results["sroie"]["date_normalization_accuracy"] == 1.0
    assert results["sroie"]["sample_count"] == 60


def test_loop11_failure_cases_taxonomy_integrity() -> None:
    """Verifies that the failure cases archive is structured and contains root causes."""
    fail_file = RESULTS_DIR / "loop11_failure_cases.json"
    assert fail_file.is_file(), f"Failure cases file missing: {fail_file}"
    failures = json.loads(fail_file.read_text(encoding="utf-8"))
    assert len(failures) > 0, "Expected non-zero benchmark failures recorded"

    for f in failures[:20]:
        assert "error_type" in f
        assert "root_cause_hypothesis" in f
        assert "dataset" in f


def test_loop11_stage_profiling_results_integrity() -> None:
    """Verifies that stage profiling data accurately reflects pipeline stages."""
    prof_file = RESULTS_DIR / "stage_profiling_results.json"
    assert prof_file.is_file(), f"Profiling results missing: {prof_file}"
    prof = json.loads(prof_file.read_text(encoding="utf-8"))

    assert "stages_ms" in prof
    assert "initial_ocr" in prof["stages_ms"]
    assert prof["stages_ms"]["initial_ocr"]["pct_of_total"] > 50.0  # OCR is dominant bottleneck


def test_loop11_multilingual_experiment_results_integrity() -> None:
    """Verifies that the multilingual generalization experiment recorded control vs treatment."""
    exp_file = RESULTS_DIR / "exp_multilingual_results.json"
    assert exp_file.is_file(), f"Multilingual experiment results missing: {exp_file}"
    exp = json.loads(exp_file.read_text(encoding="utf-8"))

    assert "control_mean_cer" in exp
    assert "treatment_mean_cer" in exp
    assert "latency_overhead_ratio" in exp
    assert exp["sample_count"] == 20
