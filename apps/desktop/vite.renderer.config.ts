import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";
import { fileURLToPath } from "node:url";

const currentDir = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  root: path.resolve(currentDir, "src/renderer"),
  base: "./",
  build: {
    outDir: path.resolve(currentDir, ".vite/renderer/main_window"),
    emptyOutDir: true
  },
  plugins: [react()]
});

