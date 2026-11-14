# DocuReady — CI Dependency Lock Maintenance

This directory contains deterministic, hash-checked dependency lockfiles for automated GitHub Actions CI workflows running on `ubuntu-24.04` (Linux x86_64).

## 1. Supported Lock Targets & Scope

- **Supported Runtime Range:** Python 3.11, 3.12, 3.13, and 3.14 (`requires-python = ">=3.11,<3.15"`).
- **Target Platform:** `x86_64-unknown-linux-gnu` (`ubuntu-24.04`).
- **Input Specification:** Generated from `pyproject.toml` using the `all` optional dependency extra (which bundles runtime dependencies, `ui`, `generator`, and `dev` tools including `build`, `setuptools`, and `wheel`).
- **Enforcement:** Hash checking (`pip install --require-hashes`) is mandatory during CI execution.

### Canonical Lockfiles

- `requirements/ci-lock-py3.11.txt`: Locked dependencies for CPython 3.11 on Linux x86_64.
- `requirements/ci-lock-py3.12.txt`: Locked dependencies for CPython 3.12 on Linux x86_64.
- `requirements/ci-lock-py3.13.txt`: Locked dependencies for CPython 3.13 on Linux x86_64.
- `requirements/ci-lock-py3.14.txt`: Locked dependencies for CPython 3.14 on Linux x86_64.

## 2. Lock Generation Tooling

Lockfiles are compiled using `uv` (Astral).

- **Maintainer Tool Only:** `uv` is a developer/maintainer tool for fast cross-compilation and dependency locking; it is **NOT** a runtime dependency of DocuReady and must not be added to `dependencies` in `pyproject.toml`.
- **Verified Tool Version:** `uv 0.13.8 (3d97a6aad 2026-11-12 x86_64-pc-windows-msvc)`.

## 3. Lock Regeneration Commands

To regenerate all four supported lockfiles when `pyproject.toml` dependencies or build requirements change, execute the following PowerShell command from the repository root:

```powershell
$versions = @("3.11", "3.12", "3.13", "3.14")

foreach ($version in $versions) {
    uv pip compile pyproject.toml `
        --extra all `
        --python-version $version `
        --python-platform x86_64-unknown-linux-gnu `
        --generate-hashes `
        -o "requirements/ci-lock-py$version.txt"
}
```

On POSIX shells (Linux/macOS):

```bash
for version in 3.11 3.12 3.13 3.14; do
    uv pip compile pyproject.toml \
        --extra all \
        --python-version "$version" \
        --python-platform x86_64-unknown-linux-gnu \
        --generate-hashes \
        -o "requirements/ci-lock-py${version}.txt"
done
```

## 4. Verification and Change Review

Before committing changes to lockfiles:

1. **Verify Metadata Alignment:** Confirm that newly added or modified dependencies in `pyproject.toml` appear with exact pins (`==`) and sha256 hashes in each generated lockfile.
2. **Review Diff:** Run `git diff requirements/` to inspect updated version pins and hashes. Ensure no unpinned or unexpected packages are introduced.
3. **Verify Build System Coverage:** Ensure the build frontend (`build`) and build backend (`setuptools`, `wheel`) remain pinned and hash-checked so CI can execute `python -m build --no-isolation` without network egress.
4. **Local / CI Test:** Run local test suite and observe remote GitHub Actions matrix jobs across all supported Python runtimes.
