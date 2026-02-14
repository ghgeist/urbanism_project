import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { SummaryCards } from "./SummaryCards";
import type { NwiSummaryResponse } from "../types/api";

function minimalSummary(overrides: Partial<NwiSummaryResponse> = {}): NwiSummaryResponse {
  return {
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
    metrics: {
      everyday_convenience: 12.5,
      variation: 2.1,
      transit_viability: 10.0,
    },
    upgrade_potential: {
      found: false,
      candidates: [],
      selected_mean_nwi: 12.5,
      message: "No improvement found within search radius.",
    },
    walkable_island: { is_island: false, label: null, high_threshold: 14, low_threshold: 10 },
    ...overrides,
  };
}

describe("SummaryCards", () => {
  it("renders four card labels", () => {
    render(<SummaryCards summary={minimalSummary()} />);
    expect(screen.getByText("Everyday Convenience")).toBeInTheDocument();
    expect(screen.getByText("Transit Viability")).toBeInTheDocument();
    expect(screen.getByText("Variation")).toBeInTheDocument();
    expect(screen.getByText("Upgrade Potential")).toBeInTheDocument();
  });

  it("displays metric values from summary", () => {
    render(<SummaryCards summary={minimalSummary()} />);
    expect(screen.getByText("12.50")).toBeInTheDocument();
    expect(screen.getByText("2.10")).toBeInTheDocument();
    expect(screen.getByText("10.00")).toBeInTheDocument();
  });

  it("shows upgrade message when no candidates", () => {
    render(<SummaryCards summary={minimalSummary()} />);
    expect(screen.getByText("No improvement found within search radius.")).toBeInTheDocument();
  });

  it("shows best nearby delta when upgrade_potential has candidates", () => {
    const summary = minimalSummary({
      upgrade_potential: {
        found: true,
        candidates: [
          { geoid20: "123", natwalkind: 15, dist_miles: 0.3, delta_nwi: 2.5 },
        ],
        selected_mean_nwi: 12.5,
        message: "",
      },
    });
    render(<SummaryCards summary={summary} />);
    expect(screen.getByText("+2.5")).toBeInTheDocument();
  });

  it("shows neutral deltas vs baseline when diffFrom and diffLabel are set", () => {
    const baseline = minimalSummary({
      metrics: { everyday_convenience: 12, transit_viability: 10, variation: 2 },
    });
    const summary = minimalSummary({
      metrics: { everyday_convenience: 12.5, transit_viability: 9, variation: 2 },
    });
    render(<SummaryCards summary={summary} diffFrom={baseline} diffLabel="A" />);
    expect(screen.getByText("+0.50 vs A")).toBeInTheDocument();
    expect(screen.getByText("-1.00 vs A")).toBeInTheDocument();
    expect(screen.getByText("same as A")).toBeInTheDocument();
  });
});
