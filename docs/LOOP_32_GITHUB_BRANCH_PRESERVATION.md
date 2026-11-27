# DocuReady GitHub Branch Preservation Protocol

**Programme:** DocuReady Product Excellence  
**Audit Milestone:** Loop 32  
**Governance Invariant:** Research Isolation & Intellectual Property Preservation

---

## 1. Preservation Principles

1. **Immutable Historical Provenance:**
   - Every loop branch contains immutable empirical artifacts (corpora, ground truth annotations, benchmark results).
   - Git commit history serves as an auditable scientific ledger. No branch may be rebased, force-pushed, or pruned.

2. **Protected Competition Release Invariant:**
   - The competition baseline branch `loop-10-competition-demo-reliability-and-final-readiness` (`bdc403a`) is permanently frozen.
   - All 5 release binaries (`DocuReady.exe`, `app.asar`, `docuready_sidecar.exe`, `DocuReady-0.1.0-Setup.exe`, `DocuReady-win32-x64-0.1.0.zip`) are verified bit-exact and checksum-locked.

3. **Contributor Work Protection:**
   - Standalone experimental branches (`feat/electron-desktop-foundation`, `fix/final-desktop-release-stabilization`, `loop-14-multilingual-indic-ocr-benchmarking`, `loop-17-multi-engine-ocr-consensus`) contain unmerged experimental code that must not be deleted.
   - Future loops may cherry-pick or adapt these modules without destroying branch lineage.

---

## 2. Remote Synchronization & Archival Recommendations

To ensure absolute preservation across remote mirrors:

```bash
# Push all local loop branches to origin with tags
git push origin --all
git push origin --tags
```

All 51 branches are documented in `docs/LOOP_32_BRANCH_INVENTORY.md` and tracked in `research/loop32/branch_inventory.json`.
