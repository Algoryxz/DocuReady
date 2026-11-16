"""
Command-Line Interface (CLI) for DocuReady
Usage:
    docuready audit <folder_path> [--json] [--export <path>]
    docuready benchmark
    docuready packs lint [<pack_path>] [--allow-draft]
"""

import sys
import os
import json
import argparse
from pathlib import Path

from docuready.domain.enums import ExitCode
from docuready.outcome.resolver import exit_code_for_readiness
from docuready.report.exporter import generate_readiness_summary_markdown, export_audit_report_json
from docuready.rules.lint import lint_all_packs


class DocuReadyArgumentParser(argparse.ArgumentParser):
    """Argument parser using the documented CLI usage-error exit code."""

    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(int(ExitCode.USAGE_ERROR), f"{self.prog}: error: {message}\n")


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


def _handle_packs_lint(args, parser: argparse.ArgumentParser) -> None:
    """Handle 'docuready packs lint' command without instantiating AuditPipeline."""
    if args.pack_path:
        target_path = Path(args.pack_path).resolve()
    else:
        # Default to ./packs in cwd or relative to repository root
        candidates = [
            Path.cwd() / "packs",
            Path(__file__).resolve().parents[3] / "packs",
        ]
        target_path = None
        for cand in candidates:
            if cand.is_dir():
                target_path = cand
                break
        if target_path is None:
            print("Error: No scheme packs directory found (searched ./packs).", file=sys.stderr)
            sys.exit(int(ExitCode.USAGE_ERROR))

    if not target_path.exists():
        print(f"Error: Path '{args.pack_path}' not found.", file=sys.stderr)
        sys.exit(int(ExitCode.USAGE_ERROR))

    results = lint_all_packs(target_path, allow_draft=args.allow_draft)

    if not results:
        print(f"Error: No scheme packs found at '{target_path}'.", file=sys.stderr)
        sys.exit(int(ExitCode.USAGE_ERROR))

    total_errors = 0
    total_warnings = 0

    print("=" * 80)
    print("DOCUREADY SCHEME PACK LINTER")
    print("=" * 80)

    for res in results:
        pack_name = res.pack_id or res.pack_dir.name
        n_err = len(res.errors)
        n_warn = len(res.warnings)
        total_errors += n_err
        total_warnings += n_warn

        if res.is_valid:
            print(f"✓ [PASS] Pack '{pack_name}' ({res.pack_dir}) — 0 errors, {n_warn} warning(s)")
        else:
            print(f"✗ [FAIL] Pack '{pack_name}' ({res.pack_dir}) — {n_err} error(s), {n_warn} warning(s)")

        for err in res.errors:
            print(f"    ERROR: {err}")
        for warn in res.warnings:
            print(f"    WARNING: {warn}")

    print("=" * 80)
    print(f"Summary: {len(results)} pack(s) inspected, {total_errors} error(s), {total_warnings} warning(s)")
    print("=" * 80)

    if total_errors > 0:
        sys.exit(int(ExitCode.NEEDS_CHECKS))
    sys.exit(int(ExitCode.NO_ISSUES))


def main():
    parser = DocuReadyArgumentParser(description="DocuReady CLI — Document Consistency Linter")
    subparsers = parser.add_subparsers(dest="command", help="Commands", parser_class=DocuReadyArgumentParser)

    # Audit command
    audit_parser = subparsers.add_parser("audit", help="Audit a packet directory containing document PDFs")
    audit_parser.add_argument("packet_dir", help="Path to folder containing packet PDFs")
    audit_parser.add_argument("--json", action="store_true", help="Output JSON format")
    audit_parser.add_argument("--export", help="Export report to file path")
    audit_parser.add_argument(
        "--no-redact",
        action="store_true",
        help="Disable default redaction (requires explicit flag; emits privacy warning)",
    )

    # Benchmark command
    subparsers.add_parser("benchmark", help="Run benchmark across all synthetic test packets")

    # Packs command (T3.1)
    packs_parser = subparsers.add_parser("packs", help="Scheme pack management and verification")
    packs_subparsers = packs_parser.add_subparsers(dest="packs_command", help="Pack subcommands", parser_class=DocuReadyArgumentParser)

    lint_parser = packs_subparsers.add_parser("lint", help="Lint scheme pack manifests and citation sources")
    lint_parser.add_argument(
        "pack_path",
        nargs="?",
        default=None,
        help="Path to specific scheme pack folder or root packs directory (defaults to ./packs)",
    )
    lint_parser.add_argument(
        "--allow-draft",
        action="store_true",
        help="Allow packs in 'draft' status without failing the lint",
    )

    args = parser.parse_args()

    if args.command == "packs":
        if args.packs_command == "lint":
            _handle_packs_lint(args, packs_parser)
        else:
            packs_parser.print_help()
            sys.exit(int(ExitCode.USAGE_ERROR))
    elif args.command == "audit":
        from docuready.pipeline import AuditPipeline

        pipeline = AuditPipeline()
        packet_path = Path(args.packet_dir).resolve()
        if not packet_path.exists() or not packet_path.is_dir():
            print(f"Error: Directory '{args.packet_dir}' not found.", file=sys.stderr)
            sys.exit(int(ExitCode.USAGE_ERROR))

        redact = not args.no_redact
        if args.no_redact:
            print(
                "WARNING: --no-redact specified. Output reports will contain unmasked sensitive identifier data.",
                file=sys.stderr,
            )

        result, docs = pipeline.load_and_audit_packet(str(packet_path))

        if args.json:
            out_data = result.to_public_dict()
            if redact:
                from docuready.report.redact import redact_audit_result_dict

                out_data = redact_audit_result_dict(out_data)
            print(json.dumps(out_data, indent=2))
        else:
            print(generate_readiness_summary_markdown(result, redact=redact))

        if args.export:
            export_path = Path(args.export).resolve()
            if str(export_path).endswith(".json"):
                export_audit_report_json(result, str(export_path), redact=redact)
                print(f"\n[Report saved to {export_path}]")
            else:
                with open(export_path, "w", encoding="utf-8") as f:
                    f.write(generate_readiness_summary_markdown(result, redact=redact))
                print(f"\n[Report saved to {export_path}]")

        raise SystemExit(int(exit_code_for_readiness(result.readiness)))
    elif args.command == "benchmark":
        from docuready.pipeline import AuditPipeline

        pipeline = AuditPipeline()
        try:
            manifest_path, synthetic_dir = _resolve_synthetic_manifest()
        except FileNotFoundError as err:
            print(f"Error: {err}", file=sys.stderr)
            sys.exit(int(ExitCode.USAGE_ERROR))

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
            legacy_to_v2 = {
                "READY_TO_SUBMIT": "NO_ISSUES_FOUND",
                "REVIEW_RECOMMENDED": "NEEDS_CHECKS",
                "ACTION_REQUIRED": "NOT_READY",
                "REJECT_PRECHECK": "NOT_READY",
                "UNREADABLE_PACKET": "NEEDS_CHECKS",
            }
            expected_readiness = legacy_to_v2.get(pdata["expected_status"], "NEEDS_CHECKS")
            is_match = (res.readiness.value == expected_readiness)
            if is_match:
                correct += 1
            status_symbol = "✓" if is_match else "✗"
            print(f"{pid:<28} | {res.readiness.value:<18} | {expected_readiness:<18} | {res.readiness_score:<6} | {res.execution_time_ms:>6.2f} ms {status_symbol}")

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
        raise SystemExit(int(ExitCode.USAGE_ERROR))


if __name__ == "__main__":
    main()
