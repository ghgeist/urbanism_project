/**
 * Shared configuration for dashboard charts.
 * Centralizes chart styling, colors, and common settings.
 */

import { COMPONENT_INFO, formatComponentLabel } from "./componentLabels";

/**
 * Component color scheme for consistent visualization across charts.
 * Colors chosen for accessibility and visual distinction.
 */
export const COMPONENT_COLORS = {
  d2a: "#8884d8", // Purple - Employment and Household Mix
  d2b: "#82ca9d", // Green - Employment Mix
  d3b: "#ffc658", // Yellow - Intersection Density
  d4a: "#ff7300", // Orange - Transit Proximity
} as const;

/**
 * Get color for a component by its key.
 */
export function getComponentColor(componentKey: "d2a" | "d2b" | "d3b" | "d4a"): string {
  return COMPONENT_COLORS[componentKey];
}

/**
 * Common chart margin configuration.
 */
export const CHART_MARGINS = {
  top: 16,
  right: 24,
  left: 60,
  bottom: 22,
} as const;

/**
 * Shared axis spacing so labels stay readable and uncut on laptop viewports.
 */
export const CHART_AXIS = {
  yAxisWidth: 72,
  xAxisHeight: 44,
  yAxisLabelOffset: 12,
  axisLabelFontSize: 12,
} as const;

/**
 * NWI score domain (1-20 scale).
 */
export const NWI_DOMAIN = [0, 20] as const;

/**
 * WAS score domain (0-30 scale).
 */
export const WAS_DOMAIN = [0, 30] as const;

/**
 * Common chart height configurations.
 */
export const CHART_HEIGHTS = {
  distribution: 320,
  correlation: 300,
  contribution: 280,
  nwiWas: 320,
} as const;

export const CHART_LAYOUT_PRESETS = {
  distribution: {
    margin: {
      ...CHART_MARGINS,
      top: 12,
      right: 12,
      bottom: 28,
    },
    axis: {
      ...CHART_AXIS,
      xAxisHeight: 48,
      yAxisWidth: 76,
    },
  },
  contribution: {
    margin: CHART_MARGINS,
    axis: CHART_AXIS,
  },
  correlation: {
    margin: {
      ...CHART_MARGINS,
      right: 16,
      left: 52,
      bottom: 26,
    },
    axis: {
      ...CHART_AXIS,
      yAxisWidth: 64,
      xAxisHeight: 46,
    },
  },
  nwiWas: {
    margin: {
      ...CHART_MARGINS,
      right: 16,
      left: 54,
      bottom: 34,
    },
    axis: {
      ...CHART_AXIS,
      yAxisWidth: 64,
      xAxisHeight: 52,
    },
  },
} as const;

/**
 * Helper to create component data array for charts.
 * Ensures consistent ordering and structure.
 */
export function createComponentData(summary: {
  components: {
    employment_housing_mix_rank_mean: number | null;
    employment_type_diversity_rank_mean: number | null;
    intersection_density_rank_mean: number | null;
    transit_proximity_rank_mean_proxy: number | null;
  };
}) {
  return [
    {
      key: "d2a" as const,
      component: formatComponentLabel(COMPONENT_INFO.d2a_ranked),
      label: COMPONENT_INFO.d2a_ranked.shortLabel,
      value: summary.components.employment_housing_mix_rank_mean,
      color: COMPONENT_COLORS.d2a,
    },
    {
      key: "d2b" as const,
      component: formatComponentLabel(COMPONENT_INFO.d2b_ranked),
      label: COMPONENT_INFO.d2b_ranked.shortLabel,
      value: summary.components.employment_type_diversity_rank_mean,
      color: COMPONENT_COLORS.d2b,
    },
    {
      key: "d3b" as const,
      component: formatComponentLabel(COMPONENT_INFO.d3b_ranked),
      label: COMPONENT_INFO.d3b_ranked.shortLabel,
      value: summary.components.intersection_density_rank_mean,
      color: COMPONENT_COLORS.d3b,
    },
    {
      key: "d4a" as const,
      component: formatComponentLabel(COMPONENT_INFO.d4a_ranked),
      label: COMPONENT_INFO.d4a_ranked.shortLabel,
      value: summary.components.transit_proximity_rank_mean_proxy,
      color: COMPONENT_COLORS.d4a,
    },
  ];
}
