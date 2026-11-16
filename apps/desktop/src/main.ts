import { app, BrowserWindow, dialog, session } from "electron";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { IpcHandlerRegistry } from "./main/ipc.ts";
import { getContentSecurityPolicy } from "./main/security.ts";
import { SidecarManager } from "./main/sidecar.ts";
import { WorkspaceManager } from "./main/workspace.ts";

const isDevelopment = !app.isPackaged;

let workspaceManager: WorkspaceManager | null = null;
let sidecarManager: SidecarManager | null = null;
let mainWindow: BrowserWindow | null = null;

function installContentSecurityPolicy(): void {
  const policy = getContentSecurityPolicy(isDevelopment);

  session.defaultSession.webRequest.onHeadersReceived((details, callback) => {
    callback({
      responseHeaders: {
        ...details.responseHeaders,
        "Content-Security-Policy": [policy]
      }
    });
  });
}

async function createMainWindow(): Promise<BrowserWindow> {
  const window = new BrowserWindow({
    width: 1440,
    height: 940,
    minWidth: 1100,
    minHeight: 720,
    show: false,
    backgroundColor: "#f6f7f9",
    webPreferences: {
      preload: path.join(__dirname, "preload.cjs"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
      webSecurity: true
    }
  });

  // Strict popup restriction: deny any window.open()
  window.webContents.setWindowOpenHandler(() => ({ action: "deny" }));

  // Strict navigation guard: prevent navigating away from application entry
  window.webContents.on("will-navigate", (event, targetUrl) => {
    if (isDevelopment && MAIN_WINDOW_VITE_DEV_SERVER_URL) {
      const allowedOrigin = new URL(MAIN_WINDOW_VITE_DEV_SERVER_URL).origin;
      try {
        if (new URL(targetUrl).origin !== allowedOrigin) event.preventDefault();
      } catch {
        event.preventDefault();
      }
      return;
    }

    const expectedEntry = pathToFileURL(
      path.join(__dirname, `../renderer/${MAIN_WINDOW_VITE_NAME}/index.html`)
    ).href;
    if (targetUrl !== expectedEntry) event.preventDefault();
  });

  if (MAIN_WINDOW_VITE_DEV_SERVER_URL) {
    await window.loadURL(MAIN_WINDOW_VITE_DEV_SERVER_URL);
  } else {
    await window.loadFile(
      path.join(__dirname, `../renderer/${MAIN_WINDOW_VITE_NAME}/index.html`)
    );
  }

  window.once("ready-to-show", () => window.show());
  mainWindow = window;
  return window;
}

app.whenReady().then(async () => {
  installContentSecurityPolicy();

  // Initialize isolated workspace manager
  workspaceManager = new WorkspaceManager();
  await workspaceManager.initialize();

  // Initialize and start the bundled sidecar before exposing document workflows.
  sidecarManager = new SidecarManager(workspaceManager.getWorkspaceRoot());
  await sidecarManager.start();

  // A process that merely spawned is not proof that the engine or OCR runtime
  // is healthy. Verify the JSON-RPC handshake and bundled OCR before showing
  // the application as ready.
  const engineHealth = await sidecarManager.getHealth(30000);
  if (!engineHealth.ok) {
    throw new Error(engineHealth.error || "The document engine failed its health check.");
  }
  if (app.isPackaged && (!engineHealth.ocrAvailable || !engineHealth.isBundled)) {
    throw new Error(
      "The bundled OCR runtime is unavailable. This installation is incomplete; reinstall a complete DocuReady package."
    );
  }

  // Register all typed IPC handlers
  const ipcRegistry = new IpcHandlerRegistry(
    workspaceManager,
    sidecarManager,
    isDevelopment,
    MAIN_WINDOW_VITE_DEV_SERVER_URL,
    MAIN_WINDOW_VITE_NAME
  );
  ipcRegistry.registerAll();

  await createMainWindow();

  app.on("activate", async () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      await createMainWindow();
    }
  });
}).catch((error: unknown) => {
  const message = error instanceof Error ? error.message : String(error);
  console.error("[startup] DocuReady failed to initialize:", message);
  dialog.showErrorBox(
    "DocuReady could not start",
    `The application failed its startup checks.\n\n${message}\n\nReinstall the complete package and try again.`
  );
  app.quit();
});

app.on("before-quit", async () => {
  if (sidecarManager) {
    await sidecarManager.shutdown().catch(() => {});
  }
  if (workspaceManager) {
    await workspaceManager.clearAll().catch(() => {});
  }
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

declare const MAIN_WINDOW_VITE_DEV_SERVER_URL: string | undefined;
declare const MAIN_WINDOW_VITE_NAME: string;
