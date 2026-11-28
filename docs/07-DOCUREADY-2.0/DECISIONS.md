# DocuReady 2.0 — Decisions, Rejected Ideas & Open Questions

## 1. Accepted Decisions

| ID | Decision | Rationale |
|---|---|---|
| **D-001** | **Electron 45 + React 19 + Python Sidecar is the canonical desktop product** (`ADR-002-desktop-runtime-and-sidecar.md`). | `ADR-002-deployment-architecture.md` (Streamlit 3-tier) is superseded for the desktop product. `site/` remains a static informational showcase only. |
| **D-002** | **Session-only human review annotations never alter engine verdicts.** | Preserves deterministic audit integrity and conservative abstention (`PASS`/`FAIL`/`REVIEW` come solely from the engine + `DecisionSafetyLayer`). |
| **D-003** | **No persistent citizen document history in 2.0.** | Prevents unencrypted PII retention on disk without a dedicated retention, encryption, and deletion architecture. |
| **D-004** | **Honest local-processing claims only.** | Replace `"100% Offline · Local Workspace"` in `main.tsx:486` with `"Local Processing · Ephemeral Workspace"` to align with `PRIVACY_NETWORK_AUDIT.md` §7. |
| **D-005** | **GitHub-hosted Actions only (`ubuntu-24.04`, `windows-2022`).** | Self-hosted runners are prohibited; PR #94 (`fix/ci-verification-stabilisation`) is merged in `main` (`b66b82b`); CI/CD and Windows release pipeline ownership remains with Deepti. |

---

## 2. Rejected Ideas (24-Hour Scope)

- **Cloud OCR / cloud document storage:** Violates offline-first privacy boundary.
- **DigiLocker / WhatsApp / live portal APIs / Flutter mobile app:** Out of scope for 24h vertical slice.
- **Automatic fraud/authenticity verdicts or AI eligibility prediction:** Violates product safety boundaries (`CLAIMS_REGISTER.md`).
- **Replacing PyMuPDF with PDFium in 24h:** `PdfiumPageBackend.get_words()` is unimplemented (`NotImplementedError`); high risk of breaking bbox parity.

---

## 3. Unresolved Questions & Blockers

1. **AGPLv3 Distribution Clearance (`LICENSING_DECISION.md` §5):** `pymupdf==2.1` is AGPLv3 and remains `OPEN` for commercial/public binary distribution legal review.
2. **Windows Qualification Completion (Resolved for PRs #94, #96, #97, #98):** `Windows desktop release qualification` passed on PR #94 (`46140310782`), PR #96 (`46142328708`), PR #97 (`46143717198`), and PR #98 (`46147105057`). Any new code PR must still pass its own qualification run.
3. **`odisha.subhadra` `ration_card` slot (`packs/odisha.subhadra/pack.yaml:48`):** `DocumentType` lacks `RATION_CARD` — Akriti/Susmita must decide whether to add `RATION_CARD` or mark that slot optional/unmapped in 2.0.
4. **Image Bounding-Box Coordinate Space:** Verify whether Python image ingestion emits pixel coordinates or 72-DPI PDF points so `EvidenceViewer.tsx:339-346` aligns overlays accurately on PNG/JPEG.
