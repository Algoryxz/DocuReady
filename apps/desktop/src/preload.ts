import { contextBridge } from "electron";

const desktopBridge = Object.freeze({
  platform: process.platform,
  version: "0.1.0"
});

contextBridge.exposeInMainWorld("docureadyDesktop", desktopBridge);
