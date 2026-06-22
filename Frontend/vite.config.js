import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Vite config for the voice agent frontend.
// - Default dev port: 5173 (Vite standard). Backend runs on 8000.
// - The Vite dev server proxies /ws to the FastAPI backend so the browser
//   doesn't get blocked by CORS or mixed-content issues during local dev.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: '0.0.0.0',
    proxy: {
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
        changeOrigin: true,
      },
    },
  },
})
