"""
Command-Line Interface (CLI) for DocuReady
Usage:
    docuready audit <folder_path> [--json] [--export <path>]
    docuready benchmark
"""

import sys
import os
import json
import argparse
from pathlib import Path

from docuready.pipeline import AuditPipeline
from docuready.report.exporter import generate_readiness_summary_markdown, export_audit_report_json


def _resolve_synthetic_manifest() -> tuple[Path, Path]:
    """
    Locates the synthetic benchmark manifest and synthetic_data directory.
    Checks:
      1. Working directory (cwd / synthetic_data / ground_truth_manifest.json)
      2. Repository root (relative to installed module location)
      3. Working directory direct manifest (cwd / ground_truth_manifest.json)
    Returns (manifest_path, synthetic_data_dir).
    Raises FileNotFoundError if not found.
    """
    candidates = [
        Path.cwd() / "synthetic_data" / "ground_truth_manifest.json",
        Path(__file__).resolve().parents[3] / "synthetic_data" / "ground_truth_manifest.json",
        Path.cwd() / "ground_truth_manifest.json",
    ]
    for cand in candidates:
        if cand.is_file():
            synthetic_dir = cand.parent if cand.parent.name == "synthetic_data" else cand.parent / "synthetic_data"
            return cand, synthetic_dir

    searched_locations = "\n  - ".join(str(c) for c in candidates)
    raise FileNotFoundError(
        f"Synthetic demonstration dataset not found. Looked in:\n  - {searched_locations}\n"
        "Demonstration datasets are included in the source repository but omitted from standard distribution wheels."
    )


def main():
    parser = argparse.ArgumentParser(description="DocuReady CLI — Pre-Submission Document Readiness Linter")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Audit command
    audit_parser = subparsers.add_parser("audit", help="Audit a packet directory containing document PDFs")
    audit_parser.add_argument("packet_dir", help="Path to folder containing packet PDFs")
    audit_parser.add_argument("--json", action="store_true", help="Output JSON format")
    audit_parser.add_argument("--export", help="Export report to file path")

    # Benchmark command
    subparsers.add_parser("benchmark", help="Run benchmark across all synthetic test packets")

    args = parser.parse_args()
    pipeline = AuditPipeline()

    if args.command == "audit":
        packet_path = Path(args.packet_dir).resolve()
        if not packet_path.exists() or not packet_path.is_dir():
            print(f"Error: Directory '{args.packet_dir}' not found.", file=sys.stderr)
            sys.exit(1)

        result, docs = pipeline.load_and_audit_packet(str(packet_path))

        if args.json:
            print(json.dumps(result.model_dump(), indent=2))
        else:
            print(generate_readiness_summary_markdown(result))

        if args.export:
            export_path = Path(args.export).resolve()
            if str(export_path).endswith(".json"):
                export_audit_report_json(result, str(export_path))
                print(f"\n[Report saved to {export_path}]")
            else:
                with open(export_path, "w", encoding="utf-8") as f:
                    f.write(generate_readiness_summary_markdown(result))
                print(f"\n[Report saved to {export_path}]")

    elif args.command == "benchmark":
        try:
            manifest_path, synthetic_dir = _resolve_synthetic_manifest()
        except FileNotFoundError as err:
            print(f"Error: {err}", file=sys.stderr)
            sys.exit(1)

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        print("=" * 80)
        print("DOCUREADY SYNTHETIC BENCHMARK EVALUATION")
        print("=" * 80)
        print(f"{'Packet ID':<28} | {'Predicted':<18} | {'Expected':<18} | {'Score':<6} | {'Latency'}")
        print("-" * 80)

        correct = 0
        latencies = []
        for pid, pdata in manifest["packets"].items():
            packet_path = synthetic_dir / pdata["folder"]
            res, _ = pipeline.load_and_audit_packet(str(packet_path), packet_id=pid)
            latencies.append(res.execution_time_ms)
            is_match = (res.overall_status == pdata["expected_status"])
            if is_match:
                correct += 1
            status_symbol = "✓" if is_match else "✗"
            print(f"{pid:<28} | {res.overall_status:<18} | {pdata['expected_status']:<18} | {res.readiness_score:<6} | {res.execution_time_ms:>6.2f} ms {status_symbol}")

        print("=" * 80)
        total = len(manifest["packets"])
        acc = (correct / total) * 100
        avg_lat = sum(latencies) / len(latencies) if latencies else 0.0
        min_lat = min(latencies) if latencies else 0.0
        max_lat = max(latencies) if latencies else 0.0
        print(f"Summary: {correct}/{total} Packets Matched Ground Truth ({acc:.1f}% Accuracy)")
        print(f"Latency: Mean {avg_lat:.2f} ms | Min {min_lat:.2f} ms | Max {max_lat:.2f} ms")
        print("=" * 80)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
