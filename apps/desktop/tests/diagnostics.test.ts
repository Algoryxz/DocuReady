import assert from "node:assert/strict";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { SidecarManager } from "../src/main/sidecar.ts";
import { WorkspaceManager } from "../src/main/workspace.ts";

test("Diagnostic metadata enforces zero-PII and includes runtime health", async () => {
  const tmpWs = await fs.mkdtemp(path.join(os.tmpdir(), "docuready-diag-test-"));
  const sidecar = new SidecarManager(tmpWs);
  const workspace = new WorkspaceManager(tmpWs);

  try {
    const health = await sidecar.getHealth();
    assert.strictEqual(health.ok, true);
    assert.strictEqual(health.status, "healthy");
    assert.strictEqual(health.sidecar, "docuready-python");
    assert.strictEqual(health.protocol, 1);
    assert.strictEqual(health.pdfBackend, "pymupdf");

    // Dynamic OCR runtime fields
    assert.strictEqual(typeof health.ocrAvailable, "boolean");
    assert.ok(Array.isArray(health.ocrLanguages));

    if (health.ocrAvailable) {
      assert.ok(health.tesseractVersion);
      assert.ok(health.tesseractPath);
      // Zero PII enforcement: Path must be sanitized to basename only
      assert.ok(
        !health.tesseractPath.includes("/") && !health.tesseractPath.includes("\\"),
        `Expected sanitized binary basename, got: ${health.tesseractPath}`
      );
      assert.ok(health.tesseractPath.startsWith("tesseract"));
    }

    // Active workspace tracking
    await workspace.initialize();
    assert.strictEqual(workspace.getActiveWorkspaceCount(), 0);
    const dummyDocPath = path.join(tmpWs, "dummy.pdf");
    await fs.writeFile(dummyDocPath, "%PDF-1.4 dummy");
    const regDoc = await workspace.registerDocument(dummyDocPath);
    const packet = await workspace.createPacket([regDoc.id], "odisha_post_matric", "2026-03-31");
    assert.strictEqual(workspace.getActiveWorkspaceCount(), 1);

    await workspace.cleanPacket(packet.packetId);
    assert.strictEqual(workspace.getActiveWorkspaceCount(), 0);

    // Sidecar type resolution
    const sidecarType = sidecar.getSidecarType();
    assert.ok(sidecarType === "packaged_binary" || sidecarType === "python_script");

    await sidecar.shutdown();
  } finally {
    await fs.rm(tmpWs, { recursive: true, force: true });
  }
});
