import { test, expect } from "@playwright/test";

/**
 * E2E smoke: Compare page loads and shows form; submit yields two panels or error.
 * Does not require the FastAPI backend for load/form tests. For full flow (compare → panels),
 * start the API and run manually or rely on timeout for cards/alert.
 */
test.describe("Compare page", () => {
  test("loads and shows Compare heading and Compare button", async ({ page }) => {
    await page.goto("/compare");
    await expect(page.getByRole("heading", { name: /compare/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /^compare$/i })).toBeVisible();
  });

  test("has Location A and B inputs and radius slider", async ({ page }) => {
    await page.goto("/compare");
    await expect(page.getByLabel(/location a/i)).toBeVisible();
    await expect(page.getByLabel(/location b/i)).toBeVisible();
    await expect(page.getByLabel(/radius/i)).toBeVisible();
  });

  test("compare yields either two summary panels or error (requires API for success)", async ({
    page,
  }) => {
    await page.goto("/compare");
    await page.getByPlaceholder(/cambridge/i).first().fill("Cambridge, MA");
    await page.getByPlaceholder(/somerville/i).fill("Somerville, MA");
    await page.getByRole("button", { name: /^compare$/i }).click();
    // Within 15s we should see either success (two panels with "Everyday Convenience") or error (alert)
    const firstPanelCards = page.getByText("Everyday Convenience").first();
    const alert = page.getByRole("alert");
    await expect(firstPanelCards.or(alert)).toBeVisible({ timeout: 15_000 });
  });
});
