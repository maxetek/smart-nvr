import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    host: true,
    port: 5173,
    proxy: {
      "/api": {
        target: "http://backend:8000",
        changeOrigin: true,
      },
      "/ws": {
        target: "http://backend:8000",
        ws: true,
      },
      "/go2rtc": {
        target: "http://go2rtc:1984",
        rewrite: (path) => path.replace(/^\/go2rtc/, ""),
        ws: true,
      },
    },
  },
});
