// Registration on the website asks for informed consent (DPDP Act 2023) and links to the Privacy Policy.
// Creates one synthetic citizen account per run ("E2E Consent <timestamp>").
import { expect, test } from "@playwright/test";

test("registration needs the privacy consent; with it the citizen is registered and signed in", async ({ page }) => {
  test.setTimeout(60_000);   // password hashing for a new account is deliberately slow
  const stamp = Date.now();
  await page.addInitScript(() => window.localStorage.setItem("smart-ration-language", JSON.stringify({ state: { language: "en" }, version: 0 })));
  await page.goto("/register");
  await expect(page.getByRole("link", { name: /Read the Privacy Policy/ })).toHaveAttribute("href", "/privacy");

  await page.getByLabel("Full name", { exact: true }).fill(`E2E Consent ${stamp}`);
  await page.getByLabel("Email", { exact: true }).fill(`e2e-consent-${stamp}@example.com`);
  await page.getByLabel("Mobile number", { exact: true }).fill(`8${String(stamp).slice(-9)}`);
  const password = `E2e-${stamp}-pass`;
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByLabel("Confirm password", { exact: true }).fill(password);

  const consent = page.getByRole("checkbox", { name: /I agree that my information is used/ });
  await expect(consent).not.toBeChecked();
  await page.locator('button[type="submit"]').click();
  await expect(page).toHaveURL(/\/register$/);                   // not registered without consent

  await consent.check();
  await page.locator('button[type="submit"]').click();
  await expect(page).toHaveURL(/\/rural\/dashboard$/, { timeout: 20_000 });
});
