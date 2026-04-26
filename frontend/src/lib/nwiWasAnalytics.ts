import type { BlockGroupFeature } from "../types/api";

export const DEFAULT_HIGH_NWI_THRESHOLD = 13;
export const DEFAULT_LOW_WAS_THRESHOLD = 10;

export type NwiWasQuadrant =
  | "walkableDestinations"
  | "hollowNeighborhood"
  | "destinationRichLowerNwi"
  | "sparseLowerNwi";

export interface NwiWasThresholds {
  highNwiThreshold: number;
  lowWasThreshold: number;
}

export interface NwiWasPoint {
  geoid20: string | null;
  nwi: number;
  was: number;
  quadrant: NwiWasQuadrant;
}

export const NWI_WAS_QUADRANT_INFO: Record<NwiWasQuadrant, { label: string; shortLabel: string; color: string }> = {
  walkableDestinations: {
    label: "Higher NWI + more amenities",
    shortLabel: "Higher NWI, more amenities",
    color: "#2563eb",
  },
  hollowNeighborhood: {
    label: "Hollow Neighborhood",
    shortLabel: "Hollow",
    color: "#d97706",
  },
  destinationRichLowerNwi: {
    label: "More amenities, lower NWI",
    shortLabel: "More amenities, lower NWI",
    color: "#16a34a",
  },
  sparseLowerNwi: {
    label: "Lower NWI + sparse amenities",
    shortLabel: "Sparse, lower NWI",
    color: "#64748b",
  },
};

export function classifyNwiWasPoint(
  nwi: number,
  was: number,
  thresholds: NwiWasThresholds
): NwiWasQuadrant {
  const highNwi = nwi >= thresholds.highNwiThreshold;
  const lowWas = was <= thresholds.lowWasThreshold;

  if (highNwi && lowWas) {
    return "hollowNeighborhood";
  }
  if (highNwi) {
    return "walkableDestinations";
  }
  if (!lowWas) {
    return "destinationRichLowerNwi";
  }
  return "sparseLowerNwi";
}

export function buildNwiWasPoints(
  blockGroups: BlockGroupFeature[],
  thresholds: NwiWasThresholds
): NwiWasPoint[] {
  return blockGroups
    .filter((blockGroup) => blockGroup.natwalkind != null && blockGroup.was_2019 != null)
    .map((blockGroup) => {
      const nwi = blockGroup.natwalkind as number;
      const was = blockGroup.was_2019 as number;
      return {
        geoid20: blockGroup.geoid20,
        nwi,
        was,
        quadrant: classifyNwiWasPoint(nwi, was, thresholds),
      };
    });
}

export function countNwiWasQuadrants(points: NwiWasPoint[]): Record<NwiWasQuadrant, number> {
  return points.reduce<Record<NwiWasQuadrant, number>>(
    (counts, point) => {
      counts[point.quadrant] += 1;
      return counts;
    },
    {
      walkableDestinations: 0,
      hollowNeighborhood: 0,
      destinationRichLowerNwi: 0,
      sparseLowerNwi: 0,
    }
  );
}
