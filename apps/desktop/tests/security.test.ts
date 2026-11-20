import assert from "node:assert/strict";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import {
  getContentSecurityPolicy,
  validateFileSize,
  validateFileSignature,
  validateIpcSender
} from "../src/main/security.ts";

test("getContentSecurityPolicy returns strict sandbox directives", () => {
  const devCsp = getContentSecurityPolicy(true);
  assert.ok(devCsp.includes("default-src 'self'"));
  assert.ok(devCsp.includes("object-src 'none'"));
  assert.ok(devCsp.includes("frame-ancestors 'none'"));

  const prodCsp = getContentSecurityPolicy(false);
  assert.ok(prodCsp.includes("connect-src 'self'"));
  assert.ok(!prodCsp.includes("localhost"));
});

test("validateFileSignature validates PDF magic bytes", async () => {
  const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "docuready-test-"));
  const pdfFile = path.join(tmpDir, "valid.pdf");
  const badFile = path.join(tmpDir, "fake.pdf");
  const shortFile = path.join(tmpDir, "tiny.pdf");

  try {
    await fs.writeFile(pdfFile, Buffer.from("%PDF-1.4 test content"));
    const validRes = await validateFileSignature(pdfFile);
    assert.strictEqual(validRes.valid, true);
    assert.strictEqual(validRes.fileType, "pdf");
    assert.strictEqual(validRes.mimeType, "application/pdf");

    await fs.writeFile(badFile, Buffer.from("NOT_A_PDF_HEADER"));
    const badRes = await validateFileSignature(badFile);
    assert.strictEqual(badRes.valid, false);

    await fs.writeFile(shortFile, Buffer.from("AB"));
    const shortRes = await validateFileSignature(shortFile);
    assert.strictEqual(shortRes.valid, false);
  } finally {
    await fs.rm(tmpDir, { recursive: true, force: true });
  }
});

test("validateFileSignature validates image formats", async () => {
  const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "docuready-test-"));
  const pngFile = path.join(tmpDir, "test.png");
  const jpgFile = path.join(tmpDir, "test.jpg");

  try {
    const pngHeader = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a, 0x00]);
    await fs.writeFile(pngFile, pngHeader);
    const pngRes = await validateFileSignature(pngFile);
    assert.strictEqual(pngRes.valid, true);
    assert.strictEqual(pngRes.fileType, "png");
    assert.strictEqual(pngRes.mimeType, "image/png");

    const jpgHeader = Buffer.from([0xff, 0xd8, 0xff, 0xe0, 0x00, 0x10]);
    await fs.writeFile(jpgFile, jpgHeader);
    const jpgRes = await validateFileSignature(jpgFile);
    assert.strictEqual(jpgRes.valid, true);
    assert.strictEqual(jpgRes.fileType, "jpeg");
    assert.strictEqual(jpgRes.mimeType, "image/jpeg");
  } finally {
    await fs.rm(tmpDir, { recursive: true, force: true });
  }
});

test("validateFileSize rejects empty files and oversized files", async () => {
  const tmpDir = await fs.mkdtemp(path.join(os.tmpdir(), "docuready-test-"));
  const emptyFile = path.join(tmpDir, "empty.pdf");
  const normalFile = path.join(tmpDir, "normal.pdf");

  try {
    await fs.writeFile(emptyFile, Buffer.alloc(0));
    const emptyRes = await validateFileSize(emptyFile);
    assert.strictEqual(emptyRes.valid, false);

    await fs.writeFile(normalFile, Buffer.alloc(1024));
    const normalRes = await validateFileSize(normalFile, 2048);
    assert.strictEqual(normalRes.valid, true);
    assert.strictEqual(normalRes.size, 1024);

    const oversizedRes = await validateFileSize(normalFile, 500);
    assert.strictEqual(oversizedRes.valid, false);
  } finally {
    await fs.rm(tmpDir, { recursive: true, force: true });
  }
});

test("validateIpcSender enforces security boundaries", () => {
  // Missing sender frame
  assert.throws(
    () => {
      validateIpcSender({ senderFrame: null } as any, true);
    },
    { message: /senderFrame is undefined/ }
  );

  // Unauthorized dev origin
  assert.throws(
    () => {
      validateIpcSender(
        { senderFrame: { url: "http://malicious-site.com/index.html" } } as any,
        true,
        "http://localhost:5173"
      );
    },
    { message: /Unauthorized IPC origin/ }
  );

  // Legitimate dev origin passes
  assert.doesNotThrow(() => {
    validateIpcSender(
      { senderFrame: { url: "http://localhost:5173/page" } } as any,
      true,
      "http://localhost:5173"
    );
  });
});
