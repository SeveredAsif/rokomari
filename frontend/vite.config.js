import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const AUTH_TARGET =
  process.env.VITE_AUTH_TARGET || "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 3000,
    proxy: {
      "/auth": {
        target: AUTH_TARGET,
        changeOrigin: true
      }
    }
  }
});