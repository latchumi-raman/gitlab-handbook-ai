/// <reference types="vitest" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { "@": path.resolve(__dirname, "./src") },
  },
  server: {
    port: 5173,
    proxy: {
      // Proxy all /api calls to FastAPI during development
      // This means you never need to worry about CORS in dev
      "/api": {
        target:      "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
    // ── Test config ───────────────────────────────────────────────────────────
  test: {
    globals:     true,
    environment: "jsdom",
    setupFiles:  ["./src/__tests__/setup.ts"],
    css:         false,
    coverage: {
      provider: "v8",
      reporter: ["text", "html"],
      include:  ["src/**/*.{ts,tsx}"],
      exclude:  ["src/**/*.d.ts", "src/main.tsx"],
    },
  },
});