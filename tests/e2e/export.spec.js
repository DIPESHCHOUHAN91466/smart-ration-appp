// "Download my data" on Settings (DPDP Act 2023): the file holds the person's own records and no credentials.
// Creates one synthetic citizen per run ("E2E Export <timestamp>").
import { readFile } from "node:fs/promises";
import { expect, test } from "@playwright/test";

const API = (process.env.E2E_API_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
const PASSWORD = "Kite-River-Lamp-42";

test("a citizen downloads their own data from Settings", async ({ page }) => {
  test.setTimeout(60_000);
  const stamp = Date.now();
  const email = `e2e-export-${stamp}@example.com`;
  await page.addInitScript(() => window.localStorage.setItem("smart-ration-language", JSON.stringify({ state: { language: "en" }, version: 0 })));
  const created = await page.request.post(`${API}/api/v1/auth/register`, { data: {
    fullName: `E2E Export ${stamp}`, email, mobileNumber: `6${String(stamp + 7).slice(-9)}`, password: PASSWORD, consentToPrivacyPolicy: true } });
  expect(created.ok(), await created.text()).toBeTruthy();

  await page.goto("/login");
  await page.getByLabel("Email", { exact: true }).fill(email);
  await page.locator('input[type="password"]').fill(PASSWORD);
  await page.locator('button[type="submit"]').click();
  await expect(page).toHaveURL(/\/rural\/dashboard$/, { timeout: 20_000 });

  await page.goto("/settings");
  const downloading = page.waitForEvent("download");
  await page.getByRole("button", { name: "Download my data (JSON)" }).click();
  const file = await downloading;
  expect(file.suggestedFilename()).toMatch(/^smart-ration-my-data-\d{4}-\d{2}-\d{2}\.json$/);
  const text = await readFile(await file.path(), "utf8");
  const data = JSON.parse(text);
  expect(data.account.Email).toBe(email);
  expect(data.beneficiary.BeneficiaryCode).toBeTruthy();
  expect(text).not.toMatch(/\$argon2|PasswordHash|TotpSecret|SRQR-/);
});
