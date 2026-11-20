import type { IpcMainInvokeEvent } from "electron";
import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";
import type { SupportedFileType, SupportedMimeType } from "../shared/types.ts";

export const MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024; // 50MB per file
export const MAX_PACKET_SIZE_BYTES = 200 * 1024 * 1024; // 200MB per packet

export function getContentSecurityPolicy(isDevelopment: boolean): string {
  return [
    "default-src 'self'",
    "script-src 'self'",
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: blob:",
    "font-src 'self' data:",
    isDevelopment
      ? "connect-src 'self' ws://localhost:* http://localhost:*"
      : "connect-src 'self'",
    "object-src 'none'",
    "base-uri 'none'",
    "form-action 'self'",
    "frame-ancestors 'none'"
  ].join("; ");
}

export function validateIpcSender(
  event: IpcMainInvokeEvent,
  isDevelopment: boolean,
  devServerUrl?: string,
  mainWindowName?: string
): void {
  if (!event.senderFrame) {
    throw new Error("Security violation: IPC senderFrame is undefined.");
  }

  const senderUrl = event.senderFrame.url;
  if (!senderUrl) {
    throw new Error("Security violation: IPC sender URL is empty.");
  }

  if (isDevelopment && devServerUrl) {
    let allowedOrigin: string;
    let senderOrigin: string;
    try {
      allowedOrigin = new URL(devServerUrl).origin;
      senderOrigin = new URL(senderUrl).origin;
    } catch {
      throw new Error("Security violation: Invalid IPC sender URL in development.");
    }

    if (senderOrigin !== allowedOrigin) {
      throw new Error(
        `Security violation: Unauthorized IPC origin '${senderOrigin}', expected '${allowedOrigin}'`
      );
    }
    return;
  }

  // Packaged build: sender must match the exact file:// URL of the bundled renderer
  if (mainWindowName) {
    const expectedEntry = pathToFileURL(
      path.join(__dirname, `../renderer/${mainWindowName}/index.html`)
    ).href;
    if (senderUrl !== expectedEntry) {
      throw new Error(
        `Security violation: Unauthorized packaged IPC entry point '${senderUrl}'`
      );
    }
  }
}

export async function validateFileSignature(
  filePath: string
): Promise<{ valid: boolean; mimeType?: SupportedMimeType; fileType?: SupportedFileType }> {
  const handle = await fs.open(filePath, "r");
  try {
    const buffer = Buffer.alloc(16);
    const { bytesRead } = await handle.read(buffer, 0, 16, 0);
    if (bytesRead < 4) {
      return { valid: false };
    }

    // PDF magic bytes: %PDF- (0x25, 0x50, 0x44, 0x46, 0x2D)
    if (
      buffer[0] === 0x25 &&
      buffer[1] === 0x50 &&
      buffer[2] === 0x44 &&
      buffer[3] === 0x46 &&
      buffer[4] === 0x2d
    ) {
      return { valid: true, mimeType: "application/pdf", fileType: "pdf" };
    }

    // PNG magic bytes: 0x89 0x50 0x4E 0x47 0x0D 0x0A 0x1A 0x0A
    if (
      bytesRead >= 8 &&
      buffer[0] === 0x89 &&
      buffer[1] === 0x50 &&
      buffer[2] === 0x4e &&
      buffer[3] === 0x47 &&
      buffer[4] === 0x0d &&
      buffer[5] === 0x0a &&
      buffer[6] === 0x1a &&
      buffer[7] === 0x0a
    ) {
      return { valid: true, mimeType: "image/png", fileType: "png" };
    }

    // JPEG magic bytes: 0xFF 0xD8 0xFF
    if (buffer[0] === 0xff && buffer[1] === 0xd8 && buffer[2] === 0xff) {
      return { valid: true, mimeType: "image/jpeg", fileType: "jpeg" };
    }

    return { valid: false };
  } finally {
    await handle.close();
  }
}

export async function validateFileSize(
  filePath: string,
  maxBytes: number = MAX_FILE_SIZE_BYTES
): Promise<{ valid: boolean; size: number }> {
  const stat = await fs.stat(filePath);
  return {
    valid: stat.size > 0 && stat.size <= maxBytes,
    size: stat.size
  };
}
