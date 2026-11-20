import assert from "node:assert";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { WorkspaceManager } from "../src/main/workspace.ts";

test("WorkspaceManager.getDocumentContent safely serves registered files and blocks directory traversal", async () => {
  const tmpRoot = path.join(os.tmpdir(), `docuready-test-bin-${Date.now()}`);
  await fs.mkdir(tmpRoot, { recursive: true });

  try {
    const manager = new WorkspaceManager(tmpRoot);
    await manager.initialize();

    // Create a dummy valid PDF file
    const samplePdfPath = path.join(tmpRoot, "sample.pdf");
    const sampleContent = Buffer.from("%PDF-1.4\n%test binary content\n%%EOF\n");
    await fs.writeFile(samplePdfPath, sampleContent);

    // Register document
    const doc = await manager.registerDocument(samplePdfPath);
    assert.ok(doc);

    // 1. Retrieve by opaque ID
    const retrievedById = await manager.getDocumentContent(doc.id);
    assert.ok(retrievedById);
    assert.deepStrictEqual(retrievedById, sampleContent);

    // 2. Retrieve by sanitized filename
    const retrievedByName = await manager.getDocumentContent(doc.name);
    assert.ok(retrievedByName);
    assert.deepStrictEqual(retrievedByName, sampleContent);

    // 3. Reject unregistered document ID
    const notFound = await manager.getDocumentContent("doc-nonexistent-1234");
    assert.strictEqual(notFound, null);

    // 4. Reject directory traversal attempts
    const traversal1 = await manager.getDocumentContent("../../../windows/win.ini");
    assert.strictEqual(traversal1, null);

    const traversal2 = await manager.getDocumentContent("/etc/passwd");
    assert.strictEqual(traversal2, null);

    const traversal3 = await manager.getDocumentContent("..\\..\\boot.ini");
    assert.strictEqual(traversal3, null);
  } finally {
    await fs.rm(tmpRoot, { recursive: true, force: true }).catch(() => {});
  }
});
