import { afterEach, describe, expect, it, vi } from "vitest";
import { geocode, health, nwiSummaryByQuery } from "./client";

describe("client", () => {
  const baseUrl = "http://127.0.0.1:8000";

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  /** Client uses res.text() then JSON.parse; mock must provide text(). */
  function mockRes(body: unknown, ok = true): { ok: boolean; text: () => Promise<string> } {
    return {
      ok,
      text: () => Promise.resolve(JSON.stringify(body)),
    };
  }

  it("health() calls /health and returns status", async () => {
    const mockFetch = vi.fn().mockResolvedValue(mockRes({ status: "ok" }));
    vi.stubGlobal("fetch", mockFetch);

    const result = await health();

    expect(mockFetch).toHaveBeenCalledWith(`${baseUrl}/health`, undefined);
    expect(result).toEqual({ status: "ok" });
  });

  it("geocode() builds URL with query param", async () => {
    const body = { lat: 42.36, lon: -71.06, label: "Cambridge, MA" };
    const mockFetch = vi.fn().mockResolvedValue(mockRes(body));
    vi.stubGlobal("fetch", mockFetch);

    const result = await geocode("Cambridge, MA");

    const expectedUrl = new URL("/geocode", baseUrl);
    expectedUrl.searchParams.set("q", "Cambridge, MA");
    expect(mockFetch).toHaveBeenCalledWith(expectedUrl.toString(), undefined);
    expect(result).toEqual(body);
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
      components: {
        employment_housing_mix_rank_mean: null,
        employment_type_diversity_rank_mean: null,
        intersection_density_rank_mean: null,
        transit_proximity_rank_mean_proxy: null,
      },
      metrics: { everyday_convenience: 12, variation: 2, transit_viability: 10 },
      upgrade_potential: { found: false, candidates: [], selected_mean_nwi: 12, message: "None" },
      walkable_island: { is_island: false, label: null, high_threshold: 14, low_threshold: 10 },
    };
    const mockFetch = vi.fn().mockResolvedValue(mockRes(summary));
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

  it("throws with mapped user message when res.ok is false and code is known", async () => {
    const mockFetch = vi.fn().mockResolvedValue(
      mockRes({ code: "location_not_found", message: "Location not found." }, false)
    );
    vi.stubGlobal("fetch", mockFetch);

    await expect(geocode("nowhere")).rejects.toThrow(
      "Location not found. Check your address and try again."
    );
  });

  it("throws with mapped message for http_404 (unhandled HTTPException)", async () => {
    const mockFetch = vi.fn().mockResolvedValue(
      mockRes({ code: "http_404", message: "Not Found" }, false)
    );
    vi.stubGlobal("fetch", mockFetch);

    await expect(geocode("x")).rejects.toThrow(
      "Location not found. Check your address and try again."
    );
  });

  it("throws with backend message for unknown code, generic for non-JSON", async () => {
    const mockFetch = vi.fn().mockResolvedValue(
      mockRes({ code: "unknown_code", message: "Backend detail." }, false)
    );
    vi.stubGlobal("fetch", mockFetch);

    await expect(geocode("x")).rejects.toThrow("Backend detail.");
  });

  it("throws generic message when error response is not JSON", async () => {
    const mockFetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      text: () => Promise.resolve("Internal error"),
    });
    vi.stubGlobal("fetch", mockFetch);

    await expect(geocode("x")).rejects.toThrow("Request failed (500).");
  });
});
