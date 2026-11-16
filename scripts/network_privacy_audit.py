"""
DocuReady Loop 6: Process-Level Network & Privacy Monitor.

Monitors the entire process tree of DocuReady (Installer, Electron Shell,
Chromium helper processes, Python sidecar, and OCR worker) during:
1. Installer execution (Squirrel Setup)
2. Application launch
3. Health check & sidecar handshake
4. Multi-document packet import
5. OCR execution on degraded scan (pkt_07_unreadable_doc)
6. Rule evaluation & audit scoring
7. Report export
8. Process termination & cleanup

Records every socket binding, listening port, and connection attempt.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Set

import psutil

REPO_ROOT = Path(__file__).resolve().parents[1]
LOG_DIR = REPO_ROOT / "docs" / "network_audit_logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
RAW_LOG_FILE = LOG_DIR / "network_audit_raw.log"
REPORT_DATA_FILE = LOG_DIR / "network_audit_summary.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(RAW_LOG_FILE, mode="w", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("NetworkAudit")


class ProcessNetworkMonitor:
    def __init__(self, root_pids: List[int], poll_interval: float = 0.05):
        self.root_pids = set(root_pids)
        self.poll_interval = poll_interval
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self.monitored_pids: Set[int] = set()
        self.detected_connections: List[Dict[str, Any]] = []
        self.samples_collected = 0

    def add_pid(self, pid: int) -> None:
        self.root_pids.add(pid)

    def start(self) -> None:
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info(f"Network monitor started for initial PIDs: {list(self.root_pids)}")

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2.0)
        logger.info(f"Network monitor stopped. Total samples collected: {self.samples_collected}")

    def _monitor_loop(self) -> None:
        while not self._stop_event.is_set():
            self.samples_collected += 1
            # Discover all descendants
            current_pids = set()
            for root_pid in list(self.root_pids):
                try:
                    if psutil.pid_exists(root_pid):
                        current_pids.add(root_pid)
                        parent = psutil.Process(root_pid)
                        for child in parent.children(recursive=True):
                            current_pids.add(child.pid)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            self.monitored_pids.update(current_pids)

            # Inspect connections for all known PIDs
            for pid in current_pids:
                try:
                    proc = psutil.Process(pid)
                    connections = proc.net_connections(kind="all")
                    for conn in connections:
                        record = {
                            "timestamp": time.time(),
                            "pid": pid,
                            "process_name": proc.name(),
                            "fd": conn.fd,
                            "family": str(conn.family),
                            "type": str(conn.type),
                            "laddr": f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None,
                            "raddr": f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                            "status": conn.status,
                        }
                        logger.warning(f"DETECTED NETWORK EVENT: {record}")
                        self.detected_connections.append(record)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

            time.sleep(self.poll_interval)


def audit_installer() -> Dict[str, Any]:
    installer_path = REPO_ROOT / "apps" / "desktop" / "out" / "make" / "squirrel.windows" / "x64" / "DocuReady-0.1.0-Setup.exe"
    if not installer_path.exists():
        logger.warning(f"Installer not found at {installer_path}")
        return {"status": "skipped", "reason": "installer_not_found"}

    logger.info("==================================================")
    logger.info("AUDITING STAGE 1: SQUIRREL INSTALLER NETWORK ACTIVITY")
    logger.info("==================================================")

    # Launch installer with --silent to avoid blocking GUI
    proc = subprocess.Popen([str(installer_path), "--silent"])
    monitor = ProcessNetworkMonitor([proc.pid])
    monitor.start()

    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        logger.info("Installer execution window reached; collecting child processes.")
        try:
            parent = psutil.Process(proc.pid)
            for child in parent.children(recursive=True):
                child.kill()
            parent.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    finally:
        monitor.stop()

    return {
        "stage": "installer",
        "pids_monitored": list(monitor.monitored_pids),
        "samples": monitor.samples_collected,
        "connections_detected": monitor.detected_connections,
        "exit_code": proc.returncode,
    }


def audit_runtime_workflow() -> Dict[str, Any]:
    app_exe = REPO_ROOT / "apps" / "desktop" / "out" / "DocuReady-win32-x64" / "DocuReady.exe"
    if not app_exe.exists():
        logger.error(f"Application executable not found at {app_exe}")
        return {"status": "error", "reason": "app_exe_not_found"}

    logger.info("==================================================")
    logger.info("AUDITING STAGE 2: APPLICATION RUNTIME & WORKFLOW")
    logger.info("==================================================")

    proc = subprocess.Popen([str(app_exe)])
    monitor = ProcessNetworkMonitor([proc.pid])
    monitor.start()

    time.sleep(3.0)  # Wait for Electron, Chromium renderers, GPU, and Sidecar to start

    # Discover and log all process names
    process_tree = []
    for pid in monitor.monitored_pids:
        try:
            p = psutil.Process(pid)
            process_tree.append({"pid": pid, "name": p.name(), "cmdline": p.cmdline()})
            logger.info(f"Monitored child process: PID {pid} ({p.name()})")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    # Audit the sidecar directly under same monitor to verify OCR + Audit pipeline
    logger.info("Stage 2.1: Executing Sidecar Direct JSON-RPC Audit under Network Monitor")
    sidecar_exe = (
        REPO_ROOT
        / "apps"
        / "desktop"
        / "out"
        / "DocuReady-win32-x64"
        / "resources"
        / "docuready_sidecar"
        / "docuready_sidecar.exe"
    )
    if not sidecar_exe.exists():
        # Fallback to sidecar/dist if unpacked location differs
        sidecar_exe = REPO_ROOT / "sidecar" / "dist" / "docuready_sidecar" / "docuready_sidecar.exe"

    sidecar_proc = None
    sidecar_pids = []
    if sidecar_exe.exists():
        logger.info(f"Spawning sidecar for full OCR + audit test: {sidecar_exe}")
        # Set DOCUREADY_WORKSPACE_ROOT for safe staging
        workspace_dir = REPO_ROOT / "temp_audit_workspace"
        workspace_dir.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        env["DOCUREADY_WORKSPACE_ROOT"] = str(workspace_dir)
        env["PYTHONUNBUFFERED"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"

        # Copy clean packet into workspace
        import shutil
        staged_clean = workspace_dir / "pkt_clean"
        if staged_clean.exists():
            shutil.rmtree(staged_clean)
        shutil.copytree(REPO_ROOT / "synthetic_data" / "pkt_01_clean", staged_clean)

        staged_ocr = workspace_dir / "pkt_ocr"
        if staged_ocr.exists():
            shutil.rmtree(staged_ocr)
        shutil.copytree(REPO_ROOT / "synthetic_data" / "pkt_07_unreadable_doc", staged_ocr)

        sidecar_proc = subprocess.Popen(
            [str(sidecar_exe)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=env
        )
        monitor.add_pid(sidecar_proc.pid)
        sidecar_pids.append(sidecar_proc.pid)

        # 1. Health check
        req_health = json.dumps({"protocol": 1, "id": "net-health", "method": "health", "params": {}}) + "\n"
        sidecar_proc.stdin.write(req_health)
        sidecar_proc.stdin.flush()
        line = sidecar_proc.stdout.readline()
        resp_health = json.loads(line) if line else {}
        logger.info(f"Sidecar health response: {resp_health.get('result', {}).get('status')}")

        # 2. Audit Clean Packet
        req_audit_clean = (
            json.dumps(
                {
                    "protocol": 1,
                    "id": "net-audit-clean",
                    "method": "audit_packet",
                    "params": {
                        "packet_dir": str(staged_clean),
                        "packet_id": "pkt_01_clean",
                        "as_of": "2026-03-31",
                    },
                }
            )
            + "\n"
        )
        sidecar_proc.stdin.write(req_audit_clean)
        sidecar_proc.stdin.flush()
        line = sidecar_proc.stdout.readline()
        resp_clean = json.loads(line) if line else {}
        logger.info(
            f"Clean audit readiness score: {resp_clean.get('result', {}).get('audit_result', {}).get('readiness_score')}"
        )

        # 3. Audit Degraded OCR Packet (forces Tesseract invocation)
        req_audit_ocr = (
            json.dumps(
                {
                    "protocol": 1,
                    "id": "net-audit-ocr",
                    "method": "audit_packet",
                    "params": {
                        "packet_dir": str(staged_ocr),
                        "packet_id": "pkt_07_unreadable_doc",
                        "as_of": "2026-03-31",
                    },
                }
            )
            + "\n"
        )
        sidecar_proc.stdin.write(req_audit_ocr)
        sidecar_proc.stdin.flush()
        line = sidecar_proc.stdout.readline()
        resp_ocr = json.loads(line) if line else {}
        logger.info(
            f"OCR audit status: {resp_ocr.get('result', {}).get('audit_result', {}).get('overall_status')}"
        )

        # 4. Shutdown sidecar
        req_shutdown = json.dumps({"protocol": 1, "id": "net-shutdown", "method": "shutdown", "params": {}}) + "\n"
        sidecar_proc.stdin.write(req_shutdown)
        sidecar_proc.stdin.flush()
        line = sidecar_proc.stdout.readline()
        logger.info(f"Sidecar shutdown response: {line.strip() if line else 'None'}")
        try:
            sidecar_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            sidecar_proc.kill()
            sidecar_proc.wait()

        # Cleanup temp workspace
        shutil.rmtree(workspace_dir, ignore_errors=True)

    # Capture the observed tree after the sidecar and OCR worker have run.
    # This remains polling, not ETW/WFP or packet capture.
    final_process_tree = []
    for pid in sorted(monitor.monitored_pids):
        try:
            observed = psutil.Process(pid)
            final_process_tree.append({
                "pid": pid,
                "ppid": observed.ppid(),
                "name": observed.name(),
                "exe": observed.exe(),
                "cmdline": observed.cmdline(),
                "create_time": observed.create_time(),
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            final_process_tree.append({"pid": pid, "unavailable": True})

    # Let runtime settle
    time.sleep(2.0)

    # Terminate main Electron process
    logger.info("Terminating application process tree.")
    try:
        parent = psutil.Process(proc.pid)
        for child in parent.children(recursive=True):
            child.kill()
        parent.kill()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass

    monitor.stop()

    return {
        "stage": "application_runtime_and_ocr",
        "pids_monitored": list(monitor.monitored_pids),
        "process_tree_initial": process_tree,
        "process_tree_final": final_process_tree,
        "samples": monitor.samples_collected,
        "connections_detected": monitor.detected_connections,
        "monitor_method": "psutil process socket polling at 50ms; not kernel event tracing",
        "coverage_limitations": [
            "short-lived sockets may occur between samples",
            "only the selected process tree is monitored",
            "this does not observe unrelated system services, DNS outside the tree, or all network transports",
        ],
    }


def main():
    logger.info("Starting Comprehensive Network & Privacy Audit for DocuReady Loop 6")
    installer_result = audit_installer()
    runtime_result = audit_runtime_workflow()

    total_connections = len(installer_result.get("connections_detected", [])) + len(
        runtime_result.get("connections_detected", [])
    )

    summary = {
        "audit_timestamp": time.time(),
        "total_connections_detected": total_connections,
        "installer_stage": installer_result,
        "runtime_stage": runtime_result,
        "verdict": (
            "NO_CONNECTIONS_OBSERVED_BY_50MS_PROCESS_SAMPLING"
            if total_connections == 0
            else "PROCESS_SOCKET_ACTIVITY_OBSERVED"
        ),
        "interpretation": (
            "A zero count means no sockets were visible to psutil during sampled process snapshots. "
            "It is not proof of zero egress, network isolation, or absence of short-lived connections."
        ),
        "monitor_method": "psutil process socket polling at 50ms; not ETW, WFP, or packet capture",
    }

    with open(REPORT_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    logger.info(f"Audit completed. Total connections detected: {total_connections}")
    logger.info(f"Summary saved to {REPORT_DATA_FILE}")


if __name__ == "__main__":
    main()
