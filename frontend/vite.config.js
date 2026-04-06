import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In docker-compose, the frontend runs inside a container, so `localhost` would
// point back to the frontend container itself. Proxying to nginx keeps routing
// consistent with production.
const BACKEND_TARGET = process.env.VITE_BACKEND_TARGET || "http://nginx";

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 3000,
    proxy: {
      "/auth": {
        target: BACKEND_TARGET,
        changeOrigin: true,
      },
      "/productsearch": {
        target: BACKEND_TARGET,
        changeOrigin: true,
      },
      "/recommendation": {
        target: BACKEND_TARGET,
        changeOrigin: true,
      },
      "/interaction": {
        target: BACKEND_TARGET,
        changeOrigin: true,
      },
    },
  },
});