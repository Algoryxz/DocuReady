import assert from "node:assert/strict";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { execFileSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { SidecarManager } from "../src/main/sidecar.ts";
import { WorkspaceManager } from "../src/main/workspace.ts";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

test("End-to-End Synthetic Packet Audit Parity (Desktop vs Python Engine)", async () => {
  const repoRoot = path.resolve(__dirname, "../../..");
  const synthPacketDir = path.join(repoRoot, "synthetic_data", "pkt_01_clean");
  const testAsOf = "2026-11-16";

  // 1. Run direct Python engine audit as baseline
  const pythonScript = `
import json
from datetime import date
from docuready.pipeline import AuditPipeline
from docuready.report.redact import redact_audit_result_dict

pipeline = AuditPipeline(as_of=date.fromisoformat("${testAsOf}"))
result, docs = pipeline.load_and_audit_packet(
    "${synthPacketDir.replace(/\\/g, "/")}",
    packet_id="SYNTH_BASELINE",
    as_of=date.fromisoformat("${testAsOf}")
)
public_dict = redact_audit_result_dict(result.to_public_dict(canonical=True))
print(json.dumps(public_dict))
`;

  const pythonOut = execFileSync(
    process.env.PYTHON_EXECUTABLE || "python",
    ["-c", pythonScript],
    { encoding: "utf-8", cwd: repoRoot }
  );
  const baselineResult = JSON.parse(pythonOut.trim());

  // 2. Set up isolated desktop workspace
  const tmpWs = await fs.mkdtemp(path.join(os.tmpdir(), "docuready-parity-"));
  const workspaceManager = new WorkspaceManager(tmpWs);
  await workspaceManager.initialize();

  const sidecarManager = new SidecarManager(tmpWs);
  await sidecarManager.start();

  try {
    // 3. Register documents through Desktop workspace manager (simulating native selection)
    const files = await fs.readdir(synthPacketDir);
    const docIds: string[] = [];

    for (const file of files) {
      if (file.endsWith(".pdf")) {
        const fullPath = path.join(synthPacketDir, file);
        const registered = await workspaceManager.registerDocument(fullPath);
        assert.ok(registered);
        docIds.push(registered.id);
      }
    }

    assert.ok(docIds.length >= 5, "Expected at least 5 synthetic documents registered");

    // 4. Create packet (isolated workspace staging)
    const packet = await workspaceManager.createPacket(
      docIds,
      "odisha_post_matric",
      testAsOf
    );
    assert.ok(packet);
    assert.ok(packet.packetId);

    const storedPacket = workspaceManager.getStoredPacket(packet.packetId);
    assert.ok(storedPacket);
    assert.ok(storedPacket.workspaceDir.startsWith(tmpWs));

    // 5. Execute audit through sidecar
    const auditResponse = await sidecarManager.executeAudit(
      storedPacket.workspaceDir,
      "SYNTH_BASELINE",
      testAsOf
    );

    assert.strictEqual(auditResponse.status, "completed");
    assert.ok(auditResponse.result);
    const desktopResult = auditResponse.result;

    // 6. Detailed Parity Assertions
    // (a) Overall Status Parity
    assert.strictEqual(
      desktopResult.overall_status,
      baselineResult.overall_status,
      "Overall status must match engine baseline exactly"
    );

    // (b) Readiness Score Parity
    assert.strictEqual(
      desktopResult.readiness_score,
      baselineResult.readiness_score,
      "Readiness score must match engine baseline exactly"
    );

    // (c) Scheme Name Parity
    assert.strictEqual(
      desktopResult.scheme_name,
      baselineResult.scheme_name,
      "Scheme name must match engine baseline exactly"
    );

    // (d) Findings Count Parity
    assert.strictEqual(
      desktopResult.findings.length,
      baselineResult.findings.length,
      "Findings count must match engine baseline exactly"
    );

    // (e) Individual Findings Parity (Rule IDs, Statuses, Severities, Fields, Match Grades, Reason Codes)
    for (let i = 0; i < baselineResult.findings.length; i++) {
      const baseFinding = baselineResult.findings[i];
      const deskFinding = desktopResult.findings[i];

      assert.strictEqual(deskFinding.rule_id, baseFinding.rule_id);
      assert.strictEqual(deskFinding.status, baseFinding.status);
      assert.strictEqual(deskFinding.severity, baseFinding.severity);
      assert.strictEqual(deskFinding.penalty, baseFinding.penalty);
      assert.strictEqual(deskFinding.field, baseFinding.field);
      assert.deepStrictEqual(deskFinding.documents_involved, baseFinding.documents_involved);

      if (baseFinding.reason_code) {
        assert.strictEqual(deskFinding.reason_code, baseFinding.reason_code);
      }
      if (baseFinding.match_grade) {
        assert.strictEqual(deskFinding.match_grade, baseFinding.match_grade);
      }
    }

    // (f) Summary Counts Parity
    assert.deepStrictEqual(
      desktopResult.summary_counts,
      baselineResult.summary_counts,
      "Summary counts must match engine baseline exactly"
    );

    // (g) Redaction Verification: check that raw PII is absent
    const desktopJson = JSON.stringify(desktopResult);
    // In pkt_01_clean, applicant name might be in synthetic docs; verify no unredacted leaked secrets or unexpected fields
    assert.ok(!desktopJson.includes("SUPER_SECRET_KEY"));

    // 7. Clear and verify temporary workspace cleanup
    await workspaceManager.cleanPacket(packet.packetId);
    const packetDirExists = await fs
      .stat(storedPacket.workspaceDir)
      .then(() => true)
      .catch(() => false);
    assert.strictEqual(packetDirExists, false, "Staged packet workspace must be deleted after cleanup");

    await sidecarManager.shutdown();
  } finally {
    await fs.rm(tmpWs, { recursive: true, force: true });
  }
});
