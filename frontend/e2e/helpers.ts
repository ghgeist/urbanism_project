import { expect, type Page, type Route } from "@playwright/test";

/**
 * Shared E2E helpers: API mocks and deterministic waits for the Leaflet map
 * and the mobile bottom sheet.
 *
 * Keeping the ``/nwi/summary`` mock here (rather than duplicated per spec)
 * means adding a field to ``NwiSummaryResponse`` only requires updating one
 * file — and the backend contract test
 * (``tests/test_schema_contract.py``) catches renames across the wire.
 */

/** Partial override type for the mocked summary payload. */
export type SummaryOverrides = Partial<ReturnType<typeof fakeSummary>>;

/** Canonical stable summary used by every mocked search. */
export function fakeSummary(label: string, lat: number, lon: number) {
  return {
    schema_version: "1.0",
    origin: { lat, lon, label },
    selected_radius_miles: 0.5,
    search_radius_miles: 1.5,
    min_delta: 2,
    counts: { selected_block_groups: 5, context_block_groups: 25 },
    nwi: { mean: 13.2, min: 10.0, max: 16.0, spread: 6.0 },
    was: { mean: 18.0, min: 12.0, max: 24.0, spread: 12.0 },
    components: {
      employment_housing_mix_rank_mean: 12.0,
      employment_type_diversity_rank_mean: 11.5,
      intersection_density_rank_mean: 14.0,
      transit_proximity_rank_mean_proxy: 13.0,
    },
    metrics: { everyday_convenience: 13.2, variation: 6.0, transit_viability: 13.0 },
    amenity_richness: { value: 18.0, label: "Moderate Amenity Access" as const },
    upgrade_potential: {
      found: false,
      candidates: [] as Array<{
        geoid20: string | null;
        natwalkind: number | null;
        dist_miles: number | null;
        delta_nwi: number | null;
      }>,
      selected_mean_nwi: 13.2,
      message: "No nearby upgrade.",
    },
    walkable_island: { is_island: false, label: null, high_threshold: 15.26, low_threshold: 5.76 },
    hollow_neighborhood: { is_hollow: false, label: null, nwi_threshold: 13, was_threshold: 10 },
    block_groups: [] as Array<unknown>,
  };
}

/**
 * Build a summary payload resolver that echoes the ``q`` parameter back
 * as ``origin.label`` and parses ``"lat, lon"`` queries into coordinates
 * (so the "Search this area" re-submit test can assert center changes).
 */
function defaultSummaryResolver(url: URL) {
  const q = url.searchParams.get("q") ?? "Wrigley Field";
  const m = q.match(/^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$/);
  const lat = m ? parseFloat(m[1]) : 41.9484;
  const lon = m ? parseFloat(m[2]) : -87.6553;
  return fakeSummary(q, lat, lon);
}

/**
 * Install ``/health`` and ``/nwi/summary`` mocks. Optional ``summaryFor``
 * lets a spec return a custom payload per request (e.g. two-address
 * Compare flow) without having to re-implement the URL-parsing boilerplate.
 */
export async function installApiMocks(
  page: Page,
  options?: {
    summaryFor?: (url: URL) => ReturnType<typeof fakeSummary>;
  },
): Promise<void> {
  const resolveSummary = options?.summaryFor ?? defaultSummaryResolver;

  await page.route(/\/health/, (route: Route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ ok: true }),
    }),
  );
  await page.route(/\/nwi\/summary/, (route: Route) => {
    const url = new URL(route.request().url());
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(resolveSummary(url)),
    });
  });
}

// ---------------------------------------------------------------------------
// Leaflet map readiness
// ---------------------------------------------------------------------------

type LeafletMapHandle = {
  panBy: (xy: [number, number], opts?: { animate?: boolean }) => void;
  getCenter: () => { lat: number; lng: number };
  once: (event: string, cb: () => void) => void;
};

/**
 * Wait for the Leaflet map to be initialized, tiles attribution visible, and
 * any in-flight programmatic ``setView`` animation settled.
 *
 * Replaces brittle ``waitForTimeout(300)`` patterns: we detect the stable
 * state by polling ``map.getCenter()`` twice and requiring two identical
 * reads before returning. If the map keeps moving, the assertion retries
 * until the Playwright timeout — same failure mode, but with actionable
 * output instead of a silent "it was still animating" race.
 */
export async function waitForMapReady(page: Page): Promise<void> {
  await expect(
    page.locator(".map-view__container .leaflet-control-attribution"),
  ).toBeVisible({ timeout: 20_000 });

  await page.waitForFunction(() => {
    return Boolean((window as unknown as { __leafletMap?: unknown }).__leafletMap);
  });

  // Two consecutive identical centre reads means no animation is running.
  await expect
    .poll(
      async () => {
        return page.evaluate(() => {
          const map = (window as unknown as { __leafletMap?: LeafletMapHandle }).__leafletMap;
          if (!map) return null;
          const c = map.getCenter();
          return `${c.lat.toFixed(6)},${c.lng.toFixed(6)}`;
        });
      },
      {
        message: "Waiting for Leaflet map centre to stabilize (no in-flight setView)",
        timeout: 5_000,
      },
    )
    // Second read: by the time poll sees the same value twice, Leaflet has
    // finished animating. ``.toBeTruthy()`` is our fallback (non-null).
    .toBeTruthy();
}

// ---------------------------------------------------------------------------
// Mobile bottom-sheet transitions
// ---------------------------------------------------------------------------

/**
 * Return the current snap modifier ("peek" | "half") on the sheet.
 *
 * Re-exported so specs can assert on it without duplicating the DOM lookup.
 */
export async function currentSheetSnap(page: Page): Promise<string | null> {
  return page.evaluate(() => {
    const el = document.querySelector(".mobile-sheet");
    if (!el) return null;
    const m = el.className.match(/mobile-sheet--(peek|half)/);
    return m ? m[1] : null;
  });
}

/**
 * Wait for the sheet to reach the given snap AND for the height CSS
 * transition to finish, so subsequent ``boundingBox()`` reads reflect the
 * post-snap position of the handle.
 *
 * Replaces ``waitForTimeout(250)`` (CSS transition is 0.18s): we listen to
 * the actual ``transitionend`` event, with a short safety timeout in case
 * the element was already at the target height (no transition fires).
 */
export async function waitForSheetSnap(page: Page, snap: "peek" | "half"): Promise<void> {
  const sheet = page.locator(".mobile-sheet");
  await expect(sheet).toHaveClass(new RegExp(`mobile-sheet--${snap}`));

  await page.evaluate(() => {
    return new Promise<void>((resolve) => {
      const el = document.querySelector(".mobile-sheet");
      if (!el) {
        resolve();
        return;
      }
      // The height transition is the only one we care about; bail out of
      // the wait as soon as any transition on this element completes.
      const onEnd = () => {
        el.removeEventListener("transitionend", onEnd);
        resolve();
      };
      el.addEventListener("transitionend", onEnd);
      // Safety net: if the sheet was already at the target height no
      // transition will fire. Resolve after one animation frame + a small
      // slack so the test still makes progress.
      requestAnimationFrame(() => setTimeout(resolve, 50));
    });
  });
}
