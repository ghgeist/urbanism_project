import { describe, expect, it } from "vitest";
import {
  buildNwiWasPoints,
  classifyNwiWasPoint,
  countNwiWasQuadrants,
  type NwiWasThresholds,
} from "./nwiWasAnalytics";
import type { BlockGroupFeature } from "../types/api";

const thresholds: NwiWasThresholds = {
  highNwiThreshold: 13,
  lowWasThreshold: 10,
};

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

describe("NWI/WAS analytics", () => {
  it("classifies each quadrant using NWI and WAS thresholds", () => {
    expect(classifyNwiWasPoint(15, 20, thresholds)).toBe("walkableDestinations");
    expect(classifyNwiWasPoint(15, 5, thresholds)).toBe("hollowNeighborhood");
    expect(classifyNwiWasPoint(8, 20, thresholds)).toBe("destinationRichLowerNwi");
    expect(classifyNwiWasPoint(8, 5, thresholds)).toBe("sparseLowerNwi");
  });

  it("builds points only when both NWI and WAS are present", () => {
    const points = buildNwiWasPoints(
      [
        blockGroup({ geoid20: "A", natwalkind: 15, was_2019: 5 }),
        blockGroup({ geoid20: "B", natwalkind: null, was_2019: 12 }),
        blockGroup({ geoid20: "C", natwalkind: 12, was_2019: null }),
      ],
      thresholds
    );

    expect(points).toEqual([{ geoid20: "A", nwi: 15, was: 5, quadrant: "hollowNeighborhood" }]);
  });

  it("counts points by quadrant", () => {
    const points = buildNwiWasPoints(
      [
        blockGroup({ natwalkind: 15, was_2019: 20 }),
        blockGroup({ natwalkind: 15, was_2019: 5 }),
        blockGroup({ natwalkind: 8, was_2019: 20 }),
        blockGroup({ natwalkind: 8, was_2019: 5 }),
      ],
      thresholds
    );

    expect(countNwiWasQuadrants(points)).toEqual({
      walkableDestinations: 1,
      hollowNeighborhood: 1,
      destinationRichLowerNwi: 1,
      sparseLowerNwi: 1,
    });
  });
});
