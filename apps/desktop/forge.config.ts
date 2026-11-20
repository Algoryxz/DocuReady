import type { ForgeConfig } from "@electron-forge/shared-types";
import { MakerZIP } from "@electron-forge/maker-zip";
import { MakerSquirrel } from "@electron-forge/maker-squirrel";
import { VitePlugin } from "@electron-forge/plugin-vite";
import path from "node:path";
import { fileURLToPath } from "node:url";

const currentDir = path.dirname(fileURLToPath(import.meta.url));

const config: ForgeConfig = {
  packagerConfig: {
    asar: true,
    extraResource: [
      path.resolve(currentDir, "../../sidecar/dist/docuready_sidecar")
    ]
  },
  makers: [
    new MakerSquirrel({
      name: "DocuReady",
      authors: "DocuReady Team",
      setupExe: "DocuReady-0.1.0-Setup.exe"
    }),
    new MakerZIP({}, ["win32"])
  ],
  plugins: [
    new VitePlugin({
      build: [
        { entry: "src/main.ts", config: "vite.main.config.ts" },
        { entry: "src/preload.ts", config: "vite.preload.config.ts" }
      ],
      renderer: [
        { name: "main_window", config: "vite.renderer.config.ts" }
      ]
    })
  ]
};

export default config;
