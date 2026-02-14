import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { CompareTable } from "./CompareTable";
import type { NwiSummaryResponse } from "../types/api";

// Helper to create mock summary data
const createMockSummary = (label: string, metrics: { everyday: number; transit: number; variation: number }, upgradeFound = false): NwiSummaryResponse => ({
  schema_version: "1.0",
  origin: { lat: 42.0, lon: -71.0, label },
  selected_radius_miles: 1.0,
  search_radius_miles: 2.0,
  min_delta: 0.5,
  counts: { selected_block_groups: 10, context_block_groups: 100 },
  nwi: { mean: 10, min: 5, max: 15, spread: 2 },
  components: {
    employment_housing_mix_rank_mean: 10,
    employment_type_diversity_rank_mean: 10,
    intersection_density_rank_mean: 10,
    transit_proximity_rank_mean_proxy: 10,
  },
  metrics: {
    everyday_convenience: metrics.everyday,
    transit_viability: metrics.transit,
    variation: metrics.variation,
  },
  upgrade_potential: {
    found: upgradeFound,
    candidates: upgradeFound
      ? [{ geoid20: "123", natwalkind: 15, dist_miles: 1.5, delta_nwi: 2.5 }]
      : [],
    selected_mean_nwi: 10,
    message: upgradeFound ? "Found" : "None found",
  },
  walkable_island: { is_island: false, label: null, high_threshold: 14, low_threshold: 8 },
});

describe("CompareTable", () => {
  const summaryA = createMockSummary("City A", { everyday: 10.0, transit: 5.0, variation: 2.0 });
  const summaryB = createMockSummary("City B", { everyday: 12.0, transit: 5.0, variation: 1.5 });

  it("renders metric rows correctly", () => {
    render(<CompareTable summaryA={summaryA} summaryB={summaryB} />);
    
    // Check for metric labels
    expect(screen.getByText("Everyday Convenience")).toBeInTheDocument();
    expect(screen.getByText("Transit Viability")).toBeInTheDocument();
    expect(screen.getByText("Variation")).toBeInTheDocument();

    // Check for values
    expect(screen.getByText("10.00")).toBeInTheDocument(); // A Everyday
    expect(screen.getByText("12.00")).toBeInTheDocument(); // B Everyday
  });

  it("calculates and displays positive difference correctly", () => {
    render(<CompareTable summaryA={summaryA} summaryB={summaryB} />);
    // B (12) - A (10) = +2.00
    const diff = screen.getByText((content, element) => {
        return element?.textContent === "↑ 2.00" && element?.className.includes("diff-positive");
    });
    expect(diff).toBeInTheDocument();
  });

  it("calculates and displays negative difference correctly", () => {
    render(<CompareTable summaryA={summaryA} summaryB={summaryB} />);
    // B (1.5) - A (2.0) = -0.50
    const diff = screen.getByText((content, element) => {
        return element?.textContent === "↓ 0.50" && element?.className.includes("diff-negative");
    });
    expect(diff).toBeInTheDocument();
  });

  it("displays neutral dash for small differences", () => {
    // Both have transit 5.0
    render(<CompareTable summaryA={summaryA} summaryB={summaryB} />);
    
    // There should be a neutral dash in the transit row
    // We look for a dash with the neutral class
    const dashes = screen.getAllByText("—");
    const neutralDash = dashes.find(el => el.classList.contains("diff-neutral"));
    expect(neutralDash).toBeInTheDocument();
  });

  it("handles Upgrade Potential comparison", () => {
    // A has none, B has none -> "Same"
    const { rerender } = render(<CompareTable summaryA={summaryA} summaryB={summaryB} />);
    expect(screen.getByText("Same")).toBeInTheDocument();

    // A has none, B has one
    const summaryBWithUpgrade = createMockSummary("City B", { everyday: 12, transit: 5, variation: 1.5 }, true);
    rerender(<CompareTable summaryA={summaryA} summaryB={summaryBWithUpgrade} />);
    
    expect(screen.getByText("None")).toBeInTheDocument(); // A
    expect(screen.getByText("+2.5 available")).toBeInTheDocument(); // B
    
    // Should NOT say "Same"
    expect(screen.queryByText("Same")).not.toBeInTheDocument();
  });

  it("renders null when props are missing", () => {
    const { container } = render(<CompareTable summaryA={null} summaryB={null} />);
    expect(container).toBeEmptyDOMElement();
  });
});
