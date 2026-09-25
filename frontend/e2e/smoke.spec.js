// Smoke tests of the real stack. Nothing here signs in or types a password: only public pages, the
// chatbot, the login form's presence and the protected-route redirect are exercised.
import { expect, test } from "@playwright/test";

let pageErrors;
let serverErrors;

test.beforeEach(async ({ page }) => {
  pageErrors = [];
  serverErrors = [];
  page.on("pageerror", (error) => pageErrors.push(error.message));
  page.on("response", (response) => {
    if (response.status() >= 500) serverErrors.push(`${response.status()} ${response.url()}`);
  });
  // Start every test in English: clear the saved language once per tab (sessionStorage survives reloads,
  // so a test's own reload still sees the language it chose).
  await page.addInitScript(() => {
    if (!window.sessionStorage.getItem("e2e-started")) {
      window.localStorage.removeItem("smart-ration-language");
      window.sessionStorage.setItem("e2e-started", "1");
    }
  });
});

test.afterEach(() => {
  expect(pageErrors, "uncaught errors in the page").toEqual([]);
  expect(serverErrors, "server errors (5xx)").toEqual([]);
});

test("landing page shows the Ration Mitra brand and the main message", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Your ration, on time");
  await expect(page.locator(".pub-header").getByText("Ration Mitra")).toBeVisible();
  await expect(page.getByRole("link", { name: "Skip to main content" })).toHaveAttribute("href", "#main");
});

test("language switch: English -> Hindi -> Marathi, and it survives a reload", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("combobox", { name: "Language" })).toBeVisible();   // English label first
  const language = page.getByRole("combobox").first();                          // its label changes with the language
  await language.selectOption("hi");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("आपका राशन");
  await expect(page.locator("html")).toHaveAttribute("lang", "hi");
  await language.selectOption("mr");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("तुमचे रेशन");
  await page.reload();
  await expect(page.getByRole("heading", { level: 1 })).toContainText("तुमचे रेशन");
  await language.selectOption("en");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Your ration, on time");
});

test("public help loads its topics from the API and answers one", async ({ page }) => {
  const categories = page.waitForResponse((r) => r.url().includes("/api/public-help/categories") && r.status() === 200);
  await page.goto("/help");
  await categories;
  const category = page.getByRole("button", { name: /^Required Documents/ });
  await expect(category).toContainText("1 topic");          // singular: "1 topics" was a bug
  await category.click();
  await expect(category).toHaveAttribute("aria-expanded", "true");
  const article = page.waitForResponse((r) => r.url().includes("/api/public-help/") && !r.url().includes("categories") && r.status() === 200);
  await page.locator(`#${await category.getAttribute("aria-controls")}`).getByRole("button").first().click();
  await article;
  await expect(page.getByText(/aadhaar/i).first()).toBeVisible();
});

test("chatbot answers a question through the real API and refuses an Aadhaar-like number", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: /open ration mitra ai assistant/i }).click();
  const dialog = page.getByRole("dialog", { name: "Ration Mitra AI Assistant" });
  await expect(dialog).toBeVisible();
  const input = dialog.getByRole("textbox");

  const answer = page.waitForResponse((r) => r.url().includes("/api/chatbot/message") && r.status() === 200);
  await input.fill("which documents do I need for a ration card?");
  await input.press("Enter");
  const body = await (await answer).json();
  expect(body.data.kind).toBe("answer");
  await expect(dialog.getByText(body.data.text.split("\n")[0]).first()).toBeVisible();

  const refusal = page.waitForResponse((r) => r.url().includes("/api/chatbot/message"));
  await input.fill("my aadhaar is 1234 5678 9012");
  await input.press("Enter");
  expect((await (await refusal).json()).data.kind).toBe("sensitive_input");
});

test("a protected page sends a signed-out visitor to the login page", async ({ page }) => {
  await page.goto("/rural/dashboard");
  await expect(page).toHaveURL(/\/login$/);
  await expect(page.locator('input[type="email"]')).toBeVisible();
  await expect(page.locator('input[type="password"]')).toBeVisible();
  await expect(page.locator(".login-brand")).toContainText("Ration Mitra");
});

test("status page reports every service", async ({ page }) => {
  await page.goto("/status");
  const table = page.getByRole("table");
  await expect(table.getByRole("row", { name: /^Python API/ })).toContainText(/healthy|ok/i);
  await expect(table.getByRole("row", { name: /^C# API/ })).toBeVisible();
});

test("an unknown address shows the not-found page", async ({ page }) => {
  await page.goto("/this-page-does-not-exist");
  await expect(page.getByText("Page not found")).toBeVisible();
  await page.getByRole("link", { name: "Go back home" }).click();
  await expect(page).toHaveURL(/\/$/);
});
