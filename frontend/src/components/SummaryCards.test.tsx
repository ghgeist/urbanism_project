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
    block_groups: [],
    ...overrides,
  };
}

describe("SummaryCards", () => {
  it("renders five card labels including Amenity Richness", () => {
    render(<SummaryCards summary={minimalSummary()} />);
    expect(screen.getByText("Everyday Convenience")).toBeInTheDocument();
    expect(screen.getByText("Transit Viability")).toBeInTheDocument();
    expect(screen.getByText("Variation")).toBeInTheDocument();
    expect(screen.getByText("Amenity Richness")).toBeInTheDocument();
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

  it("labels WAS-aware upgrade candidates with amenity improvement", () => {
    const summary = minimalSummary({
      upgrade_potential: {
        found: true,
        mode: "nwi_and_was",
        selected_mean_nwi: 12.5,
        selected_mean_was: 10,
        min_delta_was: 2,
        candidates: [
          {
            geoid20: "123",
            natwalkind: 15,
            was_2019: 13,
            dist_miles: 0.3,
            delta_nwi: 2.5,
            delta_was: 3,
          },
        ],
        message: "",
      },
    });
    render(<SummaryCards summary={summary} />);
    expect(screen.getByText("NWI + amenities (+3.0 WAS) · 0.3 mi away")).toBeInTheDocument();
  });

  it("shows amenity richness value and label when WAS data is available", () => {
    const summary = minimalSummary({
      amenity_richness: { value: 17.5, label: "Moderate Amenity Access" },
    });
    render(<SummaryCards summary={summary} />);
    expect(screen.getByText("17.50")).toBeInTheDocument();
    expect(screen.getByText("Moderate Amenity Access")).toBeInTheDocument();
  });

  it("shows graceful fallback when amenity richness is unavailable", () => {
    const summary = minimalSummary({
      amenity_richness: { value: null, label: "Unavailable" },
    });
    render(<SummaryCards summary={summary} />);
    // Amenity Richness label still renders; value shows as em-dash.
    expect(screen.getByText("Amenity Richness")).toBeInTheDocument();
    expect(screen.getByText("WAS 2019 data unavailable for this area")).toBeInTheDocument();
  });
});
