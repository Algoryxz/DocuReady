import { BrowserWindow, dialog, ipcMain, IpcMainInvokeEvent } from "electron";
import fs from "node:fs/promises";
import type {
  AuditProgress,
  AuditStatusResponse,
  ClearSessionResult,
  CreatePacketOptions,
  DiagnosticReport,
  DocumentDescriptor,
  EngineHealth,
  ExportReportOptions,
  ExportReportResult,
  PacketDescriptor,
  RedactedAuditResult
} from "../shared/types.ts";
import { validateIpcSender } from "./security.ts";
import { SidecarManager } from "./sidecar.ts";
import { WorkspaceManager } from "./workspace.ts";

export class IpcHandlerRegistry {
  private workspaceManager: WorkspaceManager;
  private sidecarManager: SidecarManager;
  private isDevelopment: boolean;
  private devServerUrl?: string;
  private mainWindowName?: string;
  private auditResults: Map<string, AuditStatusResponse> = new Map();

  constructor(
    workspaceManager: WorkspaceManager,
    sidecarManager: SidecarManager,
    isDevelopment: boolean,
    devServerUrl?: string,
    mainWindowName?: string
  ) {
    this.workspaceManager = workspaceManager;
    this.sidecarManager = sidecarManager;
    this.isDevelopment = isDevelopment;
    this.devServerUrl = devServerUrl;
    this.mainWindowName = mainWindowName;
  }

  private validateSender(event: IpcMainInvokeEvent): void {
    validateIpcSender(
      event,
      this.isDevelopment,
      this.devServerUrl,
      this.mainWindowName
    );
  }

  public registerAll(): void {
    // 1. Engine Health
    ipcMain.handle("engine:get-health", async (event): Promise<EngineHealth> => {
      this.validateSender(event);
      return await this.sidecarManager.getHealth();
    });

    // 2. Select Documents
    ipcMain.handle(
      "documents:select",
      async (event): Promise<DocumentDescriptor[]> => {
        this.validateSender(event);

        const focusedWindow = BrowserWindow.getFocusedWindow();
        const result = await dialog.showOpenDialog(focusedWindow || undefined as any, {
          title: "Select Document Files",
          properties: ["openFile", "multiSelections"],
          filters: [
            {
              name: "Supported Documents (*.pdf, *.png, *.jpg, *.jpeg)",
              extensions: ["pdf", "png", "jpg", "jpeg"]
            }
          ]
        });

        if (result.canceled || result.filePaths.length === 0) {
          return [];
        }

        const descriptors: DocumentDescriptor[] = [];
        for (const filePath of result.filePaths) {
          try {
            const descriptor = await this.workspaceManager.registerDocument(filePath);
            if (descriptor) {
              descriptors.push(descriptor);
            }
          } catch (err) {
            console.warn(`[documents:select] Skipped '${filePath}':`, err);
          }
        }

        return descriptors;
      }
    );

    // 2b. Retrieve Document Binary Safely
    ipcMain.handle(
      "documents:get-binary",
      async (event, documentId: unknown): Promise<Uint8Array | null> => {
        this.validateSender(event);

        if (typeof documentId !== "string" || !documentId || documentId.length > 256) {
          throw new Error("Invalid document identifier.");
        }

        const buffer = await this.workspaceManager.getDocumentContent(documentId);
        if (!buffer) {
          return null;
        }

        return new Uint8Array(buffer);
      }
    );

    // 3. Create Packet
    ipcMain.handle(
      "packet:create",
      async (event, options: unknown): Promise<PacketDescriptor> => {
        this.validateSender(event);

        if (!options || typeof options !== "object") {
          throw new Error("Invalid parameters: options object is required.");
        }

        const { documentIds, schemeId, asOf } = options as CreatePacketOptions;
        if (!Array.isArray(documentIds) || documentIds.length === 0) {
          throw new Error("Invalid parameters: documentIds must be a non-empty array.");
        }

        for (const id of documentIds) {
          if (typeof id !== "string" || !id.startsWith("doc-")) {
            throw new Error(`Invalid document ID format: '${id}'`);
          }
        }

        const scheme = typeof schemeId === "string" ? schemeId : "general_scholarship";
        const dateStr =
          typeof asOf === "string" && /^\d{4}-\d{2}-\d{2}$/.test(asOf)
            ? asOf
            : undefined;

        return await this.workspaceManager.createPacket(documentIds, scheme, dateStr);
      }
    );

    // 4. Start Audit
    ipcMain.handle(
      "audit:start",
      async (event, packetId: unknown): Promise<AuditStatusResponse> => {
        this.validateSender(event);

        if (typeof packetId !== "string" || !packetId.startsWith("pkt-")) {
          throw new Error("Invalid packetId parameter.");
        }

        const packet = this.workspaceManager.getStoredPacket(packetId);
        if (!packet) {
          throw new Error(`Packet '${packetId}' does not exist or has expired.`);
        }

        // Set initial running status
        const initialStatus: AuditStatusResponse = {
          jobId: `job-${packetId}`,
          packetId,
          status: "running",
          progress: {
            jobId: `job-${packetId}`,
            stage: "intake",
            completed: 1,
            total: 5,
            percent: 20
          }
        };
        this.auditResults.set(packetId, initialStatus);

        // Execute audit in sidecar
        const finalStatus = await this.sidecarManager.executeAudit(
          packet.workspaceDir,
          packetId,
          packet.asOf
        );

        this.auditResults.set(packetId, finalStatus);
        return finalStatus;
      }
    );

    // 5. Cancel Audit
    ipcMain.handle(
      "audit:cancel",
      async (event, packetId: unknown): Promise<AuditStatusResponse> => {
        this.validateSender(event);

        if (typeof packetId !== "string" || !packetId.startsWith("pkt-")) {
          throw new Error("Invalid packetId parameter.");
        }

        const cancelledStatus = await this.sidecarManager.cancelAudit(packetId);
        this.auditResults.set(packetId, cancelledStatus);

        // Clean staged workspace for this packet
        await this.workspaceManager.cleanPacket(packetId);

        return cancelledStatus;
      }
    );

    // 6. Get Audit Status
    ipcMain.handle(
      "audit:get-status",
      async (event, packetId: unknown): Promise<AuditStatusResponse> => {
        this.validateSender(event);

        if (typeof packetId !== "string") {
          throw new Error("Invalid packetId parameter.");
        }

        const existing = this.auditResults.get(packetId);
        if (existing) {
          return existing;
        }

        const packet = this.workspaceManager.getStoredPacket(packetId);
        if (packet) {
          return {
            jobId: `job-${packetId}`,
            packetId,
            status: "staged"
          };
        }

        return {
          jobId: `job-unknown`,
          packetId,
          status: "idle"
        };
      }
    );

    // 7. Export Report
    ipcMain.handle(
      "report:export",
      async (event, options: unknown): Promise<ExportReportResult> => {
        this.validateSender(event);

        if (!options || typeof options !== "object") {
          throw new Error("Invalid export options.");
        }

        const { packetId, format } = options as ExportReportOptions;
        if (typeof packetId !== "string") {
          throw new Error("Invalid packetId.");
        }

        const statusResponse = this.auditResults.get(packetId);
        if (!statusResponse || !statusResponse.result) {
          throw new Error("No completed audit result available to export.");
        }

        const result: RedactedAuditResult = statusResponse.result;
        const extension = format === "markdown" ? "md" : "json";

        const focusedWindow = BrowserWindow.getFocusedWindow();
        const saveDialog = await dialog.showSaveDialog(focusedWindow || undefined as any, {
          title: `Export Audit Report (${format.toUpperCase()})`,
          defaultPath: `docuready_report_${packetId}.${extension}`,
          filters: [
            format === "markdown"
              ? { name: "Markdown (*.md)", extensions: ["md"] }
              : { name: "JSON (*.json)", extensions: ["json"] }
          ]
        });

        if (saveDialog.canceled || !saveDialog.filePath) {
          return { ok: false, cancelled: true };
        }

        let content = "";
        if (format === "markdown") {
          content = this.generateMarkdownReport(result);
        } else {
          content = JSON.stringify(result, null, 2);
        }

        await fs.writeFile(saveDialog.filePath, content, "utf-8");
        return { ok: true, filePath: saveDialog.filePath };
      }
    );

    // 7b. Get Diagnostic Report
    ipcMain.handle(
      "diagnostics:get-report",
      async (event): Promise<DiagnosticReport> => {
        this.validateSender(event);

        const health = await this.sidecarManager.getHealth();
        const sidecarType = this.sidecarManager.getSidecarType();
        const isPackaged = !this.isDevelopment;

        return {
          timestamp: new Date().toISOString(),
          appVersion: "0.1.0",
          platform: process.platform,
          arch: process.arch,
          isPackaged,
          sidecarType,
          protocolVersion: health.protocol || 1,
          engineVersion: health.engineVersion || "0.1.0",
          pythonVersion: health.pythonVersion || "unknown",
          pdfBackend: health.pdfBackend || "pymupdf",
          ocrAvailable: health.ocrAvailable,
          ocrLanguages: health.ocrLanguages || ["eng"],
          ocrSource: health.ocrSource,
          isBundled: health.isBundled,
          tesseractVersion: health.tesseractVersion,
          tesseractPath: health.tesseractPath,
          workspaceHealth: {
            status: "healthy",
            staleWorkspacesCleaned: 0,
            activeWorkspacesCount: this.workspaceManager.getActiveWorkspaceCount()
          },
          resourceStatus: {
            sidecarExecutableFound: sidecarType === "packaged_binary",
            tesseractFound: health.ocrAvailable
          }
        };
      }
    );

    // 8. Clear Session
    ipcMain.handle("session:clear", async (event): Promise<ClearSessionResult> => {
      this.validateSender(event);

      this.auditResults.clear();
      const cleaned = await this.workspaceManager.clearAll();

      return {
        ok: true,
        cleanedWorkspaces: cleaned
      };
    });

    // Forward progress events from sidecar to all open windows
    this.sidecarManager.on("progress", (progress: AuditProgress) => {
      for (const window of BrowserWindow.getAllWindows()) {
        if (!window.isDestroyed()) {
          window.webContents.send("audit:progress", progress);
        }
      }
    });
  }

  private generateMarkdownReport(result: RedactedAuditResult): string {
    const lines: string[] = [];
    lines.push(`# DocuReady Pre-Flight Audit Report`);
    lines.push(``);
    lines.push(`**Packet ID:** \`${result.packet_id}\`  `);
    lines.push(`**Scheme:** ${result.scheme_name}  `);
    lines.push(`**Effective Date:** ${result.as_of || "N/A"}  `);
    lines.push(`**Readiness Score:** **${result.readiness_score}/100**  `);
    lines.push(`**Overall Status:** \`${result.overall_status}\`  `);
    lines.push(``);
    lines.push(`## Statutory Notice`);
    lines.push(
      `> This report is an applicant-side clerical pre-flight check. It does not certify legal eligibility or guarantee approval by any portal or authority.`
    );
    lines.push(``);
    lines.push(`## Findings Summary`);
    lines.push(``);
    lines.push(`| Status | Count |`);
    lines.push(`|---|---|`);
    for (const [k, v] of Object.entries(result.summary_counts || {})) {
      lines.push(`| ${k} | ${v} |`);
    }
    lines.push(``);
    lines.push(`## Detailed Rule Evaluations`);
    lines.push(``);

    for (const finding of result.findings) {
      lines.push(`### ${finding.rule_name} (\`${finding.rule_id}\`)`);
      lines.push(`- **Status:** \`${finding.status}\` | **Severity:** ${finding.severity}`);
      lines.push(`- **Field:** \`${finding.field}\``);
      if (finding.documents_involved && finding.documents_involved.length > 0) {
        lines.push(`- **Documents Involved:** ${finding.documents_involved.join(", ")}`);
      }
      if (finding.reason_code) {
        lines.push(`- **Reason Code:** \`${finding.reason_code}\``);
      }
      if (finding.match_grade) {
        lines.push(`- **Match Grade:** \`${finding.match_grade}\``);
      }
      if (finding.message) {
        lines.push(`- **Message:** ${finding.message}`);
      }
      if (finding.remediation) {
        lines.push(`- **Remediation:** ${finding.remediation}`);
      }
      lines.push(``);
    }

    return lines.join("\n");
  }
}
