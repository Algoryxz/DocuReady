import assert from "node:assert/strict";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { WorkspaceManager } from "../src/main/workspace.ts";

test("WorkspaceManager creates isolated workspace directory and stages packets", async () => {
  const tmpRoot = await fs.mkdtemp(path.join(os.tmpdir(), "docuready-ws-test-"));
  const docsDir = path.join(tmpRoot, "docs");
  const wsRoot = path.join(tmpRoot, "workspaces");
  await fs.mkdir(docsDir, { recursive: true });

  const manager = new WorkspaceManager(wsRoot);
  await manager.initialize();

  // Create valid PDF document
  const pdf1 = path.join(docsDir, "app_form.pdf");
  const pdf2 = path.join(docsDir, "marksheet.pdf");
  await fs.writeFile(pdf1, Buffer.from("%PDF-1.4 application form content"));
  await fs.writeFile(pdf2, Buffer.from("%PDF-1.4 marksheet content"));

  try {
    // 1. Register documents
    const doc1 = await manager.registerDocument(pdf1);
    const doc2 = await manager.registerDocument(pdf2);

    assert.ok(doc1);
    assert.ok(doc2);
    assert.strictEqual(doc1.name, "app_form.pdf");
    assert.strictEqual(doc1.fileType, "pdf");
    assert.strictEqual(doc2.name, "marksheet.pdf");

    // 2. Create packet
    const packet = await manager.createPacket(
      [doc1.id, doc2.id],
      "test_scheme",
      "2026-11-16"
    );

    assert.ok(packet);
    assert.ok(packet.packetId.startsWith("pkt-"));
    assert.strictEqual(packet.documentCount, 2);

    const stored = manager.getStoredPacket(packet.packetId);
    assert.ok(stored);
    assert.ok(stored.workspaceDir.startsWith(wsRoot));

    // Verify staged files exist in workspace
    const staged1 = path.join(stored.workspaceDir, "app_form.pdf");
    const staged2 = path.join(stored.workspaceDir, "marksheet.pdf");
    assert.strictEqual(await fs.stat(staged1).then(() => true).catch(() => false), true);
    assert.strictEqual(await fs.stat(staged2).then(() => true).catch(() => false), true);

    // 3. Clean packet
    const cleaned = await manager.cleanPacket(packet.packetId);
    assert.strictEqual(cleaned, true);

    // Verify packet dir removed
    const existsAfter = await fs.stat(stored.workspaceDir).then(() => true).catch(() => false);
    assert.strictEqual(existsAfter, false);

    // 4. Clear all
    await manager.clearAll();
  } finally {
    await fs.rm(tmpRoot, { recursive: true, force: true });
  }
});

test("WorkspaceManager rejects invalid files during registration", async () => {
  const tmpRoot = await fs.mkdtemp(path.join(os.tmpdir(), "docuready-ws-test-"));
  const badFile = path.join(tmpRoot, "fake.pdf");
  await fs.writeFile(badFile, Buffer.from("NOT_A_REAL_PDF"));

  const manager = new WorkspaceManager(path.join(tmpRoot, "ws"));
  await manager.initialize();

  try {
    await assert.rejects(
      async () => {
        await manager.registerDocument(badFile);
      },
      { message: /invalid signature or unsupported format/ }
    );
  } finally {
    await fs.rm(tmpRoot, { recursive: true, force: true });
  }
});

test("WorkspaceManager rejects empty document packet creation", async () => {
  const tmpRoot = await fs.mkdtemp(path.join(os.tmpdir(), "docuready-ws-test-"));
  const manager = new WorkspaceManager(path.join(tmpRoot, "ws"));
  await manager.initialize();

  try {
    await assert.rejects(
      async () => {
        await manager.createPacket([]);
      },
      { message: /At least one document is required/ }
    );
  } finally {
    await fs.rm(tmpRoot, { recursive: true, force: true });
  }
});
