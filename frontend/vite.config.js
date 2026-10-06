import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: 'localhost',
    // Same-origin API in development, as in production: the HttpOnly session cookie (SameSite=Strict) is only
    // sent to the site that set it. 127.0.0.1, not localhost: the API binds IPv4 only.
    proxy: {
      '/api': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000',
      '/ready': 'http://127.0.0.1:8000',
    },
  },
  // Pre-bundled at dev-server start (it's only imported by the lazily loaded QR scanner and its
  // worker, so Vite would otherwise discover it mid-session and serve "504 Outdated Optimize Dep").
  optimizeDeps: {
    include: ['jsqr'],
  },
  // The QR decoder worker imports jsQR, so it is built as an ES module worker.
  worker: {
    format: 'es',
  },
  // Vitest: component tests in a simulated browser (npm test).
  test: {
    environment: 'jsdom',
    setupFiles: ['./tests/setup.js'],
    include: ['tests/**/*.test.{js,jsx}'],
    css: false,
    restoreMocks: true,
  }
})
