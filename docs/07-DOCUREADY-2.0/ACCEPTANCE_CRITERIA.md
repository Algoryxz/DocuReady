# DocuReady 2.0 — Release Validation, Testing & Acceptance Criteria

**Policy:** Do not weaken existing assertions or silently convert unexpected failures into skips. Do not claim a test passed unless its output is available.

---

## 1. Windows Installer Objective

Produce and qualify:
- `DocuReady-Setup.exe` — primary Windows installer *(note: `apps/desktop/forge.config.ts` currently emits `DocuReady-0.1.0-Setup.exe`; align artifact naming in packaging/release step)*
- `DocuReady-Portable.zip` — portable version *(note: currently emitted as `DocuReady-win32-x64-0.1.0.zip`)*
- `SHA256SUMS.txt` — SHA-256 checksums for all release artifacts
- `INSTALLATION.md` — installation instructions
- `TROUBLESHOOTING.md` — common errors and solutions
- `RELEASE_NOTES.md` — changes in the release

The installer must:
- Install on a clean supported Windows machine and launch successfully.
- Include all required runtime dependencies, the Python sidecar, and required OCR resources.
- Handle missing or invalid configuration gracefully and support clean uninstallation.
- Avoid relying on development-machine paths and be tested independently of the developer's environment.

---

## 2. Required Release Validation Checklist

### Application
- [ ] Application launches.
- [ ] Main window renders.
- [ ] Navigation works.
- [ ] Document import works.
- [ ] Document processing works.
- [ ] Evidence review works.
- [ ] Error states are understandable.
- [ ] Application closes cleanly.

### Backend and OCR
- [ ] Backend tests pass.
- [ ] Sidecar starts successfully and health check passes.
- [ ] OCR resources are bundled.
- [ ] English OCR tested.
- [ ] Hindi OCR tested.
- [ ] Odia OCR tested.
- [ ] Representative PDFs and image documents tested.
- [ ] Regression corpus verified.

### Windows Distribution
- [ ] Installer generated (`DocuReady-Setup.exe`).
- [ ] Portable ZIP generated (`DocuReady-Portable.zip`).
- [ ] Clean-machine installation tested.
- [ ] Installed application launches.
- [ ] Uninstallation tested.
- [ ] SHA-256 checksums generated (`SHA256SUMS.txt`).
- [ ] Artifact upload verified *(note: GitHub Actions qualification artifacts are temporary CI builds and must not be represented as a permanent public release)*.
- [ ] Download instructions tested by another team member.

### Quality
- [ ] Full automated test suite passes.
- [ ] Benchmark results recorded (with before/after comparisons).
- [ ] No unexplained benchmark regressions.
- [ ] Known limitations documented.
- [ ] Release evidence attached to the final PR.

---

## 3. Distribution and Licensing Gate (Mandatory Before Public Release)

Before publishing a permanent public installer, review `LICENSING_DECISION.md`:
- The existing licensing assessment identifies an **open AGPLv3 distribution-clearance issue** involving bundled PyMuPDF/MuPDF (`pymupdf==2.1`).
- **Do not treat a successful build or a passing test suite as legal distribution clearance.**
- Before public release:
  - Confirm the chosen licensing/distribution route.
  - Verify corresponding source and required notices (`LICENSE`, `NOTICE`, `THIRD_PARTY_LICENSES.md`).
  - Verify third-party license texts and attribution.
  - Obtain appropriate legal review where needed.

---

## 4. Final Release Deliverables & Definition of Done

1. A reproducible Windows installer (`DocuReady-Setup.exe`).
2. A portable Windows package (`DocuReady-Portable.zip`).
3. Clean-machine validation evidence.
4. Automated test and benchmark reports.
5. Installation (`INSTALLATION.md`) and troubleshooting (`TROUBLESHOOTING.md`) documentation.
6. Release notes (`RELEASE_NOTES.md`) and checksums (`SHA256SUMS.txt`).
7. A permanent GitHub Release after the release and licensing gates are satisfied.
8. A prominent website download section on `https://docu-ready-steel.vercel.app/#workflow` (`site/index.html`) pointing to the approved release.

**Definition of done:** A person who has never worked on this repository can download DocuReady, install it, launch it, understand how to use it, and troubleshoot common problems without needing help from the development team.
