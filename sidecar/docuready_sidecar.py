"""DocuReady desktop sidecar: versioned JSON Lines protocol over stdio.

Stdout is reserved for protocol frames. Diagnostics are written to stderr.
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


def _write_frame(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
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
                "document_type": doc.doc_type.value,
                "page_count": doc.page_count,
                "extraction_method": doc.extraction_method,
                "fields": fields,
            }
        )
    return summaries


def _handle(request: dict[str, Any]) -> dict[str, Any]:
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
        return {
            "protocol": PROTOCOL_VERSION,
            "id": request_id,
            "ok": True,
            "result": {
                "sidecar": "docuready-python",
                "protocol": PROTOCOL_VERSION,
                "python": ".".join(map(str, sys.version_info[:3])),
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

        _write_frame(
            {
                "protocol": PROTOCOL_VERSION,
                "event": "progress",
                "job_id": request_id,
                "stage": "audit",
                "completed": 0,
                "total": 1,
            }
        )

        pipeline = AuditPipeline(as_of=effective_date)
        result, extracted_docs = pipeline.load_and_audit_packet(
            str(packet_dir),
            packet_id=packet_id,
            as_of=effective_date,
        )
        public_result = redact_audit_result_dict(result.to_public_dict(canonical=True))

        _write_frame(
            {
                "protocol": PROTOCOL_VERSION,
                "event": "progress",
                "job_id": request_id,
                "stage": "audit",
                "completed": 1,
                "total": 1,
            }
        )
        return {
            "protocol": PROTOCOL_VERSION,
            "id": request_id,
            "ok": True,
            "result": {
                "audit": public_result,
                "documents": _document_summaries(extracted_docs),
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
            request = json.loads(raw_line)
            if not isinstance(request, dict):
                raise ValueError("Request frame must be a JSON object.")
            response = _handle(request)
            _write_frame(response)
        except Exception as exc:  # protocol boundary: never leak raw exception text to renderer
            print(
                f"sidecar request failed ({type(exc).__name__})",
                file=sys.stderr,
                flush=True,
            )
            request_id = None
            request_id = request.get("id") if isinstance(request, dict) else None
            _write_frame(
                {
                    "protocol": PROTOCOL_VERSION,
                    "id": request_id,
                    "ok": False,
                    "error": {
                        "code": "REQUEST_FAILED",
                        "message": "The requested operation could not be completed.",
                    },
                }
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
