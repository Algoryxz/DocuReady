"""Unit and integration tests for T4.1 Evaluation Harness v2."""

from pathlib import Path
import json
import pytest

from eval.harness import (
    RegressionGateError,
    SplitLeakageError,
    check_regression_gate,
    check_split_leakage,
    run_evaluation_pipeline,
    wilson_ci,
)


def test_wilson_ci_zero_nonzero_and_boundaries():
    # Zero events out of 24 -> upper bound > 0 (never [0, 0])
    lo0, hi0 = wilson_ci(0, 24)
    assert lo0 == 0.0
    assert 0.13 < hi0 < 0.15

    # All events (k == n) -> lower bound < 1, upper bound == 1.0
    lo_all, hi_all = wilson_ci(24, 24)
    assert 0.85 < lo_all < 0.87
    assert hi_all == 1.0

    # Nonzero interior event (k=3, n=30)
    lo_mid, hi_mid = wilson_ci(3, 30)
    assert 0.03 < lo_mid < 0.10 < hi_mid < 0.26

    # Invalid denominators/counts raise ValueError
    with pytest.raises(ValueError):
        wilson_ci(0, 0)
    with pytest.raises(ValueError):
        wilson_ci(5, 4)


def test_eval_harness_end_to_end_and_headline_order(tmp_path: Path):
    repo_root = Path(__file__).resolve().parent.parent
    pack_dir = repo_root / "packs" / "odisha.subhadra"
    baseline_path = repo_root / "eval" / "baseline.json"

    report = run_evaluation_pipeline(
        tmp_path / "eval_data",
        pack_dir=pack_dir,
        baseline_path=baseline_path,
        n_dev=12,
        n_calib=16,
        n_test=24,
        render_pdfs=False,
    )

    assert report["leakage_check"]["leakage_detected"] is False
    assert report["calibrator_fitted_on"] == "calib"
    assert len(report["calibrator_weights"]) == 9

    metrics = report["metrics"]
    assert metrics["data_label"] == "synthetic"
    assert metrics["split"] == "test"

    # False-pass rate MUST be the first key in headline_metrics
    headline_keys = list(metrics["headline_metrics"].keys())
    assert headline_keys[0] == "false_pass_rate"
    assert metrics["headline_metrics"]["false_pass_rate"] == 0.0

    # 10-bin reliability table
    assert len(metrics["reliability_table_10bin"]) == 10
    assert sum(b["count"] for b in metrics["reliability_table_10bin"]) == 24

    # Perturbation matrix & negative controls populated
    assert len(metrics["perturbation_matrix"]) >= 4
    assert len(metrics["negative_controls"]) >= 1

    # Regression gate passed
    assert report["regression_gate"]["gate_passed"] is True

    # Counts, denominators, and Wilson CIs present and consistent
    cd = metrics["counts_and_denominators"]
    assert cd["n_test_packets"] == 24
    assert cd["n_defective"] + cd["n_clean"] == 24
    assert cd["decisive_pass_count"] + cd["decisive_fail_count"] + cd["abstention_count"] == 24
    assert cd["clean_decisive_count"] + cd["defective_decisive_count"] == (
        cd["decisive_pass_count"] + cd["decisive_fail_count"]
    )

    hm = metrics["headline_metrics"]
    assert hm["coverage"] == round((cd["decisive_pass_count"] + cd["decisive_fail_count"]) / 24, 4)
    assert hm["clean_packet_decision_coverage"] == round(cd["clean_decisive_count"] / cd["n_clean"], 4)
    assert hm["defective_packet_decision_coverage"] == round(cd["defective_decisive_count"] / cd["n_defective"], 4)
    assert hm["abstention_rate"] == round(cd["abstention_count"] / 24, 4)

    # Negative controls are a strict subset of primary test packets
    assert metrics["negative_control_population"] == "subset_of_primary_test_split"
    neg_total = sum(v["n"] for v in metrics["negative_controls"].values())
    assert neg_total <= cd["n_test_packets"]

    ci_fp = metrics["confidence_intervals_95"]["false_pass_rate"]
    assert ci_fp["method"] == "wilson_score_95"
    assert ci_fp["n"] == cd["n_defective"]
    assert ci_fp["ci"][1] > 0.0  # Zero observed false passes still has non-zero upper CI bound


def test_eval_harness_detects_layout_leakage():
    dev_m = {"layouts_used": ["L1_STANDARD_PORTRAIT"], "samples": []}
    cal_m = {"layouts_used": ["L2_COMPACT_GRID"], "samples": []}
    test_m = {"layouts_used": ["L1_STANDARD_PORTRAIT"], "samples": []}
    with pytest.raises(SplitLeakageError):
        check_split_leakage(dev_m, cal_m, test_m)


def test_eval_harness_regression_gate_fails_on_false_pass_increase(tmp_path: Path):
    baseline = tmp_path / "baseline.json"
    baseline.write_text(
        json.dumps({"max_false_pass_rate": 0.0, "false_pass_tolerance": 0.01}),
        encoding="utf-8",
    )
    bad_metrics = {"headline_metrics": {"false_pass_rate": 0.08}}
    with pytest.raises(RegressionGateError):
        check_regression_gate(bad_metrics, baseline)
