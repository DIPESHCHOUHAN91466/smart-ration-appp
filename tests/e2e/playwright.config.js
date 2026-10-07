// End-to-end smoke tests (Playwright) against the RUNNING stack: frontend :5173 -> Python API :8000 -> MySQL
// (+ AI service :8001). Start the API with AUTH_RATE_LIMIT_PER_MINUTE=60 (see README.md), then here: npm test.
// A small Node project of its own, so browser tests of the whole system don't live inside one app.
// Uses the Microsoft Edge already installed on Windows (no browser download); set E2E_BROWSER=chromium
// to use Playwright's own Chromium instead (after `npx playwright install chromium`).
import { defineConfig, devices } from "@playwright/test";

const channel = process.env.E2E_BROWSER === "chromium" ? undefined : "msedge";

export default defineConfig({
  testDir: ".",
  timeout: 30_000,
  expect: { timeout: 10_000 },
  fullyParallel: false,
  // One browser at a time: the tests share the demo accounts (a password change signs the account out everywhere)
  // and the API's per-address sign-in limit, so spec files running in parallel would break each other.
  workers: 1,
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
