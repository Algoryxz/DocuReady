import { contextBridge, ipcRenderer, IpcRendererEvent } from "electron";
import type {
  AuditProgress,
  AuditStatusResponse,
  ClearSessionResult,
  CreatePacketOptions,
  DocuReadyBridge,
  DocumentDescriptor,
  EngineHealth,
  ExportReportOptions,
  ExportReportResult,
  PacketDescriptor
} from "./shared/types.ts";

const desktopBridge: DocuReadyBridge = Object.freeze({
  platform: process.platform,
  version: "0.1.0",

  async getEngineHealth(): Promise<EngineHealth> {
    return await ipcRenderer.invoke("engine:get-health");
  },

  async selectDocuments(): Promise<DocumentDescriptor[]> {
    return await ipcRenderer.invoke("documents:select");
  },

  async createPacket(options: CreatePacketOptions): Promise<PacketDescriptor> {
    if (!options || !Array.isArray(options.documentIds) || options.documentIds.length === 0) {
      throw new Error("createPacket requires an options object with non-empty documentIds.");
    }
    return await ipcRenderer.invoke("packet:create", {
      documentIds: options.documentIds,
      schemeId: options.schemeId || "general_scholarship",
      asOf: options.asOf
    });
  },

  async startAudit(packetId: string): Promise<AuditStatusResponse> {
    if (typeof packetId !== "string" || !packetId) {
      throw new Error("startAudit requires a valid packetId string.");
    }
    return await ipcRenderer.invoke("audit:start", packetId);
  },

  async cancelAudit(packetId: string): Promise<AuditStatusResponse> {
    if (typeof packetId !== "string" || !packetId) {
      throw new Error("cancelAudit requires a valid packetId string.");
    }
    return await ipcRenderer.invoke("audit:cancel", packetId);
  },

  async getAuditStatus(packetId: string): Promise<AuditStatusResponse> {
    if (typeof packetId !== "string" || !packetId) {
      throw new Error("getAuditStatus requires a valid packetId string.");
    }
    return await ipcRenderer.invoke("audit:get-status", packetId);
  },

  async exportReport(options: ExportReportOptions): Promise<ExportReportResult> {
    if (!options || typeof options.packetId !== "string" || !options.packetId) {
      throw new Error("exportReport requires a valid packetId.");
    }
    if (options.format !== "json" && options.format !== "markdown") {
      throw new Error("exportReport format must be 'json' or 'markdown'.");
    }
    return await ipcRenderer.invoke("report:export", options);
  },

  async clearSession(): Promise<ClearSessionResult> {
    return await ipcRenderer.invoke("session:clear");
  },

  onAuditProgress(callback: (progress: AuditProgress) => void): () => void {
    if (typeof callback !== "function") {
      throw new Error("onAuditProgress callback must be a function.");
    }

    const handler = (_event: IpcRendererEvent, progress: AuditProgress) => {
      callback(progress);
    };

    ipcRenderer.on("audit:progress", handler);
    return () => {
      ipcRenderer.removeListener("audit:progress", handler);
    };
  }
});

contextBridge.exposeInMainWorld("docureadyDesktop", desktopBridge);
