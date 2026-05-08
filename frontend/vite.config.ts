/// <reference types="vitest" />
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import { resolve } from "path";

// Build into FastAPI's static dir so /ui serves the bundle.
// In dev, proxy /cno/* and /healthz to the running uvicorn on :8000.
export default defineConfig({
  plugins: [react()],
  base: "/ui/",
  build: {
    outDir: resolve(__dirname, "../cno/static"),
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    proxy: {
      "/cno":     "http://localhost:8000",
      "/healthz": "http://localhost:8000",
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/__tests__/setup.ts",
  },
});
