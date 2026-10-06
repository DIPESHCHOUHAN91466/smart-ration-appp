// Two-factor sign-in (TOTP) for staff, in the browser: set up on Settings, sign in with password + code, turn off.
// Needs a staff account whose password the test may use: E2E_STAFF_EMAIL + E2E_STAFF_PASSWORD (never committed).
// Leaves two-factor sign-in OFF again at the end. Skipped without them.
import { createHmac } from "node:crypto";
import { expect, test } from "@playwright/test";

const EMAIL = process.env.E2E_STAFF_EMAIL;
const PASSWORD = process.env.E2E_STAFF_PASSWORD;

// RFC 6238 TOTP (SHA-1, 6 digits, 30 s): what an authenticator app computes from the base32 secret.
function totp(secretBase32, stepOffset = 0) {
  const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567";
  let bits = "";
  for (const ch of secretBase32.replace(/=+$/, "")) bits += alphabet.indexOf(ch).toString(2).padStart(5, "0");
  const key = Buffer.from(bits.match(/.{8}/g).map((b) => parseInt(b, 2)));
  const counter = Buffer.alloc(8);
  counter.writeBigUInt64BE(BigInt(Math.floor(Date.now() / 30000) + stepOffset));
  const hmac = createHmac("sha1", key).update(counter).digest();
  const offset = hmac[hmac.length - 1] & 0xf;
  return String((hmac.readUInt32BE(offset) & 0x7fffffff) % 1_000_000).padStart(6, "0");
}

async function signIn(page) {
  await page.goto("/login");
  await page.getByLabel("Email", { exact: true }).fill(EMAIL);
  await page.locator('input[type="password"]').fill(PASSWORD);
  await page.locator('button[type="submit"]').click();
}

test("staff turn on two-factor sign-in, sign in with a code, and turn it off", async ({ page }) => {
  test.skip(!EMAIL || !PASSWORD, "E2E_STAFF_EMAIL / E2E_STAFF_PASSWORD not set");
  test.setTimeout(90_000);
  await page.addInitScript(() => window.localStorage.setItem("smart-ration-language", JSON.stringify({ state: { language: "en" }, version: 0 })));

  await signIn(page);
  await page.waitForURL((url) => !url.pathname.startsWith("/login"), { timeout: 20_000 });
  await page.goto("/settings");
  const card = page.locator("section.panel", { has: page.getByRole("heading", { name: "Two-factor sign-in" }) });
  await card.getByLabel("Current password").fill(PASSWORD);
  await card.getByRole("button", { name: "Set up two-factor sign-in" }).click();
  await expect(card.getByRole("img", { name: "QR code for the authenticator app" })).toBeVisible();
  const secret = (await card.locator("code").textContent()).trim();
  await card.getByLabel("6-digit code from the authenticator app").fill(totp(secret));
  await card.getByRole("button", { name: "Turn on" }).click();
  await expect(card.getByText("Two-factor sign-in is on.", { exact: true })).toBeVisible();

  // A new sign-in: the password alone is not enough.
  await page.context().clearCookies();
  await page.evaluate(() => window.localStorage.removeItem("smart-ration-auth"));
  await signIn(page);
  await expect(page.getByText("Enter the 6-digit code from your authenticator app.")).toBeVisible();
  await expect(page).toHaveURL(/\/login$/);
  await page.getByLabel("6-digit code from the authenticator app").fill("000000");
  await page.locator('button[type="submit"]').click();
  await expect(page.getByRole("alert").filter({ hasText: "The code is wrong" }).first()).toBeVisible();
  await page.getByLabel("6-digit code from the authenticator app").fill(totp(secret, 1));   // the next step (the current one was used)
  await page.locator('button[type="submit"]').click();
  await page.waitForURL((url) => !url.pathname.startsWith("/login"), { timeout: 20_000 });

  // Turn it off again (password + a code from a later step), leaving the account as it was.
  await page.goto("/settings");
  await card.getByLabel("Current password").fill(PASSWORD);
  await page.waitForTimeout(31_000);   // a code from a step after the one just used
  await card.getByLabel("6-digit code from the authenticator app").fill(totp(secret, 1));
  await card.getByRole("button", { name: "Turn off two-factor sign-in" }).click();
  await expect(card.getByRole("button", { name: "Set up two-factor sign-in" })).toBeVisible({ timeout: 15_000 });
});
