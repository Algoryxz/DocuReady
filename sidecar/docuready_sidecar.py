"""DocuReady desktop sidecar: versioned JSON Lines protocol over stdio.

Stdout is reserved exclusively for protocol frames. Diagnostics are written to stderr.
The Electron main process is the only intended client.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import date
from pathlib import Path
from typing import Any

PROTOCOL_VERSION = 1
MAX_REQUEST_BYTES = 1_048_576
MAX_PACKET_DOCUMENTS = 20
MAX_FILE_BYTES = 52_428_800  # 50MB
MAX_PAGE_COUNT_PER_DOC = 50

# Ensure stdin/stdout/stderr are UTF-8 across all operating systems and binary hooks
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
if hasattr(sys.stdin, "reconfigure"):
    try:
        sys.stdin.reconfigure(encoding="utf-8")
    except Exception:
        pass


def _write_frame(payload: dict[str, Any]) -> None:
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n"
    try:
        sys.stdout.write(data)
    except UnicodeEncodeError:
        if hasattr(sys.stdout, "buffer"):
            sys.stdout.buffer.write(data.encode("utf-8"))
            sys.stdout.buffer.flush()
            return
        raise
    sys.stdout.flush()


def _workspace_path(raw_path: Any) -> Path:
    if not isinstance(raw_path, str) or not raw_path:
        raise ValueError("A staged packet directory is required.")

    root_value = os.environ.get("DOCUREADY_WORKSPACE_ROOT")
    if not root_value:
        raise RuntimeError("The desktop workspace root was not configured.")

    root = Path(root_value).resolve(strict=True)
    candidate = Path(raw_path).resolve(strict=True)
    if candidate == root or not candidate.is_dir() or not candidate.is_relative_to(root):
        raise ValueError("The packet directory is outside the managed workspace.")
    return candidate


def _document_summaries(extracted_docs: dict[Any, Any]) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []
    for doc in extracted_docs.values():
        fields: list[dict[str, Any]] = []
        for field in doc.fields.values():
            provenance = field.provenance
            fields.append(
                {
                    "field": field.field_name,
                    "evidence_state": (
                        field.evidence_state.value
                        if hasattr(field.evidence_state, "value")
                        else str(field.evidence_state)
                    ),
                    "page": provenance.page_number if provenance else None,
                    "bounding_box": (
                        list(provenance.bounding_box)
                        if provenance and provenance.bounding_box
                        else None
                    ),
                    "extraction_method": field.extraction_method,
                }
            )
        summaries.append(
            {
                "document_type": doc.doc_type.value if hasattr(doc.doc_type, "value") else str(doc.doc_type),
                "page_count": doc.page_count,
                "extraction_method": doc.extraction_method,
                "fields": fields,
            }
        )
    return summaries


def _get_ocr_availability() -> bool:
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def _handle(request: dict[str, Any]) -> dict[str, Any]:
    from docuready import __version__ as engine_version
    from docuready.pipeline import AuditPipeline
    from docuready.report.redact import redact_audit_result_dict

    request_id = request.get("id")
    method = request.get("method")
    params = request.get("params", {})

    if not isinstance(request_id, str) or not request_id or len(request_id) > 128:
        raise ValueError("Request id must be a non-empty string of at most 128 characters.")
    if request.get("protocol") != PROTOCOL_VERSION:
        raise ValueError("Unsupported protocol version.")
    if not isinstance(params, dict):
        raise ValueError("Request params must be an object.")

    if method == "health":
        from docuready.ingest.tesseract_discovery import get_ocr_runtime_info
        ocr_info = get_ocr_runtime_info()
        pdf_backend = os.environ.get("DOCUREADY_PDF_BACKEND", "pymupdf").lower()
        return {
            "protocol": PROTOCOL_VERSION,
            "id": request_id,
            "ok": True,
            "result": {
                "sidecar": "docuready-python",
                "protocol": PROTOCOL_VERSION,
                "engine_version": engine_version,
                "python": ".".join(map(str, sys.version_info[:3])),
                "pdf_backend": pdf_backend,
                "ocr_available": ocr_info["available"],
                "ocr_languages": ocr_info.get("languages", ["eng"]),
                "ocr_source": ocr_info.get("source", "none"),
                "is_bundled": ocr_info.get("is_bundled", False),
                "tesseract_version": ocr_info.get("version"),
                "tesseract_path": ocr_info.get("binary_path"),
            },
        }

    if method == "shutdown":
        return {
            "protocol": PROTOCOL_VERSION,
            "id": request_id,
            "ok": True,
            "result": {
                "status": "shutting_down",
            },
        }

    if method == "audit_packet":
        packet_dir = _workspace_path(params.get("packet_dir"))
        packet_id = params.get("packet_id", "DESKTOP_PACKET")
        if not isinstance(packet_id, str) or not packet_id or len(packet_id) > 128:
            raise ValueError("Packet id must be a non-empty string of at most 128 characters.")

        as_of_value = params.get("as_of")
        if not isinstance(as_of_value, str) or not as_of_value:
            raise ValueError("An explicit ISO date is required for deterministic audits.")
        effective_date = date.fromisoformat(as_of_value)

        # Enforce packet document limits
        doc_files = [p for p in packet_dir.iterdir() if p.is_file() and not p.name.startswith(".")]
        if len(doc_files) > MAX_PACKET_DOCUMENTS:
            raise ValueError(f"Packet document count ({len(doc_files)}) exceeds maximum limit of {MAX_PACKET_DOCUMENTS}.")

        for doc_file in doc_files:
            file_size = doc_file.stat().st_size
            if file_size > MAX_FILE_BYTES:
                raise ValueError(f"Document '{doc_file.name}' exceeds maximum file size limit of 50MB.")
            if file_size == 0:
                raise ValueError(f"Document '{doc_file.name}' is empty (0 bytes).")

        # Stage 1: Intake
        _write_frame(
            {
                "protocol": PROTOCOL_VERSION,
                "event": "progress",
                "job_id": request_id,
                "stage": "intake",
                "completed": 1,
                "total": 5,
            }
        )

        pipeline = AuditPipeline(as_of=effective_date)

        # Stage 2: Extraction
        _write_frame(
            {
                "protocol": PROTOCOL_VERSION,
                "event": "progress",
                "job_id": request_id,
                "stage": "extraction",
                "completed": 2,
                "total": 5,
            }
        )

        result, extracted_docs = pipeline.load_and_audit_packet(
            str(packet_dir),
            packet_id=packet_id,
            as_of=effective_date,
        )

        # Stage 3: Validation
        _write_frame(
            {
                "protocol": PROTOCOL_VERSION,
                "event": "progress",
                "job_id": request_id,
                "stage": "validation",
                "completed": 3,
                "total": 5,
            }
        )

        # Stage 4: Redaction & Canonical Formatting
        public_result = redact_audit_result_dict(result.to_public_dict(canonical=True))
        doc_summaries = _document_summaries(extracted_docs)

        _write_frame(
            {
                "protocol": PROTOCOL_VERSION,
                "event": "progress",
                "job_id": request_id,
                "stage": "completed",
                "completed": 5,
                "total": 5,
            }
        )
        return {
            "protocol": PROTOCOL_VERSION,
            "id": request_id,
            "ok": True,
            "result": {
                "audit": public_result,
                "documents": doc_summaries,
            },
        }

    raise ValueError("Unsupported sidecar method.")


def main() -> int:
    for raw_line in sys.stdin.buffer:
        request: Any = None
        if len(raw_line) > MAX_REQUEST_BYTES:
            _write_frame(
                {
                    "protocol": PROTOCOL_VERSION,
                    "id": None,
                    "ok": False,
                    "error": {
                        "code": "REQUEST_TOO_LARGE",
                        "message": "Request exceeded the protocol size limit.",
                    },
                }
            )
            continue

        try:
            line_str = raw_line.decode("utf-8")
        except UnicodeDecodeError:
            _write_frame(
                {
                    "protocol": PROTOCOL_VERSION,
                    "id": None,
                    "ok": False,
                    "error": {
                        "code": "INVALID_ENCODING",
                        "message": "Protocol requests must be valid UTF-8.",
                    },
                }
            )
            continue

        try:
            request = json.loads(line_str)
            if not isinstance(request, dict):
                raise ValueError("Request frame must be a JSON object.")
            response = _handle(request)
            _write_frame(response)
            if request.get("method") == "shutdown":
                return 0
        except Exception as exc:  # protocol boundary: never leak raw exception text to renderer
            exc_name = type(exc).__name__
            exc_msg = str(exc)
            print(
                f"sidecar request failed ({exc_name}): {exc_msg}",
                file=sys.stderr,
                flush=True,
            )
            request_id = request.get("id") if isinstance(request, dict) else None

            # Map to structured error code
            code = "REQUEST_FAILED"
            if "protocol version" in exc_msg.lower():
                code = "INVALID_PROTOCOL_VERSION"
            elif "outside the managed workspace" in exc_msg.lower() or "workspace root" in exc_msg.lower():
                code = "WORKSPACE_VIOLATION"
            elif "unsupported sidecar method" in exc_msg.lower():
                code = "UNSUPPORTED_METHOD"
            elif "request frame must be a json object" in exc_msg.lower() or "request id" in exc_msg.lower():
                code = "INVALID_REQUEST"

            _write_frame(
                {
                    "protocol": PROTOCOL_VERSION,
                    "id": request_id,
                    "ok": False,
                    "error": {
                        "code": code,
                        "message": "The requested operation could not be completed.",
                    },
                }
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
