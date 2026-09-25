// End-to-end smoke tests (Playwright) against the RUNNING stack: frontend :5173 -> Python API :8000 ->
// C# API :5188 -> MySQL. Start it first (.\sr.ps1 run), then: npm run test:e2e
// Uses the Microsoft Edge already installed on Windows (no browser download); set E2E_BROWSER=chromium
// to use Playwright's own Chromium instead (after `npx playwright install chromium`).
import { defineConfig, devices } from "@playwright/test";

const channel = process.env.E2E_BROWSER === "chromium" ? undefined : "msedge";

export default defineConfig({
  testDir: "e2e",
  timeout: 30_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  retries: 0,
  reporter: [["list"]],
  use: {
    baseURL: process.env.E2E_BASE_URL || "http://localhost:5173",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  outputDir: "test-results/e2e",
  projects: [
    { name: "desktop", use: { ...devices["Desktop Edge"], channel }, testIgnore: /mobile\.spec\.js/ },
    { name: "mobile", use: { ...devices["Pixel 7"], channel, browserName: "chromium" }, testMatch: /mobile\.spec\.js/ },
  ],
});
