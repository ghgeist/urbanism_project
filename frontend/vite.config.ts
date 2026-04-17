/// <reference types="vitest" />
import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

const isReplit = Boolean(process.env.REPLIT_DOMAINS || process.env.REPL_ID)

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 5000,
    allowedHosts: true,
    ...(isReplit
      ? {
          hmr: {
            clientPort: 443,
            protocol: 'wss',
          },
        }
      : {}),
    headers: {
      'Cache-Control': 'no-store, no-cache, must-revalidate, max-age=0',
    },
    proxy: {
      '/health': 'http://127.0.0.1:8000',
      '/geocode': 'http://127.0.0.1:8000',
      '/nwi': 'http://127.0.0.1:8000',
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
  },
})
