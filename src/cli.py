"""
Command-Line Interface (CLI) for DocuReady MVP
Usage:
    python docuready-mvp/src/cli.py audit <folder_path>
    python docuready-mvp/src/cli.py benchmark
"""

import sys
import os
import json
import argparse
from src.pipeline import AuditPipeline
from src.report_exporter import generate_readiness_summary_markdown, export_audit_report_json


def main():
    parser = argparse.ArgumentParser(description="DocuReady CLI — Pre-Submission Document Readiness Linter")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Audit command
    audit_parser = subparsers.add_parser("audit", help="Audit a packet directory containing document PDFs")
    audit_parser.add_argument("packet_dir", help="Path to folder containing packet PDFs")
    audit_parser.add_argument("--json", action="store_true", help="Output JSON format")
    audit_parser.add_argument("--export", help="Export report to file path")

    # Benchmark command
    bench_parser = subparsers.add_parser("benchmark", help="Run benchmark across all synthetic test packets")

    args = parser.parse_args()
    pipeline = AuditPipeline()

    if args.command == "audit":
        if not os.path.exists(args.packet_dir):
            print(f"Error: Directory '{args.packet_dir}' not found.")
            sys.exit(1)

        result, docs = pipeline.load_and_audit_packet(args.packet_dir)

        if args.json:
            print(json.dumps(result.model_dump(), indent=2))
        else:
            print(generate_readiness_summary_markdown(result))

        if args.export:
            if args.export.endswith(".json"):
                export_audit_report_json(result, args.export)
                print(f"\n[Report saved to {args.export}]")
            else:
                with open(args.export, "w", encoding="utf-8") as f:
                    f.write(generate_readiness_summary_markdown(result))
                print(f"\n[Report saved to {args.export}]")

    elif args.command == "benchmark":
        manifest_path = "docuready-mvp/ground_truth_manifest.json"
        if not os.path.exists(manifest_path):
            print(f"Error: Manifest '{manifest_path}' not found.")
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
            packet_path = os.path.join("docuready-mvp/synthetic_data", pdata["folder"])
            res, _ = pipeline.load_and_audit_packet(packet_path, packet_id=pid)
            latencies.append(res.execution_time_ms)
            is_match = (res.overall_status == pdata["expected_status"])
            if is_match:
                correct += 1
            status_symbol = "✓" if is_match else "✗"
            print(f"{pid:<28} | {res.overall_status:<18} | {pdata['expected_status']:<18} | {res.readiness_score:<6} | {res.execution_time_ms:>6.2f} ms {status_symbol}")

        print("=" * 80)
        total = len(manifest["packets"])
        acc = (correct / total) * 100
        avg_lat = sum(latencies) / len(latencies)
        print(f"Summary: {correct}/{total} Packets Matched Ground Truth ({acc:.1f}% Accuracy)")
        print(f"Latency: Mean {avg_lat:.2f} ms | Min {min(latencies):.2f} ms | Max {max(latencies):.2f} ms")
        print("=" * 80)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
