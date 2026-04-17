import { test, expect } from "@playwright/test";

/**
 * Mobile-viewport E2E coverage for the responsive redesign.
 *
 * These tests run under the "mobile" project (Pixel 5 viewport, ~393x851).
 * They verify the structural mobile behaviors: hamburger nav, fullscreen
 * map, and the Compare table reflowing into stacked, labeled cards.
 *
 * They intentionally do not depend on the FastAPI backend; they exercise
 * what the user can observe purely from the frontend.
 */

test.describe("Mobile navigation", () => {
  test("hamburger toggles the menu and navigates between pages", async ({ page }) => {
    await page.goto("/");

    // The hamburger should be visible on mobile. The accessible name flips
    // between "Open menu" and "Close menu" depending on state, so match either.
    const toggle = page.getByRole("button", { name: /(open|close) menu/i });
    await expect(toggle).toBeVisible();
    await expect(toggle).toHaveAttribute("aria-expanded", "false");

    // Scope the Compare link to the primary nav so we don't accidentally
    // match links that may appear elsewhere on the page.
    const nav = page.getByRole("navigation", { name: /main/i });
    const compareLink = nav.getByRole("link", { name: "Compare" });

    // Desktop nav links should be hidden initially (collapsed menu).
    await expect(compareLink).toBeHidden();

    // Open the menu, see the links, navigate to Compare.
    await toggle.click();
    await expect(toggle).toHaveAttribute("aria-expanded", "true");
    await expect(compareLink).toBeVisible();
    await compareLink.click();

    // After navigation the menu auto-closes and we land on Compare.
    await expect(page).toHaveURL(/\/compare$/);
    await expect(page.getByRole("heading", { name: /compare/i, level: 1 })).toBeVisible();
    await expect(page.getByRole("button", { name: /open menu/i })).toBeVisible();
    await expect(nav.getByRole("link", { name: "Dashboard" })).toBeHidden();
  });
});

test.describe("Mobile Explore form", () => {
  test("inputs and submit button stack to full width", async ({ page }) => {
    await page.goto("/");

    const input = page.getByPlaceholder(/addison/i);
    const submit = page.getByRole("button", { name: /get summary/i });

    await expect(input).toBeVisible();
    await expect(submit).toBeVisible();

    // On a 393px viewport the submit button should span ~full width and
    // meet the 44px touch target.
    const submitBox = await submit.boundingBox();
    expect(submitBox).not.toBeNull();
    if (submitBox) {
      const viewport = page.viewportSize();
      expect(viewport).not.toBeNull();
      expect(submitBox.width).toBeGreaterThan((viewport!.width ?? 0) * 0.7);
      expect(submitBox.height).toBeGreaterThanOrEqual(44);
    }
  });

  test("submitting Explore on a phone renders summary cards (mocked API)", async ({ page }) => {
    // Mock the summary endpoint so we can assert the post-submit state
    // without depending on the FastAPI backend or live geocoding.
    // Also mock /health so the App startup gate opens immediately.
    await page.route(/\/health/, async (route) => {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ ok: true }) });
    });
    await page.route(/\/nwi\/summary/, async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          schema_version: "1.0",
          origin: { lat: 42.3736, lon: -71.1097, label: "Cambridge, MA" },
          selected_radius_miles: 0.5,
          search_radius_miles: 1.5,
          min_delta: 2,
          counts: { selected_block_groups: 5, context_block_groups: 25 },
          nwi: { mean: 13.2, min: 10.0, max: 16.0, spread: 6.0 },
          components: {
            employment_housing_mix_rank_mean: 12.0,
            employment_type_diversity_rank_mean: 11.5,
            intersection_density_rank_mean: 14.0,
            transit_proximity_rank_mean_proxy: 13.0,
          },
          metrics: { everyday_convenience: 13.2, variation: 6.0, transit_viability: 13.0 },
          upgrade_potential: { found: false, candidates: [], selected_mean_nwi: 13.2, message: "No nearby upgrade." },
          walkable_island: { is_island: false, label: null, high_threshold: 15.26, low_threshold: 5.76 },
          block_groups: [],
        }),
      });
    });

    await page.goto("/");
    const input = page.getByPlaceholder(/addison/i);
    await expect(input).toBeVisible({ timeout: 15_000 });
    await input.fill("Cambridge, MA");
    await page.getByRole("button", { name: /get summary/i }).click();

    // After submit, the summary cards should appear (with our mocked metric).
    await expect(page.getByText(/everyday convenience/i)).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText(/transit viability/i)).toBeVisible();
    await expect(page.getByText(/variation/i)).toBeVisible();
  });
});

test.describe("Mobile map fullscreen", () => {
  test("expand button enters fullscreen and ESC exits", async ({ page }) => {
    await page.goto("/");

    const expand = page.getByRole("button", { name: /expand map to fullscreen/i });
    await expect(expand).toBeVisible();
    await expand.click();

    // Toggle should now offer the close affordance.
    const close = page.getByRole("button", { name: /exit fullscreen map/i });
    await expect(close).toBeVisible();
    await expect(close).toHaveAttribute("aria-pressed", "true");

    // Map container should fill the viewport when fullscreen.
    const overlay = page.locator(".map-view--fullscreen");
    await expect(overlay).toBeVisible();
    const viewport = page.viewportSize();
    const overlayBox = await overlay.boundingBox();
    expect(overlayBox).not.toBeNull();
    if (overlayBox && viewport) {
      expect(overlayBox.width).toBeGreaterThanOrEqual(viewport.width - 1);
    }

    // Press Escape to exit fullscreen.
    await page.keyboard.press("Escape");
    await expect(page.getByRole("button", { name: /expand map to fullscreen/i })).toBeVisible();
    await expect(page.locator(".map-view--fullscreen")).toHaveCount(0);
  });
});

test.describe("Mobile Compare layout", () => {
  test("compare form stacks and is usable on a phone viewport", async ({ page }) => {
    await page.goto("/compare");
    const submit = page.getByRole("button", { name: /^compare$/i });
    await expect(submit).toBeVisible();

    const submitBox = await submit.boundingBox();
    expect(submitBox).not.toBeNull();
    if (submitBox) {
      const viewport = page.viewportSize();
      expect(viewport).not.toBeNull();
      expect(submitBox.width).toBeGreaterThan((viewport!.width ?? 0) * 0.7);
      expect(submitBox.height).toBeGreaterThanOrEqual(44);
    }
  });

  test("compare results render as stacked, labeled cards (mocked API)", async ({ page }) => {
    // Mock the summary endpoint so we can verify the table-as-cards layout
    // without needing the FastAPI backend or live geocoding.
    const fakeSummary = (label: string, lat: number, lon: number) => ({
      origin: { lat, lon, label, geocoder: "mock", confidence: 1 },
      area: { selected_radius_miles: 0.5, n_block_groups: 1, total_population: 1000, area_sq_miles: 0.79 },
      metrics: {
        nwi_mean: 12.5,
        nwi_p25: 11.0,
        nwi_p50: 12.5,
        nwi_p75: 14.0,
        nwi_min: 10.0,
        nwi_max: 15.0,
        intersections_per_sqmi: 80,
        d3a_mean: 80,
        d2a_jobpop_mean: 0.5,
        d2b_e8mixa_mean: 0.4,
        d4a_mean: 30,
        pct_high_walk: 0.3,
        pct_low_walk: 0.1,
      },
      block_groups: [],
      upgrade_potential: { found: false, candidates: [] },
    });
    await page.route(/\/nwi\/summary/, async (route) => {
      const url = new URL(route.request().url());
      const q = url.searchParams.get("q") ?? "";
      const isB = /somerville/i.test(q);
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(
          isB
            ? fakeSummary("Somerville, MA", 42.3876, -71.0995)
            : fakeSummary("Cambridge, MA", 42.3736, -71.1097),
        ),
      });
    });

    await page.goto("/compare");
    await page.getByPlaceholder(/cambridge/i).first().fill("Cambridge, MA");
    await page.getByPlaceholder(/somerville/i).fill("Somerville, MA");
    await page.getByRole("button", { name: /^compare$/i }).click();

    // The compare table should render and reflow into stacked cards.
    const table = page.locator(".compare-table");
    await expect(table).toBeVisible({ timeout: 10_000 });

    // On the mobile viewport, table headers are visually hidden but
    // value cells expose their column label via data-label.
    const labeledCell = page.locator(".compare-table tbody td[data-label]").first();
    await expect(labeledCell).toBeVisible();
    await expect(labeledCell).toHaveAttribute("data-label", /\S+/);

    // Each row should render as a block (card), not as a horizontal table row.
    const firstRow = page.locator(".compare-table tbody tr").first();
    const display = await firstRow.evaluate((el) => getComputedStyle(el).display);
    expect(display).toBe("block");
  });
});
