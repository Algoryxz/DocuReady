# Loop 28 Missing Evidence & Slot Verification Audit

## 1. Missing Supporting Evidence Hazard
In automated pipeline workflows, claims are often extracted from an application form asserting entitlements (e.g., fee waivers, category reservation, tax exemptions) where an accompanying statutory certificate is mandatory.
If the pipeline verifies the claim solely based on the application form's assertion without checking for the required attachment, the claim is improperly verified.

## 2. Policy Enforcement
DocuReady Loop 28 implements packet-level mandatory attachment validation:
- When a packet defines `required_doc_types`, all required document types must be present in the packet.
- If any required document type is missing, the engine returns `MISSING_EVIDENCE` and suppresses verification.
- If all required document types are present, but the supporting document's evidence is illegible (confidence < 70.0% or garbled glyphs), the engine returns `ABSTAIN`.
