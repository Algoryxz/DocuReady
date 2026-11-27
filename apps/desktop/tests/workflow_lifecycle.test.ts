import assert from "node:assert/strict";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";
import { SidecarManager } from "../src/main/sidecar.ts";
import { WorkspaceManager } from "../src/main/workspace.ts";
import { filterFindings, normalizeFindingsAndEvidence } from "../src/shared/evidence.ts";
import type { RedactedAuditResult } from "../src/shared/types.ts";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

test("Desktop Workflow Lifecycle: Registration, Packet Creation, Sidecar Execution, and Isolation", async () => {
  const repoRoot = path.resolve(__dirname, "../../..");
  const synthPacketDir = path.join(repoRoot, "synthetic_data", "pkt_01_clean");
  const testAsOf = "2026-11-16";

  const tmpWs = await fs.mkdtemp(path.join(os.tmpdir(), "docuready-workflow-"));
  const workspaceManager = new WorkspaceManager(tmpWs);
  await workspaceManager.initialize();

  const sidecarManager = new SidecarManager(tmpWs);
  await sidecarManager.start();

  try {
    // 1. Stage and register files
    const files = await fs.readdir(synthPacketDir);
    const docIds: string[] = [];
    for (const f of files) {
      if (f.endsWith(".pdf")) {
        const doc = await workspaceManager.registerDocument(path.join(synthPacketDir, f));
        assert.ok(doc);
        docIds.push(doc.id);
      }
    }
    assert.ok(docIds.length >= 3, "Expected at least 3 documents in pkt_01_clean");

    // 2. Create Packet
    const packet = await workspaceManager.createPacket(docIds, "odisha_post_matric", testAsOf);
    assert.ok(packet.packetId.startsWith("pkt-"));
    assert.strictEqual(packet.documentCount, docIds.length);
    assert.strictEqual(workspaceManager.getActiveWorkspaceCount(), 1);

    // Verify staged files exist on disk
    const stagedPacket = workspaceManager.getStoredPacket(packet.packetId);
    assert.ok(stagedPacket);
    const stagedFiles = await fs.readdir(stagedPacket.workspaceDir);
    assert.strictEqual(stagedFiles.length, docIds.length);

    // 3. Track progress events during execution
    const progressEvents: number[] = [];
    sidecarManager.on("progress", (p) => {
      progressEvents.push(p.percent);
    });

    // 4. Execute audit
    const response = await sidecarManager.executeAudit(
      stagedPacket.workspaceDir,
      packet.packetId,
      packet.asOf
    );

    assert.strictEqual(response.status, "completed");
    assert.ok(response.result);
    assert.strictEqual(response.result.overall_status, "NO_ISSUES_FOUND");
    assert.strictEqual(response.result.readiness_score, 100);
    assert.ok(response.result.findings.length > 0);

    // 5. Clean packet workspace
    await workspaceManager.cleanPacket(packet.packetId);
    assert.strictEqual(workspaceManager.getActiveWorkspaceCount(), 0);
  } finally {
    await sidecarManager.shutdown();
    await workspaceManager.clearAll();
    await fs.rm(tmpWs, { recursive: true, force: true });
  }
});

test("Desktop Workflow: In-Flight Audit Cancellation and Safe Process Recovery", async () => {
  const repoRoot = path.resolve(__dirname, "../../..");
  const synthPacketDir = path.join(repoRoot, "synthetic_data", "pkt_01_clean");
  const testAsOf = "2026-11-16";

  const tmpWs = await fs.mkdtemp(path.join(os.tmpdir(), "docuready-cancel-"));
  const workspaceManager = new WorkspaceManager(tmpWs);
  await workspaceManager.initialize();

  const sidecarManager = new SidecarManager(tmpWs);
  await sidecarManager.start();

  try {
    const files = await fs.readdir(synthPacketDir);
    const docIds: string[] = [];
    for (const f of files) {
      if (f.endsWith(".pdf")) {
        const doc = await workspaceManager.registerDocument(path.join(synthPacketDir, f));
        if (doc) docIds.push(doc.id);
      }
    }

    const packet = await workspaceManager.createPacket(docIds, "odisha_post_matric", testAsOf);
    const stagedPacket = workspaceManager.getStoredPacket(packet.packetId)!;

    // Launch audit asynchronously
    const auditPromise = sidecarManager.executeAudit(
      stagedPacket.workspaceDir,
      packet.packetId,
      packet.asOf
    );

    // Trigger immediate cancellation after short delay
    await new Promise((r) => setTimeout(r, 100));
    const cancelResult = await sidecarManager.cancelAudit(packet.packetId);

    assert.strictEqual(cancelResult.status, "cancelled");
    assert.strictEqual(cancelResult.packetId, packet.packetId);

    // The auditPromise should resolve with cancelled status without throwing unhandled exception
    const auditResult = await auditPromise;
    assert.strictEqual(auditResult.status, "cancelled");

    // Clean workspace
    await workspaceManager.cleanPacket(packet.packetId);

    // Verify Sidecar automatically recovered and can execute subsequent health and audit
    const health = await sidecarManager.getHealth();
    assert.strictEqual(health.ok, true);
    assert.strictEqual(health.status, "healthy");
  } finally {
    await sidecarManager.shutdown();
    await workspaceManager.clearAll();
    await fs.rm(tmpWs, { recursive: true, force: true });
  }
});

test("Desktop Workflow: Session Isolation and Complete Data Purge", async () => {
  const repoRoot = path.resolve(__dirname, "../../..");
  const synthPacketDir = path.join(repoRoot, "synthetic_data", "pkt_01_clean");

  const tmpWs = await fs.mkdtemp(path.join(os.tmpdir(), "docuready-isolate-"));
  const workspaceManager = new WorkspaceManager(tmpWs);
  await workspaceManager.initialize();

  try {
    const files = await fs.readdir(synthPacketDir);
    const docIds: string[] = [];
    for (const f of files) {
      if (f.endsWith(".pdf")) {
        const doc = await workspaceManager.registerDocument(path.join(synthPacketDir, f));
        if (doc) docIds.push(doc.id);
      }
    }

    // Create 2 distinct packets
    const p1 = await workspaceManager.createPacket([docIds[0]], "odisha_post_matric");
    const p2 = await workspaceManager.createPacket([docIds[1]], "general_scholarship");

    assert.strictEqual(workspaceManager.getActiveWorkspaceCount(), 2);

    // Clear all sessions
    const cleanedCount = await workspaceManager.clearAll();
    assert.strictEqual(cleanedCount, 2);
    assert.strictEqual(workspaceManager.getActiveWorkspaceCount(), 0);

    // Documents must no longer be retrievable
    const content = await workspaceManager.getDocumentContent(docIds[0]);
    assert.strictEqual(content, null);

    // Workspace folder must be empty of subdirectories
    const entries = await fs.readdir(tmpWs);
    assert.strictEqual(entries.length, 0);
  } finally {
    await fs.rm(tmpWs, { recursive: true, force: true });
  }
});

test("Human Review UX: REVIEW/MANUAL_REVIEW & MISSING Taxonomy Normalization and Filtering", () => {
  const sampleAudit: RedactedAuditResult = {
    packet_id: "pkt-test-review-01",
    scheme_id: "odisha_post_matric",
    scheme_name: "Odisha Post-Matric Scholarship",
    readiness_score: 65,
    overall_status: "ACTION_REQUIRED",
    as_of: "2026-11-16",
    findings: [
      {
        rule_id: "RULE-DOC-01",
        rule_name: "Mandatory Document Presence - Income Certificate",
        severity: "FATAL",
        status: "MISSING",
        field: "income_certificate",
        penalty: 35,
        reason_code: "REQUIRED_DOCUMENT_ABSENT",
        message: "Income certificate was not provided.",
        remediation: "Upload a valid Income Certificate issued by Tahsildar.",
        statutory_reference: "Section 4.1, Odisha Scholarship Guidelines",
        documents_involved: ["income_certificate.pdf"],
        evidence: []
      },
      {
        rule_id: "RULE-NAME-02",
        rule_name: "Applicant Name Consistency Across Records",
        severity: "WARNING",
        status: "REVIEW",
        field: "applicant_name",
        penalty: 0,
        reason_code: "SOFT_NAME_VARIATION",
        match_grade: "SOFT_TOKEN_SUBSET",
        message: "Name initials differ between Aadhaar and College ID.",
        remediation: "Verify identity using supporting affidavit or high-school certificate.",
        statutory_reference: "Section 2.3, Identity Verification Norms",
        documents_involved: ["aadhaar.pdf", "college_id.pdf"],
        evidence: [
          {
            rule_id: "RULE-NAME-02",
            document_type: "AADHAAR",
            file_name: "aadhaar.pdf",
            page_number: 1,
            bounding_box: [100, 150, 300, 180],
            raw_snippet: "S. K. PATEL",
            extracted_field: "applicant_name",
            extraction_method: "NATIVE_VECTOR",
            ocr_confidence: 0.96
          }
        ]
      },
      {
        rule_id: "RULE-CASTE-01",
        rule_name: "Caste Certificate Validity",
        severity: "FATAL",
        status: "PASS",
        field: "caste_category",
        penalty: 0,
        reason_code: "VERIFIED",
        message: "Caste certificate is valid.",
        remediation: "",
        statutory_reference: "Section 3.2, Category Norms",
        documents_involved: ["caste.pdf"],
        evidence: [
          {
            rule_id: "RULE-CASTE-01",
            document_type: "CASTE_CERTIFICATE",
            file_name: "caste.pdf",
            page_number: 1,
            bounding_box: [50, 80, 200, 110],
            raw_snippet: "CATEGORY: SEBC",
            extracted_field: "caste_category",
            extraction_method: "NATIVE_VECTOR",
            ocr_confidence: 0.99
          }
        ]
      }
    ],
    summary_counts: {
      PASS: 1,
      REVIEW: 1,
      MISSING: 1,
      TOTAL: 3
    }
  };

  const normalized = normalizeFindingsAndEvidence(sampleAudit, [
    { id: "doc-1", name: "aadhaar.pdf", size: 1000, mimeType: "application/pdf", fileType: "pdf" },
    { id: "doc-2", name: "caste.pdf", size: 1200, mimeType: "application/pdf", fileType: "pdf" }
  ]);

  assert.strictEqual(normalized.findings.length, 3);
  assert.strictEqual(normalized.evidenceItems.length, 3);

  // Missing finding evidence has hasProvenance === false and boundingBox === null
  const missingEv = normalized.evidenceItems.find((e) => e.ruleId === "RULE-DOC-01");
  assert.ok(missingEv);
  assert.strictEqual(missingEv.hasProvenance, false);
  assert.strictEqual(missingEv.boundingBox, null);

  // Review finding evidence has hasProvenance === true with exact coordinates
  const reviewEv = normalized.evidenceItems.find((e) => e.ruleId === "RULE-NAME-02");
  assert.ok(reviewEv);
  assert.strictEqual(reviewEv.hasProvenance, true);
  assert.deepStrictEqual(reviewEv.boundingBox, [100, 150, 300, 180]);
  assert.strictEqual(reviewEv.matchGrade, "SOFT_TOKEN_SUBSET");

  // Filter testing
  const reviewOnly = filterFindings(sampleAudit.findings, { status: "REVIEW" });
  assert.strictEqual(reviewOnly.length, 1);
  assert.strictEqual(reviewOnly[0].rule_id, "RULE-NAME-02");

  const failOnly = filterFindings(sampleAudit.findings, { status: "FAIL" });
  assert.strictEqual(failOnly.length, 1);
  assert.strictEqual(failOnly[0].rule_id, "RULE-DOC-01");

  const passOnly = filterFindings(sampleAudit.findings, { status: "PASS" });
  assert.strictEqual(passOnly.length, 1);
  assert.strictEqual(passOnly[0].rule_id, "RULE-CASTE-01");
});
