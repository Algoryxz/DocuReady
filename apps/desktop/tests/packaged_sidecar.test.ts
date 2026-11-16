import assert from "node:assert/strict";
import fs from "node:fs/promises";
import existsSync from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";
import { SidecarManager } from "../src/main/sidecar.ts";
import { WorkspaceManager } from "../src/main/workspace.ts";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

test("Packaged Sidecar Binary executes health and runs audit seamlessly", async () => {
  const isWindows = process.platform === "win32";
  const exeName = isWindows ? "docuready_sidecar.exe" : "docuready_sidecar";
  
  // Locate repo root
  let repoRoot = path.resolve(__dirname, "../../..");
  const packagedBinary = path.join(repoRoot, "sidecar", "dist", "docuready_sidecar", exeName);

  if (!existsSync.existsSync(packagedBinary)) {
    // If running on a platform where binary hasn't been built yet, skip
    console.log("Packaged binary not found at", packagedBinary, "- skipping packaged binary test");
    return;
  }

  const tmpWs = await fs.mkdtemp(path.join(os.tmpdir(), "docuready-pkg-test-"));
  const manager = new SidecarManager(tmpWs, packagedBinary);
  const workspace = new WorkspaceManager(tmpWs);

  try {
    assert.strictEqual(manager.getSidecarType(), "packaged_binary");

    // 1. Health handshake with packaged binary
    const health = await manager.getHealth();
    assert.strictEqual(health.ok, true);
    assert.strictEqual(health.sidecar, "docuready-python");
    assert.strictEqual(health.protocol, 1);
    assert.strictEqual(health.status, "healthy");
    assert.ok(health.pythonVersion);
    assert.strictEqual(health.pdfBackend, "pymupdf");

    // 2. Correlation test with unknown method
    const unknownRes = await manager.sendRequest("unknown_method_test", {});
    assert.strictEqual(unknownRes.ok, false);
    assert.strictEqual(unknownRes.error?.code, "UNSUPPORTED_METHOD");

    // 3. Synthetic audit packet execution through packaged binary
    const synthPacketDir = path.join(repoRoot, "synthetic_data", "pkt_01_clean");
    if (existsSync.existsSync(synthPacketDir)) {
      await workspace.initialize();
      const doc1 = await workspace.registerDocument(path.join(synthPacketDir, "application_form.pdf"));
      const doc2 = await workspace.registerDocument(path.join(synthPacketDir, "income_cert.pdf"));
      const packet = await workspace.createPacket([doc1.id, doc2.id], "odisha_post_matric", "2026-11-16");
      const storedPacket = workspace.getStoredPacket(packet.packetId);
      assert.ok(storedPacket);

      const auditResponse = await manager.executeAudit(
        storedPacket.workspaceDir,
        "TEST_PKG_PKT",
        "2026-11-16"
      );
      assert.strictEqual(auditResponse.status, "completed");
      assert.ok(auditResponse.result);
      assert.strictEqual(auditResponse.result.packet_id, "TEST_PKG_PKT");
      assert.ok(Array.isArray(auditResponse.result.findings));
      assert.ok(auditResponse.result.findings.length > 0);
      await workspace.cleanPacket(packet.packetId);
    }

    // 4. Graceful shutdown
    await manager.shutdown();
  } finally {
    await fs.rm(tmpWs, { recursive: true, force: true });
  }
});
