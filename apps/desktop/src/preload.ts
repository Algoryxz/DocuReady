import { contextBridge } from "electron";

const desktopBridge = Object.freeze({
  platform: process.platform,
  getVersion: (): string => process.env.npm_package_version ?? "0.1.0"
});

contextBridge.exposeInMainWorld("docureadyDesktop", desktopBridge);
