import { expect, test } from "@playwright/test";
import path from "node:path";

test("case to evidence to finding review to report", async ({ page }) => {
  const number = `E2E-${Date.now()}`;
  await page.goto("/cases/new");
  await page.getByLabel("Case number").fill(number);
  await page.getByLabel("Analyst").fill("Playwright Analyst");
  await page.getByLabel("Case name").fill("Synthetic workflow verification");
  await page.getByLabel("Description").fill("Automated consented synthetic fixture workflow");
  await page.getByRole("button", { name: "Create case" }).click();
  await expect(page.getByRole("heading", { name: "What needs attention" })).toBeVisible();

  await page.getByRole("link", { name: "Evidence", exact: true }).click();
  await page.getByRole("button", { name: "Add evidence" }).first().click();
  await page.locator("#file-upload").setInputFiles([
    path.resolve("../../fixtures/synthetic-case/synthetic-01.jpg"),
    path.resolve("../../fixtures/synthetic-case/synthetic-05.jpg"),
    path.resolve("../../fixtures/synthetic-case/synthetic-06.jpg"),
  ]);
  await page.getByRole("button", { name: /Preserve 3 files/ }).click();
  await expect(page.getByRole("cell", { name: /IMG-0001 synthetic-01.jpg/ })).toBeVisible();
  await expect(page.getByText("Acquisition hash")).toBeVisible();
  await page.getByRole("tab", { name: "Raw" }).click();
  await expect(page.getByText(/DateTimeOriginal/)).toBeVisible();

  await page.getByLabel("Case workspace").getByRole("link", { name: "Findings" }).click();
  await page.getByRole("button", { name: "Run analysis" }).first().click();
  await expect(page.getByText("Editing-software metadata present")).toBeVisible();
  await expect(page.getByText("Embedded timestamps differ beyond the configured threshold")).toBeVisible();
  await page.getByRole("button", { name: "Review finding" }).first().click();
  await page.getByLabel("Review note").fill("Tag presence reviewed; no manipulation claim is made.");
  await page.getByRole("button", { name: "Acknowledge", exact: true }).click();
  await expect(page.getByText("acknowledged").first()).toBeVisible();

  await page.getByRole("link", { name: "Evidence", exact: true }).click();
  await page.getByRole("button", { name: "Verify integrity" }).click();
  await expect(page.getByText("Integrity verification completed")).toBeVisible();

  await page.getByLabel("Case workspace").getByRole("link", { name: "Reports" }).click();
  await page.getByRole("button", { name: "Generate from latest run" }).click();
  await expect(page.getByRole("heading", { name: "IMAGE TRACE report" })).toBeVisible();
  const download = page.waitForEvent("download");
  await page.getByRole("link", { name: "PDF" }).click();
  expect((await download).suggestedFilename()).toMatch(/image-trace-.*\.pdf/);
});
