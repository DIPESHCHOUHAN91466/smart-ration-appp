// Website sessions (security S7): the refresh token is an HttpOnly, SameSite=Strict cookie; no token is ever in
// localStorage; a reload signs back in from the cookie; signing out removes it. Creates one synthetic citizen per run.
import { expect, test } from "@playwright/test";

const API = (process.env.E2E_API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
const PASSWORD = "Kite-River-Lamp-42";

test("the session cookie is HttpOnly, survives a reload, and is removed on sign-out", async ({ page, context }) => {
  test.setTimeout(60_000);
  const stamp = Date.now();
  const email = `e2e-session-${stamp}@example.com`;
  await page.addInitScript(() => window.localStorage.setItem("smart-ration-language", JSON.stringify({ state: { language: "en" }, version: 0 })));
  const created = await page.request.post(`${API}/api/v1/auth/register`, { data: {
    fullName: `E2E Session ${stamp}`, email, mobileNumber: `6${String(stamp).slice(-9)}`, password: PASSWORD, consentToPrivacyPolicy: true } });
  expect(created.ok(), await created.text()).toBeTruthy();

  await page.goto("/login");
  await page.getByLabel("Email", { exact: true }).fill(email);
  await page.locator('input[type="password"]').fill(PASSWORD);
  await page.locator('button[type="submit"]').click();
  await expect(page).toHaveURL(/\/rural\/dashboard$/, { timeout: 20_000 });

  const cookie = (await context.cookies()).find((c) => c.name === "sr_refresh");
  expect(cookie).toBeTruthy();
  expect(cookie.httpOnly).toBe(true);
  expect(cookie.sameSite).toBe("Strict");
  expect(cookie.path).toBe("/api");
  const stored = await page.evaluate(() => JSON.stringify({ ...window.localStorage }));
  expect(stored).not.toContain(cookie.value);
  expect(stored).not.toMatch(/accessToken|refreshToken|eyJ/);          // no token of any kind in storage
  expect(await page.evaluate(() => document.cookie)).not.toContain("sr_refresh");   // invisible to script

  await page.reload();                                                   // memory is gone: the cookie signs back in
  await expect(page).toHaveURL(/\/rural\/dashboard$/);
  const refreshed = page.waitForResponse((r) => r.url().includes("/auth/refresh") && r.status() === 200);
  await page.goto("/settings");
  await refreshed;
  await expect(page.getByLabel("Email")).toHaveValue(email, { timeout: 15_000 });   // profile loaded with the new token

  const lastCookie = (await context.cookies()).find((c) => c.name === "sr_refresh").value;   // rotated by the refresh
  const signedOut = page.waitForResponse((r) => r.url().includes("/auth/logout"));
  await page.locator("button.nav-item", { hasText: "Sign out" }).click();
  await signedOut;
  await expect(page).toHaveURL(/\/login$/);
  expect((await context.cookies()).find((c) => c.name === "sr_refresh")).toBeFalsy();
  const replay = await page.request.post(`${API}/api/v1/auth/refresh`, { data: { refreshToken: lastCookie } });
  expect(replay.status()).toBe(401);                                     // a copied cookie is dead on the server too
});
