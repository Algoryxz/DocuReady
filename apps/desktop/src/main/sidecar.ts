import { ChildProcess, spawn } from "node:child_process";
import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import readline from "node:readline";
import { EventEmitter } from "node:events";
import { fileURLToPath } from "node:url";
import type {
  AuditProgress,
  AuditStatusResponse,
  EngineHealth,
  RedactedAuditResult
} from "../shared/types.ts";

const currentDir = path.dirname(fileURLToPath(import.meta.url));

export interface SidecarRequest {
  protocol: number;
  id: string;
  method: string;
  params: Record<string, unknown>;
}

export interface SidecarResponse {
  protocol: number;
  id?: string;
  ok: boolean;
  result?: Record<string, unknown>;
  error?: {
    code: string;
    message: string;
  };
}

export class SidecarManager extends EventEmitter {
  private child: ChildProcess | null = null;
  private pendingRequests: Map<
    string,
    {
      resolve: (value: SidecarResponse) => void;
      reject: (reason: Error) => void;
      timeoutTimer: NodeJS.Timeout;
    }
  > = new Map();
  private sidecarScriptPath: string;
  private sidecarBinaryPath: string | null = null;
  private workspaceRoot: string;
  private isShuttingDown: boolean = false;
  private currentAuditJobId: string | null = null;

  constructor(workspaceRoot: string, customSidecarPath?: string) {
    super();
    this.workspaceRoot = workspaceRoot;
    if (customSidecarPath) {
      if (customSidecarPath.endsWith(".py")) {
        this.sidecarScriptPath = customSidecarPath;
        this.sidecarBinaryPath = null;
      } else {
        this.sidecarBinaryPath = customSidecarPath;
        this.sidecarScriptPath = "";
      }
    } else {
      const target = this.resolveSidecarTarget();
      this.sidecarBinaryPath = target.binaryPath;
      this.sidecarScriptPath = target.scriptPath;
    }
  }

  private resolveSidecarTarget(): { binaryPath: string | null; scriptPath: string } {
    const isWindows = process.platform === "win32";
    const exeName = isWindows ? "docuready_sidecar.exe" : "docuready_sidecar";

    // 1. Explicit env var override
    if (process.env.DOCUREADY_SIDECAR_EXECUTABLE) {
      const explicit = path.resolve(process.env.DOCUREADY_SIDECAR_EXECUTABLE);
      if (fs.existsSync(explicit)) {
        return { binaryPath: explicit, scriptPath: "" };
      }
    }

    // 2. Electron packaged resources
    const resourcesPath = (process as any).resourcesPath;
    if (resourcesPath) {
      const packagedBinary = path.join(resourcesPath, "sidecar", exeName);
      if (fs.existsSync(packagedBinary)) {
        return { binaryPath: packagedBinary, scriptPath: "" };
      }
    }

    // 3. Search up from currentDir
    let cur = currentDir;
    let foundBinary: string | null = null;
    let foundScript: string | null = null;

    while (cur !== path.dirname(cur)) {
      const binaryCandidate1 = path.join(cur, "sidecar", "dist", "docuready_sidecar", exeName);
      const binaryCandidate2 = path.join(cur, "dist", "docuready_sidecar", exeName);
      if (!foundBinary && fs.existsSync(binaryCandidate1)) {
        foundBinary = binaryCandidate1;
      } else if (!foundBinary && fs.existsSync(binaryCandidate2)) {
        foundBinary = binaryCandidate2;
      }
      const scriptCandidate = path.join(cur, "sidecar", "docuready_sidecar.py");
      if (!foundScript && fs.existsSync(scriptCandidate)) {
        foundScript = scriptCandidate;
      }
      cur = path.dirname(cur);
    }

    return {
      binaryPath: foundBinary,
      scriptPath: foundScript || path.resolve(currentDir, "../../../sidecar/docuready_sidecar.py")
    };
  }

  public getSidecarType(): "packaged_binary" | "python_script" {
    return this.sidecarBinaryPath && fs.existsSync(this.sidecarBinaryPath)
      ? "packaged_binary"
      : "python_script";
  }

  public getSidecarBinaryPath(): string | null {
    return this.sidecarBinaryPath;
  }

  public getScriptPath(): string {
    return this.sidecarScriptPath;
  }

  public async start(): Promise<void> {
    if (this.child && !this.child.killed) {
      return;
    }

    this.isShuttingDown = false;
    const isBinary = Boolean(this.sidecarBinaryPath && fs.existsSync(this.sidecarBinaryPath));

    const command = isBinary
      ? this.sidecarBinaryPath!
      : (process.env.PYTHON_EXECUTABLE || "python");

    const args = isBinary ? [] : ["-u", this.sidecarScriptPath];

    const child = spawn(command, args, {
      env: {
        ...process.env,
        PYTHONUNBUFFERED: "1",
        PYTHONIOENCODING: "utf-8",
        PYTHONUTF8: "1",
        DOCUREADY_WORKSPACE_ROOT: this.workspaceRoot
      },
      stdio: ["pipe", "pipe", "pipe"]
    });

    this.child = child;

    if (!child.stdout || !child.stdin) {
      throw new Error("Failed to initialize sidecar process stdio.");
    }

    const rl = readline.createInterface({
      input: child.stdout,
      terminal: false
    });

    rl.on("line", (line: string) => {
      this.handleStdoutLine(line);
    });

    child.stderr?.on("data", (chunk: Buffer) => {
      // Diagnostics only, no raw PII logged
      const msg = chunk.toString("utf-8").trim();
      if (msg) {
        console.error(`[sidecar:stderr] ${msg}`);
      }
    });

    child.on("error", (err: Error) => {
      console.error("[sidecar:process error]", err);
      this.rejectAllPending(new Error(`Sidecar process error: ${err.message}`));
    });

    child.on("exit", (code: number | null, signal: string | null) => {
      this.child = null;
      if (!this.isShuttingDown) {
        console.warn(`[sidecar:exit] Process exited with code ${code}, signal ${signal}`);
        this.rejectAllPending(
          new Error(`Sidecar process exited unexpectedly (code: ${code}, signal: ${signal})`)
        );
      }
    });
  }

  private rejectAllPending(err: Error): void {
    for (const [id, req] of Array.from(this.pendingRequests.entries())) {
      clearTimeout(req.timeoutTimer);
      req.reject(err);
      this.pendingRequests.delete(id);
    }
  }

  private handleStdoutLine(line: string): void {
    const trimmed = line.trim();
    if (!trimmed) return;

    try {
      const data = JSON.parse(trimmed);

      // Handle Progress event
      if (data.event === "progress") {
        const progress: AuditProgress = {
          jobId: data.job_id,
          stage: data.stage || "processing",
          completed: data.completed || 0,
          total: data.total || 1,
          percent: Math.min(
            100,
            Math.round(((data.completed || 0) / (data.total || 1)) * 100)
          )
        };
        this.emit("progress", progress);
        return;
      }

      // Handle correlated response
      const reqId = data.id;
      if (reqId && this.pendingRequests.has(reqId)) {
        const pending = this.pendingRequests.get(reqId)!;
        clearTimeout(pending.timeoutTimer);
        this.pendingRequests.delete(reqId);
        pending.resolve(data as SidecarResponse);
        return;
      }
    } catch {
      console.error("[sidecar:parse_error] Invalid JSON from sidecar stdout");
    }
  }

  public async sendRequest(
    method: string,
    params: Record<string, unknown> = {},
    timeoutMs: number = 60000
  ): Promise<SidecarResponse> {
    if (!this.child || this.child.killed) {
      await this.start();
    }

    if (!this.child || !this.child.stdin || !this.child.stdin.writable) {
      throw new Error("Sidecar child process is not writable.");
    }

    const id = `req-${crypto.randomUUID()}`;
    const payload: SidecarRequest = {
      protocol: 1,
      id,
      method,
      params
    };

    return new Promise((resolve, reject) => {
      const timeoutTimer = setTimeout(() => {
        this.pendingRequests.delete(id);
        reject(new Error(`Sidecar request '${method}' timed out after ${timeoutMs}ms`));
      }, timeoutMs);

      this.pendingRequests.set(id, { resolve, reject, timeoutTimer });

      try {
        this.child!.stdin!.write(JSON.stringify(payload) + "\n");
      } catch (err) {
        clearTimeout(timeoutTimer);
        this.pendingRequests.delete(id);
        reject(err instanceof Error ? err : new Error(String(err)));
      }
    });
  }

  public async getHealth(timeoutMs: number = 30000): Promise<EngineHealth> {
    try {
      const res = await this.sendRequest("health", {}, timeoutMs);
      if (res.ok && res.result) {
        return {
          ok: true,
          sidecar: String(res.result.sidecar || "docuready-python"),
          protocol: Number(res.result.protocol || 1),
          engineVersion: String(res.result.engine_version || "0.1.0"),
          pythonVersion: String(res.result.python || "unknown"),
          pdfBackend: String(res.result.pdf_backend || "pymupdf"),
          ocrAvailable: Boolean(res.result.ocr_available),
          ocrLanguages: Array.isArray(res.result.ocr_languages)
            ? (res.result.ocr_languages as string[])
            : ["eng"],
          tesseractVersion: res.result.tesseract_version
            ? String(res.result.tesseract_version)
            : undefined,
          tesseractPath: res.result.tesseract_path
            ? String(res.result.tesseract_path)
            : undefined,
          status: "healthy"
        };
      }
      return {
        ok: false,
        sidecar: "unknown",
        protocol: 1,
        engineVersion: "unknown",
        pythonVersion: "unknown",
        pdfBackend: "unknown",
        ocrAvailable: false,
        status: "unhealthy",
        error: res.error?.message || "Health check failed."
      };
    } catch (err) {
      return {
        ok: false,
        sidecar: "unknown",
        protocol: 1,
        engineVersion: "unknown",
        pythonVersion: "unknown",
        pdfBackend: "unknown",
        ocrAvailable: false,
        status: "error",
        error: err instanceof Error ? err.message : String(err)
      };
    }
  }

  public async executeAudit(
    packetDir: string,
    packetId: string,
    asOf: string
  ): Promise<AuditStatusResponse> {
    const jobId = `audit-${crypto.randomUUID()}`;
    this.currentAuditJobId = jobId;

    try {
      const response = await this.sendRequest(
        "audit_packet",
        {
          packet_dir: packetDir,
          packet_id: packetId,
          as_of: asOf
        },
        120000 // 2 min timeout for packet audit
      );

      this.currentAuditJobId = null;

      if (!response.ok) {
        return {
          jobId,
          packetId,
          status: "failed",
          error: {
            code: response.error?.code || "AUDIT_FAILED",
            message: response.error?.message || "Audit execution failed."
          }
        };
      }

      const auditData = response.result?.audit as RedactedAuditResult;
      return {
        jobId,
        packetId,
        status: "completed",
        result: auditData,
        progress: {
          jobId,
          stage: "completed",
          completed: 5,
          total: 5,
          percent: 100
        }
      };
    } catch (err) {
      this.currentAuditJobId = null;
      return {
        jobId,
        packetId,
        status: "failed",
        error: {
          code: "AUDIT_EXCEPTION",
          message: err instanceof Error ? err.message : String(err)
        }
      };
    }
  }

  public async cancelAudit(packetId: string): Promise<AuditStatusResponse> {
    const activeJobId = this.currentAuditJobId || `job-${packetId}`;
    this.currentAuditJobId = null;

    // Reject all in-flight audit requests
    this.rejectAllPending(new Error("Audit was cancelled by user."));

    // Hard kill and respawn to guarantee immediate cancellation of heavy Python loops
    if (this.child) {
      try {
        this.child.kill("SIGTERM");
      } catch {
        // Ignore kill errors
      }
      this.child = null;
    }

    // Respawn cleanly
    await this.start().catch(() => {});

    return {
      jobId: activeJobId,
      packetId,
      status: "cancelled"
    };
  }

  public async shutdown(): Promise<void> {
    this.isShuttingDown = true;
    if (this.child && !this.child.killed) {
      try {
        await this.sendRequest("shutdown", {}, 2000);
      } catch {
        // If timeout or error, force kill
        this.child.kill("SIGKILL");
      }
      this.child = null;
    }
  }
}
