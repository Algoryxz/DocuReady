# Loop 29 Baseline Provenance & Repository Ancestry Audit

## 1. Provenance Gate Verification
- **Research Branch**: `loop-29-calibration-cohort-integrity-and-generalization`
- **Base Commit**: `ce0c9e77cdb8788dbbf08e58882183282995979b` (Loop 28 research milestone)
- **Reported Parent Commit**: `511ba824ecac000180489cd2e92f1cc634fe7098` (Loop 27 research milestone)
- **Parent-Child Relationship**: Verified bit-exact via `git rev-parse HEAD~1 == 511ba824...`.
- **Remote Origin**: `https://github.com/Algoryxz/DocuReady.git`
- **Release Promotion Policy**: STRICTLY PROHIBITED. Isolated research branch.

## 2. Protected Release Bit-Exact Verification
Loop 10 competition release baseline (`bdc403a`) was audited via `tests/test_loop09_release_integrity.py`. All 5 release binaries match their SHA-256 signatures exactly (9/9 tests PASSED).
