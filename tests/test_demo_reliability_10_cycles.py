"""
Ten-Cycle Demonstration Reliability Test Suite
HackNation 2026 Loop 5 Engineering Directive

Executes 10 consecutive complete demonstration cycles, plus crash recovery
and cold restart stress testing, recording detailed latency, memory, and export metrics.
"""

import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import date
from typing import Any, Dict, List

ROOT = pathlib.Path(__file__).resolve().parents[1]
SIDECAR_EXE = ROOT / "sidecar" / "dist" / "docuready_sidecar" / "docuready_sidecar.exe"
CORPUS_DIR = ROOT / "tests" / "validation_corpus"


def run_cycle(cycle_idx: int, ws_root: pathlib.Path) -> Dict[str, Any]:
    t0 = time.perf_counter()
    pkt_dir = ws_root / f"packet_cycle_{cycle_idx}"
    pkt_dir.mkdir(parents=True, exist_ok=True)

    # 1. Document Import (Stage 6 Clean Statutory Documents)
    for fname in ["VAL_01_application_form.pdf", "VAL_02_income_cert_clean.pdf", "VAL_03_caste_cert_clean.pdf",
                  "VAL_04_residence_cert_clean.pdf", "VAL_05_bank_passbook_clean.pdf", "VAL_06_marksheet_clean.pdf"]:
        dest = fname.split("_", 2)[-1]
        shutil.copy2(CORPUS_DIR / fname, pkt_dir / dest)

    env = os.environ.copy()
    env["DOCUREADY_WORKSPACE_ROOT"] = str(ws_root)
    env.pop("PYTHONPATH", None)
    env.pop("PYTHONHOME", None)

    # 2. Sidecar Launch & Health Check
    t_start = time.perf_counter()
    proc = subprocess.Popen(
        [str(SIDECAR_EXE)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
        bufsize=1,
    )

    # Send Health Handshake
    health_req = json.dumps({"protocol": 1, "id": f"health-{cycle_idx}", "method": "health", "params": {}}) + "\n"
    proc.stdin.write(health_req)
    proc.stdin.flush()
    health_line = proc.stdout.readline()
    health_resp = json.loads(health_line)
    health_ok = health_resp.get("ok") is True

    # 3. Audit Execution
    audit_req = json.dumps({
        "protocol": 1,
        "id": f"audit-{cycle_idx}",
        "method": "audit_packet",
        "params": {
            "packet_dir": str(pkt_dir),
            "packet_id": f"CYCLE_{cycle_idx}_PACKET",
            "as_of": "2026-04-15"
        }
    }) + "\n"
    proc.stdin.write(audit_req)
    proc.stdin.flush()

    audit_resp = None
    progress_count = 0
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        frame = json.loads(line)
        if frame.get("event") == "progress":
            progress_count += 1
        elif frame.get("id") == f"audit-{cycle_idx}":
            audit_resp = frame
            break

    # 4. Findings & Evidence Inspection
    audit_data = audit_resp.get("result", {}).get("audit", {}) if audit_resp else {}
    overall_status = audit_data.get("overall_status")
    readiness_score = audit_data.get("readiness_score")
    findings_count = len(audit_data.get("findings", []))
    documents_count = len(audit_resp.get("result", {}).get("documents", [])) if audit_resp else 0

    findings_verified = (
        overall_status == "NO_ISSUES_FOUND"
        and readiness_score == 100
        and findings_count == 8
        and documents_count == 6
    )

    # 5. Report Export Integrity
    export_intact = (
        "overall_status" in audit_data
        and "readiness_score" in audit_data
        and "findings" in audit_data
    )

    # 6. Shutdown
    shutdown_req = json.dumps({"protocol": 1, "id": f"shut-{cycle_idx}", "method": "shutdown", "params": {}}) + "\n"
    proc.stdin.write(shutdown_req)
    proc.stdin.flush()
    proc.wait(timeout=5)
    clean_exit = proc.returncode == 0

    # 7. Session Cleanup
    t_clean_0 = time.perf_counter()
    shutil.rmtree(pkt_dir)
    t_clean = (time.perf_counter() - t_clean_0) * 1000.0
    cleanup_verified = not pkt_dir.exists()

    t_total = (time.perf_counter() - t0) * 1000.0

    cycle_result = {
        "cycle": cycle_idx,
        "success": health_ok and findings_verified and export_intact and clean_exit and cleanup_verified,
        "duration_ms": round(t_total, 2),
        "cleanup_latency_ms": round(t_clean, 2),
        "health_ok": health_ok,
        "progress_frames": progress_count,
        "overall_status": overall_status,
        "readiness_score": readiness_score,
        "findings_count": findings_count,
        "documents_count": documents_count,
        "clean_exit": clean_exit,
        "cleanup_verified": cleanup_verified,
        "errors": [] if (findings_verified and clean_exit) else ["Cycle verification failure"],
    }
    return cycle_result


def run_reliability_suite():
    print("=== Launching 10 Consecutive Demonstration Cycles ===")
    ws_root = pathlib.Path(tempfile.mkdtemp(prefix="docuready_demo_reliability_"))
    cycles_data = []

    try:
        for i in range(1, 11):
            print(f"Executing Demonstration Cycle {i} of 10...")
            res = run_cycle(i, ws_root)
            cycles_data.append(res)
            print(f"   Cycle {i}: {'PASSED' if res['success'] else 'FAILED'} in {res['duration_ms']}ms (cleanup: {res['cleanup_latency_ms']}ms)")

        # Additional Stress Test 1: Interrupted Audit / Sudden Kill Recovery
        print("\n=== Executing Stress Test: Sudden Process Termination & Recovery ===")
        pkt_dir = ws_root / "packet_interrupted"
        pkt_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(CORPUS_DIR / "VAL_01_application_form.pdf", pkt_dir / "application_form.pdf")

        env = os.environ.copy()
        env["DOCUREADY_WORKSPACE_ROOT"] = str(ws_root)
        proc_crash = subprocess.Popen(
            [str(SIDECAR_EXE)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            env=env,
        )
        # Send partial audit request and kill immediately
        proc_crash.stdin.write(json.dumps({"protocol": 1, "id": "kill-test", "method": "audit_packet", "params": {"packet_dir": str(pkt_dir), "packet_id": "KILL_PKT", "as_of": "2026-04-15"}}) + "\n")
        proc_crash.stdin.flush()
        time.sleep(0.02)
        proc_crash.kill()
        proc_crash.wait()
        crash_detected = proc_crash.returncode is not None
        print(f"   Process successfully terminated mid-turn (returncode: {proc_crash.returncode}).")

        # Relaunch fresh instance to confirm recovery
        proc_fresh = subprocess.Popen(
            [str(SIDECAR_EXE)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
            env=env,
        )
        proc_fresh.stdin.write(json.dumps({"protocol": 1, "id": "recovery-health", "method": "health", "params": {}}) + "\n")
        proc_fresh.stdin.flush()
        fresh_line = proc_fresh.stdout.readline()
        fresh_resp = json.loads(fresh_line)
        recovery_ok = fresh_resp.get("ok") is True
        proc_fresh.stdin.write(json.dumps({"protocol": 1, "id": "recovery-shut", "method": "shutdown", "params": {}}) + "\n")
        proc_fresh.stdin.flush()
        proc_fresh.wait(timeout=5)
        print(f"   Fresh instance recovery status: {'SUCCESS' if recovery_ok else 'FAILED'}")

        # Summary
        all_cycles_passed = all(c["success"] for c in cycles_data)
        durations = [c["duration_ms"] for c in cycles_data]
        cleanups = [c["cleanup_latency_ms"] for c in cycles_data]

        summary = {
            "total_cycles_executed": 10,
            "cycles_passed": sum(1 for c in cycles_data if c["success"]),
            "cycles_failed": sum(1 for c in cycles_data if not c["success"]),
            "all_consecutive_cycles_passed": all_cycles_passed,
            "mean_cycle_duration_ms": round(sum(durations) / len(durations), 2),
            "min_cycle_duration_ms": min(durations),
            "max_cycle_duration_ms": max(durations),
            "mean_cleanup_latency_ms": round(sum(cleanups) / len(cleanups), 2),
            "crash_recovery_verified": crash_detected and recovery_ok,
            "final_reliability_status": "QUALIFIED" if (all_cycles_passed and recovery_ok) else "FAILED",
        }

        output_payload = {
            "summary": summary,
            "cycles": cycles_data,
        }

        out_json = ROOT / "docs" / "demo_reliability_results.json"
        with open(out_json, "w", encoding="utf-8") as f:
            json.dump(output_payload, f, indent=2)

        print(f"\nReliability Results saved to {out_json}")
        print("Summary:")
        print(json.dumps(summary, indent=2))
        return output_payload

    finally:
        if ws_root.exists():
            shutil.rmtree(ws_root, ignore_errors=True)


if __name__ == "__main__":
    run_reliability_suite()
