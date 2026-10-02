// GIGW policy pages: reachable from every public page's footer, in English, Hindi and Marathi, keyboard-reachable.
import { expect, test } from "@playwright/test";

const PAGES = [
  { link: "Privacy Policy", path: "/privacy", hi: "गोपनीयता नीति", mr: "गोपनीयता धोरण" },
  { link: "Terms of Use", path: "/terms", hi: "उपयोग की शर्तें", mr: "वापराच्या अटी" },
  { link: "Accessibility Statement", path: "/accessibility", hi: "सुगम्यता वक्तव्य", mr: "सुलभता निवेदन" },
];

for (const { link, path, hi, mr } of PAGES) {
  test(`footer link "${link}" opens the page, in all three languages`, async ({ page }) => {
    const errors = [];
    page.on("pageerror", (e) => errors.push(e.message));
    await page.addInitScript(() => window.localStorage.setItem("smart-ration-language", JSON.stringify({ state: { language: "en" }, version: 0 })));
    await page.goto("/");
    await page.getByRole("contentinfo").getByRole("link", { name: link }).click();
    await expect(page).toHaveURL(new RegExp(`${path}$`));
    await expect(page.getByRole("heading", { level: 1 })).toHaveText(link);

    const language = page.getByRole("combobox").first();
    await language.selectOption("hi");
    await expect(page.getByRole("heading", { level: 1 })).toHaveText(hi);
    await language.selectOption("mr");
    await expect(page.getByRole("heading", { level: 1 })).toHaveText(mr);
    expect(errors).toEqual([]);
  });
}

test("footer Contact link lands on the contact section", async ({ page }) => {
  await page.goto("/privacy");
  await page.getByRole("contentinfo").getByRole("link", { name: "Contact" }).click();
  await expect(page).toHaveURL(/\/#contact$/);
  await expect(page.locator("#contact")).toBeVisible();
});
