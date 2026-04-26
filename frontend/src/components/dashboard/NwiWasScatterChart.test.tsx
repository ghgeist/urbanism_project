import { render, screen } from "@testing-library/react";
import type { ReactNode } from "react";
import { describe, expect, it, vi } from "vitest";
import { NwiWasScatterChart } from "./NwiWasScatterChart";
import type { BlockGroupFeature, NwiSummaryResponse } from "../../types/api";

vi.mock("recharts", () => ({
  CartesianGrid: () => null,
  ReferenceLine: () => null,
  ResponsiveContainer: ({ children }: { children: ReactNode }) => (
    <div data-testid="responsive-container">{children}</div>
  ),
  Scatter: ({ name }: { name: string }) => <div data-testid="scatter-series">{name}</div>,
  ScatterChart: ({ children }: { children: ReactNode }) => <div>{children}</div>,
  Tooltip: () => null,
  XAxis: () => null,
  YAxis: () => null,
}));

function blockGroup(overrides: Partial<BlockGroupFeature>): BlockGroupFeature {
  return {
    geoid20: "bg-1",
    natwalkind: 12,
    d2a_ranked: null,
    d2b_ranked: null,
    d3b_ranked: null,
    d4a_ranked: null,
    was_2019: 8,
    geometry: { type: "Point", coordinates: [-71, 42] },
    ...overrides,
  };
}

function summary(blockGroups: BlockGroupFeature[]): NwiSummaryResponse {
  return {
    schema_version: "1",
    origin: { lat: 42.36, lon: -71.06, label: "Cambridge, MA" },
    selected_radius_miles: 0.5,
    search_radius_miles: 1,
    min_delta: 2,
    counts: { selected_block_groups: blockGroups.length, context_block_groups: blockGroups.length },
    nwi: { mean: 12, min: 8, max: 16, spread: 8 },
    was: { mean: 8, min: 2, max: 18, spread: 16 },
    components: {
      employment_housing_mix_rank_mean: null,
      employment_type_diversity_rank_mean: null,
      intersection_density_rank_mean: null,
      transit_proximity_rank_mean_proxy: null,
    },
    metrics: {
      everyday_convenience: 12,
      variation: 2,
      transit_viability: 10,
    },
    amenity_richness: { value: 8, label: "Destination Sparse" },
    upgrade_potential: {
      found: false,
      candidates: [],
      selected_mean_nwi: 12,
      message: "No improvement found.",
    },
    walkable_island: { is_island: false, label: null, high_threshold: 15.26, low_threshold: 10.51 },
    hollow_neighborhood: {
      is_hollow: true,
      label: "Hollow Neighborhood",
      nwi_threshold: 13,
      was_threshold: 10,
    },
    block_groups: blockGroups,
  };
}

describe("NwiWasScatterChart", () => {
  it("shows quadrant counts and hollow candidate count", () => {
    render(
      <NwiWasScatterChart
        summary={summary([
          blockGroup({ natwalkind: 15, was_2019: 20 }),
          blockGroup({ natwalkind: 15, was_2019: 5 }),
          blockGroup({ natwalkind: 8, was_2019: 20 }),
          blockGroup({ natwalkind: 8, was_2019: 5 }),
        ])}
      />
    );

    expect(screen.getByText("Walkability vs Amenities")).toBeInTheDocument();
    expect(screen.getByText(/National Walkability Index \(NWI\) measures built form/)).toBeInTheDocument();
    expect(screen.getByText("Hollow candidates")).toBeInTheDocument();
    expect(screen.getByText("1")).toBeInTheDocument();
    expect(screen.getByText("Higher NWI, more amenities: 1")).toBeInTheDocument();
    expect(screen.getByText("Hollow: 1")).toBeInTheDocument();
    expect(screen.getByText("More amenities, lower NWI: 1")).toBeInTheDocument();
    expect(screen.getByText("Sparse, lower NWI: 1")).toBeInTheDocument();
    expect(screen.getByText(/Colors group block groups/)).toBeInTheDocument();
  });

  it("renders an unavailable state when block groups lack WAS coverage", () => {
    render(<NwiWasScatterChart summary={summary([blockGroup({ was_2019: null })])} />);

    expect(screen.getByText("WAS data is unavailable for the selected block groups.")).toBeInTheDocument();
  });
});
