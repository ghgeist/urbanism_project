import { afterEach, describe, expect, it, vi } from "vitest";
import { geocode, health, nwiSummaryByQuery } from "./client";

describe("client", () => {
  const baseUrl = "http://127.0.0.1:8000";

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("health() calls /health and returns status", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ status: "ok" }),
    });
    vi.stubGlobal("fetch", mockFetch);

    const result = await health();

    expect(mockFetch).toHaveBeenCalledWith(`${baseUrl}/health`);
    expect(result).toEqual({ status: "ok" });
  });

  it("geocode() builds URL with query param", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ lat: 42.36, lon: -71.06, label: "Cambridge, MA" }),
    });
    vi.stubGlobal("fetch", mockFetch);

    const result = await geocode("Cambridge, MA");

    const expectedUrl = new URL("/geocode", baseUrl);
    expectedUrl.searchParams.set("q", "Cambridge, MA");
    expect(mockFetch).toHaveBeenCalledWith(expectedUrl.toString());
    expect(result).toEqual({ lat: 42.36, lon: -71.06, label: "Cambridge, MA" });
  });

  it("nwiSummaryByQuery() builds URL with required and optional params", async () => {
    const summary = {
      schema_version: "1",
      origin: { lat: 42.36, lon: -71.06, label: "Cambridge, MA" },
      selected_radius_miles: 0.5,
      search_radius_miles: 1,
      min_delta: 2,
      counts: { selected_block_groups: 5, context_block_groups: 10 },
      nwi: { mean: 12, min: 8, max: 16, spread: 8 },
      components: {},
      metrics: { everyday_convenience: 12, variation: 2, transit_viability: 10 },
      upgrade_potential: { found: false, candidates: [], selected_mean_nwi: 12, message: "None" },
      walkable_island: { is_island: false, label: null, high_threshold: 14, low_threshold: 10 },
    };
    const mockFetch = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(summary),
    });
    vi.stubGlobal("fetch", mockFetch);

    const result = await nwiSummaryByQuery("Cambridge, MA", 0.5, {
      search_radius_miles: 1,
      min_delta: 2.5,
      top_n: 5,
    });

    const callUrl = (mockFetch.mock.calls[0] as string[])[0];
    expect(callUrl).toContain("/nwi/summary/by-query");
    expect(callUrl).toContain("q=Cambridge%2C+MA");
    expect(callUrl).toContain("selected_radius_miles=0.5");
    expect(callUrl).toContain("search_radius_miles=1");
    expect(callUrl).toContain("min_delta=2.5");
    expect(callUrl).toContain("top_n=5");
    expect(result.schema_version).toBe("1");
    expect(result.origin.label).toBe("Cambridge, MA");
  });

  it("throws with API error message when res.ok is false", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 404,
      json: () => Promise.resolve({ code: "location_not_found", message: "Location not found." }),
    });
    vi.stubGlobal("fetch", mockFetch);

    await expect(geocode("nowhere")).rejects.toThrow("Location not found.");
  });
});
