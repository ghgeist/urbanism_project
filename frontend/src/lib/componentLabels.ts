/**
 * Component labels and descriptions for NWI components.
 * Based on EPA National Walkability Index methodology.
 */

export interface ComponentInfo {
  code: string;
  shortLabel: string;
  fullLabel: string;
  description: string;
}

export const COMPONENT_INFO: Record<string, ComponentInfo> = {
  d2a_ranked: {
    code: "D2A",
    shortLabel: "Employment & Household Mix",
    fullLabel: "Employment and Household Mix",
    description: "The mix of employment types and occupied housing. A block group with diverse employment types (office, retail, service) plus many occupied housing units will have a higher score.",
  },
  d2b_ranked: {
    code: "D2B",
    shortLabel: "Employment Mix",
    fullLabel: "Employment Type Diversity",
    description: "The mix of employment types in a block group (retail, office, industrial). Higher values indicate greater diversity of employment types.",
  },
  d3b_ranked: {
    code: "D3B",
    shortLabel: "Intersection Density",
    fullLabel: "Street Intersection Density",
    description: "The density of street intersections. Higher intersection density is correlated with more walk trips and better street connectivity.",
  },
  d4a_ranked: {
    code: "D4A",
    shortLabel: "Transit Proximity",
    fullLabel: "Proximity to Transit Stops",
    description: "Distance from population center to nearest transit stop. Shorter distances (higher scores) correlate with more walk trips.",
  },
};

export function getComponentInfo(componentKey: string): ComponentInfo | undefined {
  return COMPONENT_INFO[componentKey];
}

export function getComponentLabel(componentKey: string, useFull = false): string {
  const info = COMPONENT_INFO[componentKey];
  if (!info) return componentKey;
  return useFull ? info.fullLabel : info.shortLabel;
}
