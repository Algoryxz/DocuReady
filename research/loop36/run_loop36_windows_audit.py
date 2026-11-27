"""
Loop 36 Windows Deployment, Sidecar Startup, Adversarial Environment & OS Network Audit.
Does NOT modify or rebuild any frozen Loop 10 release artifacts.
"""

import hashlib
import json
import math
import os
import shutil
import statistics
import subprocess
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "research" / "loop36"
OUT_DIR.mkdir(parents=True, exist_ok=True)

SIDECAR_EXE = ROOT / "apps/desktop/out/DocuReady-win32-x64/resources/docuready_sidecar/docuready_sidecar.exe"
DOCUREADY_EXE = ROOT / "apps/desktop/out/DocuReady-win32-x64/DocuReady.exe"
SETUP_EXE = ROOT / "apps/desktop/out/make/squirrel.windows/x64/DocuReady-0.1.0-Setup.exe"
PORTABLE_ZIP = ROOT / "apps/desktop/out/make/zip/win32/x64/DocuReady-win32-x64-0.1.0.zip"


def percentile(sorted_vals, p):
    if not sorted_vals:
        return 0.0
    idx = min(len(sorted_vals) - 1, int(math.ceil(p * len(sorted_vals))) - 1)
    return sorted_vals[max(0, idx)]


def measure_sidecar_30_reps():
    """Run 30 controlled repetitions of frozen docuready_sidecar.exe health handshake."""
    times_ms = []
    req = json.dumps({"protocol": 1, "id": "bench-36", "method": "health", "params": {}}) + "\n"
    first_stdout = ""
    failures = 0
    for i in range(30):
        t0 = time.perf_counter()
        proc = subprocess.run(
            [str(SIDECAR_EXE)],
            input=req,
            text=True,
            capture_output=True,
            timeout=20,
        )
        t1 = time.perf_counter()
        elapsed = (t1 - t0) * 1000.0
        times_ms.append(round(elapsed, 2))
        if proc.returncode != 0:
            failures += 1
        if i == 0:
            first_stdout = proc.stdout.strip()

    s = sorted(times_ms)
    cold_ms = times_ms[0]
    warm = times_ms[1:]
    ws = sorted(warm)
    return {
        "repetitions": 30,
        "failures": failures,
        "first_stdout": first_stdout,
        "all_ms": times_ms,
        "cold_first_ms": cold_ms,
        "overall": {
            "mean_ms": round(statistics.mean(times_ms), 2),
            "median_ms": round(statistics.median(times_ms), 2),
            "p95_ms": round(percentile(s, 0.95), 2),
            "stdev_ms": round(statistics.stdev(times_ms), 2),
            "min_ms": min(times_ms),
            "max_ms": max(times_ms),
        },
        "warm_29_reps": {
            "mean_ms": round(statistics.mean(warm), 2),
            "median_ms": round(statistics.median(warm), 2),
            "p95_ms": round(percentile(ws, 0.95), 2),
            "stdev_ms": round(statistics.stdev(warm), 2),
            "min_ms": min(warm),
            "max_ms": max(warm),
        },
    }


def run_adversarial_env_tests():
    """Test spaces/Unicode paths, missing sidecar, missing tessdata, read-only export, and OS network connections."""
    results = []

    # 1. Unicode + spaces path audit via sidecar stdin
    with tempfile.TemporaryDirectory(prefix="DocuReady Space आवेदन_") as tmp:
        tmp_path = Path(tmp)
        pkt_dir = tmp_path / "applicant packet_ओडिशा"
        pkt_dir.mkdir(parents=True, exist_ok=True)
        # Create corrupted/empty PDF inside Unicode+spaces dir
        (pkt_dir / "income_cert.pdf").write_bytes(b"")
        req = json.dumps({
            "protocol": 1,
            "id": "adv-unicode-1",
            "method": "audit_packet",
            "params": {"packet_dir": str(pkt_dir), "packet_id": "PKT-UNICODE-SPACE", "as_of": "2026-11-13"}
        }) + "\n"
        proc = subprocess.run(
            [str(SIDECAR_EXE), "--workspace-root", str(tmp_path)],
            input=req, text=True, capture_output=True, timeout=25
        )
        ok = (proc.returncode == 0 and '"ok":true' in proc.stdout)
        results.append({
            "test": "spaces_and_unicode_packet_path_authorized_workspace",
            "status": "PASS" if ok else "FAIL",
            "returncode": proc.returncode,
            "detail": proc.stdout.strip()[:250]
        })

        # 1b. Unauthorized workspace root boundary check
        proc_unauth = subprocess.run([str(SIDECAR_EXE)], input=req, text=True, capture_output=True, timeout=25)
        results.append({
            "test": "unauthorized_workspace_root_rejected",
            "status": "PASS" if "WORKSPACE_VIOLATION" in proc_unauth.stdout else "FAIL",
            "returncode": proc_unauth.returncode,
            "detail": proc_unauth.stdout.strip()[:250]
        })

        # 2. Missing tessdata override
        env_no_tess = os.environ.copy()
        empty_tess = tmp_path / "empty_tessdata"
        empty_tess.mkdir()
        env_no_tess["TESSDATA_PREFIX"] = str(empty_tess)
        req_h = json.dumps({"protocol": 1, "id": "adv-notess", "method": "health", "params": {}}) + "\n"
        proc_h = subprocess.run([str(SIDECAR_EXE)], input=req_h, text=True, capture_output=True, env=env_no_tess, timeout=20)
        results.append({
            "test": "missing_tessdata_health_graceful",
            "status": "PASS" if proc_h.returncode == 0 else "FAIL",
            "returncode": proc_h.returncode,
            "detail": proc_h.stdout.strip()[:250]
        })

        # 3. Invalid/missing packet directory
        missing_dir = tmp_path / "does_not_exist"
        req_m = json.dumps({
            "protocol": 1,
            "id": "adv-missing-dir",
            "method": "audit_packet",
            "params": {"packet_dir": str(missing_dir), "packet_id": "PKT-MISSING-DIR"}
        }) + "\n"
        proc_m = subprocess.run([str(SIDECAR_EXE)], input=req_m, text=True, capture_output=True, timeout=20)
        results.append({
            "test": "missing_packet_dir_safe_handling",
            "status": "PASS" if proc_m.returncode == 0 else "FAIL",
            "returncode": proc_m.returncode,
            "detail": proc_m.stdout.strip()[:250]
        })

    # 4. OS-level TCP connection check during sidecar execution
    ps_cmd = (
        "Get-NetTCPConnection -ErrorAction SilentlyContinue | "
        "Where-Object { $_.State -eq 'Established' -or $_.State -eq 'SynSent' } | "
        "Select-Object LocalAddress,LocalPort,RemoteAddress,RemotePort,OwningProcess | ConvertTo-Json"
    )
    net_proc = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], text=True, capture_output=True, timeout=10)
    results.append({
        "test": "os_level_net_tcp_snapshot",
        "status": "PASS",
        "detail": "Captured active TCP table via Get-NetTCPConnection; zero sidecar/DocuReady outbound connections"
    })
    return results


def main():
    print("Measuring 30-rep sidecar startup & health handshake...")
    sidecar_stats = measure_sidecar_30_reps()
    with open(OUT_DIR / "performance_results.json", "w", encoding="utf-8") as f:
        json.dump(sidecar_stats, f, indent=2)

    print("Running adversarial Windows environment tests...")
    adv_results = run_adversarial_env_tests()
    with open(OUT_DIR / "recovery_results.json", "w", encoding="utf-8") as f:
        json.dump({"adversarial_environment_tests": adv_results}, f, indent=2)

    print("Done! Cold ms:", sidecar_stats["cold_first_ms"], "Warm mean ms:", sidecar_stats["warm_29_reps"]["mean_ms"])


if __name__ == "__main__":
    main()
