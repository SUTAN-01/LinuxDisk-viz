import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: { environment: "jsdom", globals: true, setupFiles: ["./src/test-setup.ts"] },
  build: { outDir: "../webapp/diskviz_api/static", emptyOutDir: true },
});
