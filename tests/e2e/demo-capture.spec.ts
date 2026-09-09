import { expect, test } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

const frameDir = path.resolve(process.env.DEMO_FRAME_DIR ?? "../../work/demo-frames");
fs.mkdirSync(frameDir, { recursive: true });

test.use({ viewport: { width: 1440, height: 900 }, colorScheme: "dark" });

test("capture IMAGE TRACE walkthrough frames", async ({ page }) => {
  const capture = async (name: string) => {
    await page.waitForTimeout(900);
    await page.screenshot({ path: path.join(frameDir, `${name}.png`), fullPage: true });
  };

  await page.goto("/cases");
  await expect(page.getByRole("heading", { name: "Your investigations" })).toBeVisible();
  await capture("01-case-registry");

  await page.locator('a[href^="/cases/"]').first().click();
  await expect(page.getByRole("heading", { name: "What needs attention" })).toBeVisible();
  await capture("02-overview");

  await page.getByRole("link", { name: "Evidence", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Inventory & inspection" })).toBeVisible();
  await capture("03-evidence");
  await page.getByRole("tab", { name: "Raw" }).click();
  await expect(page.getByText(/DateTimeOriginal/)).toBeVisible();
  await capture("04-raw-metadata");

  await page.getByRole("navigation", { name: "Case workspace" }).getByRole("link", { name: "Findings" }).click();
  await expect(page.getByRole("heading", { name: "Explainable findings" })).toBeVisible();
  await capture("05-findings");

  await page.getByRole("navigation", { name: "Case workspace" }).getByRole("link", { name: "Map & route" }).click();
  await expect(page.getByRole("heading", { name: "Map & derived route" })).toBeVisible();
  await capture("06-map-route");

  await page.getByRole("navigation", { name: "Case workspace" }).getByRole("link", { name: "Reports" }).click();
  await expect(page.getByRole("heading", { name: "Versioned reports" })).toBeVisible();
  await capture("07-reports");
});
