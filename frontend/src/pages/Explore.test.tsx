import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { NwiSummaryResponse } from "../types/api";
import { Explore } from "./Explore";
import { nwiSummaryByQuery } from "../api/client";
import { useUrlDrivenSearch } from "../hooks/useUrlDrivenSearch";

vi.mock("../api/client", () => ({
  nwiSummaryByQuery: vi.fn(),
}));

vi.mock("../hooks/useUrlDrivenSearch", () => ({
  useUrlDrivenSearch: vi.fn(),
}));

vi.mock("../components/MapView", () => ({
  MapView: ({ label }: { label?: string }) => <div data-testid="map-view">{label ?? ""}</div>,
}));

vi.mock("../components/SummaryCards", () => ({
  SummaryCards: () => <div data-testid="summary-cards" />,
}));

const WRIGLEY_FIELD_ADDRESS = "1060 W Addison St, Chicago, IL 60613";

const baseHookState = {
  params: { q: "", radius: 0.5 },
  result: null,
  loading: false,
  error: null,
  validationMessage: null,
  updateDraft: vi.fn(),
  submit: vi.fn(),
};

function makeSummary(): NwiSummaryResponse {
  return {
    schema_version: "1",
    origin: { lat: 41.9484, lon: -87.6553, label: WRIGLEY_FIELD_ADDRESS },
    selected_radius_miles: 0.5,
    search_radius_miles: 0.5,
    min_delta: 0.25,
    counts: { selected_block_groups: 1, context_block_groups: 1 },
    nwi: { mean: 10, min: 8, max: 12, spread: 4 },
    components: {
      employment_housing_mix_rank_mean: 0,
      employment_type_diversity_rank_mean: 0,
      intersection_density_rank_mean: 0,
      transit_proximity_rank_mean_proxy: 0,
    },
    metrics: { everyday_convenience: 0, variation: 0, transit_viability: 0 },
    upgrade_potential: { found: false, candidates: [], selected_mean_nwi: 10, message: "" },
    walkable_island: { is_island: false, label: null, high_threshold: 15.26, low_threshold: 10.51 },
    block_groups: [],
  };
}

function deferred<T>() {
  let resolve: (value: T | PromiseLike<T>) => void = () => {};
  let reject: (reason?: unknown) => void = () => {};
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

describe("Explore page default preload", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useUrlDrivenSearch).mockReturnValue(baseHookState as never);
    vi.mocked(nwiSummaryByQuery).mockResolvedValue(makeSummary());
  });

  it("uses the Wrigley address as the input placeholder", () => {
    render(<Explore />);
    const input = screen.getByLabelText("Address, ZIP, or city");
    expect(input).toHaveAttribute("placeholder");
    expect(input.getAttribute("placeholder")).toContain("1060 W Addison");
  });

  it("preloads once and does not refetch on radius-only draft rerender", async () => {
    const hookState = {
      ...baseHookState,
      params: { q: "", radius: 0.5 },
    };
    vi.mocked(useUrlDrivenSearch).mockImplementation(() => hookState as never);
    const pendingPreload = deferred<NwiSummaryResponse>();
    vi.mocked(nwiSummaryByQuery).mockReturnValueOnce(pendingPreload.promise);

    const { rerender } = render(<Explore />);
    await waitFor(() => expect(nwiSummaryByQuery).toHaveBeenCalledTimes(1));

    hookState.params = { q: "", radius: 2.0 };
    rerender(<Explore />);
    expect(nwiSummaryByQuery).toHaveBeenCalledTimes(1);

    pendingPreload.resolve(makeSummary());
    await waitFor(() => expect(nwiSummaryByQuery).toHaveBeenCalledTimes(1));
  });

  it("retries once after a transient preload failure", async () => {
    vi.mocked(nwiSummaryByQuery)
      .mockRejectedValueOnce(new Error("temporary failure"))
      .mockResolvedValueOnce(makeSummary());

    render(<Explore />);
    await waitFor(() => expect(nwiSummaryByQuery).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(nwiSummaryByQuery).toHaveBeenCalledTimes(2), { timeout: 2500 });
  });
});
