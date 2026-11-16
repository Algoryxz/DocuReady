"""
Independent Re-audit of Loop 4 Evidence and Artifacts
For HackNation 2026 Loop 5 Directive
"""

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def verify_evidence():
    report = {
        "corpus_manifest_verified": False,
        "corpus_file_count": 0,
        "corpus_hash_matches": 0,
        "corpus_hash_mismatches": [],
        "golden_baseline_verified": False,
        "golden_baseline_hash": None,
        "accuracy_audit_matrix_verified": False,
        "accuracy_metrics": {},
        "packaged_sidecar_exists": False,
        "packaged_sidecar_clean_run": False,
        "production_electron_package_exists": False,
        "production_package_files": [],
    }

    # 1. Verify Validation Corpus against Manifest
    manifest_path = ROOT / "docs" / "validation_corpus_manifest.json"
    corpus_dir = ROOT / "tests" / "validation_corpus"

    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        docs = manifest.get("documents", [])
        report["corpus_file_count"] = len(docs)

        for d in docs:
            fname = d["file_name"]
            expected_hash = d["sha256"]
            fpath = corpus_dir / fname

            if not fpath.exists():
                report["corpus_hash_mismatches"].append({
                    "file": fname,
                    "error": "FILE_MISSING",
                    "expected": expected_hash,
                })
                continue

            actual_hash = hashlib.sha256(fpath.read_bytes()).hexdigest()
            if actual_hash == expected_hash:
                report["corpus_hash_matches"] += 1
            else:
                report["corpus_hash_mismatches"].append({
                    "file": fname,
                    "actual": actual_hash,
                    "expected": expected_hash,
                })

        report["corpus_manifest_verified"] = (
            len(report["corpus_hash_mismatches"]) == 0 and report["corpus_hash_matches"] > 0
        )

    # 2. Verify Golden Baseline Hash
    golden_path = ROOT / "tests" / "golden" / "legacy_v0" / "GOLDEN_BASELINE.json"
    hashes_file = ROOT / "tests" / "golden" / "legacy_v0" / "GOLDEN_BASELINE_HASHES.txt"

    if golden_path.exists() and hashes_file.exists():
        actual_gb_hash = hashlib.sha256(golden_path.read_bytes()).hexdigest().lower()
        report["golden_baseline_hash"] = actual_gb_hash
        hashes_txt = hashes_file.read_text(encoding="utf-8").lower()
        report["golden_baseline_verified"] = actual_gb_hash in hashes_txt

    # 3. Verify Accuracy Audit Matrix
    acc_path = ROOT / "docs" / "accuracy_audit_results.json"
    if acc_path.exists():
        with open(acc_path, "r", encoding="utf-8") as f:
            acc_data = json.load(f)
        report["accuracy_metrics"] = acc_data.get("summary", {})
        report["accuracy_confusion_matrix"] = acc_data.get("confusion_matrix", {})
        report["accuracy_audit_matrix_verified"] = (
            report["accuracy_metrics"].get("precision") == 1.0
            and report["accuracy_metrics"].get("recall") == 1.0
            and report["accuracy_metrics"].get("all_workflows_passed") is True
        )

    # 4. Verify Packaged Sidecar in Isolated Environment
    sidecar_exe = ROOT / "sidecar" / "dist" / "docuready_sidecar" / "docuready_sidecar.exe"
    report["packaged_sidecar_exists"] = sidecar_exe.exists()

    if sidecar_exe.exists():
        clean_env = os.environ.copy()
        clean_env.pop("PYTHONPATH", None)
        clean_env.pop("PYTHONHOME", None)
        clean_env.pop("DOCUREADY_SIDECAR_EXECUTABLE", None)

        test_payload = json.dumps({
            "protocol": 1,
            "id": "reaudit-health-1",
            "method": "health",
            "params": {}
        }) + "\n" + json.dumps({
            "protocol": 1,
            "id": "reaudit-shutdown-1",
            "method": "shutdown",
            "params": {}
        }) + "\n"

        proc = subprocess.run(
            [str(sidecar_exe)],
            input=test_payload,
            capture_output=True,
            text=True,
            env=clean_env,
            timeout=15,
        )

        lines = [line.strip() for line in proc.stdout.strip().splitlines() if line.strip()]
        health_ok = False
        shutdown_ok = False
        for line in lines:
            try:
                frame = json.loads(line)
                if frame.get("id") == "reaudit-health-1" and frame.get("ok"):
                    health_ok = True
                if frame.get("id") == "reaudit-shutdown-1" and frame.get("ok"):
                    shutdown_ok = True
            except json.JSONDecodeError:
                pass

        report["packaged_sidecar_clean_run"] = (health_ok and shutdown_ok and proc.returncode == 0)

    # 5. Verify Production Electron Package
    pkg_dir = ROOT / "apps" / "desktop" / "out" / "DocuReady-win32-x64"
    main_exe = pkg_dir / "DocuReady.exe"
    report["production_electron_package_exists"] = main_exe.exists()
    if pkg_dir.exists():
        report["production_package_files"] = [p.name for p in pkg_dir.iterdir()]

    print("=== Re-audit Results ===")
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    verify_evidence()
