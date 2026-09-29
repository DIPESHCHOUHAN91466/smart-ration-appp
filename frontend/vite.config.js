import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: 'localhost'
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
