#!/usr/bin/env python3
"""Reproducible benchmark and comparison script for PDF ingestion backends (ADR-001 / T1.3).

Compares extraction latency, memory usage, and coordinate consistency across available
PDF backends (PyMuPDF vs. pypdfium2) on DocuReady synthetic corpora.

Usage:
    python scripts/evaluate_pdf_backends.py
    python scripts/evaluate_pdf_backends.py --corpus synthetic_data/pkt_01_clean
    python scripts/evaluate_pdf_backends.py --json
"""

import argparse
import json
import os
from pathlib import Path
import sys
import time
import tracemalloc
from typing import Any, Dict, List, Optional

# Add src directory to sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from docuready.ingest.pdf_backend import get_pdf_backend, PyMuPDFDocumentBackend
try:
    from docuready.ingest.pdf_backend.pdfium_backend import PdfiumDocumentBackend, _PYPDFIUM2_AVAILABLE
except Exception:
    _PYPDFIUM2_AVAILABLE = False


def discover_pdf_files(target_dir: Path) -> List[Path]:
    """Finds all PDF files recursively within the specified path."""
    if target_dir.is_file() and target_dir.suffix.lower() == ".pdf":
        return [target_dir]
    return sorted(list(target_dir.rglob("*.pdf")))


def evaluate_backend_on_files(
    backend_name: str,
    pdf_files: List[Path]
) -> Dict[str, Any]:
    """Evaluates extraction speed, text yield, and memory for a given backend."""
    tracemalloc.start()
    start_time = time.perf_counter()
    
    total_pages = 0
    total_chars = 0
    errors = 0
    
    for pdf_path in pdf_files:
        try:
            with get_pdf_backend(str(pdf_path), backend_name=backend_name) as doc:
                total_pages += doc.page_count
                for page in doc:
                    text = page.get_text()
                    total_chars += len(text)
        except Exception as e:
            errors += 1

    elapsed = time.perf_counter() - start_time
    _, peak_memory = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    num_files = len(pdf_files)
    mean_latency_ms = (elapsed / num_files * 1000.0) if num_files > 0 else 0.0

    return {
        "backend": backend_name,
        "files_evaluated": num_files,
        "total_pages": total_pages,
        "total_chars_extracted": total_chars,
        "errors": errors,
        "elapsed_seconds": round(elapsed, 4),
        "mean_latency_per_doc_ms": round(mean_latency_ms, 2),
        "peak_memory_kb": round(peak_memory / 1024, 2),
    }


def main():
    parser = argparse.ArgumentParser(description="Evaluate and compare PDF ingestion backends.")
    parser.add_argument(
        "--corpus",
        type=str,
        default="synthetic_data",
        help="Path to directory containing PDF files to evaluate."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON."
    )
    args = parser.parse_args()

    corpus_path = REPO_ROOT / args.corpus
    if not corpus_path.exists():
        print(f"Error: Corpus path '{corpus_path}' does not exist.", file=sys.stderr)
        sys.exit(1)

    pdf_files = discover_pdf_files(corpus_path)
    if not pdf_files:
        print(f"No PDF files found in '{corpus_path}'.", file=sys.stderr)
        sys.exit(1)

    results: Dict[str, Any] = {
        "corpus_path": str(corpus_path.relative_to(REPO_ROOT)),
        "pdf_count": len(pdf_files),
        "backends": {}
    }

    # Evaluate PyMuPDF (Default)
    pymupdf_res = evaluate_backend_on_files("pymupdf", pdf_files)
    results["backends"]["pymupdf"] = pymupdf_res

    # Evaluate PDFium if available
    if _PYPDFIUM2_AVAILABLE:
        pdfium_res = evaluate_backend_on_files("pdfium", pdf_files)
        results["backends"]["pdfium"] = pdfium_res
    else:
        results["backends"]["pdfium"] = {
            "status": "unavailable",
            "reason": "pypdfium2 is not installed in the environment."
        }

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print("=" * 70)
        print("DocuReady PDF Backend Evaluation Report (T1.3 / ADR-001)")
        print("=" * 70)
        print(f"Corpus: {results['corpus_path']} ({results['pdf_count']} PDF documents)")
        print("-" * 70)
        for b_name, b_data in results["backends"].items():
            if b_data.get("status") == "unavailable":
                print(f"[{b_name.upper()}] Status: Unavailable ({b_data.get('reason')})")
            else:
                print(f"[{b_name.upper()}]")
                print(f"  Total Pages:            {b_data['total_pages']}")
                print(f"  Total Characters:       {b_data['total_chars_extracted']}")
                print(f"  Total Duration:         {b_data['elapsed_seconds']} s")
                print(f"  Mean Latency / Doc:     {b_data['mean_latency_per_doc_ms']} ms")
                print(f"  Peak Memory:            {b_data['peak_memory_kb']} KB")
                print(f"  Errors:                 {b_data['errors']}")
            print("-" * 70)


if __name__ == "__main__":
    main()
