import { test, expect } from "@playwright/test";
import {
  currentSheetSnap,
  fakeSummary,
  installApiMocks,
  waitForMapReady,
  waitForSheetSnap,
} from "./helpers";

/**
 * Mobile-viewport E2E coverage for the Zillow-inspired redesign.
 *
 * Runs under the "mobile" project (Pixel 5 viewport, ~393x851). These
 * tests exercise structural mobile behaviors only — the API is mocked so
 * the suite does not require the FastAPI backend.
 *
 * The ``/nwi/summary`` mock and all deterministic wait primitives live in
 * ``./helpers.ts`` so future flows reuse the same surface and a schema
 * bump only requires touching one file.
 */

// ---------------------------------------------------------------------------
// Drawer (a11y)
// ---------------------------------------------------------------------------

test.describe("Mobile drawer", () => {
  test("hamburger opens the left drawer; Escape closes and restores focus", async ({ page }) => {
    await installApiMocks(page);
    await page.goto("/");

    const toggle = page.getByRole("button", { name: /open menu/i });
    await expect(toggle).toBeVisible();

    const drawer = page.locator("#primary-nav-drawer");

    // Closed: drawer is inert (off-canvas) so its descendants cannot be tabbed to.
    await expect(drawer).toHaveAttribute("inert", "");

    // Open the drawer.
    await toggle.click();
    // Scope to the drawer dialog — the hamburger toggle's aria-label also
    // flips to "Close menu" when open, which would otherwise match.
    await expect(drawer.getByRole("button", { name: /close menu/i })).toBeVisible();
    await expect(drawer).not.toHaveAttribute("inert", /.*/);

    // Drawer holds *secondary* content (Method + external links + attribution),
    // not the primary destinations (those live in the bottom tab bar).
    await expect(drawer.getByRole("link", { name: /method/i })).toBeVisible();
    await expect(drawer.getByRole("link", { name: /github/i })).toBeVisible();

    // Escape closes and focus returns to the toggle.
    await page.keyboard.press("Escape");
    await expect(page.getByRole("button", { name: /open menu/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /open menu/i })).toBeFocused();
    await expect(drawer).toHaveAttribute("inert", "");
  });

  test("focus does not leak into the closed drawer when tabbing", async ({ page }) => {
    await installApiMocks(page);
    await page.goto("/");

    // Focus the hamburger and Tab forward several times. None of the focused
    // elements should belong to the (closed, inert) drawer.
    const toggle = page.getByRole("button", { name: /open menu/i });
    await toggle.focus();
    for (let i = 0; i < 8; i++) {
      await page.keyboard.press("Tab");
      const insideDrawer = await page.evaluate(() => {
        const drawer = document.getElementById("primary-nav-drawer");
        return !!drawer && drawer.contains(document.activeElement);
      });
      expect(insideDrawer).toBe(false);
    }
  });
});

// ---------------------------------------------------------------------------
// Bottom tab bar
// ---------------------------------------------------------------------------

test.describe("Mobile bottom tab bar", () => {
  test("primary destinations are reachable from the tab bar", async ({ page }) => {
    await installApiMocks(page);
    await page.goto("/");

    const tabbar = page.getByRole("navigation", { name: /primary/i });
    await expect(tabbar).toBeVisible();

    // The three primary tabs should be present (Method lives in the drawer).
    await expect(tabbar.getByRole("link", { name: "Explore" })).toBeVisible();
    await expect(tabbar.getByRole("link", { name: "Compare" })).toBeVisible();
    await expect(tabbar.getByRole("link", { name: "Dashboard" })).toBeVisible();

    await tabbar.getByRole("link", { name: "Compare" }).click();
    await expect(page).toHaveURL(/\/compare$/);
  });
});

// ---------------------------------------------------------------------------
// Sticky search & submit (icon + label)
// ---------------------------------------------------------------------------

test.describe("Mobile Explore search", () => {
  test("submit button is an icon + label and meets the 44px touch target", async ({ page }) => {
    await installApiMocks(page);
    await page.goto("/");

    const submit = page.getByRole("button", { name: /search this address/i });
    await expect(submit).toBeVisible();
    await expect(submit).toContainText(/search/i);

    const box = await submit.boundingBox();
    expect(box).not.toBeNull();
    expect(box!.height).toBeGreaterThanOrEqual(44);
  });

  test("submitting renders summary cards", async ({ page }) => {
    await installApiMocks(page);
    await page.goto("/");

    const input = page.getByPlaceholder(/addison/i);
    await expect(input).toBeVisible({ timeout: 15_000 });
    await input.fill("Cambridge, MA");
    await page.getByRole("button", { name: /search this address/i }).click();

    await expect(page.getByText(/everyday convenience/i)).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText(/transit viability/i)).toBeVisible();
  });
});

// ---------------------------------------------------------------------------
// Bottom sheet drag / snap
// ---------------------------------------------------------------------------

test.describe("Mobile bottom sheet", () => {
  test("tapping the handle toggles peek <-> half; dragging snaps to nearest and does not also toggle", async ({ page }) => {
    await installApiMocks(page);
    await page.goto("/");

    const sheet = page.locator(".mobile-sheet");
    await expect(sheet).toBeVisible({ timeout: 15_000 });

    // Initial snap when there's no summary is "peek".
    expect(await currentSheetSnap(page)).toBe("peek");

    const handle = page.locator(".mobile-sheet__handle");

    // Tap (no movement) → toggle peek → half.
    await handle.click();
    await waitForSheetSnap(page, "half");

    // Drag the handle upward by ~250px. There is no longer a "full" snap, so
    // the closest snap point is still "half" — the sheet should stay at half
    // and, importantly, the synthetic click after the drag must NOT toggle
    // it back to peek.
    const box = await handle.boundingBox();
    expect(box).not.toBeNull();
    const startX = box!.x + box!.width / 2;
    const startY = box!.y + box!.height / 2;
    await page.mouse.move(startX, startY);
    await page.mouse.down();
    // Multiple intermediate moves so pointermove fires and didMove flips true.
    await page.mouse.move(startX, startY - 80, { steps: 5 });
    await page.mouse.move(startX, startY - 250, { steps: 10 });
    await page.mouse.up();

    await waitForSheetSnap(page, "half");

    // A second tap should toggle back to peek.
    await handle.click();
    await waitForSheetSnap(page, "peek");
  });
});

// ---------------------------------------------------------------------------
// Map "Search this area"
// ---------------------------------------------------------------------------

test.describe("Mobile map: Search this area", () => {
  test("panning the map shows the pill and tapping it re-runs at the new center", async ({ page }) => {
    await installApiMocks(page);

    // Capture every summary request so we can assert the recenter call.
    const requestedQueries: string[] = [];
    page.on("request", (req) => {
      const u = req.url();
      if (/\/nwi\/summary/.test(u)) {
        const q = new URL(u).searchParams.get("q");
        if (q) requestedQueries.push(q);
      }
    });

    await page.goto("/");
    await waitForMapReady(page);

    // Pan the map. We can't drive Leaflet's drag handler with synthetic
    // mouse events on a touch device profile, so call panBy directly via
    // the dev-only window hook. ``waitForMapReady`` guarantees any
    // programmatic setView from React effects has already settled.
    await page.evaluate(() => {
      type Map = { panBy: (xy: [number, number], opts?: { animate?: boolean }) => void };
      const map = (window as unknown as { __leafletMap: Map }).__leafletMap;
      map.panBy([300, 300], { animate: false });
    });

    // The "Search this area" pill should appear in the map overlay.
    const searchArea = page.getByRole("button", { name: /search this area/i });
    await expect(searchArea).toBeVisible({ timeout: 5_000 });

    requestedQueries.length = 0;  // ignore preload calls
    await searchArea.click();

    // After tapping, a new summary request should fire with a "lat, lon" q.
    await expect.poll(() => requestedQueries.find((q) => /-?\d+\.\d+\s*,\s*-?\d+\.\d+/.test(q)) ?? "", {
      timeout: 5_000,
    }).toMatch(/-?\d+\.\d+\s*,\s*-?\d+\.\d+/);

    // And the pill should disappear since the map is now centered on the query.
    await expect(searchArea).toBeHidden({ timeout: 5_000 });
  });
});

// ---------------------------------------------------------------------------
// Compare layout (mobile reflow — kept from prior coverage)
// ---------------------------------------------------------------------------

test.describe("Mobile Compare layout", () => {
  test("compare results render as stacked, labeled cards (mocked API)", async ({ page }) => {
    const compareSummary = (
      label: string,
      lat: number,
      lon: number,
      metrics: {
        everyday_convenience: number;
        transit_viability: number;
        variation: number;
      },
    ): ReturnType<typeof fakeSummary> => ({
      ...fakeSummary(label, lat, lon),
      metrics,
      nwi: {
        mean: metrics.everyday_convenience,
        min: metrics.everyday_convenience - 2,
        max: metrics.everyday_convenience + 2,
        spread: 4,
      },
      components: {
        employment_housing_mix_rank_mean: metrics.everyday_convenience - 1,
        employment_type_diversity_rank_mean: metrics.everyday_convenience - 0.5,
        intersection_density_rank_mean: metrics.variation + 10,
        transit_proximity_rank_mean_proxy: metrics.transit_viability,
      },
      upgrade_potential: {
        found: false,
        candidates: [],
        selected_mean_nwi: metrics.everyday_convenience,
        message: "No nearby upgrade.",
      },
    });
    await installApiMocks(page, {
      summaryFor: (url) => {
        const q = url.searchParams.get("q") ?? "";
        return /somerville/i.test(q)
          ? compareSummary("Somerville, MA", 42.3876, -71.0995, {
              everyday_convenience: 14.2,
              transit_viability: 13.8,
              variation: 4.1,
            })
          : compareSummary("Cambridge, MA", 42.3736, -71.1097, {
              everyday_convenience: 12.5,
              transit_viability: 11.2,
              variation: 2.4,
            });
      },
    });

    await page.goto("/compare");
    await page.getByPlaceholder(/cambridge/i).first().fill("Cambridge, MA");
    await page.getByPlaceholder(/somerville/i).fill("Somerville, MA");
    await page.getByRole("button", { name: /^compare$/i }).click();

    const table = page.locator(".compare-table");
    await expect(table).toBeVisible({ timeout: 10_000 });

    const labeledCell = page.locator(".compare-table tbody td[data-label]").first();
    await expect(labeledCell).toBeVisible();
    await expect(labeledCell).toHaveAttribute("data-label", /\S+/);
    // Ensure real metric values render (not the null "—" fallback).
    await expect(table).toContainText("12.50");
    await expect(table).toContainText("14.20");
    await expect(table).toContainText("↑ 1.70");

    const firstRow = page.locator(".compare-table tbody tr").first();
    const display = await firstRow.evaluate((el) => getComputedStyle(el).display);
    expect(display).toBe("block");
  });
});
