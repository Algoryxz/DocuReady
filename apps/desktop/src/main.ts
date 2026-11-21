import { app, BrowserWindow, dialog, session } from "electron";
import { spawn } from "node:child_process";
import path from "node:path";
import { pathToFileURL } from "node:url";
import { IpcHandlerRegistry } from "./main/ipc.ts";
import { getContentSecurityPolicy } from "./main/security.ts";
import { SidecarManager } from "./main/sidecar.ts";
import { WorkspaceManager } from "./main/workspace.ts";

function handleSquirrelEvents(): boolean {
  if (process.platform !== "win32") {
    return false;
  }

  const squirrelCommand = process.argv.find((arg) =>
    arg.startsWith("--squirrel-install") ||
    arg.startsWith("--squirrel-updated") ||
    arg.startsWith("--squirrel-uninstall") ||
    arg.startsWith("--squirrel-obsolete")
  );

  if (!squirrelCommand) {
    return false;
  }

  const appExe = path.basename(process.execPath);
  const updateExe = path.resolve(path.dirname(process.execPath), "..", "Update.exe");

  const runUpdate = (args: string[]) => {
    try {
      spawn(updateExe, args, { detached: true });
    } catch {
      // Ignore shortcut error during Squirrel lifecycle
    }
  };

  if (squirrelCommand.startsWith("--squirrel-install") || squirrelCommand.startsWith("--squirrel-updated")) {
    runUpdate(["--createShortcut", appExe]);
  } else if (squirrelCommand.startsWith("--squirrel-uninstall")) {
    runUpdate(["--removeShortcut", appExe]);
  }

  app.quit();
  process.exit(0);
  return true;
}

if (handleSquirrelEvents()) {
  // Exited early for squirrel lifecycle events
}

const isDevelopment = !app.isPackaged;

let workspaceManager: WorkspaceManager | null = null;
let sidecarManager: SidecarManager | null = null;
let mainWindow: BrowserWindow | null = null;
let shutdownStarted = false;
let shutdownComplete = false;

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
  workspaceManager = new WorkspaceManager(
    path.join(app.getPath("temp"), "docuready-workspaces")
  );
  await workspaceManager.initialize();

  // Initialize and start the bundled sidecar before exposing document workflows.
  sidecarManager = new SidecarManager(workspaceManager.getWorkspaceRoot(), undefined, !isDevelopment);
  await sidecarManager.start();

  // A process that merely spawned is not proof that the engine or OCR runtime
  // is healthy. Verify the JSON-RPC handshake and bundled OCR before showing
  // the application as ready.
  const engineHealth = await sidecarManager.getHealth(45000);
  if (!engineHealth.ok) {
    throw new Error(`The document engine failed its startup check: ${engineHealth.error || "unknown sidecar error"}`);
  }
  if (!isDevelopment && (!engineHealth.ocrAvailable || !engineHealth.isBundled)) {
    throw new Error(
      `The packaged OCR runtime is unavailable. Expected bundled Tesseract; source=${engineHealth.ocrSource || "unknown"}, available=${engineHealth.ocrAvailable}.`
    );
  }
  if (!isDevelopment && !engineHealth.ocrLanguages?.includes("eng")) {
    throw new Error("The bundled OCR runtime is missing the required English trained-data file (eng.traineddata).");
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
    message + "\n\nReinstall DocuReady. If the problem continues, provide the diagnostic details to the project team."
  );
  app.quit();
});

app.on("before-quit", (event) => {
  if (shutdownComplete) return;
  event.preventDefault();
  if (shutdownStarted) return;
  shutdownStarted = true;

  void (async () => {
    try {
      await sidecarManager?.shutdown();
    } catch (error) {
      console.error("[shutdown] Sidecar cleanup failed:", error);
    }
    try {
      await workspaceManager?.clearAll();
    } catch (error) {
      console.error("[shutdown] Workspace cleanup failed:", error);
    }
    shutdownComplete = true;
    app.quit();
  })();
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

declare const MAIN_WINDOW_VITE_DEV_SERVER_URL: string | undefined;
declare const MAIN_WINDOW_VITE_NAME: string;
