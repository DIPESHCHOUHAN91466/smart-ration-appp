// Forgotten password (code to the registered mobile) and changing the password on Settings.
// Creates one synthetic citizen per run ("E2E Reset <timestamp>"). The reset step reads the development demo code
// shown on screen, so it runs only against a development backend (skipped where demo codes are off).
import { expect, test } from "@playwright/test";

const FIRST = "Kite-River-Lamp-42";
const RESET = "Monsoon-Tea-At-Five";
const CHANGED = "Quiet-Harbour-Bell-7";
// The API for direct calls: the local stack runs it on :8000; a single-origin deployment sets E2E_API_URL to the site.
const API = (process.env.E2E_API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");

test("a citizen resets a forgotten password, signs in, and changes it on Settings", async ({ page }) => {
  test.setTimeout(90_000);   // several Argon2 hashes
  const stamp = Date.now();
  const email = `e2e-reset-${stamp}@example.com`;
  const mobile = `7${String(stamp).slice(-9)}`;
  await page.addInitScript(() => window.localStorage.setItem("smart-ration-language", JSON.stringify({ state: { language: "en" }, version: 0 })));

  const created = await page.request.post(`${API}/api/v1/auth/register`,
    { data: { fullName: `E2E Reset ${stamp}`, email, mobileNumber: mobile, password: FIRST, consentToPrivacyPolicy: true } });
  expect(created.ok(), await created.text()).toBeTruthy();

  await page.goto("/login");
  await page.getByRole("link", { name: "Forgot password?" }).click();
  await expect(page).toHaveURL(/\/forgot-password$/);
  await page.getByLabel("Mobile number", { exact: true }).fill(mobile);
  await page.getByRole("button", { name: /Send code/ }).click();
  await expect(page.getByRole("status")).toContainText("a 6-digit code has been sent");
  const demo = page.getByText(/Demo code \(development only\)/);
  test.skip(!(await demo.isVisible()), "the backend does not show demo codes (not development)");
  const code = (await demo.locator("b").textContent()).trim();

  await page.getByLabel("6-digit code").fill(code);
  await page.getByLabel("New password", { exact: true }).fill("password1234");     // a common password is refused ...
  await page.getByLabel("Confirm password", { exact: true }).fill("password1234");
  await page.getByRole("button", { name: /Set new password/ }).click();
  await expect(page.getByRole("alert")).toContainText("too common");
  await page.getByLabel("New password", { exact: true }).fill(RESET);             // ... and the same code still works
  await page.getByLabel("Confirm password", { exact: true }).fill(RESET);
  await page.getByRole("button", { name: /Set new password/ }).click();
  await expect(page).toHaveURL(/\/login$/, { timeout: 20_000 });

  await page.getByLabel("Email", { exact: true }).fill(email);
  await page.locator('input[type="password"]').fill(RESET);
  await page.locator('button[type="submit"]').click();
  await expect(page).toHaveURL(/\/rural\/dashboard$/, { timeout: 20_000 });

  await page.goto("/settings");
  await page.getByLabel("Current password").fill(RESET);
  await page.getByLabel("New password", { exact: true }).fill(CHANGED);
  await page.getByLabel("Confirm password", { exact: true }).fill(CHANGED);
  await page.getByRole("button", { name: "Change password" }).click();
  await expect(page.getByText("Password changed. Other devices have been signed out.")).toBeVisible({ timeout: 20_000 });

  const signIn = await page.request.post(`${API}/api/v1/auth/login`, { data: { email, password: CHANGED } });
  expect(signIn.ok()).toBeTruthy();
});
