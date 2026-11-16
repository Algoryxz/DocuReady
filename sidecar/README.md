# Python sidecar

The sidecar is the local process boundary between Electron main and the existing DocuReady Python package. It does not implement audit rules; it calls `AuditPipeline`.

## Protocol v1

One JSON object per input line; one JSON object per response line. Progress events may appear between request and response frames. Standard output is protocol-only; diagnostics go to standard error.

Supported methods:

- `health`
- `audit_packet` with `packet_dir`, `packet_id`, and explicit ISO `as_of`

The caller must set `DOCUREADY_WORKSPACE_ROOT`. The supplied packet directory must resolve to a directory contained inside that root. Electron main is intended to create and own this workspace; renderer code must never supply arbitrary paths.

The audit response contains a redacted `AuditResult.to_public_dict(canonical=True)` projection and document metadata (document type, page count, extraction method, field keys, evidence states, and provenance coordinates). Raw extracted field values are not included in the document summary.

## Local development

```bash
export DOCUREADY_WORKSPACE_ROOT=/absolute/path/to/private-workspace
python sidecar/docuready_sidecar.py
```

Example health request:

```json
{"protocol":1,"id":"health-1","method":"health","params":{}}
```

## Not implemented yet

Cancellation, streaming extraction progress, concurrent jobs, persistent packet history, packaged Python/Tesseract binaries, and a desktop process manager. The current audit method emits coarse job progress around the synchronous pipeline call.
