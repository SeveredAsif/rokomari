import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const AUTH_TARGET =
  process.env.VITE_AUTH_TARGET || "http://localhost:8000";

const PRODUCTSEARCH_TARGET =
  process.env.VITE_PRODUCTSEARCH_TARGET || "http://localhost:8002";

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 3000,
    proxy: {
      "/auth": {
        target: AUTH_TARGET,
        changeOrigin: true,
      },
      "/productsearch": {
        target: PRODUCTSEARCH_TARGET,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/productsearch/, ""),
      },
      "/recommendation": {
      target: "http://localhost:8001",
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/recommendation/, ""),
      },
    },
  },
});