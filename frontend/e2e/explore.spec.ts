import { test, expect } from "@playwright/test";

/**
 * Quick E2E smoke: Explore page loads and shows search form.
 * Does not require the FastAPI backend. For full flow (search → summary),
 * start the API and run manually or add a test that skips when API is down.
 */
test.describe("Explore page", () => {
  test("loads and shows Explore heading and Get summary button", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("heading", { name: /explore/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /get summary/i })).toBeVisible();
  });

  test("has search input and radius slider", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByPlaceholder(/addison/i)).toBeVisible();
    await expect(page.getByLabel(/radius/i)).toBeVisible();
  });

  test("search yields either summary cards or error (requires API for success)", async ({ page }) => {
    await page.goto("/");
    await page.getByPlaceholder(/addison/i).fill("Cambridge, MA");
    await page.getByRole("button", { name: /get summary/i }).click();
    // Within 15s we should see either success (cards) or error (alert)
    const cards = page.getByText("Everyday Convenience");
    const alert = page.getByRole("alert");
    await expect(cards.or(alert)).toBeVisible({ timeout: 15_000 });
  });
});
