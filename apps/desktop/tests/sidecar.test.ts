import assert from "node:assert/strict";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import { SidecarManager } from "../src/main/sidecar.ts";

test("SidecarManager executes health handshake and manages child process", async () => {
  const tmpWs = await fs.mkdtemp(path.join(os.tmpdir(), "docuready-sc-test-"));
  const manager = new SidecarManager(tmpWs);

  try {
    // 1. Health check
    const health = await manager.getHealth();
    assert.strictEqual(health.ok, true);
    assert.strictEqual(health.sidecar, "docuready-python");
    assert.strictEqual(health.protocol, 1);
    assert.strictEqual(health.engineVersion, "0.1.0");
    assert.strictEqual(health.status, "healthy");
    assert.ok(health.pythonVersion);

    // 2. Correlation test with unknown method
    const unknownRes = await manager.sendRequest("unknown_test_method", {});
    assert.strictEqual(unknownRes.ok, false);
    assert.strictEqual(unknownRes.error?.code, "UNSUPPORTED_METHOD");

    // 3. Graceful shutdown
    await manager.shutdown();
  } finally {
    await fs.rm(tmpWs, { recursive: true, force: true });
  }
});

test("SidecarManager recovers from unexpected child process crash", async () => {
  const tmpWs = await fs.mkdtemp(path.join(os.tmpdir(), "docuready-sc-test-"));
  const manager = new SidecarManager(tmpWs);

  try {
    // Start sidecar and verify health
    const health1 = await manager.getHealth();
    assert.strictEqual(health1.ok, true);

    // Kill sidecar to simulate sudden crash
    const child = (manager as any).child;
    assert.ok(child);
    const exitPromise = new Promise<void>((resolve) => {
      child.once("exit", () => resolve());
    });
    child.kill("SIGKILL");

    // Await process termination (with 3s timeout fallback)
    await Promise.race([
      exitPromise,
      new Promise((r) => setTimeout(r, 3000))
    ]);

    // Next request should automatically respawn sidecar process
    const health2 = await manager.getHealth();
    assert.strictEqual(health2.ok, true);
    assert.strictEqual(health2.sidecar, "docuready-python");

    await manager.shutdown();
  } finally {
    await fs.rm(tmpWs, { recursive: true, force: true });
  }
});
