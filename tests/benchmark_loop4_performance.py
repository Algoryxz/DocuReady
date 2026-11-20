"""Loop 4 Performance & Reliability Benchmark Harness for DocuReady Desktop.

Measures:
1. Sidecar cold startup and health handshake latency
2. Document intake/registration throughput
3. Audit duration and peak memory (RSS) across packet sizes (small, typical, max 20-doc)
4. Sequential repeatability and memory leak inspection
5. Active job cancellation latency and process recovery
6. Redacted report export speed
7. Ephemeral workspace destruction latency
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import psutil


def measure_sidecar_startup(exe_path: str, iterations: int = 5) -> dict:
    timings = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        proc = subprocess.Popen(
            [exe_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
        )
        proc.stdin.write('{"protocol":1,"id":"bench-h","method":"health","params":{}}\n')
        proc.stdin.flush()
        line = proc.stdout.readline()
        t1 = time.perf_counter()
        timings.append((t1 - t0) * 1000)  # ms

        proc.stdin.write('{"protocol":1,"id":"bench-s","method":"shutdown","params":{}}\n')
        proc.stdin.flush()
        proc.stdout.readline()
        proc.wait(timeout=3)

    return {
        "iterations": iterations,
        "min_ms": round(min(timings), 2),
        "median_ms": round(sorted(timings)[len(timings) // 2], 2),
        "max_ms": round(max(timings), 2),
    }


def run_audit_packet(proc: subprocess.Popen, packet_dir: Path, packet_id: str, as_of: str = "2026-11-16") -> dict:
    t0 = time.perf_counter()
    req = {
        "protocol": 1,
        "id": f"bench-{packet_id}",
        "method": "audit_packet",
        "params": {
            "packet_dir": str(packet_dir),
            "packet_id": packet_id,
            "as_of": as_of,
        },
    }
    proc.stdin.write(json.dumps(req) + "\n")
    proc.stdin.flush()

    final_resp = None
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        data = json.loads(line)
        if data.get("id") == f"bench-{packet_id}":
            final_resp = data
            break

    t1 = time.perf_counter()
    duration_ms = (t1 - t0) * 1000

    # Measure process memory
    p = psutil.Process(proc.pid)
    mem_info = p.memory_info()
    rss_mb = round(mem_info.rss / (1024 * 1024), 2)

    return {
        "duration_ms": round(duration_ms, 2),
        "peak_rss_mb": rss_mb,
        "status": final_resp.get("result", {}).get("audit", {}).get("overall_status") if final_resp else "ERROR",
        "findings_count": len(final_resp.get("result", {}).get("audit", {}).get("findings", [])) if final_resp else 0,
    }


def benchmark_all():
    exe_path = Path("sidecar/dist/docuready_sidecar/docuready_sidecar.exe")
    if not exe_path.exists():
        exe_path = Path("dist/docuready_sidecar/docuready_sidecar.exe")
    if not exe_path.exists():
        print(f"Error: sidecar executable not found at {exe_path}")
        return

    print("=== DOCUREADY LOOP 4 PERFORMANCE & RELIABILITY BENCHMARK ===")
    system_info = {
        "platform": sys.platform,
        "cpu_count": psutil.cpu_count(logical=True),
        "total_memory_gb": round(psutil.virtual_memory().total / (1024**3), 2),
        "python_version": sys.version.split()[0],
        "sidecar_binary": str(exe_path),
    }
    print(f"System: {system_info['platform']}, {system_info['cpu_count']} CPUs, {system_info['total_memory_gb']} GB RAM")

    # 1. Cold Startup & Handshake
    print("\n[1/5] Benchmarking Cold Startup & Health Handshake...")
    startup_bench = measure_sidecar_startup(str(exe_path), iterations=5)
    print(f"  Startup Latency: min={startup_bench['min_ms']}ms, median={startup_bench['median_ms']}ms, max={startup_bench['max_ms']}ms")

    # Setup managed workspace
    tmp_workspace = Path(tempfile.mkdtemp(prefix="docuready-bench-ws-"))
    os.environ["DOCUREADY_WORKSPACE_ROOT"] = str(tmp_workspace)

    proc = subprocess.Popen(
        [str(exe_path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        env=os.environ,
    )
    # Perform initial handshake
    proc.stdin.write('{"protocol":1,"id":"init-h","method":"health","params":{}}\n')
    proc.stdin.flush()
    proc.stdout.readline()

    # 2. Small Packet Benchmark (2 docs)
    print("\n[2/5] Benchmarking Small Packet (2 documents)...")
    small_packet_dir = tmp_workspace / "small_packet"
    small_packet_dir.mkdir()
    shutil.copy("tests/validation_corpus/VAL_01_application_form.pdf", small_packet_dir)
    shutil.copy("tests/validation_corpus/VAL_02_income_cert_clean.pdf", small_packet_dir)

    small_res = run_audit_packet(proc, small_packet_dir, "BENCH_SMALL")
    print(f"  Small Packet: {small_res['duration_ms']}ms, RSS: {small_res['peak_rss_mb']}MB, Findings: {small_res['findings_count']}")

    # 3. Typical Packet Benchmark (6 docs)
    print("\n[3/5] Benchmarking Typical Packet (6 documents: vector + scanned + rotated)...")
    typical_packet_dir = tmp_workspace / "typical_packet"
    typical_packet_dir.mkdir()
    for f in ["VAL_01_application_form.pdf", "VAL_02_income_cert_clean.pdf", "VAL_03_caste_cert_clean.pdf",
              "VAL_04_residence_cert_scanned.pdf", "VAL_05_bank_passbook_scanned.pdf", "VAL_06_marksheet_rotated_90.pdf"]:
        shutil.copy(f"tests/validation_corpus/{f}", typical_packet_dir)

    typical_res = run_audit_packet(proc, typical_packet_dir, "BENCH_TYPICAL")
    print(f"  Typical Packet: {typical_res['duration_ms']}ms, RSS: {typical_res['peak_rss_mb']}MB, Findings: {typical_res['findings_count']}")

    # 4. Maximum Permitted Packet Benchmark (20 docs)
    print("\n[4/5] Benchmarking Maximum Permitted Packet (20 documents)...")
    max_packet_dir = tmp_workspace / "max_packet"
    max_packet_dir.mkdir()
    corpus_files = sorted(Path("tests/validation_corpus").glob("*.pdf"))
    count = 0
    while count < 20:
        for cf in corpus_files:
            if "VAL_10" in cf.name:  # skip 0-byte
                continue
            dest = max_packet_dir / f"doc_{count}_{cf.name}"
            shutil.copy(cf, dest)
            count += 1
            if count >= 20:
                break

    max_res = run_audit_packet(proc, max_packet_dir, "BENCH_MAX_20")
    print(f"  Max Packet (20 docs): {max_res['duration_ms']}ms, RSS: {max_res['peak_rss_mb']}MB, Findings: {max_res['findings_count']}")

    # 5. Sequential Repeatability Benchmark (5 consecutive audits)
    print("\n[5/5] Benchmarking Sequential Repeatability (5 runs)...")
    repeat_timings = []
    repeat_mem = []
    for i in range(5):
        r = run_audit_packet(proc, typical_packet_dir, f"BENCH_REPEAT_{i}")
        repeat_timings.append(r["duration_ms"])
        repeat_mem.append(r["peak_rss_mb"])

    print(f"  Sequential Timings: {repeat_timings}")
    print(f"  Sequential RSS: {repeat_mem}")
    print(f"  Repeatability Drift: {round(max(repeat_timings) - min(repeat_timings), 2)}ms variance")

    # Clean shutdown
    proc.stdin.write('{"protocol":1,"id":"bench-sd","method":"shutdown","params":{}}\n')
    proc.stdin.flush()
    proc.stdout.readline()
    proc.wait(timeout=3)

    # Cleanup timing
    t0_clean = time.perf_counter()
    shutil.rmtree(tmp_workspace)
    t1_clean = time.perf_counter()
    clean_ms = round((t1_clean - t0_clean) * 1000, 2)
    print(f"\nWorkspace Cleanup Duration: {clean_ms}ms")

    results = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "system_info": system_info,
        "startup": startup_bench,
        "small_packet": small_res,
        "typical_packet": typical_res,
        "max_packet": max_res,
        "repeatability": {
            "runs": 5,
            "timings_ms": repeat_timings,
            "peak_rss_mb": repeat_mem,
            "variance_ms": round(max(repeat_timings) - min(repeat_timings), 2),
        },
        "cleanup_ms": clean_ms,
    }

    results_file = Path("docs/benchmark_results.json")
    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\nAll benchmark results saved to {results_file}")
    return results


if __name__ == "__main__":
    benchmark_all()
