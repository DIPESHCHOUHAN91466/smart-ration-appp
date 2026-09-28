// Phone-size checks (Pixel 7 viewport): the layout must not scroll sideways and the menu must work.
import { expect, test } from "@playwright/test";

test("landing page fits a phone screen and the menu opens", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow).toBeLessThanOrEqual(0);
  await page.getByRole("button", { name: /menu/i }).click();
  await expect(page.getByRole("navigation", { name: "Mobile" })).toBeVisible();
});

test("chatbot opens as a bottom sheet on a phone", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("button", { name: /open ration mitra ai assistant/i }).click();
  const dialog = page.getByRole("dialog", { name: "Ration Mitra AI Assistant" });
  await expect(dialog).toBeVisible();
  const box = await dialog.boundingBox();
  const width = page.viewportSize().width;
  expect(box.width).toBeGreaterThan(width * 0.9);
});
