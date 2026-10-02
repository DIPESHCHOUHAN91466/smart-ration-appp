// Signed-in journeys: each role signs in through the real login form and opens every page of its area.
// Every page must render a heading without uncaught errors, server errors (5xx) or failed API calls (4xx).
// Browser console errors are attached to the report (they don't fail the test unless they break the page).
//
// Needs the demo accounts' password in E2E_DEMO_PASSWORD (never committed; the local README one, or the deployment's
// SEED_DEMO_PASSWORD). Without it these tests are skipped.
import { expect, test } from "@playwright/test";

const PASSWORD = process.env.E2E_DEMO_PASSWORD;

const ROLES = [
  {
    role: "citizen",
    email: process.env.E2E_CITIZEN_EMAIL || "rural@example.com",
    home: "/rural/dashboard",
    pages: ["/rural/dashboard", "/rural/book", "/rural/history", "/rural/verification", "/rural/notifications", "/settings", "/help"],
  },
  {
    role: "shop owner",
    email: process.env.E2E_SHOP_EMAIL || "shop@example.com",
    home: "/shop/dashboard",
    pages: ["/shop/dashboard", "/shop/queue", "/shop/inventory", "/shop/scanner", "/shop/notifications", "/settings"],
  },
  {
    role: "official",
    email: process.env.E2E_OFFICIAL_EMAIL || "officer@example.com",
    home: "/gov/dashboard",
    pages: ["/gov/dashboard", "/gov/statistics", "/gov/shops", "/gov/inventory", "/gov/bookings", "/gov/map", "/gov/ai",
      "/gov/reports", "/gov/audit", "/gov/users", "/gov/notifications", "/settings"],
  },
];

test.describe.configure({ mode: "serial" });

for (const { role, email, home, pages } of ROLES) {
  test(`${role}: signs in and every page of the area works`, async ({ page }, testInfo) => {
    test.skip(!PASSWORD, "E2E_DEMO_PASSWORD not set");
    const problems = [];
    const consoleErrors = [];
    page.on("pageerror", (error) => problems.push(`uncaught: ${error.message}`));
    page.on("console", (message) => {
      if (message.type() === "error") consoleErrors.push(`${page.url()}: ${message.text()}`);
    });
    page.on("response", (response) => {
      const url = response.url();
      if (response.status() >= 500) problems.push(`${response.status()} ${url}`);
      else if (response.status() >= 400 && url.includes("/api/")) problems.push(`${response.status()} ${url}`);
    });
    await page.addInitScript(() => window.localStorage.setItem("smart-ration-language", "en"));

    await page.goto("/login");
    await page.locator('input[type="email"]').fill(email);
    await page.locator('input[type="password"]').fill(PASSWORD);
    await page.locator('button[type="submit"]').click();
    await expect(page).toHaveURL(new RegExp(`${home}$`), { timeout: 20_000 });

    for (const path of pages) {
      await page.goto(path);
      await page.waitForLoadState("networkidle");
      await expect(page, `${path} stays in the area (no redirect to login)`).not.toHaveURL(/\/login$/);
      await expect(page.locator("h1, h2").first(), `${path} shows a heading`).toBeVisible();
      await expect(page.getByText(/something went wrong/i), `${path} shows no error screen`).toHaveCount(0);
    }
    if (consoleErrors.length) await testInfo.attach("console errors", { body: consoleErrors.join("\n"), contentType: "text/plain" });
    expect(problems, "page errors, server errors or failed API calls").toEqual([]);
  });
}

test("a signed-in citizen cannot open the official area", async ({ page }) => {
  test.skip(!PASSWORD, "E2E_DEMO_PASSWORD not set");
  await page.goto("/login");
  await page.locator('input[type="email"]').fill(ROLES[0].email);
  await page.locator('input[type="password"]').fill(PASSWORD);
  await page.locator('button[type="submit"]').click();
  await expect(page).toHaveURL(/\/rural\/dashboard$/, { timeout: 20_000 });
  await page.goto("/gov/dashboard");
  await expect(page).not.toHaveURL(/\/gov\/dashboard$/);
});

test("a wrong password shows an error and does not sign in", async ({ page }) => {
  await page.goto("/login");
  await page.locator('input[type="email"]').fill(ROLES[0].email);
  await page.locator('input[type="password"]').fill("definitely-not-the-password");
  await page.locator('button[type="submit"]').click();
  await expect(page.getByRole("alert").first()).toBeVisible({ timeout: 10_000 });
  await expect(page).toHaveURL(/\/login$/);
});
