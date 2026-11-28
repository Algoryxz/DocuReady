# DocuReady — Team Workstreams, Ownership & Collaboration Rules

**Goal:** Deliver a reliable, tested, installable Windows `.exe` application (`DocuReady-Setup.exe` and `DocuReady-Portable.zip`) with clear documentation and an accessible public download experience at `https://docu-ready-steel.vercel.app/#workflow`.

---

## 1. Team Ownership

| Contributor | Role / Scope | Branch (Preserve existing PR/branch if open) | Key Responsibilities |
|---|---|---|---|
| **Akriti** | **PR #95, Testing & Quality** | `feat/pr95-akriti` (or existing PR #95 branch) | Complete PR #95 scope; coordinate changes with relevant feature owners; expand automated test coverage; run post-integration regressions; improve benchmark scores via reproducible experiments; maintain before/after score comparisons; document failures, fixes, and test evidence; avoid modifying another owner's implementation without coordination. |
| **Susmita** | **Backend** | `feat/backend-susmita` | Own backend (`src/docuready/**`, `sidecar/docuready_sidecar.py`, `packs/**`) and document-intelligence implementation; maintain API contracts and validation logic; improve extraction and processing reliability; add unit and integration tests; document backend dependencies and runtime requirements; coordinate API changes with the frontend owner. |
| **Project frontend owner** | **Frontend & Electron** | `feat/frontend-electron` | Own Electron (`apps/desktop/src/**`) and frontend integration; implement and refine user-facing workflows; connect frontend features to backend services; verify IPC, sidecar communication, error handling, and application lifecycle; own overall desktop experience; coordinate final installer integration (`DocuReady-Setup.exe`, `DocuReady-Portable.zip`). |
| **Deepti** | **CI/CD, then Frontend & QA** | `fix/ci-cd-deepti` (preserve existing PR #94 `fix/ci-verification-stabilisation`) | **Phase 1 (CI/CD):** Stabilise GitHub Actions; verify cross-platform test workflows; verify Windows packaging; ensure release artifacts upload correctly; ensure failures are visible and reproducible.<br>**Phase 2 (Frontend collaboration):** Pair with the frontend owner after CI/CD is stable; review integration issues; test frontend & Electron functionality; assist with release qualification. |

---

## 2. File Ownership Boundaries

### Shared Contract Boundary (Require Prior Coordination)
- `apps/desktop/src/shared/types.ts`
- `apps/desktop/src/shared/coordinates.ts`
- `apps/desktop/src/shared/evidence.ts`
- `sidecar/docuready_sidecar.py` (JSON-RPC request/response schema)

### Workstream File Map
- **Akriti (`feat/pr95-akriti`):** PR #95 scope, `tests/**`, `eval/**`, benchmark & regression evidence.
- **Susmita (`feat/backend-susmita`):** `src/docuready/**`, `sidecar/docuready_sidecar.py`, `packs/**`, backend unit/integration tests.
- **Project frontend owner (`feat/frontend-electron`):** `apps/desktop/**` (`src/main.ts`, `src/preload.ts`, `src/main/**`, `src/renderer/**`, `forge.config.ts`, `apps/desktop/tests/**`), `site/index.html` download section.
- **Deepti (`fix/ci-verification-stabilisation` / `fix/ci-cd-deepti`):** `.github/workflows/**`, `scripts/verify_clean_windows_runtime.ps1`, CI/packaging verification, then Phase 2 frontend/QA review.

---

## 3. Branch & Collaboration Rules

If a branch or PR already exists, **preserve it instead of creating a duplicate**.

1. Never push directly to `main`.
2. Never force-push shared branches.
3. Keep PRs focused on one responsibility.
4. Run relevant tests before requesting review.
5. Document changes and test evidence in each PR.
6. Do not overwrite another contributor's work.
7. Resolve merge conflicts deliberately.
8. Do not claim a test passed unless its output is available.
