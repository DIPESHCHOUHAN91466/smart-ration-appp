// Automated WCAG 2.1 A/AA checks (axe-core, the engine behind Lighthouse's accessibility audit) on the public pages
// and, with E2E_DEMO_PASSWORD, every signed-in page of each role. Automated tools find roughly a third of WCAG issues:
// a manual audit with screen readers and keyboard-only use is still required (COMPLIANCE_CHECKLIST.md).
//
// Fails on "serious" or "critical" violations; "moderate"/"minor" ones are attached to the report.
import AxeBuilder from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

const PASSWORD = process.env.E2E_DEMO_PASSWORD;
const TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"];

// Each test scans several pages with a full axe analysis: give it room (the default is 30 s for one action-sized test).
test.describe.configure({ timeout: 120_000 });

const PUBLIC = ["/", "/help", "/login", "/register", "/privacy", "/terms", "/accessibility"];
const SIGNED_IN = [
  { email: process.env.E2E_CITIZEN_EMAIL || "rural@example.com",
    pages: ["/rural/dashboard", "/rural/book", "/rural/history", "/rural/verification", "/rural/complaints", "/rural/notifications", "/settings"] },
  { email: process.env.E2E_SHOP_EMAIL || "shop@example.com",
    pages: ["/shop/dashboard", "/shop/queue", "/shop/inventory", "/shop/scanner"] },
  { email: process.env.E2E_OFFICIAL_EMAIL || "officer@example.com",
    pages: ["/gov/dashboard", "/gov/statistics", "/gov/shops", "/gov/inventory", "/gov/complaints", "/gov/reports", "/gov/audit"] },
];

async function scan(page, path, testInfo) {
  await page.goto(path);
  await page.waitForLoadState("networkidle");
  const { violations } = await new AxeBuilder({ page }).withTags(TAGS).analyze();
  const lines = violations.map((v) => `${path} [${v.impact}] ${v.id}: ${v.help} (${v.nodes.length}x) e.g. ${v.nodes[0]?.target?.join(" ")}`);
  if (lines.length) await testInfo.attach(`axe ${path}`, { body: lines.join("\n"), contentType: "text/plain" });
  return violations.filter((v) => v.impact === "serious" || v.impact === "critical").map((v) => `${path}: ${v.id} (${v.nodes.length}x) ${v.help}`);
}

test("public pages: no serious or critical WCAG 2.1 AA violations", async ({ page }, testInfo) => {
  await page.addInitScript(() => window.localStorage.setItem("smart-ration-language", JSON.stringify({ state: { language: "en" }, version: 0 })));
  const serious = [];
  for (const path of PUBLIC) serious.push(...(await scan(page, path, testInfo)));
  expect(serious).toEqual([]);
});

for (const { email, pages } of SIGNED_IN) {
  test(`signed-in pages (${email.split("@")[0]}): no serious or critical WCAG 2.1 AA violations`, async ({ page }, testInfo) => {
    test.skip(!PASSWORD, "E2E_DEMO_PASSWORD not set");
    await page.addInitScript(() => window.localStorage.setItem("smart-ration-language", JSON.stringify({ state: { language: "en" }, version: 0 })));
    await page.goto("/login");
    await page.locator('input[type="email"]').fill(email);
    await page.locator('input[type="password"]').fill(PASSWORD);
    await page.locator('button[type="submit"]').click();
    await page.waitForURL(/\/(rural|shop|gov)\//, { timeout: 20_000 });
    const serious = [];
    for (const path of pages) serious.push(...(await scan(page, path, testInfo)));
    expect(serious).toEqual([]);
  });
}
