import crypto from "node:crypto";
import fs from "node:fs/promises";
import { createRequire } from "node:module";
import os from "node:os";
import path from "node:path";
import type {
  DocumentDescriptor,
  PacketDescriptor,
  SupportedFileType,
  SupportedMimeType
} from "../shared/types.ts";
import {
  MAX_PACKET_SIZE_BYTES,
  validateFileSize,
  validateFileSignature
} from "./security.ts";

function getElectronApp(): { getPath(name: string): string } | null {
  if (typeof process !== "undefined" && process.versions && process.versions.electron) {
    try {
      if (typeof require !== "undefined") {
        const electron = require("electron");
        return (electron as any).app || (electron as any).default?.app || null;
      }
      if (typeof import.meta !== "undefined" && import.meta && import.meta.url) {
        const nodeRequire = createRequire(import.meta.url);
        const electron = nodeRequire("electron");
        return (electron as any).app || (electron as any).default?.app || null;
      }
    } catch {
      return null;
    }
  }
  return null;
}

export interface StoredDocument {
  id: string;
  name: string;
  size: number;
  mimeType: SupportedMimeType;
  fileType: SupportedFileType;
  originalPath: string;
}

export interface StoredPacket {
  packetId: string;
  schemeId: string;
  asOf: string;
  workspaceDir: string;
  documentCount: number;
  createdAt: string;
}

export class WorkspaceManager {
  private workspaceRoot: string;
  private documents: Map<string, StoredDocument> = new Map();
  private packets: Map<string, StoredPacket> = new Map();

  constructor(customRoot?: string) {
    const app = getElectronApp();
    this.workspaceRoot =
      customRoot ||
      (app
        ? path.join(app.getPath("temp"), "docuready-workspaces")
        : path.join(process.env.TEMP || os.tmpdir(), "docuready-workspaces"));
  }

  public getWorkspaceRoot(): string {
    return this.workspaceRoot;
  }

  public async initialize(): Promise<void> {
    await fs.mkdir(this.workspaceRoot, { recursive: true });
    // Recover/clean any stale directories from previous sessions
    await this.recoverStaleWorkspaces();
  }

  private async recoverStaleWorkspaces(): Promise<void> {
    try {
      const entries = await fs.readdir(this.workspaceRoot, { withFileTypes: true });
      for (const entry of entries) {
        if (entry.isDirectory()) {
          const dirPath = path.join(this.workspaceRoot, entry.name);
          await fs.rm(dirPath, { recursive: true, force: true }).catch(() => {});
        }
      }
    } catch {
      // Ignore initial cleanup errors
    }
  }

  public async registerDocument(
    filePath: string
  ): Promise<DocumentDescriptor | null> {
    const resolvedPath = path.resolve(filePath);

    // Validate size
    const sizeCheck = await validateFileSize(resolvedPath);
    if (!sizeCheck.valid) {
      throw new Error(`File '${path.basename(resolvedPath)}' exceeds size limit or is empty.`);
    }

    // Validate file magic bytes
    const sigCheck = await validateFileSignature(resolvedPath);
    if (!sigCheck.valid || !sigCheck.mimeType || !sigCheck.fileType) {
      throw new Error(
        `File '${path.basename(resolvedPath)}' has an invalid signature or unsupported format.`
      );
    }

    const id = `doc-${crypto.randomUUID()}`;
    const sanitizedName = path.basename(resolvedPath).replace(/[^a-zA-Z0-9._-]/g, "_");

    const stored: StoredDocument = {
      id,
      name: sanitizedName,
      size: sizeCheck.size,
      mimeType: sigCheck.mimeType,
      fileType: sigCheck.fileType,
      originalPath: resolvedPath
    };

    this.documents.set(id, stored);

    return {
      id,
      name: sanitizedName,
      size: sizeCheck.size,
      mimeType: sigCheck.mimeType,
      fileType: sigCheck.fileType
    };
  }

  public getStoredDocument(id: string): StoredDocument | undefined {
    return this.documents.get(id);
  }

  public async getDocumentContent(documentIdOrName: string): Promise<Buffer | null> {
    if (!documentIdOrName || typeof documentIdOrName !== "string") {
      return null;
    }
    const cleanId = documentIdOrName.trim();
    if (cleanId.includes("..") || cleanId.includes("/") || cleanId.includes("\\")) {
      return null;
    }

    let targetDoc = this.documents.get(cleanId);
    if (!targetDoc) {
      for (const doc of this.documents.values()) {
        if (doc.name === cleanId || doc.id === cleanId) {
          targetDoc = doc;
          break;
        }
      }
    }

    if (!targetDoc) {
      return null;
    }

    try {
      return await fs.readFile(targetDoc.originalPath);
    } catch {
      return null;
    }
  }

  public async createPacket(
    documentIds: string[],
    schemeId: string = "general_scholarship",
    asOf?: string
  ): Promise<PacketDescriptor> {
    if (!documentIds || documentIds.length === 0) {
      throw new Error("Cannot create packet: At least one document is required.");
    }

    const packetId = `pkt-${crypto.randomUUID().slice(0, 8)}`;
    const packetDir = path.join(this.workspaceRoot, packetId);

    await fs.mkdir(packetDir, { recursive: true });

    let totalSize = 0;
    const seenNames = new Set<string>();
    for (const docId of documentIds) {
      const doc = this.documents.get(docId);
      if (!doc) {
        throw new Error(`Document ID '${docId}' was not found in the current session.`);
      }

      totalSize += doc.size;
      if (totalSize > MAX_PACKET_SIZE_BYTES) {
        await fs.rm(packetDir, { recursive: true, force: true }).catch(() => {});
        throw new Error("Total packet size exceeds the 200MB limit.");
      }

      let filename = doc.name;
      if (seenNames.has(filename)) {
        const ext = path.extname(doc.name);
        const base = path.basename(doc.name, ext);
        filename = `${base}_${doc.id}${ext}`;
      }
      seenNames.add(filename);

      const destPath = path.join(packetDir, filename);
      // Validate directory traversal
      if (!destPath.startsWith(packetDir)) {
        throw new Error("Directory traversal detected in document filename.");
      }

      await fs.copyFile(doc.originalPath, destPath);
    }

    const effectiveAsOf = asOf || new Date().toISOString().split("T")[0];
    const createdAt = new Date().toISOString();

    const storedPacket: StoredPacket = {
      packetId,
      schemeId,
      asOf: effectiveAsOf,
      workspaceDir: packetDir,
      documentCount: documentIds.length,
      createdAt
    };

    this.packets.set(packetId, storedPacket);

    return {
      packetId,
      schemeId,
      asOf: effectiveAsOf,
      documentCount: documentIds.length,
      createdAt
    };
  }

  public getStoredPacket(packetId: string): StoredPacket | undefined {
    return this.packets.get(packetId);
  }

  public getActiveWorkspaceCount(): number {
    return this.packets.size;
  }

  public async cleanPacket(packetId: string): Promise<boolean> {
    const packet = this.packets.get(packetId);
    if (!packet) return false;

    try {
      await fs.rm(packet.workspaceDir, { recursive: true, force: true });
    } catch {
      // Ignore removal error
    }
    this.packets.delete(packetId);
    return true;
  }

  public async clearAll(): Promise<number> {
    let count = 0;
    for (const packetId of Array.from(this.packets.keys())) {
      await this.cleanPacket(packetId);
      count++;
    }
    this.documents.clear();
    await this.recoverStaleWorkspaces();
    return count;
  }
}
