import { app, BrowserWindow, session } from "electron";
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
      sandbox: true
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

  // Initialize and start sidecar manager
  sidecarManager = new SidecarManager(workspaceManager.getWorkspaceRoot());
  await sidecarManager.start();

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
